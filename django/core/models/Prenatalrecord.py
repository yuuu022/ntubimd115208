from django.db import models

class Prenatalrecord(models.Model):
    prenatalrecord_id = models.AutoField(primary_key=True)
    pregnancyrecord = models.ForeignKey('Pregnancyrecord', on_delete=models.CASCADE)
    sbp = models.SmallIntegerField()
    dbp = models.SmallIntegerField()
    fetal_heart_rate = models.SmallIntegerField()
    urine_glucose = models.CharField(max_length=4, null=False, blank=False)
    urine_protein = models.CharField(max_length=4, null=False, blank=False)
    edema = models.CharField(max_length=4, null=False, blank=False)
    photo = models.CharField(max_length=255, null=False, blank=False)
    
    class Meta:
        db_table = 'prenatalrecord'
        managed = False

    def __str__(self):
        return f'{self.prenatalrecord_id}'