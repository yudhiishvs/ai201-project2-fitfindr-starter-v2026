# FitFindr unit 3 plan

## Intended result

Keep the course starter and its command line interface. A user asks for a
thrift item; the agent searches the 40 local listings, suggests an outfit
using the user's wardrobe, and writes a short fit card. An empty search ends
with a useful suggestion for changing the query.

This repository is also used in unit 4. Leave the unit 4 template sections
and `RUNNING.md` in place.

## Data flow and contracts

1. `agent.py::run_agent` parses the query into `description: str`,
   `size: str | None`, and `max_price: float | None` and saves them in
   `session["parsed"]`.
2. `tools.py::search_listings` loads data with `load_listings()`, applies the
   size and inclusive price filters, ranks positive keyword matches, and
   returns at most `config.SEARCH_RESULT_LIMIT` complete listing dictionaries.
   It returns `[]` when there are no matches. Letter sizes match exact size
   segments (`M` matches `S/M`, but `L` does not match `XL`); US shoe and waist
   sizes use their full numeric tokens.
3. The loop saves that list in `session["search_results"]`. If it is empty,
   the loop sets an actionable `session["error"]` and returns without either
   model tool. Otherwise it saves the first result as `selected_item`.
4. `tools.py::suggest_outfit` uses the selected item and the wardrobe through
   `generate()`. It names owned pieces when present and requests general
   styling advice when the wardrobe is empty. Its return is a nonempty string.
5. `tools.py::create_fit_card` uses the saved outfit and item through
   `generate()` to produce a 2–4 sentence caption. Empty outfit text returns
   a descriptive message. The loop saves both model tool results in the
   session before using them and calls `trace.check_iterations` on each step.

## Implementation sequence

1. Record starter field inspection and verify `python test.py`, `app.py
   fields`, six full listings, and the starter `ask` output.
2. Fill the README Tool Inventory and branch rule. Fill five numbered
   criteria with measurable targets and reasons before implementation.
3. Write failing behavioral tests for search filters and ranking, empty
   search, session handoff, empty wardrobe, and empty outfit. Implement the
   three tools in `tools.py` until those tests pass.
4. Write a failing loop test for a matching query and its saved state.
   Implement `run_agent` until both loop paths pass.
5. Run each tool from the terminal, a full query, an impossible query, and
   `python test.py`. Paste real output into the README and describe two
   specific uses of AI truthfully. Make at least four new commits in milestone
   order before pushing the fork.

## Review focus

- A one-letter clothing size must not match shoe sizes or larger sizes.
- `under $30` must be an inclusive maximum price after parsing.
- Search ranking must put an item matching the requested type ahead of a
  generic vintage listing.
- An empty search must leave `selected_item`, `outfit_suggestion`, and
  `fit_card` unset and tell the user what to change.
- The exact selected listing must reach both model tools through the session.

## Verification commands

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python test.py
.venv/bin/python app.py ask 'vintage graphic tee under $30'
.venv/bin/python app.py ask 'designer ballgown size XXS under $5'
git diff --check
```
