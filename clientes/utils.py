from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from functools import wraps

def check_permissions(view_func):
    """
    Decorator to check if the user has permission to access a specific view.
    It builds on top of the login_required decorator to first ensure the user is authenticated.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if the user has the required permissions
        # You can customize this based on your specific permission requirements
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        else:
            # Redirect to a permission denied page or dashboard
            return redirect('dashboard')  # Update this to your appropriate URL name
    return wrapper
