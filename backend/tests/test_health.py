def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "AI ExamGen" in data["message"]

def test_health_check_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] in ["healthy", "degraded"]
    assert data["service"] == "AI ExamGen"
    assert "database" in data

def test_version_endpoint(client):
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["version"] == "1.0.0"
