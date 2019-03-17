import random
from django import forms
from django.utils.translation import gettext_lazy as _

from quizz.models import QUESTION_OPEN, QUESTION_MCQ, QUESTION_LINKED


class QuestionForm(forms.Form):
    def __init__(self, question, **kwargs):
        super().__init__(**kwargs)
        self.question = question


class OpenQuestionForm(QuestionForm):
    def __init__(self, question, **kwargs):
        super().__init__(question, **kwargs)
        assert self.question.type == QUESTION_OPEN, (
            "Trying to use OpenQuestionForm with a question of type %s"
            % self.question.type
        )

    answer = forms.CharField(
        label=_("Your answer"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "resizable": "y",
                "placeholder": _("Type your answer here…"),
                "class": "textarea",
            }
        ),
    )


class MultipleChoicesQuestionForm(QuestionForm):
    def __init__(self, question, **kwargs):
        super().__init__(question, **kwargs)

        assert self.question.type == QUESTION_MCQ, (
            "Trying to use MultipleChoicesQuestionForm with a question of type %s"
            % self.question.type
        )

        choices = [
            (answer.pk, answer.answer) for answer in self.question.selectable_answers
        ]
        random.shuffle(choices)

        self.fields["answers"] = forms.MultipleChoiceField(
            label=_("Select all valid answers"),
            choices=choices,
            required=False,
            widget=forms.CheckboxSelectMultiple,
        )

        if question.has_open_choice:
            self.fields["other_answer"] = forms.CharField(
                label=_("Other"),
                required=False,
                widget=forms.TextInput(
                    attrs={
                        "class": "input",
                        "placeholder": _("Write the answer here…")
                    }
                ),
                help_text=_(
                    "If none of the above choices are correct, or if there is "
                    "another answer, write it here. Otherwise, leave this "
                    "field blank. "
                ),
            )


class LinkedQuestionForm(QuestionForm):
    def __init__(self, question, **kwargs):
        super().__init__(question, **kwargs)

        assert self.question.type == QUESTION_LINKED, (
            "Trying to use LinkedQuestionForm with a question of type %s"
            % self.question.type
        )

        answers = self.question.selectable_answers_with_pk
        linked_answers = [(answer[1][0], answer[1][1]) for answer in answers]

        random.shuffle(answers)
        random.shuffle(linked_answers)

        for answer in answers:
            self.fields[f"{answer[0][0]}"] = forms.ChoiceField(
                label=answer[0][1], choices=linked_answers, required=True
            )
