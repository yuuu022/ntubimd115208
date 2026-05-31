from django.db import models
from .PregnancyRecord import PregnancyRecord

class Prenatalrecord(models.Model):
    prenatalrecord_id = models.AutoField(primary_key=True)
    pregnancyrecord = models.ForeignKey(PregnancyRecord, on_delete=models.CASCADE)
    sbp = models.SmallIntegerField(null=True, blank=True)
    dbp = models.SmallIntegerField(null=True, blank=True)
    fetal_heart_rate = models.SmallIntegerField(null=True, blank=True)
    urine_glucose = models.CharField(max_length=4, null=True, blank=True)
    urine_protein = models.CharField(max_length=4, null=True, blank=True)
    edema = models.CharField(max_length=4, null=True, blank=True)
    photo = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'prenatalrecord'
        managed = False

    def __str__(self):
        return f'{self.prenatalrecord_id}'