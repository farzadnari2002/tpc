from django.urls import path
from blog import views


urlpatterns = [
    path('categories/', views.AuthorCategoryListView.as_view(),name='author-category-list'),
    path('articles/', views.AuthorArticleListView.as_view(), name='article-list'),
    path('articles/<int:pk>/', views.AuthorArticleDetailView.as_view(), name='author-article-detail'),
    path('upload/', views.AuthorUploadImageViewSet.as_view({'post': 'create'}), name='author-upload'),

    # region Article Request
    path(
        'articles/requests/',
        views.AuthorArticleRequestViewSet.as_view({'post': 'create', 'get': 'list'}),
        name='author-article-request'
    ),
    path(
        'articles/requests/<int:pk>/',
        views.AuthorArticleRequestViewSet.as_view(
            {'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='author-article-request-detail'
    ),
    path(
        'articles/send-request/<int:pk>/',
        views.AuthorArticleRequestViewSet.as_view({'post': 'send_request'}),
        name='author-article-send-request'
    ),
    path(
        'articles/cancel-request/<int:pk>/',
        views.AuthorArticleRequestViewSet.as_view({'post': 'cancel_request'}),
        name='author-article-cancel-request'
    ),
    # endregion
]

