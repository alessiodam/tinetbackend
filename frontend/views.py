import json
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, RedirectView, FormView
from waffle.mixins import WaffleSwitchMixin
from waffle.models import Flag

from API.storages import TINETUserFilesStorage
from leaderboards.models import Leaderboard
from users.models import AuditEntry, AppAPIKey, UserWebPopUp, WebPopUp, AllowedApp
import waffle
import re


class FlagCheckMixin:
    flag_name = None

    def dispatch(self, request, *args, **kwargs):
        if self.flag_name is not None and not waffle.flag_is_active(request, self.flag_name):
            return JsonResponse({'success': False, 'error': f'Feature is not enabled ({self.flag_name})'}, status=406)
        return super().dispatch(request, *args, **kwargs)


class RootView(TemplateView):
    template_name = 'index.html'


class PrivacyPolicyView(TemplateView):
    template_name = 'legal/privacy.html'


class ToSView(TemplateView):
    template_name = 'legal/terms-of-service.html'


class NetChatView(TemplateView):
    template_name = 'netchat.html'


class ShowPopupView(LoginRequiredMixin, View):
    template_name = 'popup.html'

    def get(self, request):
        user = request.user
        user_popup = UserWebPopUp.objects.filter(user=user, confirmed=False).first()
        if user_popup:
            return render(request, self.template_name, {'popup': user_popup})
        else:
            return redirect('index')

    @staticmethod
    def post(request):
        user = request.user
        if not UserWebPopUp.objects.filter(user=user, confirmed=True).exists():
            popup = UserWebPopUp.objects.get_or_create(user=user)[0]
            popup.confirmed = True
            popup.save()
        return redirect('index')


class DashboardView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    template_name = 'account/dashboard.html'
    success_url = reverse_lazy('dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_events = reversed(AuditEntry.objects.filter(username=user.username))
        context['user'] = user
        context['user_events'] = user_events
        return context


class LogoutView(RedirectView):
    url = '/'

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


class RegisterView(View):
    @staticmethod
    def get(request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'account/register.html')


class LoginView(View):
    @staticmethod
    def get(request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'account/login.html')


class ChangePasswordView(LoginRequiredMixin, FormView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    template_name = 'account/change_password.html'
    success_url = reverse_lazy('change_password')
    form_class = PasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, self.request.user)
        messages.success(self.request, 'Your password has been successfully updated.')
        return super().form_valid(form)


class DeleteAccountView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    template_name = 'account/delete_confirmation.html'
    success_url = reverse_lazy('index')

    def post(self, request):
        user = request.user
        user.delete()
        logout(request)
        return redirect(self.success_url)

    def get(self, request):
        return render(request, self.template_name)


class ChatView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    template_name = 'chat.html'
    success_url = reverse_lazy('chat')

    def get(self, request):
        return render(request, self.template_name)


class AppAPIKeysView(LoginRequiredMixin, FlagCheckMixin, TemplateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    template_name = 'account/app_api_keys.html'
    success_url = reverse_lazy('app_api_keys')
    flag_name = 'app_api_keys'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        app_api_keys = reversed(AppAPIKey.objects.filter(user=user))
        context['api_keys'] = app_api_keys
        return context

    @staticmethod
    def delete(request):
        if request.method == 'DELETE' and 'key' in request.GET:
            key = request.GET.get('key')
            try:
                api_key = AppAPIKey.objects.get(key=key, user=request.user)
                api_key.delete()
                return JsonResponse({'success': True})
            except AppAPIKey.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'API key not found'})
        return JsonResponse({'success': False, 'error': 'Invalid request'})

    @staticmethod
    def post(request):
        if request.method == 'POST':
            name = request.POST.get('name')
            description = request.POST.get('description')
            name = re.sub(r'[^A-Za-z0-9]', '', name)
            description = re.sub(r'[^A-Za-z0-9 .:;/]', '', description)
            if name and description:
                api_key = AppAPIKey.create_api_key(user=request.user, name=name, description=description)
                return redirect('app_api_keys')
        return redirect('app_api_keys')


class LeaderboardsView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    success_url = reverse_lazy('leaderboards')

    @staticmethod
    def get(request, leaderboard_id=None):
        context = {}
        if leaderboard_id:
            leaderboard = get_object_or_404(Leaderboard, id=leaderboard_id)
            leaderboard_entries = leaderboard.leaderboardentry_set.all().order_by('-score')
            context['leaderboard'] = {
                'id': leaderboard_id,
                'title': leaderboard.title,
                'description': leaderboard.description,
                'entries': leaderboard_entries
            }
            return render(request, 'leaderboard_detail.html', context=context)
        else:
            leaderboards_data = Leaderboard.objects.all()
            leaderboards = []
            for leaderboard in leaderboards_data:
                leaderboard_entries = leaderboard.leaderboardentry_set.all().order_by('-score')
                leaderboards.append({
                    'id': leaderboard.id,
                    'title': leaderboard.title,
                    'description': leaderboard.description,
                    'entries': leaderboard_entries
                })
            context['leaderboards'] = leaderboards
            return render(request, 'leaderboards.html', context=context)


class FilesView(LoginRequiredMixin, FlagCheckMixin, TemplateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    template_name = 'account/files.html'
    success_url = reverse_lazy('files')
    flag_name = "files"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        s3 = TINETUserFilesStorage()
        s3.bucket_name = "tinetuserfiles"

        file_directory_within_bucket = str(self.request.user)

        directory_size = sum(obj.size for obj in s3.bucket.objects.filter(Prefix=file_directory_within_bucket) if
                             not obj.key.endswith('/'))

        current_bucket_size_mb = round(directory_size / (1024 ** 2), 2)

        context['current_bucket_size'] = current_bucket_size_mb
        return context


class AllowedAppsView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    template_name = 'account/allowed_apps.html'
    success_url = reverse_lazy('allowed_apps')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        allowed_apps = reversed(AllowedApp.objects.filter(user=self.request.user))
        context['allowed_apps'] = allowed_apps
        return context

    @staticmethod
    def delete(request):
        if request.method == 'DELETE' and 'appid' in request.GET:
            app_id = request.GET.get('appid')
            try:
                app_api_key = AppAPIKey.objects.get(id=app_id)
                allowed_app = AllowedApp.objects.get(app=app_api_key, user=request.user)
                allowed_app.delete()
                return JsonResponse({'success': True})
            except (AppAPIKey.DoesNotExist, AllowedApp.DoesNotExist):
                return JsonResponse({'success': False, 'error': 'Allowed App not found'})
        return JsonResponse({'success': False, 'error': 'Invalid request'})


class OAuthRequestView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    template_name = 'account/app_request_access.html'
    success_url = reverse_lazy('allowed_apps')

    def get(self, request):
        app_id = request.GET.get('appid')
        try:
            app_api_key = AppAPIKey.objects.get(id=app_id)
            if AllowedApp.objects.filter(user=request.user, app=app_api_key).exists():
                return redirect('allowed_apps')
            context = {
                'app_id': app_id,
                'app_name': app_api_key.name,
                'app_description': app_api_key.description
            }
        except AppAPIKey.DoesNotExist:
            context = {
                'app_name': 'Unknown',
                'app_description': 'No description available'
            }
        return render(request, self.template_name, context)

    @staticmethod
    def post(request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            password = data.get('password')
            app_id = request.GET.get('appid')
            if password:
                user = authenticate(request, username=request.user.username, password=password)
                if user is not None:
                    try:
                        app_api_key = AppAPIKey.objects.get(id=app_id)
                        if AllowedApp.objects.filter(user=request.user, app=app_api_key).exists():
                            return redirect('allowed_apps')
                    except AppAPIKey.DoesNotExist:
                        return JsonResponse({
                            'success': False,
                            'message': 'Invalid app id'
                        }, status=400)

                    allowed_app = AllowedApp.objects.create(user=request.user, app=app_api_key)
                    allowed_app.save()

                    return JsonResponse({
                        'success': True,
                        'message': 'Access granted!',
                        'appid': app_id
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Access denied'
                    }, status=403)
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Password is required in JSON payload'
                }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON payload'
            }, status=400)


class ChooseExperimentView(WaffleSwitchMixin, LoginRequiredMixin, View):
    waffle_switch = "experiments_switch"
    template_name = 'experiments.html'
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    success_url = reverse_lazy('experiments')

    def get(self, request):
        flags = Flag.objects.all()
        enabled_flags = Flag.objects.filter(users=request.user)
        enabled_flag_names = [flag.name for flag in enabled_flags]
        return render(request, self.template_name, {'flags': flags, 'enabled_flags': enabled_flag_names})

    @staticmethod
    def post(request):
        if request.method == 'POST':
            user = request.user
            data = json.loads(request.body)
            for flag_name, flag_value in data.items():
                flag = Flag.objects.get(name=flag_name)
                if flag_value == 'Enabled':
                    flag.users.add(user)
                else:
                    flag.users.remove(user)
            return JsonResponse({'message': 'Flags updated successfully'}, status=200)
        return redirect('experiments')


class LinkAccountView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    template_name = 'account/link_account.html'
    success_url = reverse_lazy('dashboard')

    def get(self, request):
        social_accounts = request.user.socialaccount_set.all()
        if social_accounts:
            return redirect(self.success_url)
        return render(request, self.template_name)

    def post(self, request):
        social_accounts = request.user.socialaccount_set.all()
        if social_accounts:
            return redirect(self.success_url)

        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            if get_user_model().objects.filter(username=username).exists():
                return render(request, 'account/link_account.html', {'error': 'Username already exists'})
            if get_user_model().objects.filter(email=email).exists():
                return render(request, 'account/link_account.html', {'error': 'Email already exists'})
