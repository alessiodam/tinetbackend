from django.urls import path
from . import views

urlpatterns = [
    path('', views.RootView.as_view(), name='index'),
    path('privacy-policy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('terms-of-service/', views.ToSView.as_view(), name='terms_of_service'),
    path('popup/', views.ShowPopupView.as_view(), name='popup'),
    path('netchat/', views.NetChatView.as_view(), name='netchat'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('delete-account/', views.DeleteAccountView.as_view(), name='delete_account'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('chat/', views.ChatView.as_view(), name="chat"),
    path('dashboard/app-api-keys', views.AppAPIKeysView.as_view(), name="app_api_keys"),
    path('dashboard/allowed-apps', views.AllowedAppsView.as_view(), name="allowed_apps"),
    path('oauth/request', views.OAuthRequestView.as_view(), name="oauth_request"),
    path('dashboard/files', views.FilesView.as_view(), name="files"),
    path('leaderboards/', views.LeaderboardsView.as_view(), name='leaderboards'),
    path('leaderboard/<int:leaderboard_id>/', views.LeaderboardsView.as_view(), name='leaderboard_detail'),
    path('experiments/', views.ChooseExperimentView.as_view(), name='experiments'),
    path('account/link-account/', views.LinkAccountView.as_view(), name='link_account'),
]
