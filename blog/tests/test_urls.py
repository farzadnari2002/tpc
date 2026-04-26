from rest_framework.test import APITestCase
from blog.models import ArticleCategory
from accounts.models import User
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from blog.models import Article
from django.utils import timezone
from django.urls import reverse 


class TestUrls(APITestCase):
    @classmethod
    def create_test_image(cls, prefix='test'):
        """Helper method to create a test image with consistent filename"""
        image = Image.new('RGB', (100, 100), color='red')
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file, format='JPEG')
        tmp_file.seek(0)
        return SimpleUploadedFile(
            name=f'banner_{prefix}.jpg',
            content=tmp_file.read(),
            content_type='image/jpeg'
        ) 
    
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+989123456789',
            password='testPass123?',
        )
        self.user.first_name = 'ali'
        self.user.last_name = 'samadi'
        self.user.save()
        self.image = self.create_test_image()
        self.article1 = Article.objects.create(
            title='cyber security',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()
        )
        self.article2 = Article.objects.create(
            title='مهارت نرم',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()
        )
        self.category = ArticleCategory.objects.create(name='it')
        self.article1.categories.add(self.category)
        self.article2.categories.add(self.category)

    def test_public_article_detail_slug(self):
        response = self.client.get(reverse('public-article-detail', kwargs={'slug':self.article1.slug}))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('public-article-detail', kwargs={'slug':self.article2.slug}))
        self.assertEqual(response.status_code, 200)

