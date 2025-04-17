from rest_framework import serializers
from apps.reviews.models import Review, Comment


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'value', 'text', 'image', 'created', 'updated', 'likes_count']

    def get_likes_count(self, obj):
        return obj.likes.count()


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    children = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'review', 'user', 'text', 'parent', 'created', 'updated', 'children', 'likes_count']

    def get_children(self, obj):
        queryset = obj.cached_children
        serializer = CommentSerializer(queryset, many=True)
        return serializer.data

    def get_likes_count(self, obj):
        return obj.likes.count()


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['product', 'value', 'text', 'image']


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['review', 'text', 'parent']
