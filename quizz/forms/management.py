from django import forms
from django.utils.translation import gettext_lazy as _

from ..models import QuestionLocale, QUESTION_TYPES, QUESTION_MCQ


class ManageQuizzQuestionForm(forms.Form):

    # Common fields

    locale = forms.ModelChoiceField(
        label=_("Lang"),
        queryset=QuestionLocale.objects.all(),
        initial=QuestionLocale.objects.first(),
        help_text=_("In which language is this question written?"),
        widget=forms.RadioSelect,
    )

    type = forms.ChoiceField(
        label=_("Question type"),
        choices=QUESTION_TYPES,
        initial=QUESTION_MCQ,
        help_text=_(
            "Questions can either be <strong>open</strong> (one text field to answer, no indication), "
            "<strong>multiple-choice</strong> (users will be presented a list of answers, possibly "
            "alongside an “other” free-text option) or with <strong>linked answers</strong> "
            "(users will have to link answers together)."
        ),
        widget=forms.RadioSelect,
    )

    difficulty = forms.ChoiceField(
        label=_("Difficulty"),
        choices=((1, _("Easy")), (2, _("Medium")), (3, _("Hard"))),
        initial=2,
        help_text=_("How difficult is this question to answer?"),
        widget=forms.RadioSelect,
    )

    illustration = forms.ImageField(
        label=_("Illustration"),
        required=False,
        help_text=_("This optional illustration will be shown alongside the question."),
        widget=forms.FileInput(),
    )

    delete_illustration = forms.BooleanField(
        label=_("Or, delete the current illustration"), required=False, initial=False
    )

    question = forms.CharField(
        label=_("Question"),
        max_length=256,
        help_text=_("What is the question, actually?"),
    )
    answer_comment = forms.CharField(
        label=_("Answer's comment"),
        required=False,
        max_length=2 ** 16,
        help_text=_(
            "On the correction page, you may want to add some precisions on this question. You can do so here. These "
            "words will not be shown while the user is answering the question, so feel free to spoil the answer to add "
            "details or precisions here."
        ),
        widget=forms.Textarea(attrs={"rows": "2", "cols": ""}),
    )

    # TODO tags

    # Open questions (+ MCQ with other field)

    open_answer = forms.CharField(
        label=_("Open answer"),
        max_length=1024,
        required=False,
        help_text=_(
            "The valid answer users will have to type to get the point. The answer will be matched ignoring "
            "punctuation and case, and some points will be given if the answer is very close (like one letter "
            "forgotten)."
        ),
        widget=forms.Textarea(attrs={"rows": "2", "cols": ""}),
    )

    # MCQ

    has_open_choice = forms.BooleanField(
        label=_("Has open choice?"),
        required=False,
        help_text=_(
            "If checked, the user will see a “Other” text field under the proposed answers. If the open answer "
            "field below is filled, the answer will have to match; if it's not, it will have to be left blank."
        ),
    )


class ManageQuizzSimpleAnswerForm(forms.Form):
    answer = forms.CharField(
        max_length=256,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Type one answer here"),
                "aria-label": _("Type one answer here"),
                "class": "input",
            }
        ),
    )

    is_correct = forms.BooleanField(label=_("Correct?"), required=False)


class ManageQuizzLinkedAnswerForm(forms.Form):
    answer = forms.CharField(
        max_length=256,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Type one answer here"),
                "aria-label": _("Type one answer here"),
                "class": "input",
            }
        ),
    )

    linked_answer = forms.CharField(
        max_length=256,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Type the linked answer here"),
                "aria-label": _("Type the linked answer here"),
                "class": "input",
            }
        ),
    )


class AnswersFormSet(forms.formsets.BaseFormSet):
    def clean(self):
        """
        Checks up we don't have duplicated answers and that if this form set
        handles linked answers, all answers are filled.
        We don't check if there is at least one correct answer as questions
        without may be acceptable (to request users not to check anything, or
        to have only the extra open answer correct).
        """
        if any(self.errors) or not self.forms:
            return

        answers = [
            form.cleaned_data["answer"]
            for form in self.forms
            if "answer" in form.cleaned_data
        ]

        linked_answers = [
            form.cleaned_data["linked_answer"]
            for form in self.forms
            if "linked_answer" in form.cleaned_data
        ]

        if not answers and not linked_answers:
            raise forms.ValidationError(
                _("There wasn't any answer provided."), code="no_answers"
            )

        if self.check_duplicates(answers):
            raise forms.ValidationError(
                _("There are duplicated answers in the list."), code="duplicate_answers"
            )

        # Linked forms
        if linked_answers:
            if self.check_duplicates(linked_answers):
                raise forms.ValidationError(
                    _("There are duplicated linked answers in the list."),
                    code="duplicate_linked_answers",
                )

            if len(linked_answers) != len(answers):
                raise forms.ValidationError(
                    _(
                        "There are %(answers_count)s answers for %(linked_answers_count)s linked answers."
                    )
                    % {
                        "answers_count": len(answers),
                        "linked_answers_count": len(linked_answers),
                    },
                    code="answers_badly_linked",
                )

    @staticmethod
    def check_duplicates(answers):
        prev_answers = []

        for answer in answers:
            if answer in prev_answers:
                return True
            prev_answers.append(answer)

        return False


"""
In the formsets below, min_num is set to 0 instead of 2, as one of the formsets
will be sent 
"""

ManageQuizzSimpleAnswerFormSet = forms.formset_factory(
    ManageQuizzSimpleAnswerForm,
    formset=AnswersFormSet,
    extra=1,
    min_num=2,
    validate_min=True,
    can_delete=True,
)

ManageQuizzLinkedAnswerFormSet = forms.formset_factory(
    ManageQuizzLinkedAnswerForm,
    formset=AnswersFormSet,
    extra=1,
    min_num=2,
    validate_min=True,
    can_delete=True,
)
