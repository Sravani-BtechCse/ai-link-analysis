import pytest
from fastapi import HTTPException
from app.utils.validators import validate_public_url

def test_rejects_non_http_scheme():
    with pytest.raises(HTTPException):
        validate_public_url("file:///etc/passwd")

def test_rejects_localhost():
    with pytest.raises(HTTPException):
        validate_public_url("http://localhost:8000")
