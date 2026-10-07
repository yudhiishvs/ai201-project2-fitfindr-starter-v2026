"""
The three FitFindr tools.

Each one is a standalone function that can be called and tested apart from the
planning loop. Model-backed tools call the shared generate adapter.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

The README Tool Inventory records each tool's inputs, output, and empty case.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


_SEARCH_FILLER = {
    "a", "an", "and", "for", "in", "looking", "me", "my", "of", "on",
    "some", "the", "to", "want", "with",
}


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.casefold())) - _SEARCH_FILLER


def _size_matches(requested: str, listing_size: str) -> bool:
    """Match complete clothing or numeric size tokens, never substrings."""
    wanted = requested.strip().upper()
    label = listing_size.split("(", 1)[0].strip().upper()

    shoe = re.fullmatch(r"(?:US\s*)?(\d+(?:\.\d+)?)", wanted)
    if shoe:
        listed_shoe = re.fullmatch(r"US\s+(\d+(?:\.\d+)?)", label)
        return bool(listed_shoe and float(shoe.group(1)) == float(listed_shoe.group(1)))

    if re.fullmatch(r"[WL]\d+", wanted):
        return bool(re.search(rf"\b{re.escape(wanted)}\b", label))

    letter_sizes = {"XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"}
    if wanted in letter_sizes:
        return wanted in re.split(r"[/\s]+", label)

    return wanted == label


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    Ranking weights title matches above style tags and description matches.
    Equal scores retain the order of the source data.
    """
    terms = _words(description)
    if not terms:
        return []

    scored = []
    for position, item in enumerate(load_listings()):
        if max_price is not None and item["price"] > max_price:
            continue
        if size is not None and not _size_matches(size, item["size"]):
            continue

        title = _words(item["title"])
        tags = _words(" ".join(item["style_tags"]))
        details = _words(item["description"])
        other = _words(" ".join([item["category"], *item["colors"], item["brand"] or ""]))
        score = (
            4 * len(terms & title)
            + 3 * len(terms & tags)
            + len(terms & details)
            + len(terms & other)
        )
        if score:
            scored.append((score, position, item))

    scored.sort(key=lambda match: (-match[0], match[1]))
    return [item for _, _, item in scored[:config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    If the model returns empty text, a short general suggestion is returned.
    """
    title = new_item["title"]
    details = (
        f"New item: {title}. Size: {new_item['size']}. "
        f"Colors: {', '.join(new_item['colors'])}. "
        f"Style: {', '.join(new_item['style_tags'])}."
    )
    owned = wardrobe.get("items", [])

    if owned:
        wardrobe_lines = [
            f"- {piece['name']} ({piece['category']}; "
            f"colors: {', '.join(piece['colors'])}; "
            f"style: {', '.join(piece['style_tags'])})"
            for piece in owned
        ]
        prompt = (
            f"{details}\n\nWardrobe pieces the user already owns:\n"
            + "\n".join(wardrobe_lines)
            + "\n\nSuggest one or two wearable outfits featuring the new item. "
              "Name specific owned pieces exactly as listed. Keep it to two short sentences."
        )
    else:
        prompt = (
            f"{details}\n\nThe user has no saved wardrobe items. "
            "Give one or two general styling ideas for the new item, "
            "without claiming the user already owns any pieces."
        )

    response = generate(
        prompt,
        system="You are a practical thrift stylist. Use only the item and wardrobe facts provided.",
    ).strip()
    if response:
        return response
    if owned:
        return f"Try {title} with {owned[0]['name']} and simple accessories."
    return f"Try {title} with simple basics and shoes that suit its colors."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    An empty model response returns a retry message.
    """
    if not outfit.strip():
        return "Cannot create a fit card without an outfit suggestion."

    title = new_item["title"]
    price = f"${new_item['price']:g}"
    platform = new_item["platform"]
    prompt = (
        f"Thrift find title: {title}\n"
        f"Price: {price}\n"
        f"Platform: {platform}\n"
        f"Outfit idea: {outfit}\n"
        f"Style tags: {', '.join(new_item['style_tags'])}\n\n"
        "Write a caption someone would actually post. Use two to four short "
        "sentences. Start the first sentence with the exact title shown above, "
        "with every word in the same order. Include the price and platform once each. "
        "Describe the outfit vibe using the given idea. Do not invent a brand "
        "or any details missing from the listing."
    )
    response = generate(
        prompt,
        system="Write a concise, natural social caption grounded in the provided listing.",
    ).strip()
    return response or "I couldn't create a fit card just now. Please try again."
