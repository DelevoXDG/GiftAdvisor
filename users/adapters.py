from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import redirect

class NoNewUsersAccountAdapter(DefaultAccountAdapter):
    """Adapter to disable regular sign up and force social auth."""
    
    def is_open_for_signup(self, request):
        """No regular sign up, only social."""
        return False
    
    def get_login_redirect_url(self, request):
        """Redirect to home after login."""
        return '/'
        
    def get_signup_redirect_url(self, request):
        """Redirect to home after signup."""
        return '/' 
