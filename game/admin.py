from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Game, Team, Show

admin.site.register(User, UserAdmin)
admin.site.register(Game)
admin.site.register(Team)
admin.site.register(Show)
