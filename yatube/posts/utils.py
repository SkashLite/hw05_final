from django.conf import settings
from django.core.paginator import Paginator


def get_page_obj(request, queryset, post_on_page=settings.POSTS_ON_PAGE):
    paginator = Paginator(queryset, post_on_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
