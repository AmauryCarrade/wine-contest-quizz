from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count, Max, Case, When, IntegerField
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.views.generic import ListView

from quizz.models import Quizz
from quizz.views.public.quizzes import QuizzesListMixin


class UserProfileView(LoginRequiredMixin, PermissionRequiredMixin, QuizzesListMixin):
    permission_required = ("quizz.view_quizz", "auth.view_user")

    @cached_property
    def user(self):
        return get_object_or_404(User, username=self.kwargs["username"])

    def get_base_queryset(self):
        return Quizz.objects.filter(user=self.user)

    def get_context_data(self, *args, **kwargs):
        context = super(UserProfileView, self).get_context_data(*args, **kwargs)

        context["management"] = True
        context["quizzes_user"] = self.user

        return context


class UsersListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "management/users-list.html"
    context_object_name = "users"

    permission_required = "auth.view_user"

    model = User
    paginate_by = 20

    def get_queryset(self):
        return (
            super(UsersListView, self)
            .get_queryset()
            .annotate(
                quizzes_count=Count("quizzes", distinct=True),
                questions_count=Count("quizzes__questions", distinct=True),
                groups_count=Max(
                    Case(
                        When(groups__isnull=False, then=1),
                        default=0,
                        output_field=IntegerField(),
                    )
                ),
            )
            .order_by(
                "-is_superuser",
                "-is_staff",
                "-groups_count",
                "last_name",
                "first_name",
                "username",
            )
            .select_related("profile")
            .prefetch_related("groups")
        )
