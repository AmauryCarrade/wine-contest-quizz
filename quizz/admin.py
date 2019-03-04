from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin

from .models import QuestionLocale, Tag, Answer, Question

admin.site.register(QuestionLocale)
admin.site.register(Answer)

admin.site.register(
    Tag,
    DraggableMPTTAdmin,
    list_display=("tree_actions", "indented_title"),
    list_display_links=("indented_title",),
    expand_tree_by_default=True,
)


class AnswerInline(admin.TabularInline):
    model = Question.answers.through


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]
    exclude = ("tags", "answers")
    readonly_fields = ("type",)
