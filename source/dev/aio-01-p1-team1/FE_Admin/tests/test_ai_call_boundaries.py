import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from clients import gemini_client as service
from core.image_label import validated_image_labels


class ProviderError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(f"Provider status {code}; test-only-key")


class AdminAICallTests(unittest.TestCase):
    def setUp(self):
        self.provider = Mock()
        self.context = MagicMock()
        self.context.__enter__.return_value = self.provider
        self.provider.models.generate_content.return_value = SimpleNamespace(text='[{"housing_name":"가상 주택"}]')

    def extract(self):
        return service.extract_listings_from_pdf(b"%PDF-1.4 test")

    def test_success_uses_explicit_options_and_closes_client(self):
        with patch.object(service, "get_api_key", return_value="test-only-key"), patch("google.genai.Client", return_value=self.context) as factory:
            self.assertEqual(self.extract()[0]["housing_name"], "가상 주택")
        self.context.__exit__.assert_called_once()
        self.assertEqual(factory.call_args.kwargs["http_options"].timeout, 60_000)
        self.assertEqual(factory.call_args.kwargs["http_options"].retry_options.attempts, 1)

    def test_transient_failure_retries_once_then_succeeds(self):
        self.provider.models.generate_content.side_effect = [ProviderError(503), SimpleNamespace(text='[{"title":"가상 공고"}]')]
        with patch.object(service, "get_api_key", return_value="test-only-key"), patch("google.genai.Client", return_value=self.context), patch.object(service.time, "sleep") as sleep:
            self.assertEqual(self.extract()[0]["title"], "가상 공고")
        self.assertEqual(self.provider.models.generate_content.call_count, 2)
        sleep.assert_called_once_with(2)
        self.context.__exit__.assert_called_once()

    def test_repeated_transient_failure_stops_after_two_calls_and_hides_key(self):
        self.provider.models.generate_content.side_effect = ProviderError(503)
        with patch.object(service, "get_api_key", return_value="test-only-key"), patch("google.genai.Client", return_value=self.context), patch.object(service.time, "sleep"):
            with self.assertRaises(service.GeminiError) as caught:
                self.extract()
        self.assertEqual(self.provider.models.generate_content.call_count, 2)
        self.assertNotIn("test-only-key", str(caught.exception))
        self.context.__exit__.assert_called_once()

    def test_quota_auth_timeout_and_invalid_json_are_not_automatically_retried(self):
        for error in (ProviderError(429), ProviderError(403), TimeoutError("private timeout"), ValueError("private malformed response")):
            self.provider.models.generate_content.reset_mock()
            self.provider.models.generate_content.side_effect = error
            with self.subTest(error=type(error).__name__), patch.object(service, "get_api_key", return_value="test-only-key"), patch("google.genai.Client", return_value=self.context), patch.object(service.time, "sleep") as sleep:
                with self.assertRaises(service.GeminiError):
                    self.extract()
            self.assertEqual(self.provider.models.generate_content.call_count, 1)
            sleep.assert_not_called()

    def test_retry_depends_on_status_not_digits_in_raw_message(self):
        self.assertFalse(service._should_retry(RuntimeError("trace 503, account 500")))
        for code in (500, 502, 503, 504):
            self.assertTrue(service._should_retry(ProviderError(code)))

    def test_client_setup_failure_is_safe_and_does_not_call_model(self):
        with patch.object(service, "get_api_key", return_value="test-only-key"), patch("google.genai.Client", side_effect=RuntimeError("private test-only-key")):
            with self.assertRaises(service.GeminiError) as caught:
                self.extract()
        self.assertNotIn("test-only-key", str(caught.exception))

    def test_optional_image_invalid_types_fall_back_without_crashing(self):
        self.provider.models.generate_content.return_value.text = '[{"house_name":123,"kind":"위치도"}]'
        with patch.object(service, "get_api_key", return_value="test-only-key"), patch("google.genai.Client", return_value=self.context) as factory:
            labels = service.identify_images([{"data": b"image", "name": "test.png"}])
        self.assertEqual(labels, [{"house_name": "", "kind": ""}])
        options = factory.call_args.kwargs["http_options"]
        self.assertEqual(options.timeout, 30_000)
        self.assertEqual(options.retry_options.attempts, 1)
        self.context.__exit__.assert_called_once()

    def test_optional_image_timeout_returns_empty_labels_without_retry(self):
        self.provider.models.generate_content.side_effect = TimeoutError()
        with patch.object(service, "get_api_key", return_value="test-only-key"), patch("google.genai.Client", return_value=self.context):
            self.assertEqual(service.identify_images([{"data": b"image"}]), [{"house_name": "", "kind": ""}])
        self.assertEqual(self.provider.models.generate_content.call_count, 1)
        self.context.__exit__.assert_called_once()

    def test_no_images_or_no_key_skip_provider(self):
        with patch.object(service, "get_api_key", return_value=""), patch("google.genai.Client") as factory:
            self.assertEqual(service.identify_images([]), [])
            self.assertEqual(service.identify_images([{"data": b"image"}]), [{"house_name": "", "kind": ""}])
        factory.assert_not_called()


class ImageLabelContractTests(unittest.TestCase):
    def test_mixed_output_preserves_valid_rows_and_input_image_count(self):
        items = [{"house_name": " 가상 주택 ", "kind": " 위치도 "}, {"house_name": {"private": "value"}, "kind": "평면도"}, {"house_name": None, "kind": "로고"}]
        self.assertEqual(validated_image_labels(items, 4), [{"house_name": "가상 주택", "kind": "위치도"}, {"house_name": "", "kind": ""}, {"house_name": "", "kind": "로고"}, {"house_name": "", "kind": ""}])

    def test_unknown_kind_and_non_object_are_not_forwarded(self):
        self.assertEqual(validated_image_labels([{"kind": "unknown"}, 123, ["private"]], 3), [{"house_name": "", "kind": ""}] * 3)
