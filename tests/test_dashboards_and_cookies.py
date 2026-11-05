import pytest


@pytest.mark.parametrize('fixture_name', [
    'admin_client', 'doctor_client', 'nurse_client',
    'receptionist_client', 'pharmacist_client', 'labtech_client',
])
def test_every_role_dashboard_renders(fixture_name, request):
    """Regression: each role's dashboard must load without a 500."""
    client = request.getfixturevalue(fixture_name)
    resp = client.get('/dashboard/')
    assert resp.status_code == 200


def test_lab_dashboard_uses_verified_at(labtech_client):
    resp = labtech_client.get('/dashboard/')
    assert resp.status_code == 200
    assert b'result_date' not in resp.data
    # the abnormal-results table must actually render a seeded row
    assert b'Lipid Profile Screen' in resp.data
    assert b'/laboratory/orders/' in resp.data


def test_theme_cookie_is_set_and_applied(admin_client):
    resp = admin_client.post('/preferences/theme/dark')
    assert resp.status_code == 302  # Post-Redirect-Get
    assert 'hms_theme=dark' in resp.headers.get('Set-Cookie', '')
    page = admin_client.get('/dashboard/')
    assert b'data-bs-theme="dark"' in page.data


def test_invalid_theme_rejected(admin_client):
    admin_client.post('/preferences/theme/neon')
    assert b'data-bs-theme="neon"' not in admin_client.get('/dashboard/').data


def test_recent_pages_stored_in_session(admin_client):
    admin_client.get('/patients/')
    admin_client.get('/doctors/')
    with admin_client.session_transaction() as sess:
        assert len(sess['recent_pages']) >= 2
        assert sess['page_views'] >= 2
    admin_client.post('/preferences/recent/clear')
    with admin_client.session_transaction() as sess:
        assert 'recent_pages' not in sess


def test_preferences_require_login(client):
    assert client.post('/preferences/theme/dark').status_code in (302, 401)
