from django.test import TestCase
from blog.models import Article, ArticleCategory
from blog.serializers import ArticleRelatedField, CategoryHierarchySerializer, PublicArticleListSerializer
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User, UserProfile, Job, JobCategory, EmployeeProfile
from django.db.models import F


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

    def test_serializer_data(self):
        serializer = PublicArticleListSerializer(self.article)
        data = serializer.data

        self.assertEqual(data['title'], self.article.title)
        self.assertEqual(data['slug'], self.article.slug)
        self.assertEqual(data['short_description'], self.article.short_description)
        self.assertEqual(data['author']['full_name'], f"{self.article.author_first_name} {self.article.author_last_name}")
        self.assertEqual(data['author']['username'], self.article.author_username)
        self.assertIn('published_at', data)
    
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
        self.assertEqual(serializer.data['author']['full_name'], "ali samadi")

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

    def test_handle_empty_values(self):
        self.article.title = ""
        self.article.slug = ""
        self.article.short_description = ""
        self.article.content = {} 
        self.article.save()
        serializer = PublicArticleListSerializer(self.article)
        data = serializer.data
        self.assertEqual(data['title'], "")
        self.assertEqual(data['slug'], "")
        self.assertEqual(data['short_description'], "")

    def test_banner_thumbnail(self):
        serializer = PublicArticleListSerializer(self.article)
        data = serializer.data
        self.assertIsInstance(data['banner_thumbnail'], str)
