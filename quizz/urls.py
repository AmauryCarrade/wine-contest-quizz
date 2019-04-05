from django.urls import include, path

from .views.public.quizzes import QuizzView, CreateQuizzView, UserQuizzesListView
from .views.public.pages import LegalView

from .views.management.data_import import QuestionsImportView, UndoImportView
from .views.management.questions import (
    QuestionsListView,
    EditQuestionView,
    QuestionDeleteView,
)
from .views.management.quizzes import QuizzesListView
from .views.management.tags import MigrateTagsView
from .views.management.users import UsersListView, UserProfileView


app_name = "quizz"

# fmt: off
management_patterns = (
    [
        path("questions", QuestionsListView.as_view(), name="questions"),
        path("questions/create", EditQuestionView.as_view(), name="questions-create"),
        path("questions/import", QuestionsImportView.as_view(), name="questions-import"),
        path("questions/import/undo", UndoImportView.as_view(), name="questions-import-undo",),
        path("questions/edit/<int:pk>", EditQuestionView.as_view(), name="questions-edit"),
        path("questions/delete/<int:pk>",QuestionDeleteView.as_view(), name="questions-delete",),
        path("quizzes", QuizzesListView.as_view(), name="quizzes"),
        path("quizzes/<str:username>", UserProfileView.as_view(), name="users-quizzes"),
        path("users", UsersListView.as_view(), name="users"),
        path("tags-migration", MigrateTagsView.as_view(), name="tags-migration"),
    ],
    "management",
)

urlpatterns = [
    path("", CreateQuizzView.as_view(), name="create-quizz"),
    path("quizzes", UserQuizzesListView.as_view(), name="user-quizzes"),
    path("quizz/<slug:slug>", QuizzView.as_view(), name="quizz"),
    path("legal", LegalView.as_view(), name="legal"),
    path("management/", include(management_patterns, namespace="management")),
]
# fmt: on
