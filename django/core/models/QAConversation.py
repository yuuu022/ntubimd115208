from django.db import models

class QAConversation(models.Model):
    qa_conversation_id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    create_time = models.DateTimeField()

    class Meta:
        db_table = 'qa_conversation'
        managed = False

    def __str__(self):
        return f'{self.qa_conversation_id} - {self.title}'