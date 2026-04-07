import os
import json
import logging
import threading
import django

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://bookstore:bookstore@rabbitmq:5672/")

PAYMENT_QUEUE = "saga.reserve_payment"
COMPENSATE_QUEUE = "saga.compensate_payment"


def _run_consumer():
    """Background thread: consume payment saga commands from RabbitMQ."""
    import pika
    import django
    from django.db import connection as db_conn

    # Ensure Django is set up before accessing models
    django.setup()

    while True:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            params.heartbeat = 600
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            channel.queue_declare(queue=PAYMENT_QUEUE, durable=True)
            channel.queue_declare(queue=COMPENSATE_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)

            def on_reserve_payment(ch, method, props, body):
                from payments.models import Payment
                try:
                    data = json.loads(body)
                    payment = Payment.objects.create(
                        order_id=data["order_id"],
                        customer_id=data["customer_id"],
                        amount=data["amount"],
                        method=data.get("method", "cod"),
                        status="completed",
                    )
                    reply = {"success": True, "payment_id": payment.id}
                except Exception as exc:
                    logger.error("Payment reservation failed: %s", exc)
                    reply = {"success": False, "error": str(exc)}

                ch.basic_publish(
                    exchange="",
                    routing_key=props.reply_to,
                    properties=pika.BasicProperties(correlation_id=props.correlation_id),
                    body=json.dumps(reply),
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)

            def on_compensate_payment(ch, method, props, body):
                from payments.models import Payment
                try:
                    data = json.loads(body)
                    Payment.objects.filter(id=data["payment_id"]).update(status="refunded")
                    logger.info("Compensated payment %s", data["payment_id"])
                except Exception as exc:
                    logger.error("Payment compensation failed: %s", exc)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=PAYMENT_QUEUE, on_message_callback=on_reserve_payment)
            channel.basic_consume(queue=COMPENSATE_QUEUE, on_message_callback=on_compensate_payment)

            logger.info("Pay-service saga consumer started.")
            channel.start_consuming()

        except Exception as exc:
            logger.error("Pay saga consumer error, retrying in 5s: %s", exc)
            import time
            time.sleep(5)


def start_consumer():
    """Start the saga consumer in a daemon thread."""
    t = threading.Thread(target=_run_consumer, daemon=True, name="pay-saga-consumer")
    t.start()
