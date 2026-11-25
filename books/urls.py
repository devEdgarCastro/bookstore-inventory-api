"""Book API routes.

Mounted at the site root so the documented paths are literally /books and
/books/{id} (no /api prefix).
"""

from django.urls import path

from books.views import (
    BookDetailView,
    BookListCreateView,
    BookLowStockView,
    BookSearchView,
    CalculatePriceView,
)

urlpatterns = [
    path("books", BookListCreateView.as_view(), name="book-list"),
    path("books/search", BookSearchView.as_view(), name="book-search"),
    path("books/low-stock", BookLowStockView.as_view(), name="book-low-stock"),
    path("books/<int:pk>", BookDetailView.as_view(), name="book-detail"),
    path(
        "books/<int:pk>/calculate-price",
        CalculatePriceView.as_view(),
        name="book-calculate-price",
    ),
]
