from utils import update_descendants_active_status
from .models import ArticleCategory, Article
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.postgres.search import SearchVector


@receiver(post_save, sender=ArticleCategory)
def update_article_category_status(sender, instance, **kwargs):
    update_descendants_active_status(instance)


@receiver(post_save, sender=Article)
def update_search_vector(sender, instance, **kwargs):
    Article.objects.filter(
        id=instance.id
    ).update(
        sv=SearchVector('title')
    )

