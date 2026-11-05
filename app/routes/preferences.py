from urllib.parse import urlparse
from flask import Blueprint, request, redirect, url_for, flash, session
from flask_login import login_required

preferences_bp = Blueprint('preferences', __name__, url_prefix='/preferences')

THEME_COOKIE = 'hms_theme'
VALID_THEMES = ('light', 'dark')


def _safe_back(default_endpoint='dashboard.index'):
    """Redirect target limited to this site (prevents open-redirects)."""
    ref = request.referrer
    if ref and urlparse(ref).netloc == request.host:
        return ref
    return url_for(default_endpoint)


@preferences_bp.route('/theme/<mode>', methods=['POST'])
@login_required
def set_theme(mode):
    """Store the UI theme in a cookie, then Post-Redirect-Get back to the page."""
    if mode not in VALID_THEMES:
        flash('Unknown theme selected.', 'warning')
        return redirect(_safe_back())
    resp = redirect(_safe_back())
    resp.set_cookie(THEME_COOKIE, mode, max_age=60 * 60 * 24 * 365,
                    httponly=True, samesite='Lax')
    flash(f'Theme switched to {mode} mode.', 'success')
    return resp


@preferences_bp.route('/recent/clear', methods=['POST'])
@login_required
def clear_recent():
    """Clear the session-stored 'recently visited' list."""
    session.pop('recent_pages', None)
    flash('Recently visited list cleared.', 'info')
    return redirect(_safe_back())
