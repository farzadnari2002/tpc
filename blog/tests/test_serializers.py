from django.test import TestCase
from blog.models import Article
from blog.serializers import ArticleRelatedField
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User


class TestArticleRelatedField(TestCase):
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
        self.user = User.objects.create_user(phone='+989123456789', password='testPass123?')
        self.image = self.create_test_image()
        self.article = Article.objects.create(
            title='Test Article',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image
        )
        self.field = ArticleRelatedField(queryset=Article.objects.all())

    def test_to_representation_returns_title(self):
        representation = self.field.to_representation(self.article)
        self.assertEqual(representation, self.article.title)


