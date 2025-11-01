from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from serializers import *
from models import *
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation.trans_null import gettext_lazy as _


class AuthorCategorySelectView(generics.ListAPIView):
    serializer_class = CategoryHierarchySerializer
    queryset = ArticleCategory.objects.filter(parent=None, is_active=True, is_special=False)


class PublicCategoryListView(generics.ListAPIView):
    serializer_class = CategoryHierarchySerializer
    queryset = ArticleCategory.objects.filter(parent=None, is_active=True)


class PublicArticleListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status=Article.STATUS.PUBLISHED)
    serializer_class = PublicArticleSerializer
    lookup_field = 'slug'
    

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
    
