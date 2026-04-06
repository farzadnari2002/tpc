from blog.models import (
    Article,
    ArticleRequest,
    RequestActionChoices,
    RequestStatusChoices,
    ArticleCategory
)
from django.test import TestCase
from accounts.models import User
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile


class TestUpdateArticlePublishFields(TestCase):
    @classmethod
    def create_test_image(cls, prefix='test'):
        """Helper method to create a test image with consistent filename"""
        image = Image.new('RGB', (500, 500), color='red')
        tmp_file = tempfile.NamedTemporaryFile(suffix='.png')
        image.save(tmp_file, format='PNG')
        tmp_file.seek(0)
        return SimpleUploadedFile(
            name=f'banner_{prefix}.png',
            content=tmp_file.read(),
            content_type='image/png'
        )
    
    def setUp(self):
        self.user = User.objects.create(
            phone='+989123456789',
            password='testPass123?'
        )
        self.image = self.create_test_image()
        self.article = Article.objects.create(
            title='Test Article',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image
        ) 

    def test_request_appreoved(self):
        self.assertFalse(self.article.is_published)
        self.assertIsNone(self.article.published_at)

        self.article_request = ArticleRequest(
            author=self.user,
            target_id=self.article.id,
            action=RequestActionChoices.ADD,
            data={"test": 1}
        )
        self.assertEqual(self.article_request.status, RequestStatusChoices.DRAFT)

        self.article_request.status = RequestStatusChoices.PENDING
        self.article_request.save()
        self.assertEqual(self.article_request.status, RequestStatusChoices.PENDING)

        self.article_request.status = RequestStatusChoices.APPROVED
        self.article_request.save()
        
        self.old_updated_at = self.article.updated_at
        self.article.refresh_from_db()
        self.assertTrue(self.article.is_published)
        self.assertIsNotNone(self.article.published_at)
        self.assertNotEqual(self.old_updated_at, self.article.updated_at)

class UpdateArticleSvField(TestCase):
    @classmethod
    def create_test_image(cls, prefix='test'):
        """Helper method to create a test image with consistent filename"""
        image = Image.new('RGB', (500, 500), color='red')
        tmp_file = tempfile.NamedTemporaryFile(suffix='.png')
        image.save(tmp_file, format='PNG')
        tmp_file.seek(0)
        return SimpleUploadedFile(
            name=f'banner_{prefix}.png',
            content=tmp_file.read(),
            content_type='image/png'
        )

    def setUp(self):
        self.user = User.objects.create(
            phone='+989123456789',
            password='testPass123?'
        )
        self.image = self.create_test_image()
        self.article = Article.objects.create(
            title='soft skills',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image
        ) 

    def test_update_sv(self):
        self.assertIsNone(self.article.sv)
        self.article.refresh_from_db()
        self.assertIsNotNone(self.article.sv)


class UpdateArticleCategoryStatus(TestCase):
    def setUp(self):
        self.grandparent = ArticleCategory.objects.create(name='test1')
        self.parent1 = ArticleCategory.objects.create(name='test2', parent=self.grandparent) 
        self.parent2 = ArticleCategory.objects.create(name='test3', parent=self.grandparent)
        self.parent1_child = ArticleCategory.objects.create(name='test5', parent=self.parent1)  
        self.parent2_child = ArticleCategory.objects.create(name='test6', parent=self.parent2)
    
    def test_category_is_active_true(self):
        self.grandparent.is_active = False
        self.grandparent.save()
        self.parent1.is_active = True
        self.parent1.save()

        self.grandparent.refresh_from_db()
        self.parent1.refresh_from_db()
        self.parent2.refresh_from_db()
        self.parent1_child.refresh_from_db() 
        self.parent2_child.refresh_from_db()
    
        self.assertFalse(self.grandparent.is_active)
        self.assertFalse(self.parent2.is_active)
        self.assertFalse(self.parent2_child.is_active)

        self.assertTrue(self.parent1.is_active)
        self.assertTrue(self.parent1_child.is_active)

    def test_category_is_active_false(self):
        self.parent1.is_active = False
        self.parent1.save()

        self.grandparent.refresh_from_db()
        self.parent1.refresh_from_db()
        self.parent2.refresh_from_db()
        self.parent1_child.refresh_from_db() 
        self.parent2_child.refresh_from_db()

        self.assertTrue(self.grandparent.is_active)
        self.assertTrue(self.parent2.is_active)
        self.assertTrue(self.parent2_child.is_active)

        self.assertFalse(self.parent1.is_active)
        self.assertFalse(self.parent1_child.is_active)



     

        


    






