import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.schemas.guide_schema import GuideCategory, GuideClassification
from app.services import guide_service


class GuideOutputContractTests(unittest.TestCase):
    def test_wrong_types_and_extra_fields_are_rejected(self):
        base = {'category': 'TERM_EXPLANATION', 'confidence': 0.9, 'short_answer': '정상 모의 설명'}
        for change in ({'confidence': '0.9'}, {'confidence': True}, {'unexpected': 'value'}, {'short_answer': 123}):
            with self.subTest(change=change):
                result = guide_service._parse_classification(json.dumps({**base, **change}))
                self.assertEqual(result.confidence, 0)

    def test_empty_or_missing_short_answer_never_becomes_successful_answer(self):
        for category in ('TERM_EXPLANATION', 'SIMPLE_CALCULATION'):
            for answer in (None, '', '  \n  '):
                provider = Mock()
                provider.models.generate_content.return_value = SimpleNamespace(text=json.dumps({'category': category, 'confidence': 0.9, 'short_answer': answer}))
                with self.subTest(category=category, answer=answer), patch.object(guide_service, 'get_gemini_mode', return_value='gemini'), patch.object(guide_service, 'get_gemini_client', return_value=provider):
                    result = guide_service.create_guide_answer([], 'unknown question')
                self.assertEqual(result.response_type, 'clarification')
                self.assertTrue(result.answer.strip())

    def test_valid_json_and_fenced_json_trim_the_answer(self):
        raw = '{"category":"TERM_EXPLANATION","confidence":0.9,"short_answer":"  모의 설명  "}'
        for text in (raw, '```json\n' + raw + '\n```'):
            with self.subTest(text=text):
                result = guide_service._parse_classification(text)
                self.assertEqual(result.category, GuideCategory.TERM_EXPLANATION)
                self.assertEqual(result.short_answer, '모의 설명')

    def test_provider_receives_the_same_pydantic_contract(self):
        provider = Mock()
        provider.models.generate_content.return_value = SimpleNamespace(text='{"category":"OUT_OF_SCOPE","confidence":0.9}')
        with patch.object(guide_service, 'get_gemini_mode', return_value='gemini'), patch.object(guide_service, 'get_gemini_client', return_value=provider):
            guide_service.classify_question([], 'unknown question')
        config = provider.models.generate_content.call_args.kwargs['config']
        self.assertIs(config['response_schema'], GuideClassification)
        self.assertEqual(config['response_mime_type'], 'application/json')

    def test_installed_sdk_serializes_contract_without_real_provider_call(self):
        import httpx
        from google import genai
        from google.genai import types
        requests = []
        raw = '{"category":"TERM_EXPLANATION","confidence":0.9,"short_answer":"모의 설명"}'
        def respond(request):
            requests.append(json.loads(request.content))
            return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': raw}], 'role': 'model'}, 'finishReason': 'STOP'}]})
        with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
            with genai.Client(api_key='test-only-key', http_options=types.HttpOptions(httpx_client=transport, retry_options=types.HttpRetryOptions(attempts=1))) as provider:
                response = provider.models.generate_content(model='gemini-2.5-flash-lite', contents='test', config={'response_mime_type': 'application/json', 'response_schema': GuideClassification})
        self.assertEqual(GuideClassification.model_validate_json(response.text).short_answer, '모의 설명')
        schema = requests[0]['generationConfig']['responseSchema']
        self.assertIn('category', schema['required'])
        self.assertIn('TERM_EXPLANATION', schema['properties']['category']['enum'])
