def trial_context(request):
    if not request.user.is_authenticated:
        trial_limit = 10
        trial_count = request.session.get('trial_count', 0)
        return {
            'trial_limit': trial_limit,
            'trial_count': trial_count,
            'trial_remaining': max(0, trial_limit - trial_count)
        }
    return {}
