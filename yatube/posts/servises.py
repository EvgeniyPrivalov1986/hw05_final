from django.core.paginator import Paginator

PAGINATOR_QUANTITY = 10


def get_paginator(request, posts):
    paginator = Paginator(posts, PAGINATOR_QUANTITY)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
