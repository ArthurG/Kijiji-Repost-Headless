import sys
import test.get_ids_fake as get_ids_fake
sys.modules['get_ids'] = get_ids_fake

from unittest import TestCase, mock

from kijiji_repost_headless.generate_post_file import get_description


class TestsGenerateInfFile(TestCase):

    def test_get_description_remove_middle_line(self):
        with mock.patch('builtins.input', side_effect=["5", "6", "DEL", "7", "8", "EOF"]):
            self.assertEqual(get_description(), "5\\n7\\n8")

    def test_get_description_remove_first_line(self):
        with mock.patch('builtins.input', side_effect=["5", "DEL", "6", "7", "8", "EOF"]):
            self.assertEqual(get_description(), "6\\n7\\n8")

    def test_get_description_remove_last_line_and_char(self):
        with mock.patch('builtins.input', side_effect=["5", "6", "7", "8", "DEL", "EOF"]):
            self.assertEqual(get_description(), "5\\n6\\n7")

    def test_get_description_remove_last_line(self):
        with mock.patch('builtins.input', side_effect=["DEL", "5", "6", "7", "8", "EOF"]):
            self.assertEqual(get_description(), "5\\n6\\n7\\n8")

if __name__ == '__main__':
    unittest.main()
