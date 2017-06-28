from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from rest_framework import routers
from rest_framework_jwt.views import obtain_jwt_token

from game.views import UserViewSet, GameViewSet, TeamViewSet, set_lighting

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^token/', obtain_jwt_token),
    url(r'^lighting/', set_lighting),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'games', GameViewSet)
router.register(r'teams', TeamViewSet)
urlpatterns += router.urls
