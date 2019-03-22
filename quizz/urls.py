from django.urls import include, path

from .views.public import QuizzView, CreateQuizzView, UserQuizzesListView, LegalView

from .views.management import (
    QuestionsListView,
    EditQuestionView,
    QuestionsImportView,
    UndoImportView,
    QuestionDeleteView,
    MigrateTagsView,
    QuizzesListView,
    UserProfileView,
    UsersListView,
)

app_name = "quizz"

management_patterns = (
    [
        path("questions", QuestionsListView.as_view(), name="list"),
        path("questions/create", EditQuestionView.as_view(), name="create"),
        path("questions/import", QuestionsImportView.as_view(), name="import"),
        path("questions/import/undo", UndoImportView.as_view(), name="undo-import"),
        path("questions/edit/<int:pk>", EditQuestionView.as_view(), name="edit"),
        path("questions/delete/<int:pk>", QuestionDeleteView.as_view(), name="delete"),
        path("quizzes", QuizzesListView.as_view(), name="quizzes"),
        path("quizzes/<str:username>", UserProfileView.as_view(), name="user-quizzes"),
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
