from rest_framework.test import APITestCase
from blog.models import ArticleCategory
from accounts.models import User
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User, UserProfile, Job, JobCategory, EmployeeProfile
from blog.models import Article
from django.utils import timezone


class TestArticleFilter(APITestCase):
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

        self.grand_parent_category1 = ArticleCategory.objects.create(name='python')
        self.grand_parent_category2 = ArticleCategory.objects.create(name='java')
        self.grand_parent_category1_child = ArticleCategory.objects.create(
            name='بک اند',
            parent=self.grand_parent_category1
        )
        self.grand_parent_category1_grand_child = ArticleCategory.objects.create(
            name='جنگو',
            parent=self.grand_parent_category1_child
        )

        self.article1 = Article.objects.create(
            title='لیست ها',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()
        )
        self.article2 = Article.objects.create(
            title='آرایه ها',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()

        )
        self.article3 = Article.objects.create(
            title='فریمورک ها',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()
        )
        self.article4 = Article.objects.create(
            title='ویوها',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()
        )
        self.article5 = Article.objects.create(
            title='تست نویسی',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()
        )
        self.article5 = Article.objects.create(
            title='زبان های برنامه نویسی محبوب',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()
        )

        self.article1.categories.add(self.grand_parent_category1)
        self.article2.categories.add(self.grand_parent_category2)
        self.article3.categories.add(self.grand_parent_category1_child)
        self.article4.categories.add(self.grand_parent_category1_grand_child)
        self.article5.categories.add(self.grand_parent_category1, self.grand_parent_category2)

    def test_order_by_published_at_ascending(self):
        response = self.client.get('/articles/?ordering=published')
        
        self.assertEqual(response.data['results'][0]['title'], self.article1.title)
        self.assertEqual(response.data['results'][1]['title'], self.article2.title)
        self.assertEqual(response.data['results'][2]['title'], self.article3.title)
        self.assertEqual(response.data['results'][3]['title'], self.article4.title)
        self.assertEqual(response.data['results'][4]['title'], self.article5.title)

    def test_order_by_published_at_descending(self):
        response = self.client.get('/articles/?ordering=-published')

        self.assertEqual(response.data['results'][0]['title'], self.article5.title)
        self.assertEqual(response.data['results'][1]['title'], self.article4.title)
        self.assertEqual(response.data['results'][2]['title'], self.article3.title)
        self.assertEqual(response.data['results'][3]['title'], self.article2.title)
        self.assertEqual(response.data['results'][4]['title'], self.article1.title)

    def test_filter_by_category(self):
        response = self.client.get(f'/articles/?category=python')

        self.assertEqual(len(response.data['results']), 4)

        titles = [item['title'] for item in response.data['results']]
        self.assertIn(self.article1.title, titles) 
        self.assertIn(self.article3.title, titles)
        self.assertIn(self.article4.title, titles)
        self.assertIn(self.article5.title, titles) 

        response = self.client.get(f'/articles/?category=java')

        self.assertEqual(len(response.data['results']), 2)

        titles = [item['title'] for item in response.data['results']]
        self.assertIn(self.article2.title, titles) 
        self.assertIn(self.article5.title, titles)

        response = self.client.get(f'/articles/?category=بک-اند')

        self.assertEqual(len(response.data['results']), 2)

        titles = [item['title'] for item in response.data['results']]
        self.assertIn(self.article3.title, titles) 
        self.assertIn(self.article4.title, titles)

        response = self.client.get(f'/articles/?category=جنگو')

        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.article4.title)
    




    






        




        


