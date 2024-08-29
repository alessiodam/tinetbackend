import json
import os
import random
import string
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views import View
from django.utils.decorators import method_decorator
from functools import wraps
import time
import io
from django.views.decorators.csrf import csrf_exempt
from tivars.types import TIAppVar
from tivars.var import TIHeader
from tivars.models import TI_84PCE

from API.storages import TINETUserFilesStorage
from leaderboards.models import LeaderboardEntry, Leaderboard
from users.models import SessionToken, AuditEntry, AppAPIKey, AllowedApp, AllowedAppAuditEntry, TINETUser

User = get_user_model()


def new_ti_app_var_stream(username, key):
    kf_stream = io.BytesIO()
    keyfile_appvar = TIAppVar()
    bytes_data = username + b"\0" + key + b"\0"
    keyfile_appvar.name = "NETKEY"
    keyfile_appvar.data = bytes_data
    keyfile_appvar.archived = True
    kf_stream.seek(0)
    kf_stream.name = "NETKEY"
    kf_stream.write(
        keyfile_appvar.export(
            header=TIHeader(model=TI_84PCE, comment="log into TINET"),
            name="TINET",
            model=TI_84PCE
        ).bytes()
    )
    kf_stream.seek(0)
    return kf_stream


def generate_api_key():
    apikey = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(70))
    return apikey


def generate_calc_key():
    token = ''.join(random.choice(
        string.ascii_lowercase +
        string.ascii_uppercase +
        string.digits
    ) for _ in range(50))
    return token


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def api_auth_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        api_key = request.headers.get('Api-Key')
        if api_key:
            try:
                user = User.objects.get(api_key=api_key)
                request.user = user
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid API key'}, status=401)
        elif request.user.is_authenticated:
            user = request.user
        else:
            return JsonResponse({
                'success': False,
                'message': 'Authentication credentials were not provided.'
            }, status=401)
        if request.user != user:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        if not request.user.is_authenticated:
            return csrf_exempt(view_func)(request, *args, **kwargs)

        request.user = user
        return view_func(request, *args, **kwargs)

    return wrapped_view


def log_audit_entry(request, user, message):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    AuditEntry.objects.create(action=message, ip=ip, username=user.username)


def log_app_audit_entry(request, user, message, app):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    AllowedAppAuditEntry.objects.create(action=message, ip=ip, username=user.username, allowed_app=app)


class RootView(View):
    @method_decorator(api_auth_required)
    def get(self, request):
        response = JsonResponse(
            {
                "name": f"TINET API",
                "identifier": "V1",
                "version": {
                    "major": 1,
                    "minor": 0,
                    "revision": 0,
                },
                "server_time": int(round(time.time(), 0)),
                "your_ip": get_client_ip(request)
            }
        )
        response.status_code = 200
        return response


class UserInfoView(View):
    @method_decorator(api_auth_required)
    def get(self, request):
        user = request.user
        user_info_to_return = {
            'username': user.username,
            'email': user.email
        }
        response = JsonResponse(user_info_to_return)
        response.status_code = 200
        return response


class ExpireUserWebSessionsView(View):
    @staticmethod
    def post(request):
        user = request.user

        if user.is_authenticated:
            sessions = Session.objects.filter(expire_date__gte=timezone.now(), session_key=request.session.session_key)

            for session in sessions:
                session.expire_date = timezone.now()
                session.save()

            return JsonResponse({'message': 'All sessions for the current user expired successfully'}, status=200)
        else:
            return JsonResponse({'error': 'User is not authenticated'}, status=401)


class DownloadKeyFileView(View):
    @staticmethod
    def get(request):
        user = request.user
        if user.is_authenticated:
            new_token = generate_calc_key()
            user.calc_key = new_token
            user.save()
            kf_stream = new_ti_app_var_stream(user.username.encode(), new_token.encode())
            response = HttpResponse(kf_stream, content_type='application/octet-stream')
            response['Content-Disposition'] = 'attachment; filename="NetKey.8xv"'
            return response
        else:
            return JsonResponse({'error': 'User not authenticated'}, status=401)


class NewApiKeyView(View):
    @staticmethod
    def get(request):
        user = request.user
        if user.is_authenticated:
            new_apikey = generate_api_key()
            user.api_key = new_apikey
            user.save()
            response_data = {
                'api_key': new_apikey
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'error': 'User not authenticated'}, status=401)


class CalcAuthView(View):
    @staticmethod
    def post(request):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            calc_key = data.get('calc_key')
            user = User.objects.get(username=username, calc_key=calc_key)
            if user is not None:
                session_token = SessionToken.create_token(user)
                request.session['session_token'] = session_token.token
                log_audit_entry(request, user, "requested a new session token")
                return JsonResponse({
                    'auth_success': True,
                    'username': user.username,
                    'session_token': session_token.token
                }, status=200)
            else:
                return JsonResponse({
                    'auth_success': False,
                    'error': 'User not found or invalid credentials'
                }, status=404)
        except Exception:
            return JsonResponse({
                'auth_success': False,
                'error': 'Unexpected Error, are you sure all fields are correct?'
            }, status=500)


class SessionAuthView(View):
    @staticmethod
    def post(request):
        try:
            data = json.loads(request.body)
            app_api_key = request.headers.get('Api-Key')
            app_api_key_obj = AppAPIKey.objects.get(key=app_api_key)
            if app_api_key_obj.is_valid():
                app_api_key_obj.mark_as_used()

            session_token = data.get('session_token')
            session_token_obj = SessionToken.objects.get(token=session_token)
            if session_token_obj.is_valid():
                allowed_app = AllowedApp.objects.filter(user=session_token_obj.user, app=app_api_key_obj).first()
                if allowed_app:
                    log_app_audit_entry(request, request.user, "Authenticated using session token", app_api_key_obj)
                    user = session_token_obj.user
                    return_json = {
                        'username': user.username,
                        'email': user.email,
                        'bio': user.bio,
                        'date_joined': user.date_joined,
                        'last_login': user.last_login
                    }
                    return JsonResponse(return_json, status=200)
                else:
                    return JsonResponse({
                        'auth_success': False,
                        'error': 'User has not granted access to the app',
                        'grant_url': f'https://tinet.tkbstudios.com/oauth/request?appid={app_api_key_obj.id}'
                    }, status=403)
            else:
                return JsonResponse({
                    'auth_success': False,
                    'error': 'Session token expired'
                }, status=401)
        except SessionToken.DoesNotExist:
            return JsonResponse({
                'auth_success': False,
                'error': 'Invalid session token'
            }, status=404)
        except AppAPIKey.DoesNotExist:
            return JsonResponse({
                'auth_success': False,
                'error': 'Invalid App API Key'
            }, status=401)
        except Exception:
            return JsonResponse({
                'auth_success': False,
                'error': 'Unexpected Error, are you sure all fields are correct?'
            }, status=500)


class CalcSessionsValidityCheck(View):
    @staticmethod
    def post(request):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            session_token = data.get('session_token')
            user = User.objects.get(username=username)
            session_token_obj = SessionToken.objects.get(user=user, token=session_token)
            if session_token_obj.is_valid():
                return_json = {
                    "success": True,
                    "valid": True
                }
                return JsonResponse(return_json, status=200)
            else:
                return JsonResponse({
                    'auth_success': False,
                    'error': 'Session token expired'
                }, status=401)
        except SessionToken.DoesNotExist:
            return JsonResponse({
                'auth_success': False,
                'error': 'Invalid session token'
            }, status=404)
        except Exception as e:
            print(e)
            return JsonResponse({
                'auth_success': False,
                'error': 'Unexpected Error, are you sure all fields are correct?'
            }, status=500)


class ExpireAllCalcSessionTokensView(View):
    @staticmethod
    def post(request):
        if not request.user.is_authenticated:
            return JsonResponse({
                "success": False,
                "error": "not authenticated"
            }, status=401)
        try:
            SessionToken.objects.filter(user=request.user).update(expired=True)
            return JsonResponse({
                'success': True,
                'message': f"All tokens associated with user {request.user} have been expired."
            }, status=200)
        except Exception:
            return JsonResponse({
                'success': False,
                'error': 'Unexpected Error'
            }, status=500)


class EditBioView(View):
    @method_decorator(api_auth_required)
    def post(self, request):
        user = self.request.user
        bio = request.POST.get('bio')
        if bio is None:
            try:
                json_data = json.loads(request.body.decode('utf-8'))
                bio = json_data.get('bio')
            except json.JSONDecodeError:
                pass

        if bio:
            user.bio = bio
            user.save()
            return JsonResponse({
                "success": True,
                "new_bio": user.bio
            })
        else:
            return JsonResponse({'error': 'Bio field not found in the request'}, status=400)


class FileUploadView(View):
    @method_decorator(api_auth_required)
    def post(self, request):
        files = request.FILES.getlist('files')

        if not files:
            return JsonResponse({'message': 'Error: No files provided'}, status=400)

        storage = TINETUserFilesStorage()

        response_data = []

        for file_obj in files:
            file_size = file_obj.size

            file_directory_within_bucket = str(request.user)
            file_path_within_bucket = os.path.join(file_directory_within_bucket, file_obj.name)

            directory_size = sum(
                obj.size for obj in storage.bucket.objects.filter(
                    Prefix=file_directory_within_bucket
                ) if not obj.key.endswith('/')
            )

            total_size = directory_size + file_size

            if total_size > 32 * 1024 * 1024:
                response_data.append({
                    "success": False,
                    "message": f"Error: Upload of {file_obj.name} will exceed the 32MB bucket limit"
                })
            elif storage.exists(file_path_within_bucket):
                response_data.append({
                    "success": False,
                    "message": f"Error: File {file_obj.name} already exists"
                })
            else:
                storage.save(file_path_within_bucket, file_obj)
                response_data.append({
                    "success": True,
                    "message": f"File {file_obj.name} was successfully uploaded",
                    "filename": file_obj.name
                })

        return JsonResponse({"files": response_data})


class FileListView(View):
    @method_decorator(api_auth_required)
    def get(self, request):
        file_directory_within_bucket = str(request.user)

        storage = TINETUserFilesStorage()

        files_list = []
        for obj in storage.bucket.objects.filter(Prefix=file_directory_within_bucket):
            if not obj.key.endswith('/'):
                files_list.append(obj.key[len(file_directory_within_bucket) + 1:])

        return JsonResponse({
            "success": True,
            "files": files_list
        })


class FileDeleteView(View):
    @method_decorator(api_auth_required)
    def delete(self, request):
        try:
            data = json.loads(request.body)
            filenames_to_delete = data.get('filenames', [])
        except json.JSONDecodeError:
            return JsonResponse({
                "success": False,
                "message": "Error: Invalid JSON format in request body"
            }, status=400)

        if not filenames_to_delete:
            return JsonResponse({
                "success": False,
                "message": "Error: No filenames provided"
            }, status=400)

        file_directory_within_bucket = str(request.user)
        storage = TINETUserFilesStorage()

        deleted_files = []
        not_found_files = []

        for filename_to_delete in filenames_to_delete:
            file_path_within_bucket = os.path.join(file_directory_within_bucket, filename_to_delete)

            if storage.exists(file_path_within_bucket):
                storage.delete(file_path_within_bucket)
                deleted_files.append(filename_to_delete)
            else:
                not_found_files.append(filename_to_delete)

        response_data = {
            "success": True,
            "deleted_files": deleted_files,
            "not_found_files": not_found_files
        }

        return JsonResponse(response_data)


class FileDownloadView(View):
    @method_decorator(api_auth_required)
    def get(self, request):
        try:
            filename_to_download = request.GET.get('filename')
        except json.JSONDecodeError:
            return JsonResponse({
                "success": False,
                "message": "Error: Invalid JSON format in request body"
            }, status=400)

        if not filename_to_download:
            return JsonResponse({
                "success": False,
                "message": "Error: No filename provided"
            }, status=400)

        file_directory_within_bucket = str(request.user)
        storage = TINETUserFilesStorage()

        file_path_within_bucket = os.path.join(file_directory_within_bucket, filename_to_download)

        if storage.exists(file_path_within_bucket):
            file_content = storage.open(file_path_within_bucket).read()

            response = HttpResponse(file_content, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{filename_to_download}"'

            return response
        else:
            return JsonResponse({
                "success": False,
                "message": f"Error: File '{filename_to_download}' does not exist.",
            }, status=404)


class LeaderboardIncrementScoreView(View):
    @staticmethod
    def post(request):
        try:
            data = json.loads(request.body)
            app_api_key = request.headers.get('Api-Key')
            app_api_key_obj = AppAPIKey.objects.get(key=app_api_key)
            if app_api_key_obj.is_valid():
                app_api_key_obj.mark_as_used()

            leaderboard_id = data['leaderboard_id']
            leaderboard_obj = Leaderboard.objects.get(id=leaderboard_id)

            if leaderboard_obj.app != app_api_key_obj:
                return JsonResponse({
                    'success': False,
                    'error': 'Leaderboard does not match the App API Key'
                }, status=403)

            username = data['username']
            user_obj = TINETUser.objects.get(username=username)
            count = data['count']

            entry, created = LeaderboardEntry.objects.get_or_create(
                user=user_obj,
                leaderboard=leaderboard_obj,
                defaults={
                    'score': count
                }
            )

            if not created:
                entry.score += count
                entry.save()

            return JsonResponse({
                'success': True,
                'message': 'Leaderboard entry updated successfully' if not created else 'Leaderboard entry created successfully',
                'score': entry.score
            }, status=200)

        except AppAPIKey.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid App API Key'
            }, status=401)
        except Exception as e:
            return JsonResponse({
                'success': False
            }, status=500)


class LeaderboardDecrementScoreView(View):
    @staticmethod
    def post(request):
        try:
            data = json.loads(request.body)
            app_api_key = request.headers.get('Api-Key')
            app_api_key_obj = AppAPIKey.objects.get(key=app_api_key)
            if app_api_key_obj.is_valid():
                app_api_key_obj.mark_as_used()

            leaderboard_id = data['leaderboard_id']
            leaderboard_obj = Leaderboard.objects.get(id=leaderboard_id)

            if leaderboard_obj.app != app_api_key_obj:
                return JsonResponse({
                    'success': False,
                    'error': 'Leaderboard does not match the App API Key'
                }, status=403)

            username = data['username']
            user_obj = TINETUser.objects.get(username=username)
            count = data['count']

            entry, created = LeaderboardEntry.objects.get_or_create(
                user=user_obj,
                leaderboard=leaderboard_obj,
                defaults={
                    'score': count
                }
            )

            if not created:
                entry.score -= count
                entry.save()

            return JsonResponse({
                'success': True,
                'message': 'Leaderboard entry updated successfully' if not created else 'Leaderboard entry created successfully',
                'score': entry.score
            }, status=200)

        except AppAPIKey.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid App API Key'
            }, status=401)
        except Exception as e:
            return JsonResponse({
                'success': False
            }, status=500)


class LeaderboardSetScoreView(View):
    @staticmethod
    def post(request):
        try:
            data = json.loads(request.body)
            app_api_key = request.headers.get('Api-Key')
            app_api_key_obj = AppAPIKey.objects.get(key=app_api_key)
            if app_api_key_obj.is_valid():
                app_api_key_obj.mark_as_used()

            leaderboard_id = data['leaderboard_id']
            leaderboard_obj = Leaderboard.objects.get(id=leaderboard_id)

            if leaderboard_obj.app != app_api_key_obj:
                return JsonResponse({
                    'success': False,
                    'error': 'Leaderboard does not match the App API Key'
                }, status=403)

            username = data['username']
            user_obj = TINETUser.objects.get(username=username)
            count = data['count']

            entry, created = LeaderboardEntry.objects.get_or_create(
                user=user_obj,
                leaderboard=leaderboard_obj,
                defaults={
                    'score': count
                }
            )

            if not created:
                entry.score -= count
                entry.save()

            return JsonResponse({
                'success': True,
                'message': 'Leaderboard entry updated successfully' if not created else 'Leaderboard entry created successfully',
                'score': entry.score
            }, status=200)

        except AppAPIKey.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid App API Key'
            }, status=401)
        except Exception as e:
            return JsonResponse({
                'success': False
            }, status=500)


class LeaderboardDeleteScoreView(View):
    @staticmethod
    def delete(request):
        try:
            data = json.loads(request.body)
            app_api_key = request.headers.get('Api-Key')
            app_api_key_obj = AppAPIKey.objects.get(key=app_api_key)
            if app_api_key_obj.is_valid():
                app_api_key_obj.mark_as_used()

            leaderboard_id = data['leaderboard_id']
            leaderboard_obj = Leaderboard.objects.get(id=leaderboard_id)

            if leaderboard_obj.app != app_api_key_obj:
                return JsonResponse({
                    'success': False,
                    'error': 'Leaderboard does not match the App API Key'
                }, status=403)

            username = data['username']
            user_obj = TINETUser.objects.get(username=username)

            try:
                entry = LeaderboardEntry.objects.get(user=user_obj, leaderboard=leaderboard_obj)
                entry.delete()
                return JsonResponse({
                    'success': True,
                    'message': 'Leaderboard entry deleted successfully'
                }, status=200)
            except LeaderboardEntry.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Leaderboard entry does not exist for the given username'
                }, status=404)

        except AppAPIKey.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid App API Key'
            }, status=401)
        except Exception:
            return JsonResponse({
                'success': False
            }, status=500)
