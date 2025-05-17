from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from knox.views import LogoutView
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
from . import serializers, models
from .models import Picture, Comment, Topic, Profile, UnlockedContent, PointTransaction
from .serializers import PictureSerializer, CommentSerializer, TopicSerializer, ProfileSerializer, UnlockContentSerializer, PointTransactionSerializer
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta
import json
import os
from knox.models import AuthToken

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    if not all([username, password, email]):
        return Response({'error': 'Tüm alanlar zorunludur!'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Bu kullanıcı adı alınmış!'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Bu email zaten kayıtlı!'}, status=400)

    try:
        user = User.objects.create_user(username=username, password=password, email=email)
        # Mevcut token'ları sil (çakışmayı önlemek için)
        AuthToken.objects.filter(user=user).delete()
        # Yeni token oluştur
        _, token = AuthToken.objects.create(user=user)
        return Response({
            'username': user.username,
            'email': user.email,
            'token': token
        }, status=201)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_comment(request):
    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPI(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        _, token = AuthToken.objects.create(user)
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            },
            "token": token
        })

class LogoutAPI(LogoutView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

class TopicViewSet(ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        topic = serializer.save(user=self.request.user)
        profile = Profile.objects.get(user=self.request.user)    

        def perform_update(self, serializer):
            topic = serializer.save()
        if topic.is_locked and (topic.image or topic.pdf_file or topic.word_file):
            Profile.objects.filter(user=self.request.user).update(
                points=max(0, self.request.user.profile.points + 15)
            )
            PointTransaction.objects.create(
                user=self.request.user,
                points=15,
                description=f"Kilitli gönderi güncellendi: {topic.topic}"
            )

    def perform_destroy(self, serializer):
        topic = self.get_object()
        if topic.user != self.request.user:
            raise PermissionDenied("Bu gönderiyi silme yetkiniz yok.")

class PictureViewSet(ModelViewSet):
    queryset = Picture.objects.all()
    serializer_class = PictureSerializer
    permission_classes = [IsAuthenticated]

class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        topic = Topic.objects.get(id=self.request.data['topic'])
        # Kendi gönderinize yorum yapabilirsiniz, ancak puan kazanmazsınız
        comment = serializer.save(user=self.request.user, topic=topic)
        if topic.user != self.request.user:
            # Başka kullanıcının gönderisine yorum yapan kullanıcıya 5 puan
            Profile.objects.filter(user=self.request.user).update(
                points=max(0, self.request.user.profile.points + 5)
            )
            PointTransaction.objects.create(
                user=self.request.user,
                points=5,
                description=f"Yorum yapıldı: {topic.topic}"
            )

    def perform_update(self, serializer):
        comment = self.get_object()
        if comment.user != self.request.user:
            raise PermissionDenied("Bu yorumu düzenleme yetkiniz yok.")
        serializer.save()

    def perform_destroy(self, serializer):
        comment = self.get_object()
        if comment.user != self.request.user:
            raise PermissionDenied("Bu yorumu silme yetkiniz yok.")
        comment.delete()

    def get_serializer_context(self):
        # Serializer için request bağlamını geçir
        context = super().get_serializer_context()
        context['request'] = self.request
        return context      


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=request.user)
        serializer = ProfileSerializer(profile)
        print('Returning profile data:', serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=request.user)
        print('Received data:', request.data)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        print('Serializer errors:', serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)