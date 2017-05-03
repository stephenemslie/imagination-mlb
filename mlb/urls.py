from django.conf.urls import url
from django.contrib import admin
from rest_framework import routers

from game.views import UserViewSet, GameViewSet

urlpatterns = [
    url(r'^admin/', admin.site.urls),
]

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'games', GameViewSet)
urlpatterns += router.urls
