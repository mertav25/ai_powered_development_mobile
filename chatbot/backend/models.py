from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from firebase_admin import firestore

db = firestore.client()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='profile_pics/default.png')
    firebase_uid = models.CharField(max_length=128, blank=True, null=True)  # Firebase UID'si

    def save_to_firestore(self):
        user_ref = db.collection('users').document(str(self.user.id))
        user_ref.set({
            'username': self.user.username,
            'email': self.user.email,
            'profile_pic_url': self.profile_pic.url if self.profile_pic else None,
        })

    def __str__(self):
        return self.user.username
    
class Picture(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='pictures/')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username}'s picture"    


class Topic(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics')
    topic = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
  
    def get_image_url(self, obj):
        if obj.image:
            try:
                url = self.context['request'].build_absolute_uri(obj.image.url)
                return url
            except Exception as e:
                print(f"Error generating image_url: {e}")
                return None
        return None

    def __str__(self):
        return self.topic

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete()
        if self.pdf_file:
            self.pdf_file.delete()
        if self.word_file:
            self.word_file.delete()
        super().delete(*args, **kwargs)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)  # Varsayılan değer eklendi

    def __str__(self):
        return f"Comment by {self.user.username} on {self.topic.topic}"

