import unittest
from unittest.mock import Mock, patch
from core.session_result import session_result


class SessionResultTests(unittest.TestCase):
    def test_expiry_and_changed_identity_reload(self):
        state = {}; load = Mock(side_effect=['first', 'expired', 'other-owner'])
        with patch('core.session_result.time.monotonic', return_value=0) as clock:
            self.assertEqual(session_result(state, 'result', 'owner-a', load, ttl=10), 'first')
            clock.return_value = 9
            self.assertEqual(session_result(state, 'result', 'owner-a', load, ttl=10), 'first')
            self.assertEqual(load.call_count, 1)
            clock.return_value = 10
            self.assertEqual(session_result(state, 'result', 'owner-a', load, ttl=10), 'expired')
            self.assertEqual(session_result(state, 'result', 'owner-b', load), 'other-owner')

    def test_failed_refresh_is_not_cached_and_next_request_retries(self):
        state = {}; load = Mock(side_effect=[RuntimeError('unavailable'), 'recovered'])
        with self.assertRaises(RuntimeError):
            session_result(state, 'result', 'same', load)
        self.assertNotIn('result', state)
        self.assertEqual(session_result(state, 'result', 'same', load), 'recovered')

    def test_separate_sessions_do_not_share_private_results(self):
        first, second = {}, {}
        session_result(first, 'result', 'same', lambda: 'private-a')
        self.assertEqual(session_result(second, 'result', 'same', lambda: 'private-b'), 'private-b')
