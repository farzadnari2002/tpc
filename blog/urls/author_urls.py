from django.urls import path
from . import views


urlpatterns = [
    path('categories/', views.AuthorCategoryListView.as_view(),name='category-list'),
    path('articles/', views.AuthorArticleListView.as_view(), name='article-list'),
    path('article/<int:pk>/', views.AuthorArticleDetailView.as_view(), name='course-detail'),
    path('upload/', views.AuthorUploadImageViewSet.as_view({'post': 'create'}), name='author-upload'),

    # region Course Request
    path(
        'article/request/',
        views.AuthorArticleRequestViewSet.as_view({'post': 'create', 'get': 'list'}),
        name='author-article-request'
    ),
    path(
        'article/request/<int:pk>/',
        views.AuthorArticleRequestViewSet.as_view(
            {'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='author-article-request-detail'
    ),
    path(
        'article/send-request/<int:pk>/',
        views.AuthorArticleRequestViewSet.as_view({'post': 'send_request'}),
        name='author-article-send-request'
    ),
    path(
        'article/cancel-request/<int:pk>/',
        views.AuthorArticleRequestViewSet.as_view({'post': 'cancel_request'}),
        name='author-article-cancel-request'
    ),
    # endregion
]

