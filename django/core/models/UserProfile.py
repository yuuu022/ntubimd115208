from django.db import models
from django.utils import timezone

class UserProfile(models.Model):
    user_id = models.SmallIntegerField(primary_key=True)
    line_id = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    avatar = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=20)
    birthday = models.DateField(null=True, blank=True)
    create_time = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'userprofile'
        managed = False  # 保持你原本的設定（由你手動管理資料庫表結構）

    def __str__(self):
        return self.name

    @property
    def line_name(self):
        # compatibility alias: templates and code use `line_name` while the DB column is `line_id`
        return self.line_id

    @line_name.setter
    def line_name(self, value):
        self.line_id = value
