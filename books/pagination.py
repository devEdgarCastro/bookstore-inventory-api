"""Pagination used by every list endpoint."""

from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """``?page=`` / ``?page_size=`` pagination with the DRF JSON envelope.

    ``page_size`` defaults to ``REST_FRAMEWORK["PAGE_SIZE"]``. An empty or
    non-numeric ``page`` falls back to the first page so the documented
    ``?page=&page_size=`` form keeps working, while an explicitly requested
    page that does not exist still returns ``404``.
    """

    page_size_query_param = "page_size"
    max_page_size = 100

    def get_page_number(self, request, paginator):
        raw = request.query_params.get(self.page_query_param, 1)
        raw = "" if raw is None else str(raw).strip()
        if raw == "":
            return 1
        if raw.lower() in self.last_page_strings:
            return paginator.num_pages
        try:
            number = int(raw)
        except (TypeError, ValueError):
            raise NotFound(
                self.invalid_page_message.format(
                    page_number=raw, message="That page number is not an integer"
                )
            )
        if number < 1:
            raise NotFound(
                self.invalid_page_message.format(
                    page_number=raw, message="That page number is less than 1"
                )
            )
        return number
