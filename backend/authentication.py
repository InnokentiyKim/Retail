from .models import Profile



def create_user_pipeline(strategy, details, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}
    fields = dict((field, kwargs.get(field, details.get(field))) for field in strategy.setting(
        'USER_FIELDS', ['username', 'email']))
    fields['is_active'] = True
    if not fields:
        return None
    try:
        user = strategy.storage.user.create_user(**fields)
    except Exception as err:
        raise err
    return {'is_new': True, 'user': user}


def create_profile(backend, user, *args, **kwargs):
    Profile.objects.get_or_create(user=user)
