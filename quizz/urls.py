from django.urls import include, path

from .views.public import QuizzView, CreateQuizzView

from .views.management import (
    QuestionsListView,
    EditQuestionView,
    QuestionsImportView,
    UndoImportView,
    QuestionDeleteView,
)

app_name = "quizz"

management_patterns = (
    [
        path("questions", QuestionsListView.as_view(), name="list"),
        path("create", EditQuestionView.as_view(), name="create"),
        path("import", QuestionsImportView.as_view(), name="import"),
        path("import/undo", UndoImportView.as_view(), name="undo-import"),
        path("edit/<int:pk>", EditQuestionView.as_view(), name="edit"),
        path("delete/<int:pk>", QuestionDeleteView.as_view(), name="delete"),
    ],
    "management",
)

urlpatterns = [
    path("", CreateQuizzView.as_view(), name="create-quizz"),
    path("quizz/<slug:slug>", QuizzView.as_view(), name="quizz"),
    path("management/", include(management_patterns, namespace="management")),
]
