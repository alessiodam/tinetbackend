from django.conf import settings


def tinet_version(request):
    return {'TINET_VERSION': settings.TINET_VERSION}
