import os
import json
import logging
import threading

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://bookstore:bookstore@rabbitmq:5672/")

SHIPPING_QUEUE = "saga.reserve_shipping"


def _run_consumer():
    """Background thread: consume shipping saga commands from RabbitMQ."""
    import pika
    import django

    django.setup()

    while True:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            params.heartbeat = 600
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            channel.queue_declare(queue=SHIPPING_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)

            def on_reserve_shipping(ch, method, props, body):
                from shipping.models import Shipment
                try:
                    data = json.loads(body)
                    shipment = Shipment.objects.create(
                        order_id=data["order_id"],
                        customer_id=data["customer_id"],
                        address=data["address"],
                        method=data.get("method", "standard"),
                        status="pending",
                    )
                    reply = {"success": True, "shipping_id": shipment.id}
                except Exception as exc:
                    logger.error("Shipping reservation failed: %s", exc)
                    reply = {"success": False, "error": str(exc)}

                ch.basic_publish(
                    exchange="",
                    routing_key=props.reply_to,
                    properties=pika.BasicProperties(correlation_id=props.correlation_id),
                    body=json.dumps(reply),
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=SHIPPING_QUEUE, on_message_callback=on_reserve_shipping)

            logger.info("Ship-service saga consumer started.")
            channel.start_consuming()

        except Exception as exc:
            logger.error("Ship saga consumer error, retrying in 5s: %s", exc)
            import time
            time.sleep(5)


def start_consumer():
    """Start the saga consumer in a daemon thread."""
    t = threading.Thread(target=_run_consumer, daemon=True, name="ship-saga-consumer")
    t.start()
