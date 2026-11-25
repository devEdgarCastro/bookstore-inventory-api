"""Django admin registration for the inventory."""

from django.contrib import admin

from books.models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "isbn",
        "category",
        "cost_usd",
        "selling_price_local",
        "stock_quantity",
        "supplier_country",
        "updated_at",
    )
    list_filter = ("category", "supplier_country")
    search_fields = ("title", "author", "isbn", "isbn_normalized")
    readonly_fields = ("isbn_normalized", "created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("title",)
    list_per_page = 25
