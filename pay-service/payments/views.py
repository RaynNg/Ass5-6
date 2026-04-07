from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """Simulate payment processing."""
        payment = self.get_object()
        payment.status = "completed"
        payment.save()
        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        payment = self.get_object()
        if payment.status != "completed":
            return Response({"error": "Only completed payments can be refunded"}, status=status.HTTP_400_BAD_REQUEST)
        payment.status = "refunded"
        payment.save()
        return Response(PaymentSerializer(payment).data)

    @action(detail=False, methods=["get"])
    def by_order(self, request):
        order_id = request.query_params.get("order_id")
        if not order_id:
            return Response({"error": "order_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        payments = Payment.objects.filter(order_id=order_id)
        return Response(PaymentSerializer(payments, many=True).data)
