from django.test import TestCase

from ..utils import rtmp_key


class UtilsTest(TestCase):
    def test_rtmp_key(self):
        self.assertEqual(
            rtmp_key({'param': '?key=fdO12mlKgp0H4z3sG8ybc5Du9wQFi77vN&s=1'}),
            True)

        self.assertEqual(rtmp_key({'param': ''}), False)
        self.assertEqual(rtmp_key({'param': '?s=1'}), False)
