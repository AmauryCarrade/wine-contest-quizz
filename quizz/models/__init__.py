from django.utils.translation import gettext_lazy as _
from enum import Enum

QUESTION_OPEN = "OPEN"
QUESTION_MCQ = "MCQ"
QUESTION_LINKED = "LINKED"
QUESTION_TYPES = (
    (QUESTION_OPEN, _("Open answer")),
    (QUESTION_MCQ, _("Multiple choices")),
    (QUESTION_LINKED, _("Linked answers")),
)


class QuestionSuccess(Enum):
    """
    For MCQ and linked answers, the success status will always be
    PERFECT or FAILED. For open answers, if the text entered is very
    close to the valid answer, we'll grant an ALMOST.
    """

    PERFECT = "PERFECT"
    ALMOST = "ALMOST"
    FAILED = "FAILED"


from .users import *  # noqa
from .questions import *  # noqa
from .quizzes import *  # noqa
