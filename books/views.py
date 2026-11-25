"""Book API endpoints: CRUD, search, low stock and price calculation (S3, S4, S5)."""

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book
from books.serializers import BookSerializer, PriceCalculationSerializer
from books.services.exchange import ExchangeRateUnavailable, fetch_usd_rate
from books.services.pricing import calculate_price_breakdown


class HealthzView(APIView):
    """Liveness probe used by docker-compose and the SPA."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class BookListCreateView(generics.ListCreateAPIView):
    """GET /books (paginated) and POST /books."""

    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET, PUT, PATCH and DELETE /books/{id}."""

    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookSearchView(generics.ListAPIView):
    """GET /books/search?category= - case-insensitive exact category filter."""

    serializer_class = BookSerializer

    def get_queryset(self):
        queryset = Book.objects.all()
        category = (self.request.query_params.get("category") or "").strip()
        if category:
            queryset = queryset.filter(category__iexact=category)
        return queryset


class BookLowStockView(generics.ListAPIView):
    """GET /books/low-stock?threshold=10 - books with stock_quantity <= threshold."""

    serializer_class = BookSerializer

    def get_threshold(self):
        raw = self.request.query_params.get("threshold")
        if raw is None or str(raw).strip() == "":
            return settings.LOW_STOCK_THRESHOLD
        try:
            threshold = int(str(raw).strip())
        except (TypeError, ValueError):
            raise ValidationError(
                {"threshold": ["Threshold must be a whole number, e.g. 10."]}
            )
        if threshold < 0:
            raise ValidationError(
                {"threshold": ["Threshold must be greater than or equal to 0."]}
            )
        return threshold

    def get_queryset(self):
        return Book.objects.filter(stock_quantity__lte=self.get_threshold())


class CalculatePriceView(APIView):
    """POST /books/{id}/calculate-price - S5 flow, S6 response."""

    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)

        try:
            exchange_rate, source = fetch_usd_rate(settings.LOCAL_CURRENCY)
        except ExchangeRateUnavailable as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        breakdown = calculate_price_breakdown(book.cost_usd, exchange_rate)

        book.selling_price_local = breakdown["selling_price_local"]
        book.save(update_fields=["selling_price_local", "updated_at"])

        payload = {
            "book_id": book.pk,
            "cost_usd": book.cost_usd,
            "exchange_rate": exchange_rate,
            "cost_local": breakdown["cost_local"],
            "margin_percentage": breakdown["margin_percentage"],
            "selling_price_local": breakdown["selling_price_local"],
            "currency": settings.LOCAL_CURRENCY,
            "calculation_timestamp": timezone.now(),
            "exchange_rate_source": source,
        }
        return Response(PriceCalculationSerializer(payload).data)
