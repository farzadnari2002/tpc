from django.urls import path, re_path
from . import views


urlpatterns = [
    path('categories/', views.AuthorCategoryListView.as_view(),name='category-list'),
    path('articles/', views.AuthorArticleListView.as_view({'get':'list'}), name='article-list'),
    path('article/<int:pk>/', views.AuthorArticleDetailView.as_view(), name='course-detail'),
    path('upload/', views.AuthorUploadImageViewSet.as_view({'post': 'create'}), name='author-upload'),
    path(
        'article/request/',
        views.AuthorArticleRequestViewSet.as_view({'post': 'create', 'get': 'list'}),
        name='author-article-request'
    ),
]

