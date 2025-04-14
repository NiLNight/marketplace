from rest_framework import serializers

from apps.reviews.models import Comment, Review


class CommentSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'review', 'user', 'text', 'created', 'parent', 'children']

    def get_children(self, obj):
        return CommentSerializer(obj.get_children(), many=True).data


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['review', 'text', 'parent']


class ReviewSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'value', 'text', 'created', 'comments', 'likes_count']

    def get_likes_count(self, obj):
        return obj.likes.count()


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['product', 'value', 'text', 'image']
