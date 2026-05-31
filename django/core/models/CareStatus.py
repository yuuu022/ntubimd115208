from django.db import models


class CareStatus(models.Model):
    carestatus_id = models.AutoField(primary_key=True)
    carestatus = models.CharField(max_length=10)

    class Meta:
        db_table = 'carestatus'
        managed = False

    def __str__(self):
        return self.carestatus
