from django.contrib import admin
from .models import *


admin.site.register(ArticleCategory)
admin.site.register(Article)
admin.site.register(ArticleImage)
admin.site.register(ArticleRequest)


