from django.urls import path, re_path
from . import views


urlpatterns = [
    path('categories/', views.CategoryListView.as_view(),name='category-list'),
    path('', views.PublicArticleListView.as_view({'get': 'list'}), name='article-list'),
    re_path(
        r'^(?P<slug>[\w\-آ-ی]+)/?$',
        views.PublicArticleDetailView.as_view({'get': 'retrieve'}),
        name='article-detail'
    ),
]

