from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from .serializers import *
from models import *
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation.trans_null import gettext_lazy as _
from django.db.models import Q, Prefetch, Count, F, Exists, OuterRef


class PublicCategoryListView(generics.ListAPIView):
    serializer_class = CategoryHierarchySerializer
    queryset = ArticleCategory.objects.filter(
        parent=None, is_active=True
    ).prefetch_related(
            Prefetch(
                'children',
                queryset=ArticleCategory.objects.filter(is_active=True).order_by('lft'),
                to_attr='prefetched_children'
            )
    ).order_by('lft')


class AuthorCategoryListView(generics.ListAPIView):
    serializer_class = CategoryHierarchySerializer
    queryset = ArticleCategory.objects.filter(
        parent=None, is_active=True
    ).prefetch_related(
            Prefetch(
                'children',
                queryset=ArticleCategory.objects.filter(is_active=True).order_by('lft'),
                to_attr='prefetched_children'
            )
    ).order_by('lft')


class PublicArticleListView(generics.ListAPIView):
    queryset = Article.objects.filter(
        is_published=True,
        is_deleted=False
    ).annotate(
        author_username=F('author__user_profile__employee_profile__username'),
        author_first_name=F('author__first_name'),
        author_last_name=F('author__last_name')
    )
    serializer_class = PublicArticleListSerializer


class PublicArticleDetailView(generics.RetrieveAPIView):
    queryset = Article.objects.filter(
        is_published=True,
        is_deleted=False  
    ).annotate(
        has_active_category=Exists(
            ArticleCategory.objects.filter(
                is_active=True,
                articles=OuterRef('pk')
            )
        )
    ).filter(
        has_active_category=True
    ).annotate(
        author_username=F('author__user_profile__employee_profile__username'),
        author_first_name=F('author__first_name'),
        author_last_name=F('author__last_name')
    ).prefetch_related(
        'tags',
        Prefetch(
            'categories',
            queryset=ArticleCategory.objects.filter(is_active=True),
            to_attr='prefetched_categories'
        )
    )
    serializer_class = PublicArticleDetailSerializer
    lookup_field = 'slug'


class AuthorArticleListView(generics.ListAPIView):
    serializer_class = AuthorArticleListSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        return Article.objects.filter(is_deleted=False, author=self.request.user)
    

class AuthorArticleDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AuthorArticleDetailSerializer
    
    def get_queryset(self):
        return Article.objects.filter(
        is_deleted=False,
        author=self.request.user 
    ).prefetch_related(
        'tags',
        Prefetch(
            'categories',
            queryset=ArticleCategory.objects.all(),
            to_attr='prefetched_categories'
        )
    )
    

class AuthorUploadImageViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AuthorUploadImageSerializer
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request':request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 

class AuthorArticleRequestViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AuthorArticleRequestSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request':request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        queryset = ArticleRequest.objects.filter(author=request.user, is_deleted=False)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = get_object_or_404(ArticleRequest, author=request.user, pk=pk, is_deleted=False)
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def send_request(self, request, pk=None):
        queryset = get_object_or_404(ArticleRequest, author=request.user, pk=pk, is_deleted=False)
        
        check_status = bool(queryset.status in [RequestStatusChoices.DRAFT, RequestStatusChoices.NEED_REVISION])
        if check_status:
            queryset.status = RequestStatusChoices.PENDING
            queryset.save()
            return Response([_("درخواست ارسال شد.")], status=status.HTTP_200_OK)
        return Response([_("امکان ارسال درخواست برای این وضعیت نیست.")], status=status.HTTP_400_BAD_REQUEST)

    def cancel_request(self, request, pk=None):
        queryset = get_object_or_404(ArticleRequest, author=request.user, pk=pk, is_deleted=False)
        
        if queryset.status == RequestStatusChoices.PENDING:
            if queryset.need_revision:
                queryset.status = RequestStatusChoices.NEED_REVISION
            else:
                queryset.status = RequestStatusChoices.DRAFT
            queryset.save()
            return Response([_('درخواست لغو شد.')], status=status.HTTP_200_OK)
        return Response([_("امکان لغو درخواست برای این وضعیت نیست.")], status=status.HTTP_400_BAD_REQUEST)  
    
    def partial_update(self, request, pk=None):
        queryset = get_object_or_404(ArticleRequest, author=request.user, pk=pk, is_deleted=False)
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        
        check_status = bool(queryset.status in [RequestStatusChoices.DRAFT, RequestStatusChoices.NEED_REVISION])
        if not check_status:
            error_message = {"error": _("در این وضعیت امکان ویرایش درخواست وجود ندارد.")}
            return Response(error_message, status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.is_valid():
            try:
                queryset.clean()
                serializer.save()
            except Exception as e:
                raise serializers.ValidationError(str(e))
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        queryset = get_object_or_404(ArticleRequest, author=request.user, pk=pk, is_deleted=False)
        if queryset.status == RequestStatusChoices.DRAFT:
            queryset.is_deleted = True
            try:
                queryset.save()
            except Exception as e:
                raise serializers.ValidationError(str(e))
            return Response([_("با موفقیت حذف شد.")], status=status.HTTP_204_NO_CONTENT)
        return Response([_("امکان حذف ممکن نیست")], status=status.HTTP_400_BAD_REQUEST)
    
