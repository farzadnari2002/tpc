from django.test import TestCase
from blog.models import (
     ArticleCategory,get_upload_banner,
     Article, 
     ArticleImage, 
     ArticleRequest,
     RequestActionChoices,
     RequestStatusChoices
)
from django.core.exceptions import ValidationError
from django.utils.translation.trans_null import gettext_lazy as _
from unittest.mock import Mock
from accounts.models import User
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile


class TestArticleCategoryModel(TestCase):
    def test_unique_slug(self):
        # self.category1 = ArticleCategory.objects.create(name='android')
        # self.category2 = ArticleCategory.objects.create(name='android')

        # self.assertNotEqual(self.category1.slug, self.category2.slug)
        pass
    
    def test_clean(self):
        self.root = ArticleCategory.objects.create(name='programming')
        self.level1 = ArticleCategory.objects.create(name='backend', parent=self.root)
        self.level2 = ArticleCategory.objects.create(name='django', parent=self.level1)
        self.invalid_level3 = ArticleCategory(name='drf', parent=self.level2)

        with self.assertRaisesMessage(ValidationError, '۲ سطح'):
            self.invalid_level3.clean()


class TestGetUploadBanner(TestCase):
    def setUp(self):
        self.mock_instance = Mock()
        self.mock_instance.slug = 'network'
        self.mock_instance.id = 1

    def test_returns_expected_path(self):
        path = get_upload_banner(self.mock_instance, 'mybanner.png')

        self.assertEqual(path, 'Article/network-1/banner/mybanner.png')

# class TestGetUploadImage(TestCase):
#     def setUp(self):
#         self.mock_instance = Mock()
#         self.mock_instance.slug = 'security'
#         self.mock_instance.id = 1

#     def test_returns_expected_path(self):
#         path = get_upload_banner(self.mock_instance, 'mybanner.png')

#         self.assertEqual(path, 'Article/network-1/banner/mybanner.png')


class TestArticle(TestCase):
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
 
    def test_author_relation(self):
        self.assertEqual(self.article.author.phone, '+989123456789')
        self.assertEqual(self.user.articles.get(id=1), self.article)

    def test_categories_relation(self): 
        self.category1 = ArticleCategory.objects.create(name='backend')
        self.category2 = ArticleCategory.objects.create(name='frontend')
        self.article.categories.add(self.category1, self.category2)

        self.image = self.create_test_image()
        self.article2 = Article.objects.create(
            title='My Article',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image
        )
        self.category3 = ArticleCategory.objects.create(name='desktop')
        self.category4 = ArticleCategory.objects.create(name='mobile')
        self.article2.categories.add(self.category3, self.category4)

        self.category5 = ArticleCategory.objects.create(name='flutter')
        self.article.categories.add(self.category5)
        self.article2.categories.add(self.category5)

        self.assertEqual(len(self.article.categories.all()), 3)
        self.assertEqual(len(self.article2.categories.all()), 3)

        self.assertCountEqual(self.article.categories.all(), [self.category1, self.category2, self.category5])
        self.assertCountEqual(self.article2.categories.all(), [self.category3, self.category4, self.category5])

    def test_unique_slug(self):
        # self.article = Article.objects.create(
        #     title='Test Article',
        #     author=self.user,
        #     content={"blocks": []},
        #     short_description='Test short desc',
        #     banner=self.image
        # ) 

        # self.assertNotEqual(self.article1.slug, self.article2.slug)
        pass

    def test_sv_field(self):
        pass

    def test_sv_field_index(self):
        pass

    def test_banner_thumnbail(self):
        self.assertIsNotNone(self.article.banner_thumbnail)
        self.assertEqual(self.article.banner_thumbnail.height, 120)
        self.assertEqual(self.article.banner_thumbnail.width, 120)
        self.assertEqual(self.article.banner_thumbnail.width, 120)
        self.assertTrue(self.article.banner_thumbnail.name.endswith('.jpg'))


class TestArticleImage(TestCase): 
    @classmethod
    def create_test_image(cls, prefix='test'):
        """Helper method to create a test image with consistent filename"""
        image = Image.new('RGB', (100, 100), color='red')
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file, format='JPEG')
        tmp_file.seek(0)
        return SimpleUploadedFile(
            name=f'mypicture_{prefix}.jpg',
            content=tmp_file.read(),
            content_type='image/jpg'
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
        self.image = self.create_test_image()

    def test_min_value_validator(self):
        self.article_image = ArticleImage(image=self.image, order=0, uploaded_by=self.user, article=self.article)

        with self.assertRaisesMessage(ValidationError, 'Ensure this value is greater than or equal to 1.'):
            self.article_image.full_clean()
    
    def test_clean(self):
        self.article_image = ArticleImage(image=self.image, uploaded_by=self.user)
        
        with self.assertRaisesMessage(ValidationError,_('خطا: هر عکس باید یا متعلق به یک مقاله باشد یا یک شناسه جلسه (upload_session) داشته باشد.')):
            self.article_image.clean()
    
    def test_article_relation(self):
        self.article_image = ArticleImage.objects.create(
            image=self.image,
            uploaded_by=self.user,
            article=self.article
        )

        self.assertEqual(self.article_image.article, self.article)
        self.assertEqual(self.article.images.get(id=self.article_image.id), self.article_image)
    
    def test_uploaded_by_relation(self):
        self.article_image = ArticleImage.objects.create(
            image=self.image,
            uploaded_by=self.user,
            article=self.article
        )
        self.assertEqual(self.article_image.uploaded_by, self.user)
        self.assertEqual(self.user.article_images.get(id=self.article_image.id), self.article_image)


class TestArticleRequest(TestCase):
    @classmethod
    def create_test_image(cls, prefix='test'):
        """Helper method to create a test image with consistent filename"""
        image = Image.new('RGB', (100, 100), color='red')
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file, format='JPEG')
        tmp_file.seek(0)
        return SimpleUploadedFile(
            name=f'mypicture_{prefix}.jpg',
            content=tmp_file.read(),
            content_type='image/jpg'
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
        self.image = self.create_test_image()

    def test_pending_limit(self):
        for i in range(5):
            ArticleRequest.objects.create(
                author=self.user,
                action=RequestActionChoices.ADD,
                status = RequestStatusChoices.PENDING,
                data={"test": 1}
            )

        self.article_request = ArticleRequest(
            author=self.user,
             action=RequestActionChoices.ADD,
             status=RequestStatusChoices.PENDING,
             data={"test": 1},
        )

        with self.assertRaisesMessage(ValidationError,_('۵')):
            self.article_request.clean()

    def test_add_action_valid(self):
        self.article_request = ArticleRequest(author=self.user, action=RequestActionChoices.ADD, data={"test": 1})
        self.article_request.clean()
    
    def test_need_revision_status_valid(self):
        self.article_request = ArticleRequest(
            target_id= self.article.id,
            author=self.user,
            status=RequestStatusChoices.NEED_REVISION,
            data={"test": 1},
            admin_response = "نیاز به ویرایش دارد"
        )
        self.article_request.clean()

    def test_update_action(self):
        self.article_request = ArticleRequest(
            target_id= self.article.id,
            author=self.user,
            action=RequestActionChoices.UPDATE,
            data={"test": 1},
        )
        self.article_request.clean()

    def test_null_target_id(self):
        self.article_request = ArticleRequest(
            author=self.user,
            action=RequestActionChoices.UPDATE,
            data={"test": 1},
        )

        with self.assertRaisesMessage(ValidationError,_('انتشار')):
            self.article_request.clean()
        
        self.article_request.action= RequestActionChoices.DELETE
        self.article_request.comments= ("نیاز به حذف دارم")
    
        with self.assertRaisesMessage(ValidationError,_('انتشار')):
            self.article_request.clean()

    def test_another_user(self):
        self.another_user = User.objects.create(
            phone='+989123480900',
            password='level@UPass123?'
        )
        self.article_request = ArticleRequest(
            target_id= self.article.id,
            author=self.another_user,
            action=RequestActionChoices.UPDATE,
            data={"test": 1},
        )

        with self.assertRaisesMessage(ValidationError,_("نویسنده")):
            self.article_request.clean()
        
        self.article_request.action= RequestActionChoices.DELETE
        self.article_request.comments= ("نیاز به حذف دارم")

        with self.assertRaisesMessage(ValidationError,_("نویسنده")):
            self.article_request.clean()

    def test_need_revision_status_null_admin_response(self):
        self.article_request = ArticleRequest(
            target_id= self.article.id,
            author=self.user,
            action=RequestActionChoices.ADD,
            data={"test": 1},
            status=RequestStatusChoices.NEED_REVISION
        )
    
        with self.assertRaisesMessage(ValidationError,_("اصلاح")):
            self.article_request.clean()

    def test_delete_action_null_comments(self):
        self.article_request = ArticleRequest(
            target_id= self.article.id,
            author=self.user,
            action=RequestActionChoices.DELETE,
            data={"test": 1},
        )

        with self.assertRaisesMessage(ValidationError,_("حذف")):
            self.article_request.clean()

    def test_save(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={"test": 1},
            status=RequestStatusChoices.PENDING
        )
        
        self.assertFalse(self.article_request.need_revision)

        self.article_request.status = RequestStatusChoices.NEED_REVISION
        self.article_request.admin_response = "نیاز به ویرایش دارد"
        self.article_request.save()

        self.assertTrue(self.article_request.need_revision)
        


    




        






            

        




        

    