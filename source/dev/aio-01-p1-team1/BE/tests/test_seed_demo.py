from copy import deepcopy
from datetime import date, timedelta
from types import SimpleNamespace
import unittest

from scripts.seed_demo import PREFIX, MARKER, apply_seed, fixtures, owned_row, diagram_png
from pathlib import Path


class FakeDB:
    def __init__(self):
        self.rows = {'listings': [], 'listing_images': []}
        self.files = {}
        self.storage = self
        self.fail_image_once = False

    def get_bucket(self, _):
        return SimpleNamespace(public=True)

    def from_(self, _):
        return self

    def list(self, prefix):
        return [{'name': p.split('/')[-1]} for p in self.files if p.startswith(prefix+'/')]

    def upload(self, path, data, options):
        if path in self.files:
            raise AssertionError('duplicate upload')
        self.files[path] = data

    def download(self, path):
        return self.files[path]

    def get_public_url(self, path):
        return 'https://storage.example/'+path

    def table(self, table):
        db = self
        class Query:
            def __init__(self):
                self.filters = {}
                self.action = 'select'
            def select(self, _): return self
            def eq(self, key, value):
                self.filters[key] = value
                return self
            def limit(self, _): return self
            def insert(self, data):
                self.action, self.data = 'insert', deepcopy(data)
                return self
            def update(self, data):
                self.action, self.data = 'update', deepcopy(data)
                return self
            def execute(self):
                if self.action == 'insert':
                    if table == 'listing_images' and db.fail_image_once:
                        db.fail_image_once = False
                        raise RuntimeError('interrupted upload reference')
                    self.data['id'] = len(db.rows[table])+1
                    db.rows[table].append(self.data)
                    return SimpleNamespace(data=[deepcopy(self.data)])
                rows = [r for r in db.rows[table] if all(r.get(k)==v for k,v in self.filters.items())]
                if self.action == 'update':
                    for r in rows: r.update(self.data)
                return SimpleNamespace(data=deepcopy(rows))
        return Query()


class SeedTests(unittest.TestCase):
    def test_initial_migration_matches_bootstrap(self):
        root=Path(__file__).resolve().parents[2]
        def statements(text):
            return [line.strip() for line in text.splitlines()
                    if line.strip() and not line.lstrip().startswith("--")]
        bootstrap = (root/'BE/sql/bootstrap_portfolio.sql').read_text(encoding='utf-8')
        migrations = '\n'.join(path.read_text(encoding='utf-8') for path in (
            root/'supabase/migrations/20260923000100_initial.sql',
            root/'supabase/migrations/20260930000100_atomic_listing_save.sql',
            root/'supabase/migrations/20260930000200_listing_search_page.sql',
        ))
        self.assertEqual(statements(bootstrap), statements(migrations))

    def test_fifteen_marked_fixtures_cover_three_periods(self):
        reference = date(2026,9,28)
        rows = fixtures(reference)
        self.assertEqual(len({r['source_url'] for r in rows}),15)
        self.assertTrue(all(r['title'].startswith(MARKER) for r in rows))
        self.assertEqual(sum(date.fromisoformat(r['application_start_date'])>reference for r in rows),5)
        self.assertEqual(sum(date.fromisoformat(r['application_end_date'])<reference for r in rows),5)

    def test_repeat_reuses_ids_and_images(self):
        db = FakeDB()
        first = apply_seed(db,date(2026,9,28))
        before = deepcopy(db.rows)
        second = apply_seed(db,date(2026,10,10))
        self.assertEqual(second['created'],0)
        self.assertEqual(first['listing_ids'],second['listing_ids'])
        self.assertEqual(db.rows,before)
        self.assertEqual(len(db.files),3)
        self.assertEqual(len(db.rows['listing_images']),20)

    def test_interrupted_run_recovers_without_duplicate_listing(self):
        db = FakeDB(); db.fail_image_once = True
        with self.assertRaises(RuntimeError): apply_seed(db,date(2026,9,28))
        apply_seed(db,date(2026,9,28))
        self.assertEqual(len(db.rows['listings']),15)
        self.assertEqual(len(db.rows['listing_images']),20)

    def test_existing_unrelated_listing_is_unchanged(self):
        db = FakeDB()
        original = dict(id=1,title='original',description='retained',source_url='https://example.com')
        db.rows['listings'].append(deepcopy(original))
        apply_seed(db,date(2026,9,28))
        self.assertEqual(db.rows['listings'][0],original)

    def test_conflicting_marker_stops_before_any_write(self):
        db = FakeDB()
        db.rows['listings'].append(dict(id=1,title='original',description='retained',source_url=PREFIX+'015'))
        with self.assertRaises(RuntimeError): apply_seed(db,date(2026,9,28))
        self.assertEqual(len(db.rows['listings']),1)
        self.assertEqual(db.files,{})

    def test_duplicate_marker_is_not_guessed(self):
        with self.assertRaises(RuntimeError): owned_row([{},{}])

    def test_refresh_is_explicit(self):
        db=FakeDB(); first=date(2026,9,28)
        apply_seed(db,first)
        apply_seed(db,first+timedelta(days=10),True)
        self.assertEqual(db.rows['listings'][0]['application_start_date'],'2026-10-15')

    def test_diagrams_are_reproducible_distinct_pngs(self):
        images=[diagram_png(i) for i in range(3)]
        self.assertEqual(len(set(images)),3)
        self.assertTrue(all(x.startswith(b'\x89PNG\r\n\x1a\n') for x in images))
        self.assertEqual(images[0],diagram_png(0))
