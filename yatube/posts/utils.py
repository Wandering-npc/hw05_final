from django.core.paginator import Paginator

NUM_OF_POSTS: int = 10


def paginate(request, post_list):
    """Страницы."""
    paginator = Paginator(post_list, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
