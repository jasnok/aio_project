import unittest
from types import SimpleNamespace
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.external_error import ai_error, ExternalServiceError
from app.exceptions.handlers import register_exception_handlers
from app.services.location_service import request_kakao

class ExternalErrorTests(unittest.TestCase):
    def test_safe_service_reason_without_raw_secret(self):
        app=FastAPI();register_exception_handlers(app)
        @app.get('/failure')
        def failure():
            error=RuntimeError('secret-key-and-private-input');error.code=429
            raise ai_error(error)
        response=TestClient(app).get('/failure')
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json()['code'],'rate_limit')
        self.assertNotIn('secret',response.text)

    def test_kakao_limit_is_distinguished_from_connection_failure(self):
        with patch('app.services.location_service.get_kakao_api_key',return_value='fake'), \
             patch('httpx.Client.get',return_value=SimpleNamespace(status_code=429)):
            with self.assertRaises(ExternalServiceError) as result:
                request_kakao('https://example.invalid',{})
        self.assertEqual(result.exception.reason,'rate_limit')
