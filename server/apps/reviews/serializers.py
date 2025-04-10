from rest_framework import serializers

from apps.reviews.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'review', 'user', 'text', 'create_time', 'parent', 'children']

    def get_children(self, obj):
        return CommentSerializer(obj.get_children(), many=True).data
