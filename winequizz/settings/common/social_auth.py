from .credentials import credentials

social_credentials = credentials.get("social_auth", {})

AUTHENTICATION_BACKENDS = [
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_REDIRECT_URL = "quizz:create-quizz"
LOGOUT_REDIRECT_URL = "quizz:create-quizz"

SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'social_core.pipeline.social_auth.associate_by_email',
    'quizz.models.users.save_profile_picture',
]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = social_credentials.get(
    "google_oauth2_key",
    "831444856202-r8sdhk86tsjjttqc279ostqb736li02d.apps.googleusercontent.com",
)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = social_credentials.get(
    "google_oauth2_secret", "K9clphncnjavFL2pW-754wsb"
)
