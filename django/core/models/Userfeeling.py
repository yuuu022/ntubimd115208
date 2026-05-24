from django.db import models
from .PregnancyRecord import PregnancyRecord
from .Feeling import Feeling


#心情表
class Userfeeling(models.Model):
    userfeeling_id = models.AutoField(primary_key=True)
    pregnancyrecord = models.ForeignKey(PregnancyRecord, on_delete=models.CASCADE, db_column='pregnancyrecord_id', related_name='userfeelings')
    feeling = models.ForeignKey(Feeling, on_delete=models.CASCADE, db_column='feeling_id', related_name='userfeelings')

    class Meta:
        db_table = 'userfeeling'
        managed = False

    def __str__(self):
        try:
            return self.feeling.feeling_name
        except Exception:
            return str(self.userfeeling_id)