from django.db import models
from .QAConversation import QAConversation


class QAMessage(models.Model):
    serno = models.BigAutoField(primary_key=True)
    qa_conversation = models.ForeignKey(QAConversation, db_column='qa_conversation_id', on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=255)
    message = models.TextField()
    create_time = models.DateTimeField()

    class Meta:
        db_table = 'qa_message'
        managed = False

    def __str__(self):
        return f'{self.serno} ({self.role})'