import unittest

from core.auto_demo import sample_analysis
from core.constants import SEOUL_DISTRICTS
from core.listing_extract import summarize, validate_all


class AutoDemoTests(unittest.TestCase):
    def test_sample_requires_human_correction_before_registration(self):
        sample = sample_analysis()
        self.assertEqual(summarize(validate_all(sample, SEOUL_DISTRICTS))["blocked"], 1)
        sample[0]["monthly_rent"] = 280000
        results = validate_all(sample, SEOUL_DISTRICTS)
        self.assertEqual(summarize(results), {"total": 1, "ready": 1, "blocked": 0})
        self.assertIn("가상", results[0]["payload"]["title"])

    def test_sample_returns_an_independent_copy(self):
        changed = sample_analysis()
        changed[0]["title"] = "changed"
        self.assertNotEqual(sample_analysis()[0]["title"], "changed")

    def test_invalid_ai_numbers_are_blocked_without_crashing(self):
        for field, value in [('area_sqm', 'NaN'), ('monthly_rent', 'Infinity'),
                             ('recruitment_count', '2.7')]:
            with self.subTest(field=field):
                sample = sample_analysis()
                sample[0]['monthly_rent'] = 280000
                sample[0][field] = value
                self.assertEqual(summarize(validate_all(sample, SEOUL_DISTRICTS))['blocked'], 1)

    def test_reversed_dates_can_be_corrected(self):
        from core.listing_extract import unreadable_fields
        sample = sample_analysis()[0]
        sample['application_end_date'] = '2026-09-01'
        bad = unreadable_fields(sample)
        self.assertIn('application_start_date', bad)
        self.assertIn('application_end_date', bad)


if __name__ == "__main__":
    unittest.main()
