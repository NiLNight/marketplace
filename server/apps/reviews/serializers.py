from rest_framework import serializers

from apps.reviews.models import Comment, Review


class CommentSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'review', 'user', 'text', 'create_time', 'parent', 'children']

    def get_children(self, obj):
        return CommentSerializer(obj.get_children(), many=True).data


class ReviewSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'value', 'text', 'created', 'comments']


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['product', 'value', 'text']


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['review', 'text', 'parent']
