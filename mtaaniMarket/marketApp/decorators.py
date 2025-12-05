# marketApp/decorators.py
from django.shortcuts import redirect
from functools import wraps
from django.contrib import messages

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please login to access this page.')
                return redirect('login')
            
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'Your account profile is incomplete. Please update your profile.')
                return redirect('profile')
            
            user_role = request.user.profile.role
            
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, f'Access denied. This page is only for {", ".join(allowed_roles)}.')
            
            if user_role == 'buyer':
                return redirect('buyer_home')
            elif user_role == 'seller':
                return redirect('seller_home')
            elif user_role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('home')
        
        return wrapper
    return decorator


def buyer_required(view_func):
    """
    Shortcut decorator for buyer-only views
    Usage: @buyer_required
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Your account profile is incomplete.')
            return redirect('profile')
        
        if request.user.profile.role != 'buyer':
            messages.error(request, 'This page is only accessible to buyers.')
            return redirect('seller_home' if request.user.profile.role == 'seller' else 'home')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def seller_required(view_func):
    """
    Shortcut decorator for seller-only views
    Usage: @seller_required
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Your account profile is incomplete.')
            return redirect('profile')
        
        if request.user.profile.role != 'seller':
            messages.error(request, 'This page is only accessible to sellers.')
            return redirect('buyer_home' if request.user.profile.role == 'buyer' else 'home')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def admin_required(view_func):
    """
    Shortcut decorator for admin-only views
    Usage: @admin_required
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Your account profile is incomplete.')
            return redirect('profile')
        
        if request.user.profile.role != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            if request.user.profile.role == 'buyer':
                return redirect('buyer_home')
            elif request.user.profile.role == 'seller':
                return redirect('seller_home')
            else:
                return redirect('home')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper