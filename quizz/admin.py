from django.contrib import admin, messages
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
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


class TagsInline(admin.TabularInline):
    model = Question.tags.through


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [TagsInline]
    exclude = ("tags",)
    readonly_fields = ("type", "creator", "editors", "imported")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warning_sent_for_request = None

    def get_form(self, request, *args, **kwargs):
        """
        Sends a warning message to end users trying to update the question
        through this form.
        """
        if not self.warning_sent_for_request or self.warning_sent_for_request != request:
            if "add" in request.get_full_path():
                messages.error(
                    request,
                    mark_safe(
                        _(
                            "You cannot create a question using this form. The data "
                            'model is too complex. Please <a href="%(url)s">use the '
                            "form we designed in the primary admin interface</a>."
                        )
                        % {"url": reverse_lazy("quizz:management:create")}
                    ),
                )
            else:
                messages.warning(
                    request,
                    _(
                        "You can look at the questions (especially metadata like "
                        "creator and editors), but you shouldn't update them "
                        "through this advanced admin panel unless you know what "
                        "you are doing. It could corrupt the database!"
                    ),
                )
            self.warning_sent_for_request = request

        return super(QuestionAdmin, self).get_form(
            request, *args, **kwargs
        )
