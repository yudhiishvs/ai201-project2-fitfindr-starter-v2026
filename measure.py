"""Measure the five saved criteria with the same inputs on each run."""

import argparse
import json
import re
from pathlib import Path
from unittest.mock import patch

import config
import agent
import scenarios
import tools
import trace
from generate import ModelUnavailable
from utils.data_loader import get_example_wardrobe, load_listings


QUERY = scenarios.SCENARIOS[0]["query"]
EMPTY_QUERY = scenarios.SCENARIOS[1]["query"]
ITEM_IDS = scenarios.SCENARIOS[3]["item_ids"]
FILTER_QUERIES = scenarios.SCENARIOS[4]["queries"]
TARGETS = {1: 4, 2: 5, 3: 5, 4: 4, 5: 5}


def card_checks(card, item):
    sentence_count = len(re.findall(r"[.!?](?=\s|$)", card))
    title_count = card.casefold().count(item["title"].casefold())
    price = re.compile(r"\$" + re.escape(f"{item['price']:g}") + r"(?:\.00)?(?!\d)")
    price_count = len(price.findall(card))
    platform_count = len(re.findall(r"\b" + re.escape(item["platform"]) + r"\b", card, re.I))
    return {
        "sentences": sentence_count,
        "title_count": title_count,
        "price_count": price_count,
        "platform_count": platform_count,
        "passed": 2 <= sentence_count <= 4 and title_count == price_count == platform_count == 1,
    }


def run_measurement():
    config.CACHE_ENABLED = False
    records = {number: [] for number in TARGETS}
    wardrobe = get_example_wardrobe()
    items = {item["id"]: item for item in load_listings()}

    for attempt in range(5):
        received = []
        real_outfit = agent.suggest_outfit

        def record_outfit(item, owned):
            received.append(item["id"])
            return real_outfit(item, owned)

        trace.start_trace()
        with patch.object(agent, "suggest_outfit", side_effect=record_outfit):
            matched = agent.run_agent(QUERY, wardrobe)
        call_names = re.findall(r"^\[\d+\] ([^\n]+)", trace.get_trace(), re.M)
        records[1].append({
            "passed": not matched["error"] and bool(matched["fit_card"]) and call_names == [
                "search_listings (via MCP)", "suggest_outfit", "create_fit_card"
            ],
            "selected_id": (matched["selected_item"] or {}).get("id"),
            "fit_card": matched["fit_card"],
            "error": matched["error"],
            "calls": call_names,
            "trace": trace.get_trace(),
        })
        expected = (matched["search_results"] or [{}])[0].get("id")
        selected = (matched["selected_item"] or {}).get("id")
        records[3].append({
            "passed": len(received) == 1 and received[0] == expected == selected,
            "search_id": expected, "selected_id": selected, "outfit_arg_id": received,
            "error": matched["error"],
        })

        trace.start_trace()
        with patch.object(agent, "suggest_outfit", wraps=agent.suggest_outfit) as outfit_call:
            empty = agent.run_agent(EMPTY_QUERY, wardrobe)
        records[2].append({
            "passed": not empty["search_results"] and outfit_call.call_count == 0
                      and bool(re.search(r"broader|size|price", empty["error"] or "", re.I)),
            "error": empty["error"], "outfit_calls": outfit_call.call_count,
            "trace": trace.get_trace(),
        })

        item = items[ITEM_IDS[attempt]]
        try:
            outfit = tools.suggest_outfit(item, wardrobe)
            card = tools.create_fit_card(outfit, item) if outfit else ""
            checks = card_checks(card, item)
            records[4].append({"item_id": item["id"], "outfit": outfit, "card": card, **checks})
        except ModelUnavailable as exc:
            records[4].append({"item_id": item["id"], "passed": False, "error": str(exc)})

        query = FILTER_QUERIES[attempt]
        parsed = agent._parse_query(query)
        found = tools.search_listings(**parsed)
        valid = bool(found) and all(
            item["price"] <= parsed["max_price"] and tools._size_matches(parsed["size"], item["size"])
            for item in found
        )
        records[5].append({"passed": valid, "query": query,
                           "results": [{"id": item["id"], "size": item["size"],
                                        "price": item["price"]} for item in found]})
    return records


def save(records, label):
    destination = Path(__file__).parent / "results"
    destination.mkdir(exist_ok=True)
    json_path = destination / f"{label}.json"
    md_path = destination / f"{label}.md"
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    headings = {
        1: "Full run", 2: "Empty search", 3: "Item handoff",
        4: "Fit card facts", 5: "Size and price",
    }
    lines = [f"# {label.title()} run log", "", "Five tries per criterion with the cache off.", "",
             "| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |",
             "|---|---|---|---|---|---|---|---|"]
    for number, attempts in records.items():
        count = sum(entry["passed"] for entry in attempts)
        verdict = "MET" if count >= TARGETS[number] else "MISSED"
        cells = " | ".join("PASS" if entry["passed"] else "FAIL" for entry in attempts)
        lines.append(f"| {number}. {headings[number]} | {TARGETS[number]} of 5 | {cells} | {verdict} ({count}/5) |")
    lines.extend(["", "## Recorded output", ""])
    for number, attempts in records.items():
        lines.extend([f"### Criterion {number}", ""])
        for index, entry in enumerate(attempts, 1):
            lines.extend([f"Try {index}", "", "```json",
                          json.dumps(entry, ensure_ascii=False, indent=2), "```", ""])
    md_path.write_text("\n".join(lines))
    print(md_path)
    for number, attempts in records.items():
        count = sum(entry["passed"] for entry in attempts)
        print(f"Criterion {number}  {count}/5  {'MET' if count >= TARGETS[number] else 'MISSED'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, choices=["before", "after"])
    args = parser.parse_args()
    save(run_measurement(), args.label)
