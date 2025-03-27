from .models import Profile


def create_profile(backend, user, *args, **kwargs):
    Profile.objects.get_or_create(user=user)