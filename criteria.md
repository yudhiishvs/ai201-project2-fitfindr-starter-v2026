# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
Search uses keyword overlap rather than semantic search, so one phrasing may
rank poorly or miss. The two model calls can also fail or return weak text; four
successful runs still sets a meaningful reliability target.

**Test setup:** Use `vintage graphic tee under $30` and record calls to the
three tool functions while running the agent five times.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path uses a deterministic empty-list check and makes no model calls after
search. It should stop correctly every time, and the message should tell the
user to broaden the description, change the size, or raise the price ceiling.

**Test setup:** Use `designer ballgown size XXS under $5` and record whether
`suggest_outfit` is called on each of five runs.

---

## 3. The selected listing reaches the outfit tool unchanged

In five runs of `vintage graphic tee under $30`, record the `new_item["id"]`
argument with a wrapper around `agent.suggest_outfit`. That ID must equal both
`session["search_results"][0]["id"]` and
`session["selected_item"]["id"]` — 5 of 5 runs.

**Why this target:**
The loop copies a selected listing through session state without a model
transformation, so there is no useful reason to allow an item mismatch.

---

## 4. The fit card keeps its facts while the wording varies

For listings `lst_004`, `lst_006`, `lst_007`, `lst_013`, and `lst_019`, call
`suggest_outfit` with the example wardrobe and pass its nonempty result to
`create_fit_card`. At least 4 of 5 cards must have two to four sentences
(counting `.`, `!`, and `?` followed by whitespace or end of text as endings)
and contain the item's exact title,
price formatted as `$24` or `$24.00` for a `24.0` price, and platform name
case-insensitively, each exactly once.

**Why this target:**
The model can vary its wording, but those three facts must remain grounded in
the selected listing. Four of five is demanding without treating one model
formatting miss as a total failure.

---

## 5. Size and price filters are reliable

For each of these five queries, search returns at least one listing and every
returned listing's `price` field is at or below the stated cap, and its `size`
field contains the requested letter size as a whole slash-delimited segment
or equals the requested US shoe size exactly (so `US 8.5` fails `size 8`) —
5 of 5 queries: `graphic tee size L under $25`, `track jacket size M under
$50`, `platform sneakers size 8 under $50`, `denim jacket size S under $50`,
and `silk slip dress size M under $40`.

**Why this target:**
Size and price are explicit structured filters over local data. A wrong size
or an over-budget suggestion wastes the user's time, and there is no model
variability in this part of the system.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
