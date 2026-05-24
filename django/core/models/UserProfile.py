import uuid
from django.db import models
from django.utils import timezone

class UserProfile(models.Model):
    # 💡 直接改用 uuid.uuid4（記得後面不要加括號）
    user_id = models.CharField(max_length=255, primary_key=True, default=uuid.uuid4, editable=False)
    line_name = models.CharField(max_length=255)
    avatar = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    password = models.CharField(max_length=255)
    birthday = models.DateField(null=True, blank=True)
    create_time = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = 'userprofile'
        managed = False  # 保持你原本的設定（由你手動管理資料庫表結構）

    def __str__(self):
        return self.line_name