from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User, Subscription


@admin.register(User)
class UserAdmin(UserAdmin):
    """Админка для модели User."""

    list_display = (
        'id', 'username', 'email', 'first_name',
        'last_name', 'is_staff', 'is_active'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password', 'email', 'avatar')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name')}),
        ('Права доступа', {'fields': (
            'is_staff', 'is_active', 'is_superuser',
            'groups', 'user_permissions',
        )}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name', 'last_name',
                'password1', 'password2', 'is_staff', 'is_active',
            ),
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для модели Follow."""

    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')
    list_filter = ('user', 'author')
    ordering = ('id',)
