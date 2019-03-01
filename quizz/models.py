from uuslug import uuslug

from django.db import models
from django.utils.translation import gettext_lazy as _

from versatileimagefield.fields import VersatileImageField


class QuestionLocale(models.Model):
    """
    Questions are separated by locale.
    """

    """The ISO language tag for this locale (e.g. “fr_FR”)."""
    code = models.CharField(_("ISO code"), max_length=8)

    """The display name for this locale (e.g. “Français”)."""
    name = models.CharField(_("Display name"), max_length=255)

    def __str__(self):
        return f"{self.name}"


class Tag(models.Model):
    """
    Tags are used to categorize questions: users can ask for questions
    with a specific tag only. Tags are hierarchical: if one ask for
    a tag, all questions with this tag or any child tag will be selected.
    """

    """The name of a tag, displayed to the end users."""
    name = models.CharField("Name of the tag", max_length=128)

    """The slug of a tag, for URLs."""
    slug = models.SlugField(editable=False)

    """
    In the tags hierarchy, this is the parent of this tag.
    If None, the tag is a root tag.
    """
    parent = models.ForeignKey("Tag", on_delete=models.CASCADE, blank=True, null=True)

    """Persists a tag, recalculating its slug."""

    def save(self, *args, **kwargs):
        self.slug = uuslug(self.name, instance=self)
        super(Tag, self).save(*args, **kwargs)

    def __str__(self):
        return f"Tag {self.name}"


class Answer(models.Model):
    """
    An answer to a question. Questions can either be multiple-choice,
    single-choice, free text or with linked answers; this represents
    all the cases.

    For multiple-choice questions, the Question will contain a list of
    answers, some marked as correct (using self.is_correct), some as incorrect.
    The user will have to select all correct answers, and only them.

    For linked answers questions, the Question will contain two lists: the
    list of answers, and the list of related answers. The user will have to link
    all answers correctly. The answers in the first list will have the
    self.correct_linked_answer field pointing to the correct answer. The other's
    and both self.is_correct fields are not relevant in this case.
    """

    """The answer's text displayed to the user, to be selected if correct."""
    answer = models.CharField(max_length=256)

    """True if this answer is correct."""
    is_correct = models.BooleanField()

    """
    The correct related answer. If this is set, the answer will be correct if
    linked to this other answer.
    """
    linked_answer = models.OneToOneField(
        "Answer",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="linked_answer_reverse",
    )

    """
    True if this answer was deleted.
    Because quizz results reference answers, if an answer is deleted, it cannot
    be removed from the database. So, quizz results reference the questions and
    the answers that were active when the quizz was passed. Quizz will only display
    for new questions non-deleted answers.
    """
    is_deleted = models.BooleanField(default=False)

    @property
    def primary(self):
        return (
            not hasattr(self, "linked_answer_reverse") or not self.linked_answer_reverse
        )

    def __str__(self):
        return (
            ("[DELETED] " if self.is_deleted else "")
            + self.answer
            + (" (correct)" if self.is_correct else "")
            + (
                " (→ linked)"
                if not self.primary
                else ("(linked →)" if self.linked_answer else "")
            )
        )


QUESTION_OPEN = "OPEN"
QUESTION_MCQ = "MCQ"
QUESTION_LINKED = "LINKED"

QUESTION_TYPES = (
    (QUESTION_OPEN, _("Open answer")),
    (QUESTION_MCQ, _("Multiple choices")),
    (QUESTION_LINKED, _("Linked answers")),
)


class Question(models.Model):
    """
    A question.

    Questions can either be:

     - open answer, without choices to select: the `answers` is empty
       as well as the `linked_answers`; the correct answer is in
       `open_valid_answer`;

     - multiple choices (MCQ): `answers` contains the choices (their
       correctness is stored into the answers); if `has_open_choice` is True,
       an “Other Answer” field will be displayed and matched against
       `open_valid_answer` (if this one is None, the answer will not be in the
       other input, but it will still be displayed);

     - linked choices: `answers` contains the choices; the answers reference
       their linked answer inside their model (using a self-one-to-one relation).
    """

    """The question's type"""
    type = models.CharField(
        verbose_name=_("Question's type"), choices=QUESTION_TYPES, max_length=6
    )

    """The question's locale"""
    locale = models.ForeignKey(
        QuestionLocale, on_delete=models.PROTECT, verbose_name=_("Locale"), max_length=8
    )

    """The question's difficulty, between 1 (easy) and 3 (hard)"""
    difficulty = models.PositiveSmallIntegerField(
        verbose_name=_("Difficulty"), default=1
    )

    """The question's text."""
    question = models.CharField(verbose_name=_("Question"), max_length=256)

    """The question's tags."""
    tags = models.ManyToManyField(
        Tag, verbose_name=_("Question's tags for quizz generation filtering")
    )

    """The question's illustration, if any."""
    illustration = VersatileImageField(
        verbose_name=_("Illustration"),
        null=True,
        blank=True,
        upload_to="quizz/illustrations/",
    )

    """True if we should add a “other” input after the proposed choices."""
    has_open_choice = models.BooleanField(
        verbose_name=_("Has open choice"), default=False
    )

    """For MCQ and linked choices, the choices."""
    answers = models.ManyToManyField(
        Answer, verbose_name=_("Question's proposed answers"), related_name="questions"
    )

    """
    For open answers ans MCQ with open answer, the correct open answer.
    For MCQ with open answer, if None, the “Other” input will be displayed but
    have to be left empty.
    """
    open_valid_answer = models.CharField(
        verbose_name=_(
            "Question's valid answer if this is an open question or if this is a MCQ and the answer is not in the "
            "proposed answers"
        ),
        blank=True,
        null=True,
        default=None,
        max_length=1024,
    )

    """In the correction phase, will allow to display an extra explanation."""
    answer_comment = models.TextField(
        verbose_name=_("Answer's comment"), max_length=2 ** 16
    )

    def __str__(self):
        return f"{self.question} ({self.verbose_type})"

    @property
    def verbose_type(self):
        return {
            "OPEN": _("Open answer"),
            "MCQ": _("Multiple choices"),
            "LINKED": _("Linked answers"),
        }[self.type]

    @property
    def selectable_answers(self):
        """
        Returns the selectable answers of this question.

        If this question is an open question, returns None.
        If it is a MCQ, returns a list of answers.
        If it is a linked question, returns a list of tuples of answers linked
        together.
        :return: The answers.
        """
        if self.type == "OPEN":
            return None
        elif self.type == "MCQ":
            return self.answers.filter(is_deleted=False)
        elif self.type == "LINKED":
            return [
                (answer.answer, answer.linked_answer.answer)
                for answer in self.answers.filter(is_deleted=False)
                if answer.answer and answer.linked_answer.answer
            ]

    @property
    def answers_count(self):
        return self.answers.filter(is_deleted=False).count()

    def _update_common(
        self,
        question=None,
        locale=None,
        difficulty=2,
        illustration=None,
        delete_illustration=False,
        comment=None,
        tags=None,
    ):
        if question:
            self.question = question

        if locale:
            self.locale = locale

        if difficulty:
            self.difficulty = difficulty

        if illustration:
            self.illustration = illustration
        elif delete_illustration:
            self.illustration = None

        if comment:
            self.answer_comment = comment

        if tags:
            self.tags.clear()
            for tag in tags:
                self.tags.add(tag)

    @staticmethod
    def create_open(
        question,
        answer,
        locale=None,
        difficulty=2,
        illustration=None,
        comment=None,
        tags=None,
        **kwargs,
    ):
        """
        Creates a new open question, accepting an open answer without propositions.

        :param question: The question.
        :param answer: The answer to that question.
        :param locale: The locale of this question, as an instance of QuestionLocale.
        :param difficulty: The difficulty of this question, between 1 (easy) and 3 (hard).
        :param illustration: An illustration for this question (can be None).
        :param comment: A comment on the answer of this question (can be None).
        :param tags: A list of tags for this question (can be None/empty).
        :return: The created question.
        """
        if tags is None:
            tags = []

        question = Question(
            type=QUESTION_OPEN,
            question=question,
            open_valid_answer=answer,
            locale=locale or QuestionLocale.objects.first(),
            difficulty=difficulty,
            illustration=illustration,
            answer_comment=comment,
        )
        question.save()

        for tag in tags:
            question.tags.add(tag)

        return question

    def update_open(
        self,
        question=None,
        answer=None,
        locale=None,
        difficulty=None,
        illustration=None,
        delete_illustration=False,
        comment=None,
        tags=None,
        **kwargs,
    ):
        """
        Updates an open question.

        This method asserts that this question is indeed an open question.

        :param question: The question.
        :param answer: The answer to that question.
        :param locale: The locale of this question, as an instance of QuestionLocale.
        :param difficulty: The difficulty of this question, between 1 (easy) and 3 (hard).
        :param illustration: An illustration for this question (can be None).
        :param delete_illustration: If True, the associated illustration will be deleted.
        :param comment: A comment on the answer of this question (can be None).
        :param tags: A list of tags for this question (can be None/empty). Existing tags will be replaced.
        :return: The updated question (i.e. self).
        """
        assert (
            self.type == QUESTION_OPEN
        ), f"Trying to update a {self.type} question with update_open"
        if answer:
            self.open_valid_answer = answer

        self._update_common(
            question=question,
            locale=locale,
            difficulty=difficulty,
            illustration=illustration,
            delete_illustration=delete_illustration,
            comment=comment,
            tags=tags,
        )

        self.save()
        return self

    @staticmethod
    def create_or_update_open(instance, *args, **kwargs):
        """
        Creates or updates an open question.

        If the given instance is not None, the instance will be updated. Else,
        it will be created.

        :param instance: The instance (can be None to create).
        :return: The created or updated instance.
        """
        if instance:
            return instance.update_open(*args, **kwargs)

        else:
            return Question.create_open(*args, **kwargs)

    @staticmethod
    def create_mcq(
        question,
        answers,
        has_open_answer=False,
        open_answer=None,
        locale=None,
        difficulty=2,
        illustration=None,
        comment=None,
        tags=None,
        **kwargs,
    ):
        """
        Creates a multiple-choices question.

        :param question: The question.
        :param answers: A list of answers. Each answer is a dictionary containing the
                        keys `answer` (the answer's text) and `is_correct` (True/False).
        :param has_open_answer: True if this question should display an “Other” answer field.
        :param open_answer: The open answer, if any. Can be None even if `has_open_answer` is
                            True; in this case, the field will have to be left blank.
        :param locale: The question's locale, as an instance of QuestionLocale.
        :param difficulty: The question's difficulty, between 1 (easy) and 3 (hard).
        :param illustration: The question's illustration (can be None).
        :param comment: A comment on the question's answer (can be None).
        :param tags: A list of tags for this question (can be None/empty).
        :return: The created question.
        """
        if tags is None:
            tags = []

        question = Question(
            type=QUESTION_MCQ,
            question=question,
            has_open_choice=has_open_answer,
            open_valid_answer=open_answer,
            locale=locale or QuestionLocale.objects.first(),
            difficulty=difficulty,
            illustration=illustration,
            answer_comment=comment,
        )
        question.save()

        for tag in tags:
            question.tags.add(tag)

        for answer in answers:
            question.answers.create(
                answer=answer["answer"],
                is_correct=answer["is_correct"],
                linked_answer=None,
            )

        return question

    def update_mcq(
        self,
        question=None,
        answers=None,
        has_open_answer=False,
        open_answer=None,
        locale=None,
        difficulty=2,
        illustration=None,
        delete_illustration=False,
        comment=None,
        tags=None,
        **kwargs,
    ):
        """
        Updates a multiple-choices question.

        This method asserts that this question is indeed an open question.

        :param question: The question.
        :param answers: A list of answers. Each answer is a dictionary containing the
                        keys `answer` (the answer's text) and `is_correct` (True/False).
        :param has_open_answer: True if this question should display an “Other” answer field.
        :param open_answer: The open answer, if any. Can be None even if `has_open_answer` is
                            True; in this case, the field will have to be left blank.
        :param locale: The question's locale, as an instance of QuestionLocale.
        :param difficulty: The question's difficulty, between 1 (easy) and 3 (hard).
        :param illustration: The question's illustration (can be None).
        :param delete_illustration: If True, the associated illustration will be deleted.
        :param comment: A comment on the question's answer (can be None).
        :param tags: A list of tags for this question (can be None/empty). Existing tags will be overwritten.
        :return:
        """
        assert (
            self.type == QUESTION_MCQ
        ), f"Trying to update a {self.type} question with update_mcq"

        self.has_open_choice = has_open_answer

        if open_answer:
            self.open_valid_answer = open_answer

        if answers:
            # We compare the answers we were given and the existing answers.
            # If there is differences, we remove all previous answers and add
            # all new ones.
            recreate_answers = False
            if len(answers) != self.answers.count():
                recreate_answers = True
            else:
                answers = sorted(answers, key=lambda answer: answer["answer"])
                current_answers = self.answers.order_by("answer")

                for i in range(len(answers)):
                    if (
                        answers[i]["answer"] != current_answers[i].answer
                        or answers[i]["is_correct"] != current_answers[i].is_correct
                    ):
                        recreate_answers = True
                        break

            if recreate_answers:
                self.answers.update(is_deleted=True)
                for answer in answers:
                    self.answers.create(
                        answer=answer["answer"],
                        is_correct=answer["is_correct"],
                        linked_answer=None,
                    )

        self._update_common(
            question=question,
            locale=locale,
            difficulty=difficulty,
            illustration=illustration,
            delete_illustration=delete_illustration,
            comment=comment,
            tags=tags,
        )

        self.save()

        return self

    @staticmethod
    def create_or_update_mcq(instance, *args, **kwargs):
        """
        Creates or updates a multiple-choices question.

        If the given instance is not None, the instance will be updated. Else,
        it will be created.

        :param instance: The instance (can be None to create).
        :return: The created or updated instance.
        """
        if instance:
            return instance.update_mcq(*args, **kwargs)

        else:
            return Question.create_mcq(*args, **kwargs)

    @staticmethod
    def create_linked(
        question,
        answers,
        locale=None,
        difficulty=2,
        illustration=None,
        comment=None,
        tags=None,
        **kwargs,
    ):
        """
        Creates a linked-choices question.

        :param question: The question.
        :param answers: A list of answers. Each answer is a 2-tuple containing
                        the answer and the linked answer, as strings.
        :param locale: The question's locale, as an instance of QuestionLocale.
        :param difficulty: The question's difficulty, between 1 (easy) and 3 (hard).
        :param illustration: The question's illustration (can be None).
        :param comment: A comment on the question's answer (can be None).
        :param tags: A list of tags for this question (can be None/empty).
        :return: The created question.
        """
        if tags is None:
            tags = []

        question = Question(
            type=QUESTION_LINKED,
            question=question,
            locale=locale or QuestionLocale.objects.first(),
            difficulty=difficulty,
            illustration=illustration,
            answer_comment=comment,
        )
        question.save()

        for tag in tags:
            question.tags.add(tag)

        for answer in answers:
            linked_answer = Answer(
                answer=answer[1], is_correct=False, linked_answer=None
            )
            linked_answer.save()
            question.answers.create(
                answer=answer[0], is_correct=False, linked_answer=linked_answer
            )

        return question

    def update_linked(
        self,
        question,
        answers,
        locale=None,
        difficulty=2,
        illustration=None,
        delete_illustration=False,
        comment=None,
        tags=None,
        **kwargs,
    ):
        """
        Creates a linked-choices question.

        :param question: The question.
        :param answers: A list of answers. Each answer is a 2-tuple containing
                        the answer and the linked answer, as strings.
        :param locale: The question's locale, as an instance of QuestionLocale.
        :param difficulty: The question's difficulty, between 1 (easy) and 3 (hard).
        :param illustration: The question's illustration (can be None).
        :param delete_illustration: If True, the associated illustration will be deleted.
        :param comment: A comment on the question's answer (can be None).
        :param tags: A list of tags for this question (can be None/empty).
        :return: The created question.
        """
        assert (
            self.type == QUESTION_LINKED
        ), f"Trying to update a {self.type} question with update_linked"

        if answers:
            # We compare the answers we were given and the existing answers.
            # If there is differences, we remove all previous answers and add
            # all new ones.
            recreate_answers = False
            if len(answers) != self.answers.count():
                recreate_answers = True
            else:
                answers = sorted(answers, key=lambda answer: answer[0])
                current_answers = self.answers.prefetch_related(
                    "linked_answer"
                ).order_by("answer")

                for i in range(len(answers)):
                    if (
                        answers[i][0] != current_answers[i].answer
                        or answers[i][1] != current_answers[i].linked_answer.answer
                    ):
                        recreate_answers = True
                        break

            if recreate_answers:
                self.answers.update(is_deleted=True, linked_answer__is_deleted=True)
                for answer in answers:
                    linked_answer = Answer(
                        answer=answer[1], is_correct=False, linked_answer=None
                    )
                    linked_answer.save()
                    self.answers.create(
                        answer=answer[0], is_correct=False, linked_answer=linked_answer
                    )

        self._update_common(
            question=question,
            locale=locale,
            difficulty=difficulty,
            illustration=illustration,
            delete_illustration=delete_illustration,
            comment=comment,
            tags=tags,
        )

        self.save()

        return self

    @staticmethod
    def create_or_update_linked(instance, *args, **kwargs):
        """
        Creates or updates a linked-choices question.

        If the given instance is not None, the instance will be updated. Else,
        it will be created.

        :param instance: The instance (can be None to create).
        :return: The created or updated instance.
        """
        if instance:
            return instance.update_linked(*args, **kwargs)

        else:
            return Question.create_linked(*args, **kwargs)
