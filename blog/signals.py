from utils import update_descendants_active_status
from .models import ArticleCategory, Article
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
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


@receiver(pre_save, sender=Article)
def update_title_and_slug_on_delete(sender, instance, **kwargs):
    if instance.pk:
        original_article = Article.objects.get(pk=instance.pk)
        if original_article.is_deleted != instance.is_deleted and instance.is_deleted:
            instance.title = f"{instance.title} del"
            instance.slug = f"{instance.slug}-del"

