from django.db import models, connections
from django.utils import timezone
import random
import string
from datetime import timedelta
from django.contrib.auth.models import AbstractUser


class TINETUser(AbstractUser):
    bio = models.CharField(max_length=300, default='This user doesnt have a bio yet.')
    calc_key = models.CharField(max_length=120, null=True)
    api_key = models.CharField(max_length=70, null=True)

    def delete(self, *args, **kwargs):
        AppAPIKey.objects.filter(user=self).delete()
        SessionToken.objects.filter(user=self).delete()
        AuditEntry.objects.filter(username=self.username).delete()
        super().delete(*args, **kwargs)


class SessionToken(models.Model):
    user = models.ForeignKey(TINETUser, on_delete=models.CASCADE, null=True)
    token = models.CharField(max_length=256, unique=True)
    expiry_date = models.DateTimeField()
    expired = models.BooleanField(default=False)

    @classmethod
    def create_token(cls, user):
        token = cls.generate_token()
        expiry_date = timezone.now() + timedelta(hours=12)
        session_token = cls(user=user, token=token, expiry_date=expiry_date)
        session_token.save()
        return session_token

    @staticmethod
    def generate_token():
        new_session_token = ''.join(
            random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
            for _ in range(256)
        )
        return new_session_token

    def is_valid(self):
        date_expired = self.expiry_date > timezone.now()
        if not date_expired or not self.expired:
            return True
        else:
            return False


class AppAPIKey(models.Model):
    user = models.ForeignKey(TINETUser, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=100)
    key = models.CharField(max_length=256, unique=True)
    expires = models.IntegerField(default=-1)
    last_used = models.DateTimeField(default=timezone.now)
    expired = models.BooleanField(default=False)

    @classmethod
    def create_api_key(cls, user, name, description):
        key = cls.generate_key()
        api_key = cls(user=user, name=name, description=description, key=key)
        api_key.save()
        return api_key

    @staticmethod
    def generate_key():
        new_api_key = ''.join(
            random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
            for _ in range(256)
        )
        return new_api_key

    def is_valid(self):
        if self.expires == -1 and not self.expired:
            return True
        elif not self.expired:
            return self.last_used > timezone.now() - timezone.timedelta(hours=self.expires)
        return False

    def mark_as_used(self):
        self.last_used = timezone.now()
        self.save()

    def update_expired_status(self):
        if not self.expired:
            self.expired = True
            self.save()


class AllowedApp(models.Model):
    allow_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(TINETUser, on_delete=models.CASCADE)
    app = models.ForeignKey(AppAPIKey, on_delete=models.CASCADE, null=True)
    granted_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'app')


class AllowedAppAuditEntry(models.Model):
    action = models.CharField(max_length=64)
    ip = models.GenericIPAddressField(null=True)
    username = models.CharField(max_length=256, null=True)
    allowed_app = models.ForeignKey(AllowedApp, on_delete=models.CASCADE, null=True)


class AuditEntry(models.Model):
    action = models.CharField(max_length=64)
    ip = models.GenericIPAddressField(null=True)
    username = models.CharField(max_length=256, null=True)

    def __unicode__(self):
        return '{0} - {1} - {2}'.format(self.action, self.username, self.ip)

    def __str__(self):
        return '{0} - {1} - {2}'.format(self.action, self.username, self.ip)


class WebPopUp(models.Model):
    title = models.TextField(null=True)
    description = models.TextField(null=True)
    users = models.ManyToManyField(TINETUser, through='UserWebPopUp', related_name='webpopups')


class UserWebPopUp(models.Model):
    user = models.ForeignKey(TINETUser, on_delete=models.CASCADE)
    popup = models.ForeignKey(WebPopUp, on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)
