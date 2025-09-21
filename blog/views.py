from rest_framework import generics
from .serializers import ArticleCategorySerializer, ArticleSerializer
from .models import *
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated


class CategorySelectView(generics.ListAPIView):
    serializer_class = ArticleCategorySerializer
    queryset = ArticleCategory.objects.filter(parent=None, is_active=True, is_special=False)


class CategoryListView(generics.ListAPIView):
    serializer_class = ArticleCategorySerializer
    queryset = ArticleCategory.objects.filter(parent=None, is_active=True)


class PublicArticleViewSet(ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status=Article.STATUS.PUBLISHED)
    serializer_class = ArticleSerializer
    lookup_field = 'slug'


class AuthorArticleViewset(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ArticleSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return self.request.user.articles.all()
    
    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save(author=self.request.user, status='published')
        else:
            serializer.save(author=self.request.user)


    



