from django.db import models

#小孩成長地圖
class BabyGrowthMap(models.Model):
    babygrowthmap_id = models.BigAutoField(primary_key=True)
    timecourse = models.BigIntegerField()
    growthrecord = models.CharField(max_length=255)

    class Meta:
        db_table = 'babygrowthmap'
        managed = False

    def __str__(self):
        return f"Growth Map: {self.timecourse}"