from django.db import models

#心情表
class Feeling(models.Model):
    feeling_id = models.AutoField(primary_key=True)
    feeling_name = models.CharField(max_length=5, unique=True)

    class Meta:
        db_table = 'feeling'
        managed = True

    def __str__(self):
        return self.feeling_name