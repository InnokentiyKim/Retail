from .models import Profile
from social_core.pipeline.user import create_user
from social_core.pipeline.social_auth import associate_user
from social_core.pipeline.user import user_details


def create_profile(backend, user, *args, **kwargs):
    Profile.objects.get_or_create(user=user)

# def create_user_pipeline(strategy, details, user=None, *args, **kwargs):
#     if user:
#         return {'is_new': False}
#     fields = dict((field, kwargs.get(field, details.get(field))) for field in strategy.setting(
#         'USER_FIELDS', ['username', 'email']))
#     if not fields:
#         return None
#     try:
#         user = strategy.storage.user.create_user(fields)
#     except Exception as err:
#         strategy.storage.user.delete_user(user)
#         raise err
#     return {'is_new': True, 'user': user}
#
#
# def associate_user_pipeline(strategy, details, user=None, *args, **kwargs):
#     if user:
#         return None
#     try:
#         user = strategy.storage.user.get_user(details['email'])
#     except strategy.storage.user.model.DoesNotExist:
#         return None
#
#     return {'user': user}
#
#
# def update_user_details_pipeline(strategy, user, response, details, *args, **kwargs):
#     user.username = details.get('username', '')
#     user.email = details.get('email', '')
#     user.save()
#     return user





