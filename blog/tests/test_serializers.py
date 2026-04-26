from django.test import TestCase
from blog.models import Article, ArticleCategory, ArticleImage, ArticleRequest
from blog.serializers import (
    ArticleRelatedField,
    CategoryHierarchySerializer,
    PublicArticleListSerializer,
    PublicArticleDetailSerializer,
    AuthorArticleListSerializer,
    AuthorArticleDetailSerializer,
    AuthorUploadImageSerializer,
    AuthorArticleRequestSerializer
)
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User, UserProfile, Job, JobCategory, EmployeeProfile
from django.db.models import F
from io import BytesIO
from uuid import uuid4


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


class TestCategoryHierarchySerializer(TestCase):
    def setUp(self):
        self.category_root = ArticleCategory.objects.create(name="Root Category", slug="root-category")
        self.category_child_1 = ArticleCategory.objects.create(name="Child 1", slug="child-1", parent=self.category_root)
        self.category_child_2 = ArticleCategory.objects.create(name="Child 2", slug="child-2", parent=self.category_root)
        self.category_grandchild = ArticleCategory.objects.create(name="Grandchild", slug="grandchild", parent=self.category_child_1)
        self.category_root.prefetched_children = [self.category_child_1, self.category_child_2]
        self.category_child_1.prefetched_children = [self.category_grandchild]
        self.category_child_2.prefetched_children = []
        self.category_grandchild.prefetched_children = []

    def test_simple_fields(self):
        serializer = CategoryHierarchySerializer(self.category_root)
        data = serializer.data

        self.assertEqual(data['name'], self.category_root.name)
        self.assertEqual(data['slug'], self.category_root.slug)
        self.assertIsNone(data['parent_slug'])

    def test_hierarchy_serialization(self):
        serializer = CategoryHierarchySerializer(self.category_root)
        data = serializer.data
        children_data = data['children']

        self.assertEqual(len(children_data), 2)
        self.assertEqual(children_data[0]['name'], self.category_child_1.name)
        self.assertEqual(children_data[0]['slug'], self.category_child_1.slug)
        self.assertEqual(children_data[0]['parent_slug'], self.category_root.slug)


        self.assertEqual(children_data[1]['name'], self.category_child_2.name)
        self.assertEqual(children_data[1]['slug'], self.category_child_2.slug)
        self.assertEqual(children_data[1]['parent_slug'], self.category_root.slug)

        grandchild_data = children_data[0]['children']
        self.assertEqual(len(grandchild_data), 1)
        self.assertEqual(grandchild_data[0]['name'], self.category_grandchild.name)
        self.assertEqual(grandchild_data[0]['slug'], self.category_grandchild.slug)
        self.assertEqual(grandchild_data[0]['parent_slug'], self.category_child_1.slug)
        self.assertEqual(grandchild_data[0]['children'], [])
    

class TestPublicArticleListSerializer(TestCase):
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
        self.article = Article.objects.create(
            title='Test Article',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image
        )
        self.job_category = JobCategory.objects.create(title='developer')
        self.job = Job.objects.create(name='backend developer')
        self.job.category.add(self.job_category)
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            gender='M',
            job=self.job,
            age=18,
            bio='example bio'
        )
        self.employee_profile = EmployeeProfile.objects.create(
            user_profile=self.user_profile,
            username='selisamadi80',
        )
        self.article = Article.objects.filter(pk=self.article.pk).annotate(
            author_first_name=F('author__first_name'),
            author_last_name=F('author__last_name'),
            author_username=F('author__user_profile__employee_profile__username')
        ).first()

    def test_simple_fields(self):
        serializer = PublicArticleListSerializer(self.article)
        data = serializer.data

        self.assertEqual(data['title'], self.article.title)
        self.assertEqual(data['slug'], self.article.slug)
        self.assertEqual(data['short_description'], self.article.short_description)
        self.assertIn('banner_thumbnail', data)
        self.assertIn('published_at', data)

    def test_author_field(self):
        serializer = PublicArticleListSerializer(self.article)
        data = serializer.data

        self.assertEqual(data['author']['full_name'], f"{self.article.author_first_name} {self.article.author_last_name}")
        self.assertEqual(data['author']['username'], self.article.author_username)

    def test_author_full_name_strips_whitespace(self):
        self.user.first_name = "  ali  "
        self.user.last_name = "  samadi  "
        self.user.save()
        self.article = Article.objects.filter(pk=self.article.pk).annotate(
            author_first_name=F('author__first_name'),
            author_last_name=F('author__last_name'),
            author_username=F('author__user_profile__employee_profile__username')
        ).first()

        serializer = PublicArticleListSerializer(self.article)
        data = serializer.data

        self.assertEqual(data['author']['full_name'], "ali samadi")

    def test_author_fields_handle_nulls(self):
        self.user_profile.delete()
        self.user.first_name = ""
        self.user.last_name = ""
        self.user.save()
        self.article = Article.objects.filter(pk=self.article.pk).annotate(
            author_first_name=F('author__first_name'),
            author_last_name=F('author__last_name'),
            author_username=F('author__user_profile__employee_profile__username')
        ).first()

        serializer = PublicArticleListSerializer(self.article)
        data = serializer.data

        self.assertEqual(data['author']['full_name'], " ")
        self.assertIsNone(data['author']['username'])


class TestPublicArticleDetailSerializer(TestCase):
    # mock?
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

    def get_category_dict(self, category_obj):
        return {
            "name": category_obj.name,
            "slug": category_obj.slug
        }       
    
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+989123456789',
            password='testPass123?',
        )
        self.user.first_name = 'ali'
        self.user.last_name = 'samadi'
        self.user.save()
        self.image = self.create_test_image()
        self.article = Article.objects.create(
            title='Test Article',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image
        )
        self.article.tags.add("python", "django", "tabriz")
        self.job_category = JobCategory.objects.create(title='developer')
        self.job = Job.objects.create(name='backend developer')
        self.job.category.add(self.job_category)
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            gender='M',
            job=self.job,
            age=18,
            bio='example bio'
        )
        self.employee_profile = EmployeeProfile.objects.create(
            user_profile=self.user_profile,
            username='selisamadi80',
        )
        self.article = Article.objects.filter(pk=self.article.pk).annotate(
            author_first_name=F('author__first_name'),
            author_last_name=F('author__last_name'),
            author_username=F('author__user_profile__employee_profile__username')
        ).first()
        self.article.prefetched_categories = self.article.categories.all()

    def test_simple_fields(self):
        serializer = PublicArticleDetailSerializer(self.article)
        data = serializer.data

        self.assertEqual(data['title'], self.article.title)
        self.assertEqual(data['slug'], self.article.slug)
        self.assertIn('published_at', data)
        self.assertIn('banner', data)

    def test_author_field(self):
        serializer = PublicArticleDetailSerializer(self.article)
        data = serializer.data
        
        self.assertEqual(data['author']['full_name'], f"{self.article.author_first_name} {self.article.author_last_name}")
        self.assertEqual(data['author']['username'], self.article.author_username)

    def test_author_field_full_name_strips_whitespace(self):
        self.user.first_name = "  ali  "
        self.user.last_name = "  samadi  "
        self.user.save()
        self.article = Article.objects.filter(pk=self.article.pk).annotate(
            author_first_name=F('author__first_name'),
            author_last_name=F('author__last_name'),
            author_username=F('author__user_profile__employee_profile__username')
        ).first()
        self.article.prefetched_categories = self.article.categories.all()

        serializer = PublicArticleDetailSerializer(self.article)
        data = serializer.data
        self.assertEqual(data['author']['full_name'], "ali samadi")

    def test_author_field_handle_nulls(self):
        self.user_profile.delete()
        self.user.first_name = ""
        self.user.last_name = ""
        self.user.save()
        self.article = Article.objects.filter(pk=self.article.pk).annotate(
            author_first_name=F('author__first_name'),
            author_last_name=F('author__last_name'),
            author_username=F('author__user_profile__employee_profile__username')
        ).first()
        self.article.prefetched_categories = self.article.categories.all()

        serializer = PublicArticleDetailSerializer(self.article)
        data = serializer.data

        self.assertEqual(data['author']['full_name'], " ")
        self.assertIsNone(data['author']['username'])

    def test_tags_field(self):
        serializer = PublicArticleDetailSerializer(self.article)
        data = serializer.data

        self.assertEqual(data['tags'], ['python', 'django', 'tabriz'])

    def test_categories_field(self):
        self.category1 = ArticleCategory.objects.create(name="news")
        self.category2 = ArticleCategory.objects.create(name="it")
        self.category3 = ArticleCategory.objects.create(name="programming")
        self.article.categories.add(self.category1, self.category2, self.category3)
        self.article.prefetched_categories = self.article.categories.all()

        serializer = PublicArticleDetailSerializer(self.article)
        data = serializer.data

        actual_categories = data['categories']
        expected_categories = [
            self.get_category_dict(self.category1),
            self.get_category_dict(self.category2),
            self.get_category_dict(self.category3),
        ]
        self.assertCountEqual(actual_categories, expected_categories)

    def test_categories_field_one_object(self):
        self.category = ArticleCategory.objects.create(name="programming")
        self.article.categories.add(self.category)
        self.article.prefetched_categories = self.article.categories.all()

        serializer = PublicArticleDetailSerializer(self.article)
        data = serializer.data

        actual_categories = data['categories']
        expected_categories = [self.get_category_dict(self.category)]
        self.assertCountEqual(actual_categories, expected_categories)

    def test_category_field_empty(self):
        self.article.categories.clear()
        self.article.prefetched_categories = self.article.categories.none()

        serializer = PublicArticleDetailSerializer(self.article)
        data = serializer.data

        self.assertEqual(data['categories'], [])


class TestAuthorArticleListSerializer(TestCase):
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
        self.article = Article.objects.create(
            title='Test Article',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image
        )

    def test_fields(self):
        serializer = AuthorArticleListSerializer(self.article)
        data = serializer.data
        self.assertEqual(data['title'], self.article.title)
        self.assertEqual(data['slug'], self.article.slug)
        self.assertEqual(data['short_description'], self.article.short_description)
        self.assertIn('is_published', data)
        self.assertIn('published_at', data)
        self.assertIn('banner_thumbnail', data)


class TestAuthorArticleDetailSerializer(TestCase):
    # mock?
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

    def get_category_dict(self, category_obj):
        return {
            "name": category_obj.name,
            "slug": category_obj.slug
        }       
    
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+989123456789',
            password='testPass123?',
        )
        self.user.first_name = 'ali'
        self.user.last_name = 'samadi'
        self.user.save()
        self.image = self.create_test_image()
        self.article = Article.objects.create(
            title='Test Article',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image
        )
        self.article.tags.add("python", "django", "tabriz")
        self.article.prefetched_categories = self.article.categories.all()

    def test_simple_fields(self):
        serializer = AuthorArticleDetailSerializer(self.article)
        data = serializer.data

        self.assertEqual(data['title'], self.article.title)
        self.assertEqual(data['slug'], self.article.slug)
        self.assertIn('banner', data)
        self.assertIn('is_published', data)
        self.assertIn('published_at', data)
        self.assertIn('updated_at', data)

    def test_tags_field(self):
        serializer = AuthorArticleDetailSerializer(self.article)
        data = serializer.data

        self.assertEqual(data['tags'], ['python', 'django', 'tabriz'])

    def test_categories_field(self):
        self.category1 = ArticleCategory.objects.create(name="news")
        self.category2 = ArticleCategory.objects.create(name="it")
        self.category3 = ArticleCategory.objects.create(name="programming")
        self.article.categories.add(self.category1, self.category2, self.category3)
        self.article.prefetched_categories = self.article.categories.all()

        serializer = AuthorArticleDetailSerializer(self.article)
        data = serializer.data

        actual_categories = data['categories']
        expected_categories = [
            self.get_category_dict(self.category1),
            self.get_category_dict(self.category2),
            self.get_category_dict(self.category3),
        ]
        self.assertCountEqual(actual_categories, expected_categories)

    def test_categories_field_one_object(self):
        self.category = ArticleCategory.objects.create(name="programming")
        self.article.categories.add(self.category)
        self.article.prefetched_categories = self.article.categories.all()

        serializer = AuthorArticleDetailSerializer(self.article)
        data = serializer.data

        actual_categories = data['categories']
        expected_categories = [self.get_category_dict(self.category)]
        self.assertCountEqual(actual_categories, expected_categories)

    def test_categories_field_empty(self):
        self.article.categories.clear()
        self.article.prefetched_categories = self.article.categories.none()

        serializer = AuthorArticleDetailSerializer(self.article)
        data = serializer.data

        self.assertEqual(data['categories'], [])


class TestAuthorUploadImageSerializer(TestCase):
    @classmethod
    def _create_test_image(cls, prefix='test'):
        """Helper method to create a test image with consistent filename"""
        image = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return SimpleUploadedFile(
            name=f'image_{prefix}.png',
            content=buffer.read(),
            content_type='image/png'
        )

    def setUp(self):
        self.user = User.objects.create_user(phone='+989123456789', password='testPass123?')
        self.other_user = User.objects.create_user(phone='+989111111111', password='testPass123?')
        
        self.article = Article.objects.create(
            title='test-article-slug',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc'
        )
        self.other_article = Article.objects.create(
            title='other-article-slug',
            author=self.other_user,
            content={"blocks": []},
            short_description='Test short desc'
        )
        
        self.context = {'request': type('Request', (), {'user': self.user})}
        self.valid_session = str(uuid4())

    def _get_fresh_image(self):
        return self._create_test_image()

    def test_read_only_fields_are_ignored_on_input(self):
        data = {
            'article': self.article.pk,
            'image': self._get_fresh_image(),
            'alt_text': 'Test Alt',
            'order': 1,
            'id': 999,
            'article_id': 888
        }
        serializer = AuthorUploadImageSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()
        self.assertNotEqual(instance.id, 999)
        self.assertNotEqual(instance.article_id, 888)

    def test_successful_creation_with_article(self):
        data = {
            'article': self.article.pk,
            'image': self._get_fresh_image(),
            'alt_text': 'Test Alt',
            'order': 1
        }
        serializer = AuthorUploadImageSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()

        self.assertIsNotNone(instance.image)

        self.assertEqual(instance.article, self.article)
        self.assertEqual(instance.uploaded_by, self.user)
        self.assertEqual(instance.alt_text, 'Test Alt')
        self.assertEqual(instance.order, 1)
        self.assertIsNone(instance.upload_session)

    def test_successful_creation_with_upload_session_only(self):
        data = {
            'upload_session': self.valid_session,
            'image': self._get_fresh_image(),
            'alt_text': 'Test Alt',
            'order': 1
        }
        serializer = AuthorUploadImageSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()

        self.assertIsNotNone(instance.image)
        
        self.assertIsNone(instance.article)
        self.assertEqual(str(instance.upload_session), self.valid_session)
        self.assertEqual(instance.uploaded_by, self.user)
        # self.assertIn('temp-', instance.image.name)
        # self.assertIn(self.valid_session, instance.image.name)

    def test_validation_error_when_both_article_and_session_missing(self):
        data = {
            'image': self._get_fresh_image(),
            'alt_text': 'Test Alt',
            'order': 1
        }
        serializer = AuthorUploadImageSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_permission_denied_for_non_owner_article(self):
        data = {
            'article': self.other_article.pk,
            'image': self._get_fresh_image(),
            'alt_text': 'Test Alt',
        }
        serializer = AuthorUploadImageSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_representation_includes_article_id(self):
        instance = ArticleImage.objects.create(
            article=self.article,
            image=self._get_fresh_image(),
            uploaded_by=self.user
        )
        serializer = AuthorUploadImageSerializer(instance)
        data = serializer.data
        self.assertEqual(data['article_id'], self.article.pk)
        self.assertIn('id', data)


class TestAuthorArticleRequestSerializer(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone='+989123456789', password='testPass123?')
        self.other_user = User.objects.create_user(phone='+989111111111', password='testPass123?')
        
        self.article = Article.objects.create(
            title='test-article-slug',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc'
        )
        self.other_article = Article.objects.create(
            title='other-article-slug',
            author=self.other_user,
            content={"blocks": []},
            short_description='Test short desc'
        )
        
        self.context = {'request': type('Request', (), {'user': self.user})}

    def test_successful_creation_add_action(self):
        data = {
            'action': 'add',
            'data': {'title': 'New Article', 'content': '{"blocks": []}'},
            'comments': 'Please publish this'
        }
        serializer = AuthorArticleRequestSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()
        
        self.assertEqual(instance.author, self.user)
        self.assertEqual(instance.action, 'add')
        self.assertEqual(instance.status, 'draft')
        self.assertIsNone(instance.admin_response)
        self.assertIsNone(instance.target_id)

    def test_successful_creation_update_action(self):
        data = {
            'target_id': self.article.pk,
            'action': 'update',
            'data': {'title': 'Updated Title'},
            'comments': 'Fixing typo'
        }
        serializer = AuthorArticleRequestSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()
        
        self.assertEqual(instance.target_id, self.article.pk)
        self.assertEqual(instance.action, 'update')

    def test_read_only_fields_are_ignored(self):
        data = {
            'action': 'add',
            'data': {'title': 'New'},
            'status': 'approved',
            'admin_response': 'I approved it myself'
        }
        serializer = AuthorArticleRequestSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()
        
        self.assertNotEqual(instance.status, 'approved')
        self.assertIsNone(instance.admin_response)

    def test_to_representation_shows_display_values(self):
        instance = ArticleRequest.objects.create(
            author=self.user,
            action='add',
            status='approved',
            data={'title': 'Test'}
        )
        serializer = AuthorArticleRequestSerializer(instance)
        data = serializer.data
        
        self.assertEqual(data['action'], 'ایجاد')
        self.assertEqual(data['status'], 'تایید شده')

    def test_validation_error_on_full_clean_fail(self):
        data = {
            'target_id': self.other_article.pk,
            'action': 'delete',
            'data': {},  
            'comments': ''  
        }
        serializer = AuthorArticleRequestSerializer(data=data, context=self.context)
        
        self.assertFalse(serializer.is_valid())
        
        self.assertIn('comments', serializer.errors)
        
        self.assertIn('author', serializer.errors)
        
        self.assertEqual(
            serializer.errors['comments'][0], 
            "برای درخواست از نوع حذف باید توضیحات درج شود."
        )