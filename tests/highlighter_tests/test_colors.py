import unittest

from pepys_import.file.highlighter.support.color_picker import (
    color_for,
    hex_color_for,
    mean_color_for,
)


class ColorTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_color_for(self):
        color_dict = {}
        color1 = color_for("aaa", color_dict)
        assert color1 is not None
        self.assertEqual(1, len(color_dict))

        color2 = color_for("bbb", color_dict)
        assert color2 is not None
        self.assertEqual(2, len(color_dict))
        self.assertNotEqual(color1, color2)

        color3 = color_for("aaa", color_dict)
        self.assertEqual(2, len(color_dict), "Should not have created new dict entry")
        self.assertEqual(color1, color3)

    def test_hex_conversion(self):
        red = (255, 0, 0)
        self.assertEqual("rgba(255,0,0,0.3)", hex_color_for(red))

    def test_mean_color(self):
        color1 = (100, 50, 200)
        color2 = (50, 0, 150)
        color3 = (150, 100, 250)

        self.assertEqual((75, 25, 175), mean_color_for((color1, color2)))
        self.assertEqual((100, 50, 200), mean_color_for((color3, color2)))
        self.assertEqual((100, 50, 200), mean_color_for((color1, color2, color3)))


if __name__ == "__main__":
    unittest.main()
