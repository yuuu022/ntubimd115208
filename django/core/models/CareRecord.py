from django.db import models
from django.utils import timezone
import datetime
from zoneinfo import ZoneInfo

from .CareStatus import CareStatus
from .UserProfile import UserProfile


class CareRecord(models.Model):
    carerecord_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, db_column='user_id', related_name='care_records')
    carestatus = models.ForeignKey(CareStatus, on_delete=models.CASCADE, db_column='carestatus_id', related_name='care_records')
    recordtime = models.DateTimeField()
    content = models.CharField(max_length=255, null=True, blank=True)
    state = models.BooleanField(default=False)
    def _taipei_now():
        # return naive datetime representing current time in Asia/Taipei
        return datetime.datetime.now(ZoneInfo('Asia/Taipei')).replace(tzinfo=None)

    create_time = models.DateTimeField(default=_taipei_now)

    class Meta:
        db_table = 'carerecord'
        managed = False

    def __str__(self):
        status_label = self.carestatus.carestatus if self.carestatus_id else '-'
        return f"{self.recordtime} {status_label}"
