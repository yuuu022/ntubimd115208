from django.db import models
from .PregnancyCase import PregnancyCase

#懷孕紀錄
class PregnancyRecord(models.Model):
    pregnancyrecord_id = models.BigAutoField(primary_key=True)
    pregnancycase = models.ForeignKey(PregnancyCase, on_delete=models.CASCADE, db_column='pregnancycase_id', related_name='records')
    check_date = models.DateTimeField()
    record = models.TextField()
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'pregnancyrecord'
        managed = False

    def __str__(self):
        return f"Pregnancy Record: {self.check_date}"