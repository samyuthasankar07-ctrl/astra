import sys
import unittest
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.privacy import redact_event_description, redact_person_label


class PrivacyRedactionTest(unittest.TestCase):
    def test_event_description_is_generic(self):
        text = 'Person #17 moved toward object #5'
        self.assertEqual(redact_event_description(text), 'Person detected.')

    def test_person_label_is_generic(self):
        self.assertEqual(redact_person_label('PERSON #17'), 'Person detected')


if __name__ == '__main__':
    unittest.main()
