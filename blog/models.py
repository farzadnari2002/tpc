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
    
    if instance.article:
        object_name = f"{instance.article.slug}-{instance.article.id}"
    else:
        object_name = f"temp-{instance.upload_session}"
        
    folder_type = 'images'
    
    return get_upload_to(instance, filename, model_name, object_name, folder_type)

class RequestStatusChoices(models.TextChoices):
    PENDING = 'pending', _('در حال بررسی')
    APPROVED = 'approved', _('تایید شده')
    REJECTED = 'rejected', _('رد شده')
    NEED_REVISION = 'need_revision', _('نیاز به اصلاح')
    DRAFT = 'draft', _('پیش نویس')


class RequestActionChoices(models.TextChoices):
        # ADD or PUBLISH?
        ADD = 'add', _('ایجاد')
        UPDATE = 'update', _('ویرایش')
        DELETE = 'delete', _('حذف')


class ArticleCategory(MPTTModel):
    name = models.CharField(max_length=100, verbose_name=_('نام دسته بندی'))
    slug = AutoSlugField(source_field='name', verbose_name=_('آدرس دسته بندی'))
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children',
        verbose_name=_('دسته بندی والد')
        )
    # help_text test
    priority = models.PositiveSmallIntegerField(
        null=True, 
        blank=True, 
        verbose_name=_('اولویت نمایش'),
        help_text=_('هر چه عدد کمتر باشد، در لیست بالاتر نمایش داده می‌شود')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('وضعیت فعال بودن/نبودن'))
    is_special = models.BooleanField(default=False, verbose_name=_('وضعیت ویژه بودن/نبودن'))
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
        verbose_name = _('دسته بندی مقاله')
        verbose_name_plural = _('دسته بندی های مقاله')
        ordering = ['priority', 'id', 'created_at']
        db_table = 'article_category'
        indexes = [
            models.Index(fields=['slug'])
        ]


class Article(models.Model):
    author = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='articles',
    verbose_name=_('نویسنده مقاله')
    )
    title = models.CharField(max_length=250, verbose_name=_('عنوان مقاله'))
    slug = AutoSlugField(source_field='title', verbose_name=_('آدرس مقاله'))
    sv = SearchVectorField(blank=True, null=True, editable=False)
    banner = models.ImageField(
        upload_to=get_upload_banner,
        validators=[validate_image_size],
        verbose_name=_('بنر مقاله')

    )
    banner_thumbnail = ImageSpecField(
        source='banner',
        processors=[ResizeToFill(120, 120)],
        format='JPEG',
        options={'quality': 80}
    ) 
    categories = models.ManyToManyField(
        ArticleCategory,
        related_name="articles",
        db_table='article_category_link',
        verbose_name=_('دسته بندی های مقاله')
    )
    tags = TaggableManager(verbose_name=_('برچسب ها'))
    content = models.JSONField(verbose_name=_('محتوای مقاله'))
    short_description = models.TextField()
    # check published_at field
    published_at = models.DateTimeField(auto_now_add=True,verbose_name=_('تاریخ انتشار'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    is_published = models.BooleanField(default=False, verbose_name=_('وضعیت انتشار'))
    is_deleted = models.BooleanField(default=False, verbose_name=_('وضعیت حذف'))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('مقاله')
        verbose_name_plural = _('مقالات')
        ordering = ['-published_at']
        db_table = 'article'
        indexes = [
            models.Index(fields=['slug'])
        ]

class ArticleRequest(models.Model):
    target_id = models.PositiveIntegerField(null=True, blank=True)
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
        error_message = _("یافت نشد.")

        if self.action != RequestActionChoices.ADD and self.target_id:
            if not Article.objects.filter(pk=self.target_id, is_deleted=False).exists():
                errors['target_id'] = error_message
            else:
                article_obj = Article.objects.get(pk=self.target_id)
                
                if self.author != article_obj.author:
                    errors['author'] = _("فقط نویسنده مقاله مجاز به ثبت درخواست برای آن است.")
                
                if self.action == RequestActionChoices.ADD and article_obj.is_published:
                    error_msg = _('این مقاله قبلاً منتشر شده است. برای مقالات منتشر شده فقط امکان ثبت درخواست بروزرسانی یا حذف وجود دارد.')
                    errors['action'] = error_msg

        if self.action == RequestActionChoices.DELETE and (not self.comments or self.comments == ''):
            errors['comments'] = _("برای درخواست از نوع حذف باید توضیحات درج شود.")

        if self.action != RequestActionChoices.ADD and not self.target_id:
            errors['target_id'] = _("نباید خالی باشد.")

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
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField(upload_to=get_upload_images, validators=[validate_image_size])
    alt_text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0, db_index=True)
    upload_session = models.UUIDField(null=True, blank=True, db_index=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.article}"
    
    class Meta:
        verbose_name = _('Article Image')
        verbose_name_plural = _("Article Images")
        db_table = 'article_image'


