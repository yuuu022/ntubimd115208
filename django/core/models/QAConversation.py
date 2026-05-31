from django.db import models
from .UserProfile import UserProfile

class QAConversation(models.Model):
    qa_conversation_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    create_time = models.DateTimeField()

    class Meta:
        db_table = 'qaconversation'
        managed = False

    def __str__(self):
        return f'{self.qa_conversation_id} - {self.title}'