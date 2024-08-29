from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path("v1", views.RootView.as_view(), name="api_root"),
    path("v1/user/info", csrf_exempt(views.UserInfoView.as_view()), name="api_user_info"),
    path("v1/user/edit/bio", csrf_exempt(views.EditBioView.as_view()), name="api_user_edit_bio"),
    path("v1/user/keyfile/download", views.DownloadKeyFileView.as_view(), name="api_user_keyfile_download"),
    path("v1/user/apikey/new", views.NewApiKeyView.as_view(), name="api_user_apikey_new"),
    path("v1/user/sessions/expireallweb", views.ExpireUserWebSessionsView.as_view(), name="api_user_sessions_expireall"),
    path("v1/user/calc/auth", csrf_exempt(views.CalcAuthView.as_view()), name="api_user_calc_auth"),
    path("v1/user/sessions/auth", csrf_exempt(views.SessionAuthView.as_view()), name="api_user_sessions_auth"),
    path("v1/user/sessions/validity-check", csrf_exempt(views.CalcSessionsValidityCheck.as_view()), name="api_user_sessions_validity_check"),
    path("v1/user/sessions/expireallcalc", views.ExpireAllCalcSessionTokensView.as_view(), name="api_user_sessions_expire_all"),
    path("v1/user/files/upload", csrf_exempt(views.FileUploadView.as_view()), name="api_user_files_upload"),
    path("v1/user/files/list", csrf_exempt(views.FileListView.as_view()), name="api_user_files_list"),
    path("v1/user/files/delete", csrf_exempt(views.FileDeleteView.as_view()), name="api_user_files_delete"),
    path("v1/user/files/download", csrf_exempt(views.FileDownloadView.as_view()), name="api_user_files_download"),
    path("v1/leaderboards/increment", csrf_exempt(views.LeaderboardIncrementScoreView.as_view()), name="api_leaderboards_increment"),
    path("v1/leaderboards/decrement", csrf_exempt(views.LeaderboardDecrementScoreView.as_view()), name="api_leaderboards_decrement"),
    path("v1/leaderboards/set", csrf_exempt(views.LeaderboardSetScoreView.as_view()), name="api_leaderboards_set"),
    path("v1/leaderboards/delete", csrf_exempt(views.LeaderboardDeleteScoreView.as_view()), name="api_leaderboards_delete"),
    # TODO: add API routes to create/delete leaderboards
]
