import sys
import unittest
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from detection.person_detector import Detection
from tracking.object_tracker import ObjectTracker
from tracking.person_tracker import PersonTracker


class PersonTrackerDuplicateTest(unittest.TestCase):
    def test_same_person_with_new_track_id_is_merged(self):
        tracker = PersonTracker()

        tracker.update([
            Detection((10, 20, 80, 150), 0.92, 0, 'person', track_id=1)
        ])

        tracker.update([
            Detection((12, 22, 82, 152), 0.88, 0, 'person', track_id=99)
        ])

        self.assertEqual(len(tracker.states), 1)
        self.assertIn(1, tracker.states)
        self.assertEqual(tracker.states[1].bbox, (12, 22, 82, 152))

    def test_same_object_with_new_track_id_is_merged(self):
        tracker = ObjectTracker()

        tracker.update([
            Detection((60, 120, 120, 180), 0.90, 1, 'cup', track_id=7)
        ])

        tracker.update([
            Detection((62, 122, 122, 182), 0.88, 1, 'cup', track_id=55)
        ])

        self.assertEqual(len(tracker.states), 1)
        self.assertIn(7, tracker.states)
        self.assertEqual(tracker.states[7].bbox, (62, 122, 122, 182))


if __name__ == '__main__':
    unittest.main()
