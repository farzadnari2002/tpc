from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    
    path('courses/', include('courses.urls.public_urls')),
    path('teacher/', include('courses.urls.teacher_urls')),

    path('articles/', include('blog.urls.public_urls')),
    path('author/', include('blog.urls.author_urls')),
    
    path('comments/', include('comments.urls')),

    # document schema patterns
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # document schema optional ui
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
] 


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
if settings.DEBUG and not settings.TESTING:
    import debug_toolbar
    from debug_toolbar.toolbar import debug_toolbar_urls
    # urlpatterns += debug_toolbar_urls()
    urlpatterns = [path('__debug__/', include(debug_toolbar.urls)),] + urlpatterns

