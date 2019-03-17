from django import forms
from django.utils.translation import gettext_lazy as _

from quizz.fields import TreeNodeAllMultipleChoiceField
from quizz.models import Tag, QuestionLocale, Contest
from quizz.widgets import CheckboxTreeSelectMultiple


class CreateQuizzForm(forms.Form):
    how_many = forms.IntegerField(
        label=_("How many questions?"),
        min_value=1,
        max_value=100,
        initial=10,
        widget=forms.NumberInput(attrs={"class": "input is-inline is-medium"}),
    )

    tags = TreeNodeAllMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=CheckboxTreeSelectMultiple(
            container_classes="columns is-multiline",
            columns_classes="column is-6",
            bold_parents=True,
            attrs={"class": "checkbox"},
        ),
        required=False,
    )

    difficulty = forms.ChoiceField(
        label=_("Difficulty"),
        choices=(
            (0, _("Indifferent")),
            (1, _("Easy")),
            (2, _("Medium")),
            (3, _("Hard")),
        ),
        required=False,
        initial=0,
        widget=forms.RadioSelect,
    )

    locale = forms.ModelChoiceField(
        label=_("Language"),
        queryset=QuestionLocale.objects.all(),
        required=False,
        empty_label=_("Indifferent"),
        widget=forms.RadioSelect,
    )

    contest = forms.ModelChoiceField(
        label=_("Pick questions from"),
        queryset=Contest.objects.all(),
        required=False,
        empty_label=_("All contests, plus exclusive training questions"),
    )
