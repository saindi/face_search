from django.contrib import admin
from user.models import UserModel


@admin.register(UserModel)
class UserModelAdmin(admin.ModelAdmin):
    list_display = "username", "first_name", "last_name", "email", "is_staff", "is_active"
    list_filter = "is_staff", "is_active"
