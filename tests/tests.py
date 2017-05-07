import unittest
import mock
from GenerateInfFile import getDescription


class TestsGenerateInfFile(unittest.TestCase):

    def test_getDescription_remove_middle_line(self):
        with mock.patch('builtins.input', side_effect=["5", "6", "DEL", "7", "8", "EOF"]):
            self.assertEqual(getDescription(), "5\\n7\\n8")

    def test_getDescription_remove_first_line(self):
        with mock.patch('builtins.input', side_effect=["5", "DEL", "6", "7", "8", "EOF"]):
            self.assertEqual(getDescription(), "6\\n7\\n8")

    def test_getDescription_remove_last_line(self):
        with mock.patch('builtins.input', side_effect=["5", "6", "7", "8", "DEL", "EOF"]):
            self.assertEqual(getDescription(), "5\\n6\\n7")

    def test_getDescription_remove_last_line(self):
        with mock.patch('builtins.input', side_effect=["DEL", "5", "6", "7", "8", "EOF"]):
            self.assertEqual(getDescription(), "5\\n6\\n7\\n8")
