from rest_framework import serializers
from .models import *
from taggit.serializers import TagListSerializerField, TaggitSerializer
from accounts.models import User
from utils import BaseNameRelatedField


class ArticleRelatedField(BaseNameRelatedField):
    model = Article
    display_field = 'title'


class AuthorSerializer(serializers.ModelSerializer):
    avatar_thumbnail = serializers.ImageField(source='user_profile.avatar_thumbnail', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'avatar_thumbnail']


class CategoryHierarchySerializer(serializers.ModelSerializer):
    """
    This serializer is used to display the hierarchy of all categories,
    including parent and child categories. It helps users understand
    the structure of categories within the system.
    """
    
    children = serializers.SerializerMethodField()
    parent_slug = serializers.SerializerMethodField()
    class Meta:
        model = ArticleCategory
        fields = ['name', 'slug', 'parent_slug', 'childrens']

    def get_parent_slug(self, obj):
        return obj.parent.slug if obj.parent else None
    
    def get_childrens(self, obj):
        return ArticleCategorySerializer(obj.childrens, many=True).data
    

class PublicArticleSerializer(TaggitSerializer, serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    banner_thumbnail = serializers.ImageField(read_only=True)
    tags = TagListSerializerField()
    category = serializers.SlugRelatedField(
        many=True,
        slug_field='slug',
        queryset=ArticleCategory.objects.filter(is_active=True)
    )

    class Meta:
        model = Article
        fields = (
            'author','title', 'slug', 'banner', 'banner_thumbnail',
            'category', 'content', 'short_description', 'tags',
            'created_at', 'updated_at', 'published_at',
        )


class AuthorUploadImageSerializer(serializers.ModelSerializer):
    article = ArticleRelatedField(
        queryset=Article.objects.filter(is_deleted=False),
        required=False, allow_null=True
    )
    article_id = serializers.IntegerField(source='article.pk', read_only=True)

    class Meta:
        model = ArticleImage
        fields = ('article_id' ,'article', 'id', 'image', 'alt_text', 'order', 'upload_session')
        read_only_fields = ('id', 'article_id')
        
    def create(self, validated_data):
        user = self.context['request'].user
        article_image = ArticleImage(**validated_data, uploaded_by=user)
        
        try:
            article_image.full_clean()
            article_image.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        return article_image

    def validate(self, attrs):
        article = attrs.get('article', None)
        upload_session = attrs.get('upload_session', None)

        if not article and not upload_session:
            raise serializers.ValidationError("یا article یا upload_session را بفرستید.")
        request = self.context.get('request')
        if article and request:
            user = request.user
            if article.author != user and not user.has_perm('articles.change_article'):
                raise serializers.ValidationError("شما اجازه آپلود برای این مقاله را ندارید.")
        return attrs
    

class AuthorArticleRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleRequest
        fields = (
            'id', 'target_id', 'action',
            'status', 'comments', 'admin_response',
            'data',
        )
        extra_kwargs = {
            'status': {'read_only': True},
            'admin_response': {'read_only': True},
        }
        
    def create(self, validated_data):
        user = self.context['request'].user
        
        article_request = ArticleRequest(**validated_data, author=user)
        
        try:
            article_request.full_clean()
            article_request.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['action'] = instance.get_action_display()
        representation['status'] = instance.get_status_display()
        return representation
