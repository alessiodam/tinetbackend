from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import TINETUser, AppAPIKey, SessionToken, WebPopUp, UserWebPopUp, AllowedApp


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = TINETUser


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = TINETUser


class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'bio', 'calc_key', 'api_key')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)


class SessionTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'expiry_date', 'expired')
    search_fields = ('user__username', 'token')
    list_filter = ('expired',)


class AppAPIKeyAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'key', 'expires', 'last_used', 'expired')
    search_fields = ('id', 'user__username', 'name', 'key')
    list_filter = ('id', 'expired', 'expires')


class UserWebPopUpInline(admin.TabularInline):
    model = UserWebPopUp


class WebPopUpAdmin(admin.ModelAdmin):
    inlines = [
        UserWebPopUpInline,
    ]
    list_display = ('title', 'description', 'get_users_accepted')

    def get_users_accepted(self, obj):
        return obj.users.count()

    get_users_accepted.short_description = 'Users Accepted'


class UserWebPopUpAdmin(admin.ModelAdmin):
    list_display = ('user', 'popup', 'confirmed')


class AllowedAppAdmin(admin.ModelAdmin):
    list_display = ('allow_id', 'user', 'app', 'granted_date')


admin.site.register(TINETUser, CustomUserAdmin)
admin.site.register(SessionToken, SessionTokenAdmin)
admin.site.register(AppAPIKey, AppAPIKeyAdmin)
admin.site.register(WebPopUp, WebPopUpAdmin)
admin.site.register(UserWebPopUp, UserWebPopUpAdmin)
admin.site.register(AllowedApp, AllowedAppAdmin)
