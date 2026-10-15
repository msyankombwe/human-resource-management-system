def user_role(request):
    role = None
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile:
            role = profile.role
    return {'user_role': role}
