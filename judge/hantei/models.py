from django.db import models

# Create your models here.
class SubjectTable(models.Model):
    # 科目コード(主キー設定)
    id = models.CharField(max_length=8, primary_key=True, verbose_name='科目コード')
    # 科目名
    name = models.CharField(max_length=50, verbose_name='科目名')
    # 配当年次
    assigned_year = models.PositiveIntegerField(verbose_name='配当年次')
    # 単位数
    credits = models.PositiveIntegerField(verbose_name='単位数')
    # 判定区分1
    category1 = models.CharField(max_length=4, verbose_name='判定区分1')
    # 判定区分2
    category2 = models.CharField(max_length=4, verbose_name='判定区分2', blank=True)
    # 判定区分3
    category3 = models.CharField(max_length=4, verbose_name='判定区分3',blank=True)
    # 体育フラグ
    pe_flag = models.CharField(max_length=4, verbose_name='体育フラグ', blank=True)
    # A/Bフラグ
    ab_flag = models.CharField(max_length=4, verbose_name='A/Bフラグ', blank=True)
    # 留学生フラグ
    foreign_student_flag = models.BooleanField(default=False, verbose_name='留学生科目',)
    # 前提科目
    pre_sub = models.CharField(max_length=8, verbose_name='前提科目', blank=True)
    
    def __str__(self):
        return self.name

class AcquiredCredits(models.Model):
    subject = models.ForeignKey(SubjectTable, on_delete=models.CASCADE)
    credits = models.PositiveIntegerField(default=0)
    category1 = models.CharField(max_length=4, blank=True)
    category2 = models.CharField(max_length=4, blank=True)
    category3 = models.CharField(max_length=4, blank=True)
    pe_flag = models.CharField(max_length=4, blank=True)
    ab_flag = models.CharField(max_length=4, blank=True)
    
    def save(self, *args, **kwargs):
        self.subject_code = self.subject.id
        self.credits = self.subject.credits
        self.category1 = self.subject.category1
        self.category2 = self.subject.category2
        self.category3 = self.subject.category3
        self.pe_flag = self.subject.pe_flag
        self.ab_flag = self.subject.ab_flag
        super().save(*args, **kwargs)

    def __str__(self):
        return self.subject.name