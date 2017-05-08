from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Game, Team

admin.site.register(User, UserAdmin)
admin.site.register(Game)
admin.site.register(Team)
