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


class AuthorArticleViewset(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ArticleSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Article.objects.filter(author=self.request.user, status=Article.STATUS.PUBLISHED)


class ArticleRequestViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request':request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

