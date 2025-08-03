from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from autoslug import AutoSlugField
from django.utils.translation.trans_null import gettext_lazy as _
from taggit.managers import TaggableManager
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.conf import settings
from utils import get_upload_to, validate_image_size, AutoSlugField
from django.utils import timezone
from simple_history.models import HistoricalRecords
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ValidationError


def get_upload_banner(instance, filename):
    model_name = 'Article'
    object_name = f"{instance.slug}-{instance.id}"
    folder_type = 'banner'
    return get_upload_to(instance, filename, model_name, object_name, folder_type)


def get_upload_images(instance, filename):
    model_name = 'Article'
    object_name = f"{instance.article.slug}-{instance.article.id}"
    folder_type = 'images'
    return get_upload_to(instance, filename, model_name, object_name, folder_type)


class RequestStatusChoices(models.TextChoices):
    PENDING = 'pending', _('در حال بررسی')
    APPROVED = 'approved', _('تایید شده')
    REJECTED = 'rejected', _('رد شده')
    NEED_REVISION = 'need_revision', _('نیاز به اصلاح')
    DRAFT = 'draft', _('پیش نویس')


class RequestActionChoices(models.TextChoices):
        PUBLISH = 'publish', _('انتشار')
        UPDATE = 'update', _('ویرایش')
        DELETE = 'delete', _('حذف')


class ArticleCategory(MPTTModel):
    name = models.CharField(max_length=100, verbose_name=_('نام دسته بندی'))
    slug = AutoSlugField(source_field='name', verbose_name=_('آدرس دسته بندی'))
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='childrens',
        verbose_name=_('دسته بندی والد')
        )
    is_active = models.BooleanField(default=True), verbose_name=_('وضعیت فعال بودن/نبودن')
    is_special = models.BooleanField(default=False, verbose_name=_('تاریخ ایجاد'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
                 
    def clean(self):
        if self.parent:
            level = self.parent.get_level() + 1
            if level > 2:
                raise ValidationError(_('حداکثر تعداد سطوح دسته بندی ۲ سطح می‌باشد.'))
            
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
                        
    def __str__(self):
        return self.name
           
    class Meta:
        verbose_name = _('دسته بندی دوره')
        verbose_name_plural = _('دسته بندی های دوره')
        ordering = ['name']
        db_table = 'article_category'
        indexes = [
            models.Index(fields=['slug'])
        ]


class Article(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=250)
    slug = AutoSlugField(source_field='title')
    sv = SearchVectorField(blank=True, null=True, editable=False)
    banner = models.ImageField(
        upload_to=get_upload_banner,
        validators=[validate_image_size],

    )
    banner_thumbnail = ImageSpecField(
        source='banner',
        processors=[ResizeToFill(120, 120)],
        format='JPEG',
        options={'quality': 80}
    ) 
    category = models.ManyToManyField(ArticleCategory, related_name="articles", db_table='article_category_link')
    content = models.JSONField()
    published_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False, verbose_name=_('وضعیت انتشار'))
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')
        ordering = ['-published_at']
        db_table = 'article'
        indexes = [
            models.Index(fields=['slug'])
        ]


class ArticleRequest(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='requests', null=True, blank=True)
    action = models.CharField(max_length=20, choices=RequestActionChoices.choices)
    status = models.CharField(
        max_length=20, choices=RequestStatusChoices.choices,
        default=RequestStatusChoices.DRAFT,
    )
    data = models.JSONField()
    history = HistoricalRecords()
    comments = models.TextField(null=True, blank=True)
    admin_response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    need_revision = models.BooleanField(default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='article_requests'
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        editable=False,
        related_name='admin_article_requests'
    )
    
    def clean(self):
        super().clean()
        errors = {}

        if self.article:
            if self.action == RequestActionChoices.PUBLISH:
                error_msg = _('این مقاله قبلاً منتشر شده است. برای مقالات منتشر شده فقط امکان ثبت درخواست بروزرسانی یا حذف وجود دارد.')
                errors['action'] = error_msg
        
            if self.author != self.article.author:
                error_msg = _("فقط نویسنده مقاله مجاز به ثبت درخواست برای آن است.")
                errors['author'] = error_msg

            if self.action == RequestActionChoices.DELETE and (not self.comments or self.comments == ''):
                error_msg = _("برای درخواست حذف باید توضیحات درج شود.")
                errors['action'] = error_msg
        else:
            if self.action in [RequestActionChoices.UPDATE, RequestActionChoices.DELETE]:
                error_msg = _('برای ثبت درخواست ویرایش یا حذف، مقاله باید ابتدا منتشر شده باشد.')
                errors['action'] = error_msg
            
        if self.status == RequestStatusChoices.NEED_REVISION and (not self.admin_response or self.admin_response == ''):
            error_msg = _("در وضعیت نیاز به اصلاح باید پاسخی به نویسنده داده شود.")
            errors['admin_response'] = error_msg
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        
        if self.status == RequestStatusChoices.NEED_REVISION:
            self.need_revision = True
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ArticleRequest(id={self.pk}, action={self.action}, status={self.status})"
    
    class Meta:
        verbose_name = _("درخواست")
        verbose_name_plural = _("درخواست ها")
        ordering = ['-created_at', '-id']
        db_table = 'article_request'


class ArticleImage(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=get_upload_images, validators=[validate_image_size])
    alt_text = models.CharField(max_length=255)

    def __str__(self):
        return f"Image for {self.article}"
    
    class Meta:
        verbose_name = _('Article Image')
        verbose_name_plural = _("Article Images")
        ordering = ['-created_at']
        db_table = 'article_image'


