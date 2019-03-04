# Generated by Django 2.1.7 on 2019-03-01 16:43

from django.db import migrations, models
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('quizz', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tag',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='question',
            name='tags',
        ),
        migrations.AlterField(
            model_name='question',
            name='answers',
            field=models.ManyToManyField(related_name='questions', to='quizz.Answer', verbose_name="Question's proposed answers"),
        ),
        migrations.AlterField(
            model_name='question',
            name='illustration',
            field=versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to='quizz/illustrations/', verbose_name='Illustration'),
        ),
        migrations.DeleteModel(
            name='Tag',
        ),
    ]