from django.db import models
from .QAConversation import QAConversation


class QAMessage(models.Model):
    serno = models.AutoField(primary_key=True)
    qa_conversation = models.ForeignKey(QAConversation, on_delete=models.CASCADE)
    role = models.CharField(max_length=10)
    message = models.TextField()
    create_time = models.DateTimeField()

    class Meta:
        db_table = 'qa_message'
        managed = False

    def __str__(self):
        return f'{self.serno} ({self.role})'