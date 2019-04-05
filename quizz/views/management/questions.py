from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count, Q, FloatField, Sum, Case, When, F
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, FormView, DeleteView

from quizz.forms.management import (
    ManageQuizzQuestionForm,
    ManageQuizzSimpleAnswerFormSet,
    ManageQuizzLinkedAnswerFormSet,
)
from quizz.models import Question, QUESTION_MCQ, QUESTION_LINKED, QUESTION_OPEN


class QuestionsListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "management/question-list.html"
    context_object_name = "questions"

    permission_required = "quizz.view_question"

    model = Question
    paginate_by = 20

    @cached_property
    def sort_by(self):
        sort: str = self.request.GET.get("sort", "name")
        sort_reversed = sort.startswith("-")
        return sort.strip("-"), sort_reversed

    def get_context_data(self, **kwargs):
        context = super(QuestionsListView, self).get_context_data(**kwargs)

        context["sort_by"] = self.sort_by[0]
        context["sort_reversed"] = self.sort_by[1]

        context["batch"] = self.get_paginate_by(None)

        return context

    def get_paginate_by(self, queryset):
        if "batch" in self.request.GET:
            if self.request.GET["batch"].lower() == "all":
                # We still return a (big) number instead of None
                # to be able to use the paginator the same way to
                # get the questions count (else the paginator is not
                # available at all).
                return 2**31 - 1
            else:
                try:
                    return int(self.request.GET["batch"])
                except ValueError:
                    return self.paginate_by
        return self.paginate_by

    def get_queryset(self):
        questions = (
            Question.objects.all()
            .annotate(
                user_answers_count=Count(
                    "user_answers",
                    filter=Q(user_answers__finished_at__isnull=False),
                    output_field=FloatField(),
                ),
                success_rate=Sum(
                    Case(
                        When(user_answers__success="PERFECT", then=1.0),
                        default=0.0,
                        output_field=FloatField(),
                    ),
                    output_field=FloatField(),
                )
                / F("user_answers_count")
                * 100,
            )
            .prefetch_related("tags")
            .select_related("locale", "source")
        )
        sort_by, sort_reversed = self.sort_by
        rev = "-" if sort_reversed else ""

        if sort_by == "difficulty":
            questions = questions.order_by(rev + "difficulty")
        elif sort_by == "source":
            questions = questions.order_by(
                F("source__name").asc(nulls_last=True, descending=sort_reversed)
            )
        elif sort_by == "illustration":
            # “Ordered” sorting for illustrations is with illustrations first,
            # so we need to have empty values last, corresponding to a reverse
            # sorting in SQL.
            questions = questions.order_by(
                ("" if sort_reversed else "-") + "illustration"
            )
        elif sort_by == "type":
            questions = questions.order_by(rev + "type")
        elif sort_by == "locale":
            questions = questions.order_by(rev + "locale__name")
        elif sort_by == "created":
            questions = questions.order_by(
                F("created_at").asc(nulls_last=True, descending=not sort_reversed)
            )
        elif sort_by == "updated":
            questions = questions.order_by(
                F("updated_at").asc(nulls_last=True, descending=not sort_reversed)
            )
        elif sort_by == "answered":
            questions = questions.order_by(
                ("" if sort_reversed else "-") + "user_answers_count"
            )
        elif sort_by == "success-rate":
            questions = questions.order_by(
                F("success_rate").asc(nulls_last=True, descending=not sort_reversed)
            )
        else:
            questions = questions.order_by(rev + "question")

        return questions


class EditQuestionView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "management/question-edit.html"
    form_class = ManageQuizzQuestionForm

    def get_permission_required(self):
        if self.edited_question:
            return ("quizz.change_question",)
        else:
            return ("quizz.add_question",)

    @cached_property
    def edited_question(self):
        """
        Returns the currently edited question, or None if this form is used for creation.
        :rtype: Question
        """
        if "pk" in self.kwargs:
            question = Question.objects.filter(pk=self.kwargs["pk"]).first()
            if not question:
                raise Http404()
            return question
        else:
            return None

    def get_form(self, form_class=None):
        """
        If we're editing a question, disables the question type field,
        as types cannot be changed.
        Even if the user try to temper with that, any new value will be ignored.
        """
        form = super(EditQuestionView, self).get_form(form_class=form_class)

        if self.edited_question:
            form.fields["type"].disabled = True

        return form

    def get_initial(self):
        if not self.edited_question:
            return {}

        return {
            "type": self.edited_question.type,
            "locale": self.edited_question.locale,
            "difficulty": self.edited_question.difficulty,
            "illustration": self.edited_question.illustration,
            "question": self.edited_question.question,
            "answer_comment": self.edited_question.answer_comment,
            "open_answer": self.edited_question.open_valid_answer,
            "has_open_choice": self.edited_question.has_open_choice,
            "source": self.edited_question.source,
            "tags": self.edited_question.tags.all(),
        }

    def get_initial_answers_formset(self):
        if not self.edited_question or self.edited_question.type != QUESTION_MCQ:
            return []

        return [
            {"answer": answer.answer, "is_correct": answer.is_correct}
            for answer in self.edited_question.answers.filter(is_deleted=False)
        ]

    def get_initial_linked_answers_formset(self):
        if not self.edited_question or self.edited_question.type != QUESTION_LINKED:
            return []

        return [
            {"answer": answer.answer, "linked_answer": answer.linked_answer.answer}
            for answer in self.edited_question.answers.filter(
                is_deleted=False
            ).prefetch_related("linked_answer")
        ]

    def get_context_data(self, form_answers=None, form_linked_answers=None, **kwargs):
        context = super(EditQuestionView, self).get_context_data(**kwargs)

        context["question"] = self.edited_question
        context["form_answers"] = form_answers or ManageQuizzSimpleAnswerFormSet(
            prefix="answers", initial=self.get_initial_answers_formset()
        )
        context["form_linked_answers"] = (
            form_linked_answers
            or ManageQuizzLinkedAnswerFormSet(
                prefix="linked-answers",
                initial=self.get_initial_linked_answers_formset(),
            )
        )

        return context

    def form_invalid(self, form, form_answers=None, form_linked_answers=None, **kwargs):
        return self.render_to_response(
            self.get_context_data(
                form=form,
                form_answers=form_answers,
                form_linked_answers=form_linked_answers,
            )
        )

    def form_valid(self, form):
        question = self.edited_question
        is_update = question is not None

        # The question type can't be changed. It would be too difficult/touchy
        # to keep history clean for past quizz.
        question_type = question.type if question else form.cleaned_data["type"]
        form_answers = None
        form_linked_answers = None

        if question_type == QUESTION_MCQ:
            form_answers = ManageQuizzSimpleAnswerFormSet(
                self.request.POST, self.request.FILES, prefix="answers"
            )
        elif question_type == QUESTION_LINKED:
            form_linked_answers = ManageQuizzLinkedAnswerFormSet(
                self.request.POST, self.request.FILES, prefix="linked-answers"
            )

        if (
            form.has_changed()
            or (not form_answers or form_answers.has_changed())
            or (not form_linked_answers or form_linked_answers.has_changed())
        ) and self.request.user.is_authenticated:
            user = self.request.user
        else:
            user = None

        if (not form_answers or form_answers.is_valid()) and (
            not form_linked_answers or form_linked_answers.is_valid()
        ):
            if question_type == QUESTION_OPEN:
                question = Question.create_or_update_open(
                    instance=question,
                    question=form.cleaned_data["question"],
                    answer=form.cleaned_data["open_answer"],
                    locale=form.cleaned_data["locale"],
                    difficulty=form.cleaned_data["difficulty"],
                    illustration=self.request.FILES.get("illustration", None),
                    delete_illustration=form.cleaned_data["delete_illustration"]
                    if "delete_illustration" in form.cleaned_data
                    else False,
                    comment=form.cleaned_data["answer_comment"],
                    tags=form.cleaned_data["tags"],
                    source=form.cleaned_data["source"],
                    user=user,
                )

            elif question_type == QUESTION_MCQ:
                answers = []
                if form_answers.has_changed():
                    for form_answer in form_answers.forms:
                        if (
                            "answer" in form_answer.cleaned_data
                            and "is_correct" in form_answer.cleaned_data
                            and form_answer.cleaned_data["answer"].strip()
                        ):
                            answers.append(
                                {
                                    "answer": form_answer.cleaned_data[
                                        "answer"
                                    ].strip(),
                                    "is_correct": form_answer.cleaned_data[
                                        "is_correct"
                                    ],
                                }
                            )

                question = Question.create_or_update_mcq(
                    instance=question,
                    question=form.cleaned_data["question"],
                    answers=answers,
                    has_open_answer=form.cleaned_data["has_open_choice"],
                    open_answer=form.cleaned_data["open_answer"],
                    locale=form.cleaned_data["locale"],
                    difficulty=form.cleaned_data["difficulty"],
                    illustration=self.request.FILES.get("illustration", None),
                    delete_illustration=form.cleaned_data["delete_illustration"]
                    if "delete_illustration" in form.cleaned_data
                    else False,
                    comment=form.cleaned_data["answer_comment"],
                    tags=form.cleaned_data["tags"],
                    source=form.cleaned_data["source"],
                    user=user,
                )

                if not any([answer["is_correct"] for answer in answers]) and (
                    not question.has_open_choice or not question.open_valid_answer
                ):
                    messages.warning(
                        self.request,
                        _(
                            "All answers are marked “incorrect” in the question “%(question)s”, and there is no "
                            "valid open choice. The question will only be considered valid if submitted blank. "
                            "Make sure that's indeed what you want."
                        )
                        % {"question": form.cleaned_data["question"]},
                    )

            elif question_type == QUESTION_LINKED:
                answers = []
                if form_linked_answers.has_changed():
                    for form_linked_answer in form_linked_answers.forms:
                        if (
                            "answer" in form_linked_answer.cleaned_data
                            and form_linked_answer.cleaned_data["answer"].strip()
                            and "linked_answer" in form_linked_answer.cleaned_data
                            and form_linked_answer.cleaned_data["linked_answer"].strip()
                        ):
                            answers.append(
                                (
                                    form_linked_answer.cleaned_data["answer"].strip(),
                                    form_linked_answer.cleaned_data[
                                        "linked_answer"
                                    ].strip(),
                                )
                            )

                question = Question.create_or_update_linked(
                    instance=question,
                    answers=answers,
                    question=form.cleaned_data["question"],
                    locale=form.cleaned_data["locale"],
                    difficulty=form.cleaned_data["difficulty"],
                    illustration=self.request.FILES.get("illustration", None),
                    delete_illustration=form.cleaned_data["delete_illustration"]
                    if "delete_illustration" in form.cleaned_data
                    else False,
                    comment=form.cleaned_data["answer_comment"],
                    tags=form.cleaned_data["tags"],
                    source=form.cleaned_data["source"],
                    user=user,
                )

            if is_update:
                messages.success(
                    self.request,
                    _(
                        "Question “%(question)s” (%(question_type)s) updated successfully."
                    )
                    % {
                        "question": question.question,
                        "question_type": question.verbose_type,
                    },
                )
            else:
                messages.success(
                    self.request,
                    _(
                        "Question “%(question)s” (%(question_type)s) created successfully."
                    )
                    % {
                        "question": question.question,
                        "question_type": question.verbose_type,
                    },
                )

            if (
                "and_after" in self.request.POST
                and self.request.POST["and_after"] == "ANOTHER"
            ):
                return HttpResponseRedirect(
                    reverse_lazy("quizz:management:questions-create")
                )
            else:
                return HttpResponseRedirect(reverse_lazy("quizz:management:questions"))

        else:
            return self.form_invalid(
                form=form,
                form_answers=form_answers,
                form_linked_answers=form_linked_answers,
            )


class QuestionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    template_name = "management/question-delete.html"
    context_object_name = "question"

    permission_required = "quizz.delete_question"

    model = Question

    def delete(self, *args, **kwargs):
        question: Question = self.get_object()

        question.delete()

        messages.success(
            self.request,
            _("Question “%(question)s” deleted successfully.")
            % {"question": question.question},
        )

        return HttpResponseRedirect(reverse_lazy("quizz:management:questions"))
