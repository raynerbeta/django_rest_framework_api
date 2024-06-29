from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class Pagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page_size"
    max_page_size = 20

    def get_paginated_response(self, data):
        return Response(
            {
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "page_size": self.page_size,
                "current_page_size": self.page.paginator.count,
                "results": data,
            }
        )
