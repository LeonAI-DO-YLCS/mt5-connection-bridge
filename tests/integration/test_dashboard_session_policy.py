from __future__ import annotations

import time


def test_dashboard_shell_is_public_and_prompts_for_auth(client):
    response = client.get("/dashboard/")
    assert response.status_code == 200
    assert "Authenticate" in response.text


def test_dashboard_access_with_api_key(client, auth_headers):
    response = client.get("/dashboard/", headers=auth_headers)
    assert response.status_code == 200
    assert "MT5 Bridge Verification Dashboard" in response.text


def test_no_inactivity_timeout_while_tab_open(client, auth_headers):
    first = client.get("/dashboard/", headers=auth_headers)
    time.sleep(0.1)
    second = client.get("/dashboard/", headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
