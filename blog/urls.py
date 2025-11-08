from django.urls import path, re_path
from . import views



urlpatterns = [

    
    path('categories/', views.CategoryListView.as_view(),name='category-list'),
    path('categories/select/', views.CategorySelectView.as_view(),name='category-select'),
    
    path('articles/', views.PublicArticleViewSet.as_view({'get': 'list'}), name='article-list'),
    re_path(r'^(?P<slug>[\w\-آ-ی]+)/?$', views.PublicArticleViewSet.as_view({'get': 'retrieve'}), name='article-detail'),
    path('author/articles/', views.AuthorArticleViewset.as_view({'get':'list'}), name='author-articles-list')
]






