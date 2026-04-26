from django.urls import path, re_path
from blog import views


urlpatterns = [
    path('categories/', views.PublicCategoryListView.as_view(),name='public-category-list'),
    path('', views.PublicArticleListView.as_view(), name='public-article-list'),
    re_path(
        r'^(?P<slug>[\w\-آ-ی]+)/?$',
        views.PublicArticleDetailView.as_view(),
        name='public-article-detail'
    ),
]

