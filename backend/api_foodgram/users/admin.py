from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Subscription, User


class UserAdmin(BaseUserAdmin):
    list_filter = ('email', 'username')


admin.site.register(User, UserAdmin)
admin.site.register(Subscription)
