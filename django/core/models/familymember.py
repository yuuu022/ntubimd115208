from django.db import models
from django.utils import timezone
from .PregnancyCase import PregnancyCase
from .UserProfile import UserProfile

class FamilyMember(models.Model):
    familymember_id = models.AutoField(max_length=255, primary_key=True)
    pregnancycase_id = models.ForeignKey(PregnancyCase, on_delete=models.CASCADE)
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    role = models.CharField(max_length=5)
    join_time = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'familymember'
        managed = False 

    def __str__(self):
        return self.role