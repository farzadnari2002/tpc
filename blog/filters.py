from django_filters import rest_framework as filters
from blog.models import Article, ArticleCategory


class ArticleFilter(filters.FilterSet):
    ordering = filters.OrderingFilter(
        fields=(
            ('published_at', 'published'),
            ('-published_at', '-published')
        )
    )
    category = filters.CharFilter(method='filter_by_category')

    def filter_by_category(self, queryset, name, value):
        try:
            category = ArticleCategory.objects.get(slug=value)
            descendants = category.get_descendants(include_self=True)
            return queryset.filter(categories__in=descendants)

        except ArticleCategory.DoesNotExist:
            return queryset.none()

    class Meta:
        model = Article
        fields = ['ordering', 'category']
