import unittest
from dataclasses import replace
from game_core import World, Throw, GestureController, speed_from_power

class PhysicsTests(unittest.TestCase):
    def test_ranges(self):
        for speed, expected in [(4, 'short'), (8, 'success'), (12, 'long')]:
            shot = Throw(World(), speed)
            shot.advance(10)
            self.assertEqual(shot.status, expected)
    def test_short_at_table_height(self):
        shot = Throw(World(), 7)
        shot.advance(10)
        self.assertEqual(shot.status, 'short')

    def test_frame_independent(self):
        a, b = Throw(World(), 8), Throw(World(), 8)
        a.advance(10)
        for _ in range(1000): b.advance(.01)
        self.assertEqual(a.status, b.status)
        self.assertAlmostEqual(a.z, b.z)
    def test_whole_sausage(self):
        shot = Throw(replace(World(), half_width=.3), 8)
        shot.advance(10)
        self.assertEqual(shot.status, 'edge')
        shot = Throw(replace(World(), half_width=.65), 8)
        shot.advance(10)
        self.assertEqual(shot.status, 'success')
    def test_bad_dt(self):
        for dt in [-1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError): Throw(World(), 8).advance(dt)
    def test_power_clamped(self):
        self.assertEqual(speed_from_power(-1), 4)
        self.assertEqual(speed_from_power(2), 12)

class GestureTests(unittest.TestCase):
    def ready(self):
        g = GestureController(); g.prepare(0)
        for i in range(11): g.feed((0, 0, 10), i / 10)
        self.assertEqual(g.state, 'ready')
        return g
    def test_peak_once(self):
        g = self.ready()
        g.feed((0, 0, 15), 1.1); g.feed((0, 0, 20), 1.2)
        self.assertAlmostEqual(g.update(1.36), .5)
        self.assertIsNone(g.update(1.4))
    def test_capture_window_excludes_late_peak(self):
        g = self.ready()
        g.feed((0,0,15), 1.1)
        g.feed((0,0,100), 1.4)
        self.assertAlmostEqual(g.update(1.4), .25)

    def test_static_disconnect_timeout(self):
        g = self.ready(); self.assertIsNone(g.update(1.5))
        g.update(2.1); self.assertEqual(g.state, 'idle')
        g = self.ready()
        for i in range(2, 13):
            g.feed((0, 0, 10), i); g.update(i)
        self.assertEqual(g.state, 'idle')
    def test_insufficient_unstable_reset(self):
        g = GestureController(); g.prepare(0); g.feed((0,0,10), 0); g.update(1.1)
        self.assertEqual(g.state, 'idle')
        g.prepare(2)
        for i in range(11): g.feed((0,0,10 + i), 2 + i / 10)
        self.assertEqual(g.state, 'calibrating')
        for i in range(31, 72): g.feed((0,0,10 + i), i / 10)
        self.assertEqual(g.state, 'idle')
        g = self.ready(); g.feed((0,0,20), 1.1); g.prepare(2)
        g.feed((0,0,100), 1.5)
        self.assertEqual(g.strength, 0)
        self.assertIsNone(g.update(2.1))


class CalibrationRecoveryTests(unittest.TestCase):
    def test_slow_stream_waits_for_five_samples(self):
        g = GestureController(); g.prepare(0)
        for i in range(5):
            g.feed((0,0,9.8), i * .5)
            g.update(i * .5)
        self.assertEqual(g.state, 'ready')
        self.assertAlmostEqual(g.baseline, 9.8)

    def test_initial_motion_can_settle_without_retry(self):
        g = GestureController(); g.prepare(0)
        g.feed((0,0,20), 0)
        for i in range(1, 32):
            g.feed((0,0,9.8), i / 10)
            g.update(i / 10)
        self.assertEqual(g.state, 'ready')
        self.assertAlmostEqual(g.baseline, 9.8)

    def test_unstable_timeout_has_specific_reason(self):
        g = GestureController(); g.prepare(0)
        for i in range(51):
            g.feed((0,0,10 + (i % 2)*5), i / 10)
            g.update(i / 10)
        self.assertEqual(g.state, 'idle')
        self.assertIn('moving', g.message)
