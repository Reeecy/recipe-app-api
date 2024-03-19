"""
Sample tests
"""

from django.test import SimpleTestCase
from app import calc


class CalcTest(SimpleTestCase):
    """ test the calc module"""

    def test_add_number(self):
        res = calc.add(3, 8)

        self.assertEqual(res, 11)

    def test_subtract_number(self):
        res = calc.subtract(10, 15)

        self.assertEqual(res, -5)
