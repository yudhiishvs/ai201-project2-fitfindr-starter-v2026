# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> The command prints a matching item, an outfit idea, and a fit card. An
> impossible query prints a suggestion for changing the search.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr accepts a plain-language request for a thrift item, including an
optional size and price ceiling. It searches local listings and chooses the
strongest matching item within those filters. It uses the user's wardrobe, or
an empty wardrobe, to suggest an outfit and write a short fit card caption.
When nothing matches, it stops and suggests ways to revise the search.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the local listing data by size and inclusive price ceiling, then ranks keyword matches to the description.
- **Inputs:** `description` (`str`); `size` (`str | None`, default `None`); `max_price` (`float | None`, default `None`). A letter size matches a whole segment, so `M` matches `S/M` but `L` does not match `XL`. Numeric US shoe and waist sizes must match the full number.
- **Returns:** A `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` complete listing records, best keyword match first. Each record contains `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.
- **When it has nothing:** Returns `[]`, including when every listing fails a filter or no remaining listing shares a meaningful keyword.

### `suggest_outfit`

- **What it does:** Uses the model to suggest an outfit that includes a found item and pieces in the user's wardrobe.
- **Inputs:** `new_item` (`dict`, a complete listing record); `wardrobe` (`dict` with an `items: list[dict]` field containing wardrobe records).
- **Returns:** A nonempty `str` with one or two outfit ideas naming owned pieces when available.
- **When it has nothing:** For `wardrobe["items"] == []`, returns general styling advice for the item. If the model returns empty text, returns a short general suggestion.

### `create_fit_card`

- **What it does:** Uses the model to write a short, postable caption for the outfit and thrift find.
- **Inputs:** `outfit` (`str`, the outfit suggestion); `new_item` (`dict`, the selected listing record).
- **Returns:** A `str` caption of two to four sentences that names the item, price, platform, and outfit vibe.
- **When it has nothing:** A blank `outfit` returns an explanatory string without calling the model; an empty model response returns a retry message.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns `[]`, save a message suggesting a broader description, a different size, or a higher price ceiling in `session["error"]` and stop before `suggest_outfit`. Otherwise save the first listing as `selected_item`, use it in `suggest_outfit`, then pass the saved outfit and item to `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regular expressions extract an explicit size and an `under`/`below` price ceiling; the remaining words become the search description. This parsing uses no model call.

**What moves through the session:** `parsed` → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. Each tool's result is saved before the next tool reads it.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ .venv/bin/python app.py ask 'vintage graphic tee under $30'
  Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

  Outfit:   Pair the Graphic Tee with baggy straight-leg jeans, black combat boots, and the black crossbody bag for a classic grunge look. Alternatively, layer the vintage black denim jacket over the Graphic Tee, paired with wide-leg khaki trousers, chunky white sneakers, and the brown leather belt.

  Fit card: Scored this awesome Graphic Tee — 2003 Tour Bootleg Style on depop for just $24. Pair it with baggy jeans and combat boots for a classic grunge look. Grab it before it's gone!

1 model calls this session, 1 served from cache, 169 prompt + 47 output tokens
```

The empty-search branch used no model calls:

```
$ .venv/bin/python app.py ask 'designer ballgown size XXS under $5'
  No listings matched. Try a broader description, a different size, or a higher price ceiling.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ .venv/bin/python -c "from tools import search_listings; print([(item['id'], item['title'], item['size'], item['price']) for item in search_listings('graphic tee', size='L', max_price=30)])"
[('lst_006', 'Graphic Tee — 2003 Tour Bootleg Style', 'L', 24.0), ('lst_033', 'Vintage Band Tee — Faded Grey', 'L', 19.0), ('lst_015', 'Vintage Graphic Hoodie — Faded Black', 'L', 26.0)]
```

```
$ .venv/bin/python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[5], get_example_wardrobe()))"
Pair the Graphic Tee with baggy straight-leg jeans, black combat boots, and the black crossbody bag for a classic grunge look. Alternatively, layer the vintage black denim jacket over the Graphic Tee, paired with wide-leg khaki trousers, chunky white sneakers, and the brown leather belt.
```

```
$ .venv/bin/python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('Baggy straight-leg jeans, black combat boots, and a black crossbody bag', load_listings()[5]))"
Found this sick Graphic Tee — 2003 Tour Bootleg Style on depop for just $24. Style it with baggy straight-leg jeans, black combat boots, and a black crossbody bag for the ultimate grunge streetwear look. Grab it before it’s gone!
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked an AI assistant to draft criteria 3–5 from the assignment, then asked a model to describe exactly how someone would test all five without rewriting them.
- *What came back:* The draft covered state handoff, fit-card facts, and size and price filters. The critique found missing details for recording the item passed into `suggest_outfit` and ambiguity about the card's listings and price format.
- *What I changed:* The final criteria include a recording-wrapper procedure for state, five named listing IDs for the card check, and explicit dollar formatting and sentence endings. These were set before implementing the tools.

**Moment 2**

- *What I asked for:* I asked the assistant to implement `search_listings` and the planning loop from the starter contracts.
- *What came back:* It produced keyword-ranked results and a loop that chooses its next tool from the saved result. The starter warned that substring size checks would confuse `S` with `US 9` and `L` with `XL`.
- *What I changed:* The final implementation uses exact size segments and includes tests for size collisions, state handoff, and the empty-search stop.

**Moment 3**

- *What I asked for* I used an assistant to wire the search through MCP and set up the five criterion runs.
- *What came back* The first five runs showed two fit cards that shortened or reordered the exact listing title.
- *What I changed* I kept the original targets, changed only the fit card prompt, and ran the same checks again. The raw runs are saved in `results/`.

---

## Run Log Before

The cache was off. The five tries for criteria 1 and 3 are the same five agent runs because both criteria inspect that run. Criterion 4 uses the five listing IDs named in `criteria.md`. Criterion 5 uses its five named queries. The complete records are in [results/before.md](results/before.md).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full three tool run | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stop | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item handoff | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card facts | 4 of 5 | PASS | FAIL | PASS | FAIL | PASS | MISSED (3/5) |
| 5. Size and price filters | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Output from `measure.py` and the functions it calls is shown below. These are recorded values from one try of each criterion.

```
Criterion 1  agent.run_agent
Selected lst_006
Fit card Scored this vintage Graphic Tee — 2003 Tour Bootleg Style on Depop for just $24. Pair it with baggy straight-leg jeans and combat boots for an effortless grunge look. Grab it before it’s gone!

#graphictee #vintage #grunge #streetwear #bandtee

Criterion 2  agent.run_agent
No listings matched. Try a broader description, a different size, or a higher price ceiling.
Outfit calls 0

Criterion 3  agent.run_agent and recorded suggest_outfit argument
Search item lst_006
Selected item lst_006
Outfit argument lst_006

Criterion 4  tools.suggest_outfit then tools.create_fit_card
Item lst_006
Fit card Scored this 2003 Tour Bootleg Style Graphic Tee on Depop for just $24! Style it with baggy straight-leg jeans and black combat boots for an effortless grunge look. Grab this piece of streetwear before it's gone.
Exact title occurrences 0

Criterion 5  agent._parse_query then tools.search_listings
Query graphic tee size L under $25
Returned lst_006 size L price $24, lst_033 size L price $19
```

## Verdicts and Diagnoses

| Criterion | Target | Verdict | How I decided |
|---|---|---|---|
| 1. Full three tool run | 4 of 5 | MET 5 of 5 | Each trace shows the MCP search, outfit tool, and card tool in order, followed by a nonempty card. |
| 2. Empty search stop | 5 of 5 | MET 5 of 5 | Each search returned an empty list, the outfit tool was never called, and the message named ways to change the query. |
| 3. Selected item handoff | 5 of 5 | MET 5 of 5 | The recorded outfit argument ID matched the first search result and selected session item every time. |
| 4. Fit card facts | 4 of 5 | MISSED 3 of 5 | Two cards had zero occurrences of the exact listing title. The other required facts and sentence counts passed. |
| 5. Size and price filters | 5 of 5 | MET 5 of 5 | Every query returned at least one item and every returned size and price met the parsed limits. |

The miss was in the `create_fit_card` model output. For `lst_006`, it reordered the title words. For `lst_013`, it omitted part of the title. The prompt asked for the exact title but left the model free to start with a paraphrase. The search, session handoff, and outfit step were intact in both cases.

## Loop Trace

The first trace is one complete run from `agent.run_agent` recorded by `trace.step`. The search call went through MCP.

```
[1] search_listings (via MCP)
      in:  {"description": "vintage graphic tee", "size": "None", "max_price": "30.0"}
      out: 10 listings [{"id": "lst_006", "title": "Graphic Tee — 2003 Tour Bootleg Style"}, {"id": "lst_033", "title": "Vintage Band Tee — Faded Grey"}, {"id": "lst_015", "title": "Vintage Graphic Hoodie — Faded Black"}, {"id": "lst_002", "title": "Y2K Baby Tee — Butterfly Print"}, {"id": "lst_012", "title": "Oversized Crewneck Sweatshirt — Vintage Navy"}, {"id": "lst_030", "title": "Vintage Knit Vest — Argyle Brown/Cream"}, {"id": "lst_024", "title": "Vintage Polo Shirt — Forest Green"}, {"id": "lst_003", "title": "Oversized Flannel Shirt — Plaid Red/Black"}, {"id": "lst_013", "title": "90s Silk Slip Dress — Floral, Midi Length"}, {"id": "lst_014", "title": "Leather Belt — Brown, Braided"}]
[2] suggest_outfit
      in:  {"new_item": "{\"id\": \"lst_006\", \"title\": \"Graphic Tee — 2003 Tour Bootleg Style\", \"price\": 24.0, \"platform\": \"depop\"}", "wardrobe": "{\"items\": \"10 items: {'id': 'w_001', 'name': 'Baggy straight-leg jeans, dark wash…\"}"}
      out: Pair the Graphic Tee with your Baggy straight-leg jeans, dark wash and Black combat boots for an effortless gr…
[3] create_fit_card
      in:  {"outfit": "Pair the Graphic Tee with your Baggy straight-leg jeans, dark wash and Black combat boots for an effortless gr…", "new_item": "{\"id\": \"lst_006\", \"title\": \"Graphic Tee — 2003 Tour Bootleg Style\", \"price\": 24.0, \"platform\": \"depop\"}"}
      out: Scored this vintage Graphic Tee — 2003 Tour Bootleg Style on Depop for just $24. Pair it with baggy straight-l…
```

The impossible query stopped after search.

```
[1] search_listings (via MCP)
      in:  {"description": "designer ballgown", "size": "XXS", "max_price": "5.0"}
      out: [] (empty)
```

The server registered `search_listings` with the same input names and types as the tool inventory. `agent.run_agent` now calls it through `mcp_client.call_tool`. A direct search and an MCP search returned equal listing records for the same test query. The two model tools stayed local.

I triggered the three required failure cases. An impossible query said "No listings matched. Try a broader description, a different size, or a higher price ceiling." An empty wardrobe returned an outfit suggestion starting with "Here are two ways to style your new Light Wash, Cropped Denim Jacket" and then a fit card. A temporary invalid key produced "The model could not be reached for an outfit suggestion. Check your connection and try again." The saved key was not changed.

## The Improvement

I changed one prompt in `tools.create_fit_card` to tell the model to start its first sentence with the complete listing title in the original word order. The baseline miss pointed to title paraphrasing, so this change targeted that step. No listing data, filter, branch, or target changed.

### Run Log After

The complete records are in [results/after.md](results/after.md).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full three tool run | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stop | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item handoff | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card facts | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Size and price filters | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

The fit card check rose from 3 of 5 to 5 of 5. The other four counts stayed at 5 of 5. The after cards for `lst_006` and `lst_013` contained their full titles once each. Five tries show this run met the target, not that every future model response will.

## What's Still Broken

None of the five criteria missed in the after run. The model can still vary its wording, so the exact title check is worth repeating on later runs. The unavailable model message names a connection check and retry, while search and the saved key remain available for another attempt.

---

[How to run this project](RUNNING.md)
