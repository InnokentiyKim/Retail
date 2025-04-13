from baton.autodiscover import admin
from django.urls import path
from django.urls.conf import include, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from backend.views import authorize_by_oauth, oauth_complete_redirect

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path('', include('social_django.urls', namespace='social')),
    path('social-auth/', authorize_by_oauth),
    path('social-auth/success/', oauth_complete_redirect, name='oauth-complete'),
    path('baton/', include('baton.urls')),
    path('sentry-debug/', trigger_error),
    path('api/v1/', include('backend.urls'), name='backend'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]
