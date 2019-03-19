import requests
from django.core.files import File
from django.dispatch import receiver

from os.path import splitext

from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from path import TempDir

from versatileimagefield.fields import VersatileImageField
from versatileimagefield.placeholder import OnDiscPlaceholderImage


def profile_image_path(instance, filename):
    return f"users/{instance.user.pk}{splitext(filename)[1] or '.jpg'}"


class Profile(models.Model):
    """
    Additional data attached to an user.
    """

    """The user this profile is linked to."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    locale = models.CharField(
        verbose_name=_("User locale"), blank=True, null=True, max_length=6
    )

    """A picture to represent this user."""
    picture = VersatileImageField(
        verbose_name=_("User picture"),
        null=True,
        blank=True,
        upload_to=profile_image_path,
        placeholder_image=OnDiscPlaceholderImage(
            path=settings.BASE_DIR / "static" / "images" / "user-default-picture.png"
        ),
    )


@receiver(models.signals.post_save, sender=User)
def create_profile_for_new_users(sender, instance, created, **kwargs):
    """
    This signal ensures there is a profile for every user.
    """
    if not created:
        return

    profile = Profile.objects.filter(user=instance).first()
    if profile is None:
        profile = Profile(user=instance)
        profile.save()


def save_profile_picture(backend, user, response, *args, **kwargs):
    """
    This method is called in the social pipeline when a user logs in
    using its Google account.

    It creates a profile, if needed, and updates the profile picture.
    """
    profile = Profile.objects.filter(user=user).first()
    if profile is None:
        profile = Profile(user=user)

    if "locale" in response:
        profile.locale = response["locale"]

    if "picture" in response:
        with TempDir() as d:
            _name, ext = splitext(response["picture"])
            r = requests.get(response["picture"], stream=True)

            if r.ok:
                temp_file = d / f"{user.pk}{ext or '.jpg'}"

                with open(temp_file, "wb") as fd:
                    for chunk in r.iter_content(chunk_size=128):
                        fd.write(chunk)

                with temp_file.open("rb") as fd:
                    profile.picture.save(
                        f"{user.pk}{ext or '.jpg'}", File(fd), save=False
                    )

    profile.save()
