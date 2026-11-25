from pathlib import Path
import unittest

from color_gang_shimeji.core import load_catalog
from color_gang_shimeji.motion import choose_direction, clamp


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MotionTests(unittest.TestCase):
    def test_clamp_inside_range(self):
        self.assertEqual(clamp(5, 0, 10), 5)

    def test_clamp_outside_range(self):
        self.assertEqual(clamp(-5, 0, 10), 0)
        self.assertEqual(clamp(15, 0, 10), 10)

    def test_clamp_rejects_invalid_range(self):
        with self.assertRaises(ValueError):
            clamp(1, 5, 2)

    def test_direction_is_left_or_right(self):
        self.assertIn(choose_direction(), (-1, 1))


class CatalogueTests(unittest.TestCase):
    def test_all_repository_characters_have_existing_sprites(self):
        characters = load_catalog(PROJECT_ROOT)
        self.assertEqual(
            [character.name for character in characters],
            ["Blue", "Green", "Red", "The Second Coming", "Yellow"],
        )
        for character in characters:
            self.assertTrue(character.sprite.is_file())


if __name__ == "__main__":
    unittest.main()
