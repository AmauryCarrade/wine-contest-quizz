# Generated by Django 2.1.7 on 2019-03-07 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizz', '0007_quizzes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quizzquestion',
            name='open_answer',
            field=models.CharField(blank=True, default=None, max_length=1024, null=True, verbose_name='Open answer'),
        ),
    ]