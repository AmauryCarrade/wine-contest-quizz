from os.path import splitext
from hashlib import sha256

from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField
from uuslug import uuslug
from versatileimagefield.fields import VersatileImageField

from quizz.forms.quizzes import (
    OpenQuestionForm,
    MultipleChoicesQuestionForm,
    LinkedQuestionForm,
)
from quizz.models import QUESTION_OPEN, QUESTION_MCQ, QUESTION_LINKED, QUESTION_TYPES


def quizz_illustration_path(instance, filename):
    hash_name = sha256(str(settings.SECRET_KEY[:10] + '-' + str(instance.pk)).encode('utf-8')).hexdigest()
    return f"quizz/illustrations/{hash_name}{splitext(filename)[1] or '.jpg'}"


class QuestionLocale(models.Model):
    """
    Questions are separated by locale.
    """

    """The ISO language tag for this locale (e.g. “fr_FR”)."""
    code = models.CharField(_("ISO code"), max_length=8)

    """The display name for this locale (e.g. “Français”)."""
    name = models.CharField(_("Display name"), max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)


class Contest(models.Model):
    """
    Questions can be from an existing contest.
    """

    name = models.CharField(_("Contest name"), max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)


class Tag(MPTTModel):
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
    """
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True, related_name="children"
    )

    def save(self, *args, **kwargs):
        """Persists a tag, recalculating its slug."""
        self.slug = uuslug(self.name, instance=self)
        super(Tag, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class MPTTMeta:
        order_insertion_by = ["name"]


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

    """Some questions are extracted from a contest."""
    source = models.ForeignKey(
        Contest,
        on_delete=models.SET_NULL,
        verbose_name=_("Contest from which this question is taken"),
        blank=True,
        null=True,
    )

    """The question's difficulty, between 1 (easy) and 3 (hard)"""
    difficulty = models.PositiveSmallIntegerField(
        verbose_name=_("Difficulty"), default=1
    )

    """The question's tags."""
    tags = TreeManyToManyField(Tag, related_name="questions", verbose_name=_("Tags"))

    """The user who created or imported the question."""
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_("Creator"),
        editable=False,
        blank=True,
        null=True,
        related_name="questions_created",
    )

    """The user(s) who edited the question."""
    editors = models.ManyToManyField(
        User, verbose_name=_("Editors"), editable=False, related_name="questions_edited"
    )

    """True if this question was imported."""
    imported = models.BooleanField(
        verbose_name=_("Was this question imported?"), editable=False, default=False
    )

    """The question's text."""
    question = models.CharField(verbose_name=_("Question"), max_length=256)

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
        verbose_name=_("Answer's comment"), max_length=2 ** 16, blank=True, null=True
    )

    def __str__(self):
        return f"{self.question} ({self.verbose_type})"

    @property
    def verbose_type(self):
        for question_type, verbose in QUESTION_TYPES:
            if self.type == question_type:
                return verbose
        return "UNKNOWN"  # Only for non-filled & unsaved questions

    @property
    def is_open(self):
        return self.type == QUESTION_OPEN

    @property
    def is_mcq(self):
        return self.type == QUESTION_MCQ

    @property
    def is_linked(self):
        return self.type == QUESTION_LINKED

    def _selectable_answers(self, with_pk=False):
        """
        Returns the selectable answers of this question.

        If this question is an open question, returns None.
        If it is a MCQ, returns a list of answers.
        If it is a linked question, returns a list of tuples of answers linked
        together, or a tuple of tuples (pk, answer) if `with_pk_ is set to True.

        :param with_pk: For linked answers, changes the data structure returned
                        (see above).
        :return: The answers.
        """
        if self.type == "OPEN":
            return None
        elif self.type == "MCQ":
            return self.answers.filter(is_deleted=False)
        elif self.type == "LINKED":
            if with_pk:
                return [
                    (
                        (answer.pk, answer.answer),
                        (answer.linked_answer.pk, answer.linked_answer.answer),
                    )
                    for answer in self.answers.filter(is_deleted=False)
                    if answer.answer and answer.linked_answer.answer
                ]
            else:
                return [
                    (answer.answer, answer.linked_answer.answer)
                    for answer in self.answers.filter(is_deleted=False)
                    if answer.answer and answer.linked_answer.answer
                ]

    selectable_answers = property(
        _selectable_answers,
        doc="""
        The selectable answers of this question.

        If this question is an open question, None.
        If it is a MCQ, a list of answers.
        If it is a linked question, a list of tuples of answers linked together.
        """,
    )

    @property
    def selectable_answers_with_pk(self):
        """
        Returns the selectable answers of this question.

        If this question is an open question, returns None.
        If it is a MCQ, returns a list of answers.
        If it is a linked question, returns a tuple of tuples (pk, answer) of
        answers linked together.

        :return: The answers.
        """
        return self._selectable_answers(with_pk=True)

    @property
    def answers_count(self):
        return self.answers.filter(is_deleted=False).count()

    @property
    def form_class(self):
        """
        The form class to use to display this question to an user passing
        a quizz.

        All classes returned are subclasses of `QuestionForm`, and they all
        require a `question` argument in their constructors, alongside the
        usual.

        :return: The form's class to use for this question, according to
                 its type.
        """
        if self.type == QUESTION_OPEN:
            return OpenQuestionForm
        elif self.type == QUESTION_MCQ:
            return MultipleChoicesQuestionForm
        elif self.type == QUESTION_LINKED:
            return LinkedQuestionForm
        else:
            return None

    @property
    def reduced_tags(self):
        """
        Reduces the tags to a minimal set, for display.

        If there is a tag and all its children, the children are omitted.
        Also, for each tag we check all ancestors; if there are ancestors in
        the tags list, they are removed as they will be implied anyway.

        :return: A dictionary {tag_pk: (tag, number of children omitted)}
        """
        tags = self.tags.all()
        reduced = {tag.pk: (tag, 1) for tag in tags}

        tag: Tag
        for tag in tags:
            if tag.is_leaf_node():
                continue

            descendants = tag.get_descendants()
            all_in = True
            for child in descendants:
                all_in &= child in tags

            if all_in:
                reduced[tag.pk] = tag, tag.get_descendant_count()
                for child in tag.get_descendants():
                    del reduced[child.pk]

        for tag, children_removed in reduced.copy().values():
            for parent in tag.get_ancestors():
                if parent in tags:
                    del reduced[parent.pk]

        return reduced

    def delete(self, using=None, keep_parents=False):
        for answer in self.answers.all():
            answer.delete()
        super(Question, self).delete(using=using, keep_parents=keep_parents)

    def _update_common(
        self,
        question=None,
        locale=None,
        difficulty=2,
        illustration=None,
        delete_illustration=False,
        comment=None,
        tags=None,
        source=None,
        user=None,
    ):
        """
        Common things updated for every question type.

        :param question: The question.
        :param locale: The question's locale.
        :param difficulty: The question's difficulty.
        :param illustration: The question's illustration.
        :param delete_illustration: True if any existing illustration should be deleted.
        :param comment: The comment on the question's answer.
        :param tags: A list of tags. They will *replace* existing tags.
        :param source: The contest from which this question is taken, or None if there is none.
        :param user: The user who made this edit.
        """
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
            # For tag, we replace all existing tags with the given ones.
            self.tags.clear()
            for tag in tags:
                self.tags.add(tag)

        if user:
            self.editors.add(user)

        self.source = source

    @staticmethod
    def create_open(
        question,
        answer,
        locale=None,
        difficulty=2,
        illustration=None,
        comment=None,
        tags=None,
        source=None,
        user=None,
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
        :param source: The contest from which this question is taken, or None if there is none.
        :param user: The user who created this question.
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
            source=source,
            creator=user,
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
        source=None,
        user=None,
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
        :param source: The contest from which this question is taken, or None if there is none.
        :param user: The user who did this update.
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
            source=source,
            user=user,
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
        source=None,
        user=None,
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
        :param source: The contest from which this question is taken, or None if there is none.
        :param user: The user who created this question.
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
            source=source,
            creator=user,
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
        source=None,
        user=None,
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
        :param source: The contest from which this question is taken, or None if there is none.
        :param user: The user who did this update.
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
            source=source,
            user=user,
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
        source=None,
        user=None,
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
        :param source: The contest from which this question is taken, or None if there is none.
        :param user: The user who created this question.
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
            source=source,
            creator=user,
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
        source=None,
        user=None,
        **kwargs,
    ):
        """
        Updates a linked-choices question.

        :param question: The question.
        :param answers: A list of answers. Each answer is a 2-tuple containing
                        the answer and the linked answer, as strings.
        :param locale: The question's locale, as an instance of QuestionLocale.
        :param difficulty: The question's difficulty, between 1 (easy) and 3 (hard).
        :param illustration: The question's illustration (can be None).
        :param delete_illustration: If True, the associated illustration will be deleted.
        :param comment: A comment on the question's answer (can be None).
        :param tags: A list of tags for this question (can be None/empty). Existing tags will be overwritten.
        :param source: The contest from which this question is taken, or None if there is none.
        :param user: The user who did this update.
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
            source=source,
            user=user,
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
