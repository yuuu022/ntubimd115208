from django.db import models
from .UserProfile import UserProfile

#懷孕紀錄
class PregnancyRecord(models.Model):
    pregnancyrecord_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    check_date = models.DateTimeField()
    record = models.TextField()
    weight = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'pregnancyrecord'
        managed = False

    def __str__(self):
        return f"Pregnancy Record: {self.check_date}"