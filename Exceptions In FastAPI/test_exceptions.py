import pytest
from fastapi.testclient import TestClient

from user_exceptions import UserNotFoundException
from main import app, get_user_from_db
 # Simulate user not found

client = TestClient(app)



def test_user_not_found_route():
    response = client.get("/user/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "User with ID 999 not found"}
