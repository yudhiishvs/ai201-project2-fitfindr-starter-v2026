"""Checks for branch choice, parsing, and visible session handoff."""

import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

import agent
import trace
from generate import ModelUnavailable
from utils.data_loader import get_example_wardrobe, load_listings


class AgentLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.item = next(item for item in load_listings() if item["id"] == "lst_002")
        cls.wardrobe = get_example_wardrobe()

    def test_matching_query_saves_each_result_and_passes_selected_item(self):
        with (
            patch("agent.call_tool", return_value=[self.item]) as search,
            patch("agent.suggest_outfit", return_value="Jeans and white sneakers") as outfit,
            patch("agent.create_fit_card", return_value="A short fit card.") as card,
        ):
            session = agent.run_agent(
                "vintage graphic tee under $30, size M", self.wardrobe
            )

        self.assertEqual(
            session["parsed"],
            {"description": "vintage graphic tee", "size": "M", "max_price": 30.0},
        )
        search.assert_called_once_with("search_listings", {"description": "vintage graphic tee", "size": "M", "max_price": 30.0})
        self.assertIs(session["search_results"][0], self.item)
        self.assertIs(session["selected_item"], self.item)
        self.assertIs(outfit.call_args.args[0], session["selected_item"])
        self.assertIs(outfit.call_args.args[1], session["wardrobe"])
        self.assertEqual(session["outfit_suggestion"], "Jeans and white sneakers")
        self.assertEqual(card.call_args.args, ("Jeans and white sneakers", self.item))
        self.assertEqual(session["fit_card"], "A short fit card.")
        self.assertIsNone(session["error"])

    def test_empty_search_stops_with_actionable_message(self):
        with (
            patch("agent.call_tool", return_value=[]),
            patch("agent.suggest_outfit") as outfit,
            patch("agent.create_fit_card") as card,
        ):
            session = agent.run_agent(
                "designer ballgown size XXS under $5", self.wardrobe
            )

        self.assertEqual(session["search_results"], [])
        self.assertIsNone(session["selected_item"])
        self.assertIsNone(session["outfit_suggestion"])
        self.assertIsNone(session["fit_card"])
        self.assertIn("description", session["error"].lower())
        self.assertIn("size", session["error"].lower())
        self.assertIn("price", session["error"].lower())
        outfit.assert_not_called()
        card.assert_not_called()

    def test_iteration_limit_stops_before_extra_tool_call(self):
        with (
            patch("agent.config.MAX_ITERATIONS", 2),
            patch("agent.call_tool", return_value=[self.item]),
            patch("agent.suggest_outfit", return_value="Jeans and sneakers"),
            patch("agent.create_fit_card") as card,
        ):
            with self.assertRaisesRegex(RuntimeError, "MAX_ITERATIONS"):
                agent.run_agent("baby tee", self.wardrobe)

        card.assert_not_called()

    def test_five_explicit_size_and_price_queries_select_expected_items(self):
        examples = [
            ("graphic tee size L under $25", "lst_006"),
            ("track jacket size M under $50", "lst_004"),
            ("platform sneakers size 8 under $50", "lst_019"),
            ("denim jacket size S under $50", "lst_007"),
            ("silk slip dress size M under $40", "lst_013"),
        ]
        with (
            patch("agent.suggest_outfit", return_value="Jeans and sneakers"),
            patch("agent.create_fit_card", return_value="A short fit card."),
        ):
            for query, expected_id in examples:
                with self.subTest(query=query):
                    session = agent.run_agent(query, self.wardrobe)
                    self.assertIsNotNone(session["selected_item"])
                    self.assertEqual(session["selected_item"]["id"], expected_id)
                    self.assertTrue(session["search_results"])
                    self.assertIsNone(session["error"])

    def test_missing_size_and_price_leave_filters_open(self):
        with (
            patch("agent.call_tool", return_value=[self.item]) as search,
            patch("agent.suggest_outfit", return_value="Jeans and sneakers"),
            patch("agent.create_fit_card", return_value="A short fit card."),
        ):
            agent.run_agent("baby tee", self.wardrobe)

        search.assert_called_once_with("search_listings", {"description": "baby tee", "size": None, "max_price": None})

    def test_trace_records_all_three_tools_in_order(self):
        trace.start_trace()
        with (
            patch("agent.call_tool", return_value=[self.item]),
            patch("agent.suggest_outfit", return_value="Jeans and sneakers"),
            patch("agent.create_fit_card", return_value="A short fit card."),
            redirect_stdout(StringIO()),
        ):
            agent.run_agent("baby tee", self.wardrobe)
        output = trace.get_trace()
        self.assertLess(output.index("search_listings (via MCP)"), output.index("suggest_outfit"))
        self.assertLess(output.index("suggest_outfit"), output.index("create_fit_card"))
        self.assertIn("Jeans and sneakers", output)
        self.assertIn("baby tee", output)
        self.assertIn(self.item["id"], output)

    def test_model_unavailable_returns_actionable_message(self):
        with (
            patch("agent.call_tool", return_value=[self.item]),
            patch("agent.suggest_outfit", side_effect=ModelUnavailable("bad key")),
            patch("agent.create_fit_card") as card,
        ):
            session = agent.run_agent("baby tee", self.wardrobe)
        self.assertIn("model", session["error"].lower())
        self.assertIn("try again", session["error"].lower())
        card.assert_not_called()


if __name__ == "__main__":
    unittest.main()
