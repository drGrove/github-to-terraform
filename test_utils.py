import unittest

from utils import bool_to_str, simplify


class TestUtils(unittest.TestCase):
    def test_simplify(self):
        options = {
            '0xxsls': 'xxsls',
            'x0x': 'x0x',
            '*': 'wildcard',
            '--': '_',
            'foo/bar': 'foo_bar',
            'foo/bar--baz': 'foo_bar_baz'
        }
        for data, expected in options.items():
            self.assertEqual(simplify(data), expected)

    def test_bool_to_str(self):
        self.assertEqual(bool_to_str(True), "true")
        self.assertEqual(bool_to_str(False), "false")
