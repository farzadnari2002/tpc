from django.urls import path
from . import views



urlpatterns = [

    
    path('categories/', views.CategoryListView.as_view(),name='category-list'),
    path('categories/select/', views.CategorySelectView.as_view(),name='category-select'),

    path('public/articles/', views.PublicArticleViewSet.as_view({'get': 'list'}), name='public-articles-list'),
    path('public/articles/<slug:slug>/', views.PublicArticleViewSet.as_view({'get': 'retrieve'}), name='public-articles-detail'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('author/articles/', views.AuthorArticleViewset.as_view({'get':'list'}), name='author-articles-list')
]