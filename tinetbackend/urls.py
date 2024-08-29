from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path, re_path
from django.views.generic import RedirectView
# import os
# from allauth.socialaccount.providers.openid_connect.views import callback, login

urlpatterns = [
    path("", include("frontend.urls")),
    path("api/", include("API.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    # re_path(
    #     r"accounts/oidc/(?P<provider_id>[^/]+)/",
    #     include(
    #         [
    #             path(
    #                 "login/",
    #                 login,
    #                 name="openid_connect_login",
    #             ),
    #             path(
    #                 "login/callback/",
    #                 callback,
    #                 name="openid_connect_callback",
    #             ),
    #         ]
    #     )
    # ),
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("favicon.ico")),
    ),
]
