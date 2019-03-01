from django.contrib import admin

from .models import QuestionLocale, Tag, Answer, Question

admin.site.register(QuestionLocale)
admin.site.register(Tag)
admin.site.register(Answer)


class AnswerInline(admin.TabularInline):
    model = Question.answers.through


class TagInline(admin.StackedInline):
    model = Question.tags.through


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline, TagInline]
    exclude = ("tags", "answers")
    readonly_fields = ("type",)
