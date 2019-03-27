from datetime import timedelta, datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F, FloatField, Count, Case, When, IntegerField
from django.http import HttpResponseRedirect, Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, FormView, ListView, TemplateView
from ipware import get_client_ip

from quizz.forms.public import CreateQuizzForm
from quizz.models import Quizz, QuizzQuestion


class CreateQuizzView(FormView):
    form_class = CreateQuizzForm
    template_name = "public/quizz-create.html"

    def form_valid(self, form):
        ip, _routable = get_client_ip(self.request)
        quizz = Quizz.generate_quizz(
            user=self.request.user,
            ip=ip,
            questions_count=form.cleaned_data["how_many"],
            locale=form.cleaned_data["locale"],
            contest=form.cleaned_data["contest"],
            tags=form.cleaned_data["tags"],
            difficulty=int(form.cleaned_data["difficulty"]),
        )

        if not quizz:
            messages.error(
                self.request,
                _(
                    "We are really sorry, but we have no questions that "
                    "satisfy your wishes. You might try asking for something "
                    "else…"
                ),
            )
            return HttpResponseRedirect(reverse_lazy("quizz:create-quizz"))

        if quizz.questions_total < form.cleaned_data["how_many"]:
            messages.warning(
                self.request,
                _(
                    "This quiz contains fewer questions than you asked because "
                    "we don't have enough. We hope it won't be too annoying."
                ),
            )

        return HttpResponseRedirect(reverse_lazy("quizz:quizz", args=(quizz.slug,)))


class QuizzView(DetailView):
    model = Quizz
    context_object_name = "quizz"

    def check_allowed(self, quizz):
        """
        Checks if the current user is allowed to access this quizz.

        :param quizz: The quizz to check access for.
        :raises Http404: If the user is not allowed to access this quizz.
        """
        # For ongoing quizzes, only the owner is allowed to access the quizz, or
        # everyone but only if the owner is anonymous.
        allowed = (quizz.user is None and not self.request.user.is_authenticated) or (
            quizz.user == self.request.user
        )

        # If the quizz is finished, we also allow users with the permission to
        # view quizzes to view all quizzes.
        if not quizz.is_running:
            allowed |= (
                self.request.user.is_authenticated
                and self.request.user.has_perm("quizz.view_quizz")
            )

        if not allowed:
            raise Http404("User is not allowed to access this quizz.")

    def get_template_names(self):
        if self.object.is_running:
            return ["public/quizz-question.html"]
        else:
            return ["public/quizz-report.html"]

    def get_queryset(self):
        return super().get_queryset().prefetch_related("questions")

    def get_object(self, queryset=None):
        quizz: Quizz = super(QuizzView, self).get_object(queryset=queryset)

        self.check_allowed(quizz)

        # Rotten quizz (somehow)
        if quizz.questions_total == 0:
            quizz.delete()
            raise Http404

        if (
            quizz.is_running
            and quizz.current_question
            and (
                not quizz.current_question.started_at
                or timezone.now() - quizz.current_question.started_at
                > timedelta(hours=1)
            )
        ):
            quizz.current_question.started_at = timezone.now()
            quizz.current_question.save()

        return quizz

    def post(self, request, *args, **kwargs):
        if "slug" not in kwargs or not kwargs["slug"]:
            raise Http404

        quizz = get_object_or_404(Quizz, slug=kwargs["slug"])

        self.check_allowed(quizz)

        question: QuizzQuestion = quizz.current_question

        # If the quizz is finished, we don't allow POST requests to it.
        if not question:
            return HttpResponseNotAllowed(["GET", "OPTIONS", "HEAD"])

        # register_answer returns False if the form was not valid.
        if not question.register_answer(request.POST):
            messages.error(
                request,
                _(
                    "It looks like you tried to temper with the form's data. "
                    "We were therefore unable to save your answer. "
                    "Don't do that."
                ),
            )

        # If it's the last question of the quizz, we mark it as, well, finished.
        if quizz.questions_left == 0:
            quizz.finished_at = timezone.now()
            quizz.save()

        # We always redirect to ourself. Either the quizz is not finished, and
        # the next question will be displayed, either it is and the summary
        # will be.
        return HttpResponseRedirect(reverse_lazy("quizz:quizz", args=(quizz.slug,)))


class QuizzesListMixin(ListView):
    template_name = "public/quizz-list.html"

    model = Quizz
    paginate_by = 20

    context_object_name = "quizzes"

    def get_base_queryset(self):
        return super(QuizzesListMixin, self).get_queryset()

    def get_queryset(self):
        return (
            self.get_base_queryset()
            .filter(finished_at__isnull=False)
            .annotate(
                score=Sum("questions__points", output_field=FloatField())
                / Sum("questions__question__difficulty", output_field=FloatField())
                * 100,
                questions_count=Count("questions"),
                perfect_answers=Sum(
                    Case(
                        When(questions__success="PERFECT", then=1),
                        default=0,
                        output_field=IntegerField(),
                    )
                ),
                almost_answers=Sum(
                    Case(
                        When(questions__success="ALMOST", then=1),
                        default=0,
                        output_field=IntegerField(),
                    )
                ),
                failed_answers=Sum(
                    Case(
                        When(questions__success="FAILED", then=1),
                        default=0,
                        output_field=IntegerField(),
                    )
                ),
            )
            .prefetch_related("user", "user__profile")
            .order_by("-finished_at")
        )


class UserQuizzesListView(LoginRequiredMixin, QuizzesListMixin):
    def get_base_queryset(self):
        return Quizz.objects.filter(user=self.request.user)


class LegalView(TemplateView):
    template_name = "public/legal.html"
    extra_context = {"now": timezone.now()}
