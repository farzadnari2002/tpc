from blog.models import (
    Article,
    ArticleRequest,
    RequestActionChoices,
    RequestStatusChoices,
    ArticleCategory
)
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from django.contrib.postgres.search import SearchVector
from utils import update_descendants_active_status


@receiver(post_save, sender=ArticleRequest)
def update_article_publish_fields(sender, instance, created, **kwargs):
    if not created:
        if instance.action == RequestActionChoices.ADD and instance.status == RequestStatusChoices.APPROVED:
            if instance.target_id:
                article = Article.objects.filter(pk=instance.target_id, is_deleted=False).first() 

                if article:
                    article.is_published = True
                    article.published_at = timezone.now()
                    article.save(update_fields=['is_published', 'published_at', 'updated_at'])


@receiver(post_save, sender=Article)
def update_article_sv_field(sender, instance, **kwargs):
    Article.objects.filter(
        pk=instance.id
    ).update(sv=SearchVector('title'))


@receiver(post_save, sender=ArticleCategory)
def update_article_category_status(sender, instance, **kwargs):
    update_descendants_active_status(instance)

        


