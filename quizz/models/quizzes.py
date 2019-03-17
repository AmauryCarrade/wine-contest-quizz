import random
import string
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils.functional import cached_property
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from quizz.forms.quizzes import (
    OpenQuestionForm,
    MultipleChoicesQuestionForm,
    LinkedQuestionForm,
)
from quizz.models import QuestionSuccess
from quizz.models.questions import Question, Answer
from quizz.text_processors import gentle_levenshtein_distance
from quizz.utils import as_choices


class QuizzAnswer(models.Model):
    """
    This is an answer from an user for MCQ and linked ones.

    It references the first proposed answer (for linked, only one else) and the
    answer provided by the user.

    These instances are created when the user reply to the related question. So,
    the fields can be (and are) required.
    """

    """
    The answer this record is about.
    """
    proposed_answer = models.ForeignKey(
        Answer,
        on_delete=models.PROTECT,
        related_name="user_answers",
        verbose_name=_("The answer that was proposed to the user"),
        editable=False,
    )

    """
    For MCQ only: was the answer checked?
    """
    is_checked = models.BooleanField(
        verbose_name=_("Was this answer checked?"), null=True, blank=True
    )

    """
    For linked only: to which answer was this answer linked?
    """
    linked_to = models.ForeignKey(
        Answer,
        on_delete=models.PROTECT,
        related_name="linked_to_by_users",
        verbose_name=_("The answer linked to this answer by the user"),
        null=True,
        blank=True,
    )

    def clean(self):
        if not self.is_checked and not self.linked_to:
            raise ValidationError(
                "Trying to save a quizz answer with neither a checked state "
                "nor a linked answer."
            )


class QuizzQuestion(models.Model):
    """
    In this model are stored both the questions of a specific
    quizz, and the answers the user responded to these questions,
    as well as the earned points and success.
    """

    # Question and general metadata

    """
    The question this is all about.
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        verbose_name=_("The question"),
        related_name="user_answers",
    )

    """
    The order of the question in the quizz.
    """
    order = models.SmallIntegerField(
        verbose_name=_("The ordering of the question in the quizz")
    )

    """
    The moment when this question was started (i.e. displayed to the user).
    """
    started_at = models.DateTimeField(
        verbose_name=_("The moment when this question was started"),
        null=True,
        blank=True,
        editable=False,
        default=None,
    )

    """
    The moment when this question was finished (i.e. form submitted by the user).
    """
    finished_at = models.DateTimeField(
        verbose_name=_("The moment when this quizz was finished"),
        null=True,
        blank=True,
        editable=False,
        default=None,
    )

    # Answers
    # All fields after this point must be nullable, as they will be filled only
    # when the question is answered.

    """
    The open answer the user submitted.
    
    Used for:
    → open questions;
    → MCQ with open answer.
    """
    open_answer = models.CharField(
        verbose_name=_("Open answer"),
        blank=True,
        null=True,
        default=None,
        max_length=1024,
    )

    """
    All other answers the user submitted. This includes both MCQ and linked
    answers, following the fields filled in the related model (like in
    models.questions.Answer).
    
    Used for:
    → multiple-choices questions;
    → linked questions.
    """
    answers = models.ManyToManyField(
        QuizzAnswer, verbose_name=_("All non-open answers")
    )

    # Success & points

    """
    The correctness of the user's answer to this question.
    """
    success = models.CharField(
        verbose_name=_("Was this question correctly answered?"),
        choices=as_choices(QuestionSuccess),
        null=True,
        blank=True,
        default=None,
        max_length=8,
    )

    """
    The points given for the user's answer to this question.
    """
    points = models.FloatField(
        verbose_name=_("The points earned for this question"),
        null=True,
        blank=True,
        default=None,
    )

    @property
    def is_finished(self):
        return self.finished_at is not None

    @cached_property
    def form(self):
        """
        Returns a form instance to use to answer this question.

        :return: The form's instance ready to be used.
        """
        return self.question.form_class(question=self.question)

    def register_answer(self, data):
        """
        From the given POST data (generated by the question's form), analyses
        the answers and stores them alongside success and points.

        :param data: The POST data generated by this question's form.
        :return: True if the answer was correctly saved; False else. (Unrelated
                 to the fact the answer is actually correct.)
        """
        form = self.question.form_class(data=data, question=self.question)

        if not form.is_valid():
            return False

        self.finished_at = timezone.now()

        if self.question.is_open:
            form: OpenQuestionForm = form

            # For open answers, we compare the answer to the valid one, and
            # according to the Levenshtein distance between both (ignoring
            # spaces, punctuation, etc.), we give more or less points.

            self.open_answer = form.cleaned_data["answer"]

            distance = gentle_levenshtein_distance(
                self.question.open_valid_answer, self.open_answer
            )

            if distance == 0:
                self.points = self.question.difficulty
                self.success = QuestionSuccess.PERFECT.value
            elif distance < 4:
                self.points = float(self.question.difficulty) / 2.0
                self.success = QuestionSuccess.ALMOST.value
            else:
                self.points = 0
                self.success = QuestionSuccess.FAILED.value

        elif self.question.is_mcq:
            form: MultipleChoicesQuestionForm = form

            # For MCQ, points are awarded in proportion to the correctly ticked
            # answers, with a penalty if incorrect answers are ticked, to
            # penalize those who would seek to maximize their points by
            # systematically tick all answers. In the case of an open answer,
            # it reports such an exact point, half a point if it is close, and
            # none otherwise.

            answers = self.question.selectable_answers

            user_answers = []
            correct_user_answers = 0
            wrong_user_answers_checked = 0

            open_answer_points = 0.0
            open_answer_count = 0.0

            if self.question.has_open_choice:
                open_answer_count = 1

                distance = gentle_levenshtein_distance(
                    self.question.open_valid_answer,
                    form.cleaned_data["other_answer"]
                    if "other_answer" in form.cleaned_data
                    else None,
                )

                if distance == 0:
                    open_answer_points = 1.0
                elif distance < 4:
                    open_answer_points = 0.5
                else:
                    open_answer_points = 0.0

            for answer in answers:
                user_checked = str(answer.pk) in form.cleaned_data["answers"]
                if user_checked == answer.is_correct:
                    correct_user_answers += 1
                elif user_checked and not answer.is_correct:
                    wrong_user_answers_checked += 1

                user_answer = QuizzAnswer(
                    proposed_answer=answer, is_checked=user_checked, linked_to=None
                )
                user_answer.save()
                user_answers.append(user_answer)

            self.points = max(
                self.question.difficulty
                * (
                    float(
                        correct_user_answers
                        - wrong_user_answers_checked
                        + open_answer_points
                    )
                    / float(len(answers) + open_answer_count)
                ),
                0,
            )

            if correct_user_answers == len(answers):
                self.success = QuestionSuccess.PERFECT.value
            elif correct_user_answers == len(answers) - 1 and correct_user_answers > 1:
                self.success = QuestionSuccess.ALMOST.value
            else:
                self.success = QuestionSuccess.FAILED.value

            self.answers.add(*user_answers)

        elif self.question.is_linked:
            form: LinkedQuestionForm = form

            # For linked questions, we check if answers are linked to the good
            # ones. Unlinked or badly-linked answers gives no points.

            answers = self.question.selectable_answers_with_pk

            user_answers = []
            correct_user_answers = 0

            for answer, linked in answers:
                if str(answer[0]) not in form.cleaned_data:
                    continue

                user_linked = Answer.objects.get(pk=form.cleaned_data[str(answer[0])])
                if linked[1] == user_linked:
                    correct_user_answers += 1

                user_answer = QuizzAnswer(
                    proposed_answer=Answer.objects.get(pk=answer[0]),
                    is_checked=None,
                    linked_to=user_linked,
                )
                user_answer.save()
                user_answers.append(user_answer)

            self.points = self.question.difficulty * (
                float(correct_user_answers) / len(answers)
            )

            if correct_user_answers == len(answers):
                self.success = QuestionSuccess.PERFECT.value
            elif correct_user_answers == len(answers) - 1 and correct_user_answers > 1:
                self.success = QuestionSuccess.ALMOST.value
            else:
                self.success = QuestionSuccess.FAILED.value

            self.answers.add(*user_answers)

        self.save()
        return True


class Quizz(models.Model):
    """
    This is a quizz passed by an user. When someone request a quizz, all
    questions are created and stored there, and this is used as reference for
    ongoing quizzes and history.
    """

    """
    The quizz' slug. As quizzes may be generated by anonymous users, and
    there could not be any security for these, we don't use PKs to identify
    quizzes in the URL.
    """
    slug = models.SlugField(verbose_name=_("The quizz' slug"), max_length=8)

    """
    The user passing the quizz. It can be anonymous (and then, this field is set
    to None).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("The user passing this quizz"),
        related_name="quizzes",
        editable=False,
        null=True,
        blank=True,
    )

    """
    The IP address of the user passing the quizz.
    As anonymous quizzes are allowed, we store the users IPs to be able to
    block abuses later, if required.
    
    The field is nullable to be able to delete IPs after a delay (RGPD).
    """
    # TODO Addresses should be deleted after one year.
    ip = models.GenericIPAddressField(
        verbose_name=_("The IP address of the user passing this quizz"),
        editable=False,
        null=True,
        blank=True,
    )

    """
    The moment when this quizz was started (i.e. first question displayed to the
    user).
    """
    started_at = models.DateTimeField(
        verbose_name=_("The moment when this quizz was started"),
        auto_now_add=True,
        editable=False,
    )

    """
    The moment when this quizz was finished (i.e. last question submitted by the
    user).
    """
    finished_at = models.DateTimeField(
        verbose_name=_("The moment when this quizz was finished"),
        null=True,
        blank=True,
        editable=False,
        default=None,
    )

    """
    All the questions in this quizz. Their order is also in this related model.
    """
    questions = models.ManyToManyField(
        QuizzQuestion, verbose_name=_("The questions in this quizz")
    )

    def save(self, **kwargs):
        """
        Generates a random unique slug on the fly if needed.
        """
        if not self.slug:
            slug = None
            while slug is None:
                slug = "".join(
                    random.choices(
                        string.ascii_lowercase + string.digits,
                        k=self._meta.get_field("slug").max_length,
                    )
                )
                # We said unique slug
                if Quizz.objects.filter(slug=slug).exists():
                    slug = None
            self.slug = slug
        return super(Quizz, self).save(**kwargs)

    @property
    def is_running(self):
        return not self.finished_at

    @cached_property
    def all_questions(self):
        return self.questions.order_by("order").prefetch_related("question")

    @cached_property
    def current_question(self):
        return self.questions.filter(finished_at__isnull=True).order_by("order").first()

    @cached_property
    def questions_total(self):
        return self.questions.count()

    @cached_property
    def questions_finished(self):
        return self.questions.filter(finished_at__isnull=False).count()

    @cached_property
    def questions_left(self):
        return self.questions_total - self.questions_finished

    @cached_property
    def points(self):
        """
        Returns a 3-tuple containing first the amount of points gained by the
        user, then the maximum number of points, then the percentage of success
        as a number between 0 and 1. All floats.

        :return: (user_points, max_points, percentage)
        """
        points = self.all_questions.aggregate(
            user_points=Sum("points"), max_points=Sum("question__difficulty")
        )
        return (
            points["user_points"],
            points["max_points"],
            float(points["user_points"]) / float(points["max_points"]),
        )

    @staticmethod
    def generate_quizz(
        user,
        questions_count,
        ip=None,
        locale=None,
        contest=None,
        tags=None,
        difficulty=None,
    ):
        """
        Generates and returns a new quizz for the given user and following
        the criteria.

        :param user: The user to generate this quizz for. This can be None if
                     the user is anonymous.
        :param questions_count: The amount of questions in the quizz.
        :param ip: The IP of the user passing this quizz.
        :param locale: The locale to restrict questions to. If None, no
                       restriction.
        :param contest: The contest of the questions in the quizz. If None,
                        no filtering.
        :param tags: The tags of the questions in the quizz. Child tags will be
                     selected too.
        :param difficulty: The difficulty of the questions. Some questions with
                           a smaller difficulty may be selected.

        :return: The generated quizz instance, already saved.
        """
        questions = Question.objects.all()

        # We first hard-filter questions with strict conditions (locale, contest…)

        if locale:
            questions = questions.filter(locale=locale)

        if contest:
            questions = questions.filter(source=contest)

        if tags:
            # We use all tags and their children on all levels
            all_tags = set(tags)
            for tag in tags:
                for child in tag.get_descendants():
                    all_tags.add(child)
            questions = questions.filter(tags__in=all_tags)

        if difficulty != 0:
            # The case of difficulty is a bit different:
            # if the user select “medium” we give him 80% medium and 20% easy questions
            # (randomly with weights, so the amounts may be a little bit different).
            # Here we only exclude questions with a too high difficulty.
            questions = questions.filter(difficulty__lte=difficulty)

        # Then we retrieve all questions matching these criteria, and we randomly
        # select them in Python, to be able to have weighted random choice.

        questions = list(questions)
        questions_weights = []

        questions_count = min(questions_count, len(questions))

        # If nothing match the criteria…
        if not questions:
            return None

        # If we have to select questions
        elif questions_count < len(questions):
            for index, question in enumerate(questions):
                weight = 100

                # Difficulty
                if question.difficulty == difficulty:
                    weight += 80
                elif question.difficulty == difficulty - 1:
                    weight += 20
                elif question.difficulty == difficulty - 2:
                    weight -= 10

                # TODO option to weight up new questions or questions with difficulties

                questions_weights.insert(index, weight)

            selected_questions = random.choices(
                questions, questions_weights, k=questions_count
            )

        # We will select all questions anyway, as we want as many as we have.
        else:
            selected_questions = questions
            random.shuffle(selected_questions)

        # Now that we have the questions, we create the quizz in the database,
        # using the order from the selected questions list.

        quizz = Quizz(user=user if user.is_authenticated else None, ip=ip)
        quizz.save()

        for index, question in enumerate(selected_questions):
            quizz.questions.create(question=question, order=index)

        return quizz
