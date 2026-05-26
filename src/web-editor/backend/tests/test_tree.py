def test_get_tree_empty_state(client):
    resp = client.get("/api/tree")
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data
    assert data["products"] == {}
    assert "globals" in data


def test_get_overview_empty_state(client):
    resp = client.get("/api/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["products"] == []


def test_get_units(client):
    resp = client.get("/api/units")
    assert resp.status_code == 200
    data = resp.json()
    assert "units" in data
    assert "vCPU" in data["units"]
    assert "GB" in data["units"]
