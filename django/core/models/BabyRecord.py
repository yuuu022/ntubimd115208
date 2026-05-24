from django.db import models
from django.utils import timezone
from .BabyInformation import BabyInformation

#嬰兒紀錄
class BabyRecord(models.Model):
    babyrecord_id = models.BigAutoField(primary_key=True)
    baby = models.ForeignKey(BabyInformation, on_delete=models.CASCADE, db_column='baby_id', related_name='records')
    date = models.DateField()
    record = models.TextField()
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    headcircumference = models.FloatField(null=True, blank=True)
    chestcircumference = models.FloatField(null=True, blank=True)
    photo = models.CharField(max_length=255, null=True, blank=True)
    update_time = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'babyrecord'
        managed = False

    def __str__(self):
        return f"Baby Record: {self.date}"