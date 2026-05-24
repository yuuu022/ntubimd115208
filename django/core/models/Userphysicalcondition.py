from django.db import models

from .Physicalcondition import PhysicalCondition
from .PregnancyRecord import PregnancyRecord


# 使用者選取的身體狀況
class Userphysicalcondition(models.Model):
    userphysicalcondition_id = models.AutoField(primary_key=True)
    pregnancyrecord = models.ForeignKey(PregnancyRecord, on_delete=models.CASCADE, db_column='pregnancyrecord_id', related_name='userphysicalconditions')
    physicalcondition = models.ForeignKey(PhysicalCondition, on_delete=models.CASCADE, db_column='physicalcondition_id', related_name='userphysicalconditions')

    class Meta:
        db_table = 'userphysicalcondition'
        managed = False

    def __str__(self):
        try:
            return self.physicalcondition.physicalcondition_name
        except Exception:
            return str(self.userphysicalcondition_id)