# Generated by Django 2.1.7 on 2019-03-18 18:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizz', '0012_add-user-profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='locale',
            field=models.CharField(blank=True, max_length=6, null=True, verbose_name='User locale'),
        ),
    ]