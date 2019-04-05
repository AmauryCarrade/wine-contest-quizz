from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _, ngettext_lazy
from django.views.generic import FormView

from quizz.forms.management import MigrateTagsForm
from quizz.models import Tag, Question


class MigrateTagsView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "management/tags-migrate.html"
    permission_required = ("quizz.delete_tag", "quizz.change_question")

    form_class = MigrateTagsForm
    success_url = reverse_lazy("quizz:management:tags-migration")

    def form_valid(self, form):
        old_tag: Tag = form.cleaned_data["old_tag"]
        target_tag: Tag = form.cleaned_data["new_tag"]
        delete_old = form.cleaned_data["delete_old_tag"]

        if old_tag == target_tag:
            messages.error(self.request, _("You cannot migrate a tag to itself"))
            return HttpResponseRedirect(self.get_success_url())

        count = 0
        for question in Question.objects.filter(tags=old_tag):
            question.tags.add(target_tag)
            if not delete_old:
                question.tags.remove(old_tag)
            count += 1

        if delete_old:
            # If the tag have children, we want to move them to its parent
            # because deleting a tag deletes all its children
            has_children = not old_tag.is_leaf_node()
            if has_children:
                parent = old_tag.parent
                for child in old_tag.get_children():
                    child.parent = parent
                    child.save()

            old_tag.delete()

            if has_children:
                Tag.objects.rebuild()

            messages.success(
                self.request,
                ngettext_lazy(
                    "The tag %(old_tag)s was deleted, and %(questions_count)d "
                    "question was moved to the tag %(new_tag)s.",
                    "The tag %(old_tag)s was deleted, and %(questions_count)d "
                    "questions were moved to the tag %(new_tag)s.",
                    count,
                )
                % {
                    "old_tag": old_tag.name,
                    "new_tag": target_tag.name,
                    "questions_count": count,
                },
            )
        else:
            messages.success(
                self.request,
                ngettext_lazy(
                    "%(questions_count)d question was moved to the tag %(new_tag)s.",
                    "%(questions_count)d questions were moved to the tag %(new_tag)s.",
                    count,
                )
                % {"new_tag": target_tag.name, "questions_count": count},
            )

        return HttpResponseRedirect(self.get_success_url())
