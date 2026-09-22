import sys
import unittest
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from detection.foundation_pose_adapter import Detection
from detection.object_detector import ObjectDetector


class ObjectDetectorClassNamespaceTest(unittest.TestCase):
    def test_c_astra_class_zero_is_retained_and_general_person_is_filtered(self):
        detector = ObjectDetector(object(), object())
        detector.custom_adapter.track = lambda *args, **kwargs: [
            Detection((10, 20, 80, 100), 0.91, 0, 'Astronaut', track_id=7)
        ]
        detector.general_adapter.track = lambda *args, **kwargs: [
            Detection((12, 22, 82, 102), 0.99, 0, 'person', track_id=8),
            Detection((100, 120, 140, 160), 0.80, 39, 'bottle', track_id=9),
        ]

        detections = detector.track(object())

        self.assertEqual([d.class_name for d in detections], ['Astronaut', 'bottle'])
        self.assertEqual(detections[0].track_id, 7)


if __name__ == '__main__':
    unittest.main()