from django.test import TestCase
from blog.models import Article, ArticleCategory
from blog.serializers import ArticleRelatedField, CategoryHierarchySerializer
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



