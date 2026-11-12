def user_role(request):
    role = None
    role_display = None
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile:
            role = profile.role
            role_display = profile.get_role_display()
    return {'user_role': role, 'user_role_display': role_display}
