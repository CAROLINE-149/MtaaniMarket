# decorators.py (in your app folder)
from django.shortcuts import redirect

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')  # Redirect to login if not logged in

            if hasattr(request.user, 'profile'):
                user_role = request.user.profile.role
                if user_role in allowed_roles:
                    return view_func(request, *args, **kwargs)
            
            # Redirect to home if role not allowed
            return redirect('register')
        return wrapper
    return decorator
