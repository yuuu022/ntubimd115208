import uuid
from django.db import models
from django.utils import timezone

def get_uuid_str():
    return str(uuid.uuid4())

class UserProfile(models.Model):
    user_id = models.CharField(max_length=255, primary_key=True, default=get_uuid_str, editable=False)
    line_name = models.CharField(max_length=255)
    avatar = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    password = models.CharField(max_length=255)
    birthday = models.DateField(null=True, blank=True)
    create_time = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = 'userprofile'
        managed = False

    def __str__(self):
        return self.line_name
