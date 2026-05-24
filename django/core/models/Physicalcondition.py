from django.db import models

#身體狀況表
class PhysicalCondition(models.Model):
    physicalcondition_id = models.AutoField(primary_key=True, db_column='physicalcondition_id')
    physicalcondition_name = models.CharField(max_length=255, null=False, blank=False, db_column='physicalcondition_name')

    class Meta:
        db_table = 'physicalcondition'
        managed = False

    def __str__(self):
        return self.physicalcondition_name