from django.contrib import admin

from .models import Tag, Answer, Question

admin.site.register(Tag)
admin.site.register(Answer)


class AnswerInline(admin.TabularInline):
    model = Question.proposed_answers.through


class TagInline(admin.StackedInline):
    model = Question.tags.through


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline, TagInline]
    exclude = ("tags", "proposed_answers")
