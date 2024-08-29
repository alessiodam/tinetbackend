from django.urls import reverse
from django.shortcuts import redirect
from users.models import UserWebPopUp, WebPopUp


class PopupMiddleware:
    EXCLUDED_ROUTES = {'privacy_policy', 'terms_of_service'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if self.should_show_popup(request) and not self.is_excluded_route(request):
            popup_url = reverse('popup')
            if request.path != popup_url:
                return redirect(popup_url)
        return response

    @staticmethod
    def should_show_popup(request):
        user = request.user
        if user.is_authenticated:
            user_popups = UserWebPopUp.objects.filter(user=user)
            popup_exists = user_popups.filter(confirmed=True).exists()
            if not popup_exists:
                unconfirmed_popup = user_popups.filter(confirmed=False).exists()
                if unconfirmed_popup:
                    return True
                else:
                    web_popup = WebPopUp.objects.first()
                    if web_popup:
                        UserWebPopUp.objects.create(user=user, popup=web_popup)
                        return True
        return False

    def is_excluded_route(self, request):
        current_route_name = request.resolver_match.url_name
        if current_route_name in self.EXCLUDED_ROUTES:
            return True
        return False


class ForceLinkAccountToTKBStudiosAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        link_account_url = reverse('link_account')
        if self.should_show_popup(request, link_account_url):
            return redirect(link_account_url)
        return response

    @staticmethod
    def should_show_popup(request, link_account_url):
        if request.user.is_authenticated:
            if request.path != link_account_url:
                if not request.path.startswith('/accounts'):
                    if not request.path.startswith('/admin'):
                        social_accounts = request.user.socialaccount_set.all()
                        if not social_accounts:
                            return True
        return False
