from django.utils import timezone
from django.views.generic import TemplateView


class LegalView(TemplateView):
    template_name = "public/legal.html"
    extra_context = {"year": timezone.now().year}
