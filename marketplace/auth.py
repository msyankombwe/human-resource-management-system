import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class SupabaseAuthError(Exception):
    pass


def is_supabase_auth_configured():
    return bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY)


def supabase_auth_request(endpoint, payload):
    if not is_supabase_auth_configured():
        raise SupabaseAuthError('Supabase Auth is not configured.')
    request = Request(
        f'{settings.SUPABASE_URL}/auth/v1/{endpoint}',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'apikey': settings.SUPABASE_ANON_KEY,
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        try:
            error = json.loads(exc.read().decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            error = {}
        message = error.get('msg') or error.get('message') or error.get('error_description')
        raise SupabaseAuthError(message or 'Supabase could not complete the authentication request.') from exc
    except (URLError, TimeoutError) as exc:
        raise SupabaseAuthError('Could not reach Supabase Auth. Please try again.') from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SupabaseAuthError('Supabase returned an invalid authentication response.') from exc
