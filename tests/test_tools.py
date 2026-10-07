"""Behavioral checks for the three standalone tools."""

import unittest
from unittest.mock import patch

from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe, load_listings


class SearchListingsTests(unittest.TestCase):
    def test_graphic_tee_results_are_ranked_and_filtered(self):
        results = search_listings("graphic tee", size="L", max_price=24)

        self.assertEqual([item["id"] for item in results], ["lst_006", "lst_033"])
        self.assertTrue(all(item["price"] <= 24 for item in results))

    def test_letter_sizes_do_not_match_parts_of_other_sizes(self):
        self.assertEqual(
            [item["id"] for item in search_listings("flannel", size="XL")],
            ["lst_003"],
        )
        self.assertEqual(search_listings("flannel", size="L"), [])
        self.assertEqual(search_listings("sneakers", size="S"), [])

    def test_price_ceiling_is_inclusive_and_no_keyword_is_empty(self):
        self.assertEqual(
            [item["id"] for item in search_listings("slip", size="M", max_price=30)],
            ["lst_013"],
        )
        self.assertEqual(search_listings("slip", size="M", max_price=29.99), [])
        self.assertEqual(search_listings("unicorn ballgown"), [])

    def test_shoe_size_matches_the_whole_us_number(self):
        self.assertEqual(
            [item["id"] for item in search_listings("platform sneakers", size="8", max_price=50)],
            ["lst_019"],
        )
        self.assertEqual(search_listings("platform sneakers", size="8.5", max_price=50), [])


class ModelToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.item = next(item for item in load_listings() if item["id"] == "lst_006")

    def test_outfit_prompt_uses_the_selected_item_and_owned_pieces(self):
        prompts = []

        def fake_generate(prompt, **_kwargs):
            prompts.append(prompt)
            return "Wear it with your dark wash jeans and white sneakers."

        with patch("tools.generate", side_effect=fake_generate):
            result = suggest_outfit(self.item, get_example_wardrobe())

        self.assertIn("dark wash jeans", result)
        self.assertIn(self.item["title"], prompts[0])
        self.assertIn("Baggy straight-leg jeans, dark wash", prompts[0])
        self.assertIn("Chunky white sneakers", prompts[0])

    def test_empty_wardrobe_requests_general_advice(self):
        prompts = []

        def fake_generate(prompt, **_kwargs):
            prompts.append(prompt)
            return "Try it with relaxed jeans and simple shoes."

        with patch("tools.generate", side_effect=fake_generate):
            result = suggest_outfit(self.item, get_empty_wardrobe())

        self.assertTrue(result.strip())
        self.assertIn("general", prompts[0].lower())
        self.assertNotIn("Baggy straight-leg jeans, dark wash", prompts[0])

    def test_empty_model_outfit_response_still_gives_advice(self):
        with patch("tools.generate", return_value="   "):
            result = suggest_outfit(self.item, get_empty_wardrobe())

        self.assertTrue(result.strip())
        self.assertIn("tee", result.lower())

    def test_fit_card_prompt_includes_item_facts_and_outfit(self):
        prompts = []

        def fake_generate(prompt, **_kwargs):
            prompts.append(prompt)
            return "Graphic Tee — 2003 Tour Bootleg Style with jeans feels easy. $24 on depop."

        with patch("tools.generate", side_effect=fake_generate):
            result = create_fit_card("dark wash jeans and white sneakers", self.item)

        self.assertIn("$24 on depop", result)
        self.assertIn(self.item["title"], prompts[0])
        self.assertIn("$24", prompts[0])
        self.assertIn("depop", prompts[0])
        self.assertIn("dark wash jeans and white sneakers", prompts[0])
        self.assertIn("Start the first sentence with the exact title", prompts[0])

    def test_blank_outfit_returns_a_message_without_calling_the_model(self):
        with patch("tools.generate") as model:
            result = create_fit_card("  ", self.item)

        self.assertIn("outfit", result.lower())
        model.assert_not_called()

    def test_empty_model_card_response_requests_retry(self):
        with patch("tools.generate", return_value=""):
            result = create_fit_card("dark wash jeans", self.item)

        self.assertIn("try again", result.lower())


if __name__ == "__main__":
    unittest.main()
