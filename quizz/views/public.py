from django.shortcuts import render

from django.views.generic import DetailView

from quizz.models import Question


class QuestionView(DetailView):
    model = Question
