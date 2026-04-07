import os
import uuid
import json
import threading
import pika

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://bookstore:bookstore@rabbitmq:5672/")


def get_connection():
    """Create a new RabbitMQ blocking connection."""
    params = pika.URLParameters(RABBITMQ_URL)
    params.heartbeat = 600
    params.blocked_connection_timeout = 300
    return pika.BlockingConnection(params)


def rpc_call(queue: str, message: dict, timeout: int = 30) -> dict | None:
    """
    Send a command to a queue and wait for a reply using the RabbitMQ RPC pattern.
    Returns the parsed JSON reply, or None on timeout.
    """
    connection = get_connection()
    channel = connection.channel()

    # Create an exclusive, auto-delete reply queue
    result = channel.queue_declare(queue="", exclusive=True, auto_delete=True)
    reply_queue = result.method.queue

    correlation_id = str(uuid.uuid4())
    response_holder = {}
    event = threading.Event()

    def on_response(ch, method, props, body):
        if props.correlation_id == correlation_id:
            response_holder["data"] = json.loads(body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            event.set()

    channel.basic_consume(queue=reply_queue, on_message_callback=on_response)

    channel.basic_publish(
        exchange="",
        routing_key=queue,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            reply_to=reply_queue,
            correlation_id=correlation_id,
            content_type="application/json",
            delivery_mode=2,  # persistent
        ),
    )

    # Poll for the response
    deadline = timeout
    while deadline > 0 and not event.is_set():
        connection.process_data_events(time_limit=1)
        deadline -= 1

    connection.close()
    return response_holder.get("data")


def publish_command(queue: str, message: dict) -> None:
    """Fire-and-forget publish to a queue (for compensation commands)."""
    connection = get_connection()
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=queue,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
        ),
    )
    connection.close()
