from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Game, Team, Show
from .tasks import render_souvenir, send_souvenir_sms


class GameAdmin(admin.ModelAdmin):

    actions = ['regenerate_souvenirs']
    list_display = ['pk', 'user', 'show', 'state']

    def regenerate_souvenirs(self, request, queryset):
        for game in queryset:
            s = render_souvenir.s(game.pk)
            s.link(send_souvenir_sms.s())
            s.delay()
    regenerate_souvenirs.short_description = 'Regenerate and send souvenirs'


admin.site.register(User, UserAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Team)
admin.site.register(Show)
