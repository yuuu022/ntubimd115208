import uuid
from django.db import models
from django.utils import timezone

def get_uuid_str():
    return str(uuid.uuid4())

class UserProfile(models.Model):
    user_id = models.CharField(max_length=255, primary_key=True, default=get_uuid_str, editable=False)
    line_name = models.CharField(max_length=255)
    avatar = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    password = models.CharField(max_length=255)
    birthday = models.DateField(null=True, blank=True)
    create_time = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = 'userprofile'
        managed = False

    def __str__(self):
        return self.line_name


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

#懷孕胎數
class PregnancyCase(models.Model):
    pregnancycase_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, db_column='user_id', related_name='pregnancy_cases')
    menstruation = models.DateField(null=True, blank=True)
    expecteddate = models.DateField(null=True, blank=True)
    code = models.CharField(max_length=255, unique=True)
    create_time = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = 'pregnancycase'
        managed = False

    def __str__(self):
        return self.code

#懷孕紀錄
class PregnancyRecord(models.Model):
    pregnancyrecord_id = models.BigAutoField(primary_key=True)
    pregnancycase = models.ForeignKey(PregnancyCase, on_delete=models.CASCADE, db_column='pregnancycase_id', related_name='records')
    check_date = models.DateTimeField()
    record = models.TextField()
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'pregnancyrecord'
        managed = False

    def __str__(self):
        return f"Pregnancy Record: {self.check_date}"

#小孩資訊
class BabyInformation(models.Model):
    baby_id = models.BigAutoField(primary_key=True)
    pregnancycase = models.ForeignKey(PregnancyCase, on_delete=models.CASCADE, db_column='pregnancycase_id', related_name='babies')
    name = models.CharField(max_length=255)
    birthdaytime = models.DateTimeField(null=True, blank=True)
    baby_height = models.FloatField(null=True, blank=True)
    baby_weight = models.FloatField(null=True, blank=True)
    babyheadcircumference = models.FloatField(null=True, blank=True)
    chestcircumference = models.FloatField(null=True, blank=True)
    production_method = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'babyinformation'
        managed = False

    def __str__(self):
        return self.name

#嬰兒紀錄
class BabyRecord(models.Model):
    babyrecord_id = models.BigAutoField(primary_key=True)
    baby = models.ForeignKey(BabyInformation, on_delete=models.CASCADE, db_column='baby_id', related_name='records')
    date = models.DateField()
    record = models.TextField()
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    headcircumference = models.FloatField(null=True, blank=True)
    chestcircumference = models.FloatField(null=True, blank=True)
    photo = models.CharField(max_length=255, null=True, blank=True)
    update_time = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'babyrecord'
        managed = False

    def __str__(self):
        return f"Baby Record: {self.date}"

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

#嬰兒狀態紀錄
class BabyStatus(models.Model):
    babystatus_id = models.BigAutoField(primary_key=True)
    babyrecord = models.ForeignKey(BabyRecord, on_delete=models.CASCADE, db_column='babyrecord_id', related_name='statuses')
    babygrowthmap = models.ForeignKey(BabyGrowthMap, on_delete=models.CASCADE, db_column='babygrowthmap_id', related_name='baby_statuses')

    class Meta:
        db_table = 'babystatus'
        managed = False

    def __str__(self):
        return f"Baby Status: {self.babystatus_id}"
