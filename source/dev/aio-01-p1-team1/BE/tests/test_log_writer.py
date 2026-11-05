import threading
import unittest
from app.core.log_store import LogWriter

class LogWriterTests(unittest.TestCase):
    def test_slow_save_does_not_block_submit_and_queue_is_bounded(self):
        entered, release = threading.Event(), threading.Event()
        saved = []
        def slow(entry):
            entered.set()
            release.wait(3)
            saved.append(entry)
        writer = LogWriter(slow, capacity=1)
        writer.start()
        try:
            writer.submit({'id':1})
            self.assertTrue(entered.wait(1))
            writer.submit({'id':2})
            writer.submit({'id':3})
            self.assertEqual(writer.dropped,1)
            self.assertEqual(saved,[])
        finally:
            release.set()
            writer.stop()
        self.assertEqual([x['id'] for x in saved],[1,2])

    def test_failure_does_not_kill_worker_and_shutdown_drains_queue(self):
        saved=[]
        def save(entry):
            if entry['id']==1: raise RuntimeError('secret')
            saved.append(entry['id'])
        writer=LogWriter(save)
        writer.start()
        writer.submit({'id':1});writer.submit({'id':2})
        writer.stop()
        self.assertEqual(saved,[2])

    def test_inactive_writer_does_not_touch_db(self):
        writer=LogWriter(lambda _: self.fail('DB should not run'))
        writer.submit({'id':1})
        self.assertTrue(writer.pending.empty())
