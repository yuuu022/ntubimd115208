from django.db import models
from .BabyRecord import BabyRecord
from .BabyGrowthMap import BabyGrowthMap

#嬰兒狀態紀錄
class BabyStatus(models.Model):
    babystatus_id = models.AutoField(primary_key=True)
    babyrecord = models.ForeignKey(BabyRecord, on_delete=models.CASCADE, db_column='babyrecord_id', related_name='statuses')
    babygrowthmap = models.ForeignKey(BabyGrowthMap, on_delete=models.CASCADE, db_column='babygrowthmap_id', related_name='baby_statuses')

    class Meta:
        db_table = 'babystatus'
        managed = False

    def __str__(self):
        return f"Baby Status: {self.babystatus_id}"
