import unittest

import mock
from kijiji_repost_headless.generate_inf_file import get_description


class TestsGenerateInfFile(unittest.TestCase):

    def test_get_description_remove_middle_line(self):
        with mock.patch('builtins.input', side_effect=["5", "6", "DEL", "7", "8", "EOF"]):
            self.assertEqual(get_description(), "5\\n7\\n8")

    def test_get_description_remove_first_line(self):
        with mock.patch('builtins.input', side_effect=["5", "DEL", "6", "7", "8", "EOF"]):
            self.assertEqual(get_description(), "6\\n7\\n8")

    def test_get_description_remove_last_line(self):
        with mock.patch('builtins.input', side_effect=["5", "6", "7", "8", "DEL", "EOF"]):
            self.assertEqual(get_description(), "5\\n6\\n7")

    def test_get_description_remove_last_line(self):
        with mock.patch('builtins.input', side_effect=["DEL", "5", "6", "7", "8", "EOF"]):
            self.assertEqual(get_description(), "5\\n6\\n7\\n8")
