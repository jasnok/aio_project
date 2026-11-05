import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from fastapi import HTTPException
from app.routers import login_handoff_router as handoff
from app.schemas.admin_schema import AdminLogin, AdminPublic


class LoginHandoffTests(unittest.TestCase):
    def test_authenticated_ticket_is_short_lived_and_consumed_once(self):
        values = {}
        redis = Mock()
        redis.set.side_effect = lambda key, value, ex: values.update({key: value})
        redis.getdel.side_effect = lambda key: values.pop(key, None)
        account = AdminPublic(id=1, username='test-admin', created_at=datetime.now(timezone.utc))
        with patch.object(handoff, 'get_redis', return_value=redis), patch.object(handoff, 'admin_login_process', return_value=account), patch.object(handoff, 'create_admin_token', return_value='private-token'), patch.object(handoff, 'get_current_admin') as verify:
            result = handoff.issue(AdminLogin(username='test-admin', password='password'))
            self.assertNotIn('private-token', str(result.data))
            self.assertEqual(redis.set.call_args.kwargs['ex'], 60)
            request = handoff.HandoffRequest(ticket=result.data['ticket'])
            self.assertEqual(handoff.consume(request).data['username'], 'test-admin')
            verify.assert_called_once()
            with self.assertRaises(HTTPException) as denied:
                handoff.consume(request)
            self.assertEqual(denied.exception.status_code, 401)

    def test_invalid_credentials_do_not_issue_ticket(self):
        with patch.object(handoff, 'admin_login_process', side_effect=HTTPException(401)), patch.object(handoff, 'get_redis') as redis:
            with self.assertRaises(HTTPException):
                handoff.issue(AdminLogin(username='user', password='bad'))
            redis.assert_not_called()
