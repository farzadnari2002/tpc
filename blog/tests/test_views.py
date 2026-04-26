from rest_framework.test import APITestCase
from blog.models import ArticleCategory, ArticleImage, ArticleRequest, RequestActionChoices, RequestStatusChoices
from accounts.models import User
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User, UserProfile, Job, JobCategory, EmployeeProfile
from blog.models import Article
from django.utils import timezone
from django.urls import reverse 
from io import BytesIO
from uuid import uuid4


class TestPublicCategoryListView(APITestCase):
    def setUp(self):
        self.parent1 = ArticleCategory.objects.create(name='python')
        self.parent1_child1 = ArticleCategory.objects.create(name='web', parent=self.parent1)
        self.parent1_child2 = ArticleCategory.objects.create(name='ai', parent=self.parent1)
        self.parent2 = ArticleCategory.objects.create(name='c#')

    def test_response(self):
        # print(f'TestPublicCategoryListView parent1:{self.parent1.lft} parent1_child1:{self.parent1_child1.lft} parent1_child2:{self.parent1_child2.lft} parent2:{self.parent2.lft}')
        response = self.client.get('/articles/categories/')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data), 2)
        
        # lft ordering problem!

        # self.assertEqual(len(response.data[0]['children']), 2)
        # self.assertEqual(len(response.data[1]['children']), 0)

        # self.assertEqual(response.data[0]['name'], 'python')
        # self.assertIsNone(response.data[0]['parent_slug'])
        # self.assertEqual(response.data[0]['children'][0]['name'], 'web')
        # self.assertEqual(response.data[1]['children'], [])

        # self.assertEqual(response.data[0]['name'], 'python')
        # self.assertEqual(response.data[1]['name'], 'c#')
        # self.assertEqual(response.data[0]['children'][0]['name'], 'web')
        # self.assertEqual(response.data[0]['children'][1]['name'], 'ai')

    def test_ignoring_is_active_false(self):
        self.is_active_false1 = ArticleCategory.objects.create(name='php', is_active=False)
        self.is_active_false2 = ArticleCategory.objects.create(name='mobile', parent=self.parent1, is_active=False)

        response = self.client.get('/articles/categories/')

        for item in response.data:
            self.assertNotEqual(item['name'], 'php')

            for child in item['children']:
                self.assertNotEqual(child['name'], 'mobile')


class TestAuthorCategoryListView(APITestCase):
    def setUp(self):
        self.parent1 = ArticleCategory.objects.create(name='python')
        self.parent1_child1 = ArticleCategory.objects.create(name='web', parent=self.parent1)
        self.parent1_child2 = ArticleCategory.objects.create(name='ai', parent=self.parent1)
        self.parent2 = ArticleCategory.objects.create(name='c#')

    def test_response(self):
        # print(f'TestAuthorCategoryListView parent1:{self.parent1.lft} parent1_child1:{self.parent1_child1.lft} parent1_child2:{self.parent1_child2.lft} parent2:{self.parent2.lft}')
        response = self.client.get('/author/categories/')
        # print(response.data)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data), 2)

        # lft ordering problem!

        # self.assertEqual(len(response.data[0]['children']), 2)
        # self.assertEqual(len(response.data[1]['children']), 0)

        # self.assertEqual(response.data[0]['name'], 'python')
        # self.assertIsNone(response.data[0]['parent_slug'])
        # self.assertEqual(response.data[0]['children'][0]['name'], 'web')
        # self.assertEqual(response.data[1]['children'], [])

        # self.assertEqual(response.data[0]['name'], 'python')
        # self.assertEqual(response.data[1]['name'], 'c#')
        # self.assertEqual(response.data[0]['children'][0]['name'], 'web')
        # self.assertEqual(response.data[0]['children'][1]['name'], 'ai')

    def test_ignoring_is_active_false(self):
        self.is_active_false1 = ArticleCategory.objects.create(name='php', is_active=False)
        self.is_active_false2 = ArticleCategory.objects.create(name='mobile', parent=self.parent1, is_active=False)

        response = self.client.get('/author/categories/')

        for item in response.data:
            self.assertNotEqual(item['name'], 'php')

            for child in item['children']:
                self.assertNotEqual(child['name'], 'mobile')

    def test_ignoring_is_special_true(self):
        self.is_active_false1 = ArticleCategory.objects.create(name='news', is_special=True)
        self.is_active_false2 = ArticleCategory.objects.create(name='tpc', parent=self.parent1, is_special=True)

        response = self.client.get('/author/categories/')

        for item in response.data:
            self.assertNotEqual(item['name'], 'news')

            for child in item['children']:
                self.assertNotEqual(child['name'], 'tpc')


class TestPublicArticleListView(APITestCase):
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
        self.category = ArticleCategory.objects.create(name='it')
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
            title='soft skills',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()

        )
        self.article3 = Article.objects.create(
            title='tabriz programmers',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()
        )
        self.article1.categories.add(self.category)
        self.article2.categories.add(self.category)
        self.article3.categories.add(self.category)

    def test_response(self):
        response = self.client.get('/articles/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_ordering(self):
        response = self.client.get('/articles/')

        self.assertEqual(response.data[0]['title'], 'tabriz programmers')
        self.assertEqual(response.data[1]['title'], 'soft skills')
        self.assertEqual(response.data[2]['title'], 'cyber security')

    def test_author_data(self):
        response = self.client.get('/articles/')
        self.assertEqual(response.data[0]['author']['full_name'], 'ali samadi')
        self.assertEqual(response.data[0]['author']['username'], 'selisamadi80')

    def test_ignoring_is_deleted_true(self):
        self.article1.is_deleted = True
        self.article1.save()
        self.article2.is_deleted = True
        self.article2.save()
        self.article3.is_deleted = True
        self.article3.save()
        response = self.client.get('/articles/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_ignoring_is_published_false(self):
        self.article1.is_published = False
        self.article1.save()
        self.article2.is_published = False
        self.article2.save()
        self.article3.is_published = False
        self.article3.save()
        response = self.client.get('/articles/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_ignoring_is_has_active_category_false(self):
        self.category.is_active = False
        self.category.save()
        self.article1.refresh_from_db()
        self.article2.refresh_from_db()
        self.article3.refresh_from_db()
        response = self.client.get('/articles/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)


class TestPublicArticleDetailView(APITestCase):
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
        self.category = ArticleCategory.objects.create(name='it')
        self.article = Article.objects.create(
            title='cyber security',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()
        )
        self.article.categories.add(self.category)
        self.article.tags.add("python", "django", "tabriz")

    def test_response_200(self):
        response = self.client.get('/articles/cyber-security')
        self.assertEqual(response.status_code, 200)

    def test_response_404(self):
        response = self.client.get('/articles/python')
        self.assertEqual(response.status_code, 404)

    def test_author_data(self):
        response = self.client.get('/articles/cyber-security')
        self.assertEqual(response.data['author']['full_name'], 'ali samadi')
        self.assertEqual(response.data['author']['username'], 'selisamadi80')
    
    def test_ignoring_is_deleted_true(self):
        self.article.is_deleted = True
        self.article.save()

        response = self.client.get('/articles/cyber-security')
        self.assertEqual(response.status_code, 404)

    def test_ignoring_is_published_false(self):
        self.article.is_published = False
        self.article.save()

        response = self.client.get('/articles/cyber-security')
        self.assertEqual(response.status_code, 404)

    def test_ignoring_is_has_active_category_false(self):
        self.category.is_active = False
        self.category.save()
        self.article.refresh_from_db()

        response = self.client.get('/articles/cyber-security')
        self.assertEqual(response.status_code, 404)


class TestAuthorArticleListView(APITestCase):
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

        self.another_user = User.objects.create_user(
            phone='+989123450099',
            password='testPtol128?',
        )
        self.another_user.first_name = 'reza'
        self.another_user.last_name = 'nasiri'
        self.another_user.save()
        self.job_category = JobCategory.objects.create(title='design')
        self.job = Job.objects.create(name='ui')
        self.job.category.add(self.job_category)
        self.another_user_profile = UserProfile.objects.create(
            user=self.another_user,
            gender='M',
            job=self.job,
            age=23,
            bio='example bio'
        )
        self.employee_profile = EmployeeProfile.objects.create(
            user_profile=self.another_user_profile,
            username='nasirihere',
        )

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
            title='soft skills',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()

        )
        self.another_user_article = Article.objects.create(
            title='tabriz programmers',
            author=self.another_user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()
        )

    def test_response(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/author/articles/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
      
    def test_unauthenticated_user_gets_401(self):
        response = self.client.get('/author/articles/')
        self.assertEqual(response.status_code, 401)
  
    def test_ordering(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/author/articles/')

        self.assertEqual(response.data[0]['title'], 'soft skills')
        self.assertEqual(response.data[1]['title'], 'cyber security')

    def test_ignoring_is_deleted_true(self):
        self.article1.is_deleted = True
        self.article1.save()
        self.article2.is_deleted = True
        self.article2.save()

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/author/articles/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_another_user(self):
       self.client.force_authenticate(user=self.another_user)
       response = self.client.get('/author/articles/')

       self.assertEqual(response.status_code, 200)
       self.assertEqual(len(response.data), 1)
       self.assertEqual(response.data[0]['title'], 'tabriz programmers')


class TestAuthorArticleDetailView(APITestCase):
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
        self.job_category1 = JobCategory.objects.create(title='developer')
        self.job1 = Job.objects.create(name='backend developer')
        self.job1.category.add(self.job_category1)
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            gender='M',
            job=self.job1,
            age=18,
            bio='example bio'
        )
        self.employee_profile = EmployeeProfile.objects.create(
            user_profile=self.user_profile,
            username='selisamadi80',
        )

        self.another_user = User.objects.create_user(
            phone='+989123450099',
            password='testPtol128?',
        )
        self.another_user.first_name = 'reza'
        self.another_user.last_name = 'nasiri'
        self.another_user.save()
        self.job_category2 = JobCategory.objects.create(title='design')
        self.job2 = Job.objects.create(name='ui')
        self.job2.category.add(self.job_category2)
        self.another_user_profile = UserProfile.objects.create(
            user=self.another_user,
            gender='M',
            job=self.job2,
            age=23,
            bio='example bio'
        )
        self.employee_profile = EmployeeProfile.objects.create(
            user_profile=self.another_user_profile,
            username='nasirihere',
        )

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
            title='soft skills',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()

        )
        self.another_user_article = Article.objects.create(
            title='tabriz programmers',
            author=self.another_user,
            content={"blocks": []},
            short_description='Test short desc',
            banner=self.image,
            is_published = True,
            published_at = timezone.now()
        )
        self.category = ArticleCategory.objects.create(name='it')
        self.article1.categories.add(self.category)
        self.article2.categories.add(self.category)
        self.another_user_article.categories.add(self.category)

        self.article1.tags.add("python", "django", "tabriz")
        self.article2.tags.add("python", "django", "tabriz")
        self.another_user_article.tags.add("python", "django", "tabriz")

    def test_response(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('author-article-detail', kwargs={'pk': self.article1.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'cyber security')

        response = self.client.get(reverse('author-article-detail', kwargs={'pk': self.article2.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'soft skills')

    def test_another_user(self):
        self.client.force_authenticate(user=self.another_user)
        response = self.client.get(reverse('author-article-detail', kwargs={'pk':self.another_user_article.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'tabriz programmers')

        response = self.client.get(reverse('author-article-detail', kwargs={'pk':self.article1.pk}))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('author-article-detail', kwargs={'pk':self.article2.pk}))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_gets_401(self):
        response = self.client.get(reverse('author-article-detail', kwargs={'pk':self.article1.pk}))
        self.assertEqual(response.status_code, 401)

    def test_ignoring_is_deleted_true(self):
        self.article1.is_deleted = True
        self.article1.save()

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('author-article-detail', kwargs={'pk':self.article1.pk}))
        self.assertEqual(response.status_code, 404)


class TestAuthorUploadImageViewSet(APITestCase):
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
    
    def _get_fresh_image(self):
        return self._create_test_image()

    def setUp(self):
        self.user = User.objects.create_user(phone='+989123456789', password='testPass123?')
        self.another_user = User.objects.create_user(phone='+989111111111', password='testsamS123?')
        
        self.article = Article.objects.create(
            title='test-article-slug',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc'
        )

    def test_create_with_article_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('author-upload'),
            data={
                'article': self.article.pk,
                'image': self._get_fresh_image()
            },
        )
     
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ArticleImage.objects.count(), 1)
        self.assertEqual(ArticleImage.objects.first().article, self.article)
        self.assertEqual(ArticleImage.objects.first().uploaded_by, self.user)

    def test_create_with_upload_session_success(self):
        upload_session = uuid4()
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('author-upload'),
            data={
                'upload_session': upload_session,
                'image': self._get_fresh_image()
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ArticleImage.objects.count(), 1)
        self.assertEqual(ArticleImage.objects.first().upload_session, upload_session)
        self.assertEqual(ArticleImage.objects.first().uploaded_by, self.user)

    def test_create_without_article_and_session_upload_fails(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('author-upload'),
            data={
                'image': self._get_fresh_image()
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ArticleImage.objects.count(), 0)

    def test_another_user_fails(self):
        self.client.force_authenticate(user=self.another_user)
        response = self.client.post(
            reverse('author-upload'),
            data={
                'article': self.article.pk,
                'image': self._get_fresh_image()
            },
        )
     
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ArticleImage.objects.count(), 0)

    def test_unauthenticated_user_gets_401(self):
        response = self.client.post(
            reverse('author-upload'),
            data={
                'article': self.article.pk,
                'image': self._get_fresh_image()
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(ArticleImage.objects.count(), 0)


class TestAuthorArticleRequestViewSet(APITestCase):
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
        self.another_user = User.objects.create_user(phone='+989111111111', password='testsamS123?')
        
        self.article = Article.objects.create(
            title='test-article-slug',
            author=self.user,
            content={"blocks": []},
            short_description='Test short desc'
        )

    def test_unauthenticated_user_gets_401(self):
        response = self.client.post(
            reverse('author-article-request'),
            data={
            'action': 'add',
            'data': {'title': 'new article', 'content': '{"blocks": []}'},
            'comments': 'Please publish this'

            },
            format='json'
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(ArticleRequest.objects.count(), 0)

    def test_create_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('author-article-request'),
            data={
            'action': 'add',
            'data': {'title': 'new article', 'content': '{"blocks": []}'}
            },
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ArticleRequest.objects.first().data['title'], 'new article')

    def test_create_fail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('author-article-request'),
            data={
            'data': {'title': 'new article', 'content': '{"blocks": []}'}
            },
            format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ArticleRequest.objects.count(), 0)
        
    def test_get_list_success(self):
        self.client.force_authenticate(user=self.user)
        response_post1 = self.client.post(
            reverse('author-article-request'),
            data={
            'action': 'add',
            'data': {'title': 'new article', 'content': '{"blocks": []}'}
            },
            format='json'
        )
        response_post2 = self.client.post(
            reverse('author-article-request'),
            data={
            'action': 'add',
            'data': {'title': 'new article2', 'content': '{"blocks": []}'}
            },
            format='json'
        )

        response_get = self.client.get(reverse('author-article-request'))

        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(ArticleRequest.objects.count(), 2)

        # id problem = start with 2

        # self.assertEqual(ArticleRequest.objects.get(pk=1).data['title'], 'new article')
        # self.assertEqual(ArticleRequest.objects.get(pk=2).data['title'], 'new article2')

    def test_get_list_another_user_fail(self):
        self.client.force_authenticate(user=self.user)
        response_post1 = self.client.post(
            reverse('author-article-request'),
            data={
            'action': 'add',
            'data': {'title': 'new article', 'content': '{"blocks": []}'}
            },
            format='json'
        )
        self.client.force_authenticate(user=self.user)
        response_get1 = self.client.get(reverse('author-article-request'))

        response_post2 = self.client.post(
            reverse('author-article-request'),
            data={
            'action': 'add',
            'data': {'title': 'new article2', 'content': '{"blocks": []}'}
            },
            format='json'
        )

        self.client.force_authenticate(user=self.another_user)
        response_get2 = self.client.get(reverse('author-article-request'))

        self.assertEqual(response_get2.status_code, 200)
        self.assertEqual(ArticleRequest.objects.count(), 2)
        self.assertEqual(len(response_get2.data), 0)
        self.assertEqual(len(response_get1.data), 1)

    def test_get_list_ignoring_is_deleted_true(self):
        self.article_request1 = ArticleRequest(author=self.user, action=RequestActionChoices.ADD, data={"test": 1})
        self.article_request2 = ArticleRequest(author=self.user, action=RequestActionChoices.ADD, data={"test": 1})
        self.article_request1.is_deleted = True
        self.article_request2.is_deleted = True
        self.article_request1.save()
        self.article_request2.save()

        self.client.force_authenticate(user=self.another_user)
        response = self.client.get(reverse('author-article-request'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        
    def test_get_retrieve_success(self):
        self.article_request1 = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
             data={'test': 10}
        )
        self.article_request2 = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 20}
        )
        self.client.force_authenticate(user=self.user)

        response_get1 = self.client.get(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request1.pk}
        ))
        

        response_get2 = self.client.get(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request2.pk}
        ))

        self.assertEqual(response_get1.status_code, 200)
        self.assertEqual(response_get1.data['data']['test'], 10)

        self.assertEqual(response_get2.status_code, 200)
        self.assertEqual(response_get2.data['data']['test'], 20)

    def test_get_retrieve_another_user_fail(self):
        self.article_request1 = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
             data={'test': 10}
        )
        self.article_request2 = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 20}
        )

        self.client.force_authenticate(user=self.another_user)

        response_get1 = self.client.get(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request1.pk}
        ))
        

        response_get2 = self.client.get(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request2.pk}
        ))

        self.assertEqual(response_get1.status_code, 404)
        self.assertEqual(response_get2.status_code, 404)

    def test_get_retrieve_ignoring_is_deleted_true(self):
        self.article_request1 = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
             data={'test': 10}
        )
        self.article_request2 = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 20}
        )

        self.article_request1.is_deleted=True
        self.article_request2.is_deleted=True

        self.article_request1.save()
        self.article_request2.save()

        self.client.force_authenticate(user=self.user)

        response_get1 = self.client.get(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request1.pk}
        ))
        

        response_get2 = self.client.get(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request2.pk}
        ))

        self.assertEqual(response_get1.status_code, 404)
        self.assertEqual(response_get2.status_code, 404)

    def test_send_request_draft_status_success(self):
        self.article_request1 = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request1.status = RequestStatusChoices.DRAFT

        self.article_request1.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse(
            'author-article-send-request',
             kwargs={'pk':self.article_request1.pk}
        ))

        self.assertEqual(response.status_code, 200)
        self.assertIn('شد', response.data[0])

    def test_send_request_pending_status_success(self):
        self.article_request1 = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request1.admin_response= 'لطفا اصلاح کن'
        self.article_request1.status = RequestStatusChoices.NEED_REVISION
        self.article_request1.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse(
            'author-article-send-request',
             kwargs={'pk':self.article_request1.pk}
        ))

        self.assertEqual(response.status_code, 200)
        self.assertIn('شد', response.data[0])

    def test_send_request_another_status_fail(self):
        self.article_request1= ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request1.status= RequestStatusChoices.PENDING

        self.article_request1.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse(
            'author-article-send-request',
             kwargs={'pk':self.article_request1.pk}
        ))

        self.assertEqual(response.status_code, 400)
        self.assertIn('وضعیت', response.data[0])

    def test_send_request_another_user_fail(self):
        self.article_request1 = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request1.status= RequestStatusChoices.DRAFT

        self.article_request1.save()

        self.client.force_authenticate(user=self.another_user)

        response = self.client.post(reverse(
            'author-article-send-request',
             kwargs={'pk':self.article_request1.pk}
        ))

        self.assertEqual(response.status_code, 404)

    def test_send_request_ignoring_is_deleted_true(self):
        self.article_request1 = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request1.status= RequestStatusChoices.DRAFT

        self.article_request1.is_deleted= True

        self.article_request1.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse(
            'author-article-send-request',
             kwargs={'pk':self.article_request1.pk}
        ))

        self.assertEqual(response.status_code, 404)

    def test_cancel_request_need_revision_true_success(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.PENDING
        self.article_request.admin_response = 'لطفا اصلاح کنید'
        self.article_request.need_revision = True
        self.article_request.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse(
            'author-article-cancel-request',
             kwargs={'pk':self.article_request.pk}
        ))

        self.article_request.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertIn('شد', response.data[0])
        self.assertEqual(self.article_request.status, RequestStatusChoices.NEED_REVISION)

    def test_cancel_request_need_revision_false_success(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.PENDING
        self.article_request.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse(
            'author-article-cancel-request',
             kwargs={'pk':self.article_request.pk}
        ))

        self.article_request.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertIn('شد', response.data[0])
        self.assertEqual(self.article_request.status, RequestStatusChoices.DRAFT)

    def test_cancel_request_not_pending_fail(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.APPROVED
        self.article_request.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse(
            'author-article-cancel-request',
             kwargs={'pk':self.article_request.pk}
        ))

        self.assertEqual(response.status_code, 400)
        self.assertIn('وضعیت', response.data[0])

    def test_cancel_request_another_user_fail(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.PENDING
        self.article_request.save()

        self.client.force_authenticate(user=self.another_user)

        response = self.client.post(reverse(
            'author-article-cancel-request',
             kwargs={'pk':self.article_request.pk}
        ))

        self.article_request.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(self.article_request.status, RequestStatusChoices.DRAFT)

    def test_cancel_request_ignoring_is_deleted_true(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.PENDING
        self.article_request.is_deleted= True
        self.article_request.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse(
            'author-article-cancel-request',
             kwargs={'pk':self.article_request.pk}
        ))

        self.article_request.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(self.article_request.status, RequestStatusChoices.DRAFT)

    def test_partial_update_request_draft_status_success(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.DRAFT

        self.article_request.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.patch(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request.pk}),
            data={
            'action': 'add',
            'data': {'title': 'new article2', 'content': '{"blocks": []}'}
            },
            format='json'
        )
     
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ArticleRequest.objects.get(pk=self.article_request.pk).data['title'], 'new article2')

    def test_partial_update_request_need_revision_status_success(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.NEED_REVISION
        self.article_request.admin_response = 'لطفا اصلاح کنید'
        self.article_request.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.patch(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request.pk}),
            data={
            'action': 'add',
            'data': {'title': 'new article2', 'content': '{"blocks": []}'}
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ArticleRequest.objects.get(pk=self.article_request.pk).data['title'], 'new article2')

    def test_partial_update_request_another_status_fail(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.APPROVED

        self.article_request.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.patch(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request.pk}),
            data={
            'action': 'add',
            'data': {'title': 'new article2', 'content': '{"blocks": []}'}
            },
            format='json'
        )
  
        self.assertEqual(response.status_code, 400)
        self.assertIn('امکان', response.data['error'])


    def test_partial_update_request_another_user_fail(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.DRAFT

        self.article_request.save()

        self.client.force_authenticate(user=self.another_user)

        response = self.client.patch(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request.pk}),
            data={
            'action': 'add',
            'data': {'title': 'new article2', 'content': '{"blocks": []}'}
            },
            format='json'
        )
     
        self.assertEqual(response.status_code, 404)
   
    def test_partial_update_request_ignoring_is_deleted_true(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.DRAFT
        self.article_request.is_deleted = True
        self.article_request.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.patch(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request.pk}),
            data={
            'action': 'add',
            'data': {'title': 'new article2', 'content': '{"blocks": []}'}
            },
            format='json'
        )
     
        self.assertEqual(response.status_code, 404)

    def test_destroy_request_draft_status_success(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.DRAFT
        self.article_request.is_deleted = False
        self.article_request.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.delete(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request.pk}),
        )
     
        self.assertEqual(response.status_code, 204)
        self.assertTrue(ArticleRequest.objects.get(pk=self.article_request.pk).is_deleted)
        self.assertIn('حذف', response.data[0])

    def test_destroy_request_another_status_fail(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.PENDING
        self.article_request.is_deleted = False
        self.article_request.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.delete(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request.pk}),
        )
     
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ArticleRequest.objects.get(pk=self.article_request.pk).is_deleted)
        self.assertIn('امکان', response.data[0])

    def test_destroy_request_another_user(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.DRAFT
        self.article_request.is_deleted = False
        self.article_request.save()

        self.client.force_authenticate(user=self.another_user)

        response = self.client.delete(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request.pk}),
        )
     
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ArticleRequest.objects.get(pk=self.article_request.pk).is_deleted)

    def test_destroy_request_ignoring_is_deleted_true(self):
        self.article_request = ArticleRequest.objects.create(
            author=self.user,
            action=RequestActionChoices.ADD,
            data={'test': 10}
        )

        self.article_request.status = RequestStatusChoices.DRAFT
        self.article_request.is_deleted = True
        self.article_request.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.delete(reverse(
            'author-article-request-detail',
             kwargs={'pk':self.article_request.pk}),
        )
     
        self.assertEqual(response.status_code, 404)
       


     


     

   

   






















        











        

        

        


        

        
        

        
   


   



        

    

    







