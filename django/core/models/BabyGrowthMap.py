from django.db import models

#小孩成長地圖
class BabyGrowthMap(models.Model):
    babygrowthmap_id = models.AutoField(primary_key=True)
    timecourse = models.SmallIntegerField()
    growthrecord = models.CharField(max_length=50)

    class Meta:
        db_table = 'babygrowthmap'
        managed = True

    def __str__(self):
        return self.timecourse