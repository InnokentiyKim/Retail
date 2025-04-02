from baton.autodiscover import admin
from django.urls import path
from django.urls.conf import include, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from backend.views import authorize_by_oauth

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path('', include('social_django.urls', namespace='social')),
    path('social-auth/', authorize_by_oauth),
    path('baton/', include('baton.urls')),
    path('api/v1/', include('backend.urls'), name='backend'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]
