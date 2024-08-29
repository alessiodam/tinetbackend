from django.contrib.auth import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from users.models import AuditEntry


@receiver(user_logged_in)
def user_web_logged_in_callback(sender, request, user, **kwargs):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    AuditEntry.objects.create(action='logged in on web', ip=ip, username=user.username)


@receiver(user_logged_out)
def user_web_logged_out_callback(sender, request, user, **kwargs):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    AuditEntry.objects.create(action='logged out on web', ip=ip, username=user.username)
