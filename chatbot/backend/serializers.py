from rest_framework import serializers
from .models import Picture, Topic, Comment, Profile
from django.urls import reverse
from django.contrib.auth.models import User
from firebase_admin import auth

from django.contrib.auth import get_user_model

User = get_user_model()

class GeminiPromptSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    model = serializers.CharField(required=False, default="gemini-pro")

class FirebaseAuthSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, data):
        try:
            decoded_token = auth.verify_id_token(data['token'])
            data['uid'] = decoded_token['uid']
            return data
        except Exception as e:
            raise serializers.ValidationError(str(e))

class PictureSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Picture
        fields = ['id', 'user', 'image', 'created_at']

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all())
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'topic', 'content', 'created_at']

    def validate_topic(self, value):
        if not Topic.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Geçersiz gönderi ID'si.")
        return value

class UserSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['username', 'profile_pic']

    def get_profile_pic(self, obj):
        request = self.context.get('request')
        try:
            profile = Profile.objects.get(user=obj)
            if profile.profile_pic:
                return request.build_absolute_uri(profile.profile_pic.url)
            return request.build_absolute_uri('/media/profile_pics/default.png')
        except Profile.DoesNotExist:
            return request.build_absolute_uri('/media/profile_pics/default.png')

class TopicSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)        

    class Meta:
        model = Topic
        fields = [
            'id', 'user', 'topic', 'content', 'created_at',
             'comments',  'image','remove_image',
        ]
        

    def get_image_url(self, obj):
        request = self.context.get('request')
        user = request.user
        if obj.image:
            if user.is_authenticated and (obj.user == user or not obj.is_locked or user in obj.unlocked_by_image.all()):
                return request.build_absolute_uri(obj.image.url)
            return "locked"
        return None    
    
class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    username = serializers.CharField(source='user.username')

    class Meta:
        model = Profile
        fields = ['university', 'year', 'profile_pic', 'email', 'department', 'username', 'points','is_new_user']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if 'email' in user_data:
            instance.user.email = user_data['email']
        if 'username' in user_data:
            instance.user.username = user_data['username']
        instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance    