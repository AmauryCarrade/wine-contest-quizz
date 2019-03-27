from django.core.cache import cache
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.http import HttpRequest

from quizz.models import Question
from .models.quizzes import Quizz


def ongoing_quizzes(request: HttpRequest):
    """
    Context processor injecting the ongoing quizzes of the logged-in user
    into the context. If the user is not logged in, nothing is added.
    """
    context = {}

    if hasattr(request, "user") and request.user.is_authenticated:
        context["ongoing_quizzes"] = Quizz.objects.filter(
            user=request.user, finished_at__isnull=True
        )

    return context


def _collect_stats():
    """
    Collects generic statistics about this instance for display in the
    management menu.
    """
    return {
        "questions": Question.objects.count(),
        "users": User.objects.count(),
        "anonymous": Quizz.objects.filter(user__isnull=True)
        .values("ip")
        .distinct()
        .count(),
        "quizzes": Quizz.objects.filter(finished_at__isnull=False).count(),
        "mean_quizzes_per_user": int(
            User.objects.all()
            .annotate(quizzes_count=Count("quizzes"))
            .aggregate(mean_quizzes=Avg("quizzes_count"))["mean_quizzes"]
        ),
        "mean_questions_per_quizz": int(
            Quizz.objects.all()
            .annotate(questions_count=Count("questions"))
            .aggregate(mean_questions=Avg("questions_count"))["mean_questions"]
        ),
    }


def overview_statistics(request: HttpRequest):
    context = {}

    if hasattr(request, "user") and request.user.is_authenticated:
        if (
            request.user.has_perm("quizz.view_question")
            or request.user.has_perm("auth.view_user")
            or request.user.has_perm("quizz.view_quizz")
        ):
            context["overview_statistics"] = cache.get_or_set(
                "overview-statistics", _collect_stats, timeout=86400
            )

    return context
