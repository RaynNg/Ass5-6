from .rabbitmq import rpc_call, publish_command

PAYMENT_QUEUE = "saga.reserve_payment"
SHIPPING_QUEUE = "saga.reserve_shipping"
COMPENSATE_PAYMENT_QUEUE = "saga.compensate_payment"


class OrderSagaOrchestrator:
    """
    Orchestrates the order creation saga:
      1. Order is created with status=pending (done by caller)
      2. Reserve payment  → pay-service via RabbitMQ RPC
      3. Reserve shipping → ship-service via RabbitMQ RPC
      4. Confirm order    → status=confirmed
      5. Compensate on failure (refund payment, cancel order)
    """

    def execute(self, order, order_items, customer_id, payment_method, shipping_method, shipping_address):
        """
        Run the saga. Returns (order, error_message).
        On success error_message is None.
        On failure the order status is set to 'failed' and error_message describes what went wrong.
        """
        total = float(order.total_amount)

        # ── Step 2: Reserve Payment ────────────────────────────────────────────
        payment_result = self._reserve_payment(order, customer_id, payment_method, total)
        if not payment_result or not payment_result.get("success"):
            order.status = "failed"
            order.save(update_fields=["status"])
            reason = (payment_result or {}).get("error", "No response from pay-service")
            return order, f"Payment failed: {reason}"

        payment_id = payment_result.get("payment_id")

        # ── Step 3: Reserve Shipping ───────────────────────────────────────────
        shipping_result = self._reserve_shipping(order, customer_id, shipping_address, shipping_method)
        if not shipping_result or not shipping_result.get("success"):
            # Compensate: cancel the reserved payment
            self._compensate_payment(payment_id)
            order.status = "failed"
            order.save(update_fields=["status"])
            reason = (shipping_result or {}).get("error", "No response from ship-service")
            return order, f"Shipping failed: {reason}"

        shipping_id = shipping_result.get("shipping_id")

        # ── Step 4: Confirm Order ──────────────────────────────────────────────
        order.status = "confirmed"
        order.payment_id = payment_id
        order.shipping_id = shipping_id
        order.save(update_fields=["status", "payment_id", "shipping_id"])

        return order, None

    def _reserve_payment(self, order, customer_id, payment_method, total):
        return rpc_call(
            PAYMENT_QUEUE,
            {
                "order_id": order.id,
                "customer_id": customer_id,
                "amount": str(total),
                "method": payment_method,
            },
            timeout=30,
        )

    def _reserve_shipping(self, order, customer_id, shipping_address, shipping_method):
        return rpc_call(
            SHIPPING_QUEUE,
            {
                "order_id": order.id,
                "customer_id": customer_id,
                "address": shipping_address,
                "method": shipping_method,
            },
            timeout=30,
        )

    def _compensate_payment(self, payment_id):
        if payment_id:
            publish_command(COMPENSATE_PAYMENT_QUEUE, {"payment_id": payment_id})
