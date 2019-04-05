from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from quizz.models import Quizz
from quizz.views.public.quizzes import QuizzesListMixin


class QuizzesListView(LoginRequiredMixin, PermissionRequiredMixin, QuizzesListMixin):
    permission_required = "quizz.view_quizz"

    def get_base_queryset(self):
        return Quizz.objects.all()

    def get_context_data(self, *args, **kwargs):
        context = super(QuizzesListView, self).get_context_data(*args, **kwargs)

        context["management"] = True
        context["quizzes_user"] = None

        return context
