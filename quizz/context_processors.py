from django.http import HttpRequest

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
