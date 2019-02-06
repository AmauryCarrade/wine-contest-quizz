from uuslug import uuslug

from django.db import models
from django.utils.translation import gettext_lazy as _


class Tag(models.Model):
    name = models.CharField("Name of the tag", max_length=128)
    slug = models.SlugField(editable=False)

    def save(self, *args, **kwargs):
        self.slug = uuslug(self.name, instance=self)
        super(Tag, self).save(*args, **kwargs)

    def __str__(self):
        return f"Tag {self.name}"


class Answer(models.Model):
    answer = models.CharField(max_length=256)
    is_correct = models.BooleanField()

    def __str__(self):
        return f'{self.answer} ({"correct" if self.is_correct else "wrong"})'


class Question(models.Model):
    question = models.CharField("Question", max_length=256)
    tags = models.ManyToManyField(Tag, verbose_name="Question's tags for quizz generation filtering")
    is_mcq = models.BooleanField()
    proposed_answers = models.ManyToManyField(
        Answer, verbose_name="Question's proposed answers"
    )
    open_valid_answer = models.CharField(
        "Question's valid answer if this is an open question or if this is a MCQ and the answer is not in the "
        "proposed answers",
        blank=True,
        null=True,
        default=None,
        max_length=256
    )
    answer_comment = models.TextField()

    def __str__(self):
        return f'{self.question} ({"MCQ" if self.is_mcq else "Open"})'
