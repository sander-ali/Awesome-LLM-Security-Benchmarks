# Contributing to Awesome LLM Security Benchmarks

Thanks for helping improve the catalog! 🎉

This repository is **data-driven**: the README, the per-category pages under
`docs/`, and the `CSV`/`YAML` exports are all **generated** from a single source
of truth, [`data/benchmarks.json`](data/benchmarks.json). To keep everything
consistent, please **edit the data and regenerate** rather than hand-editing the
generated Markdown.

---

## Ground rules

1. **No fabrication.** Every field must be traceable to a primary source (the
   benchmark's paper or official site). Do not invent numbers, venues, author
   names, or findings. If you are unsure, link the source and leave the summary
   conservative.
2. **Link primary sources.** Each entry needs a working **Website / Code** link
   and a **Paper** link (arXiv, ACL Anthology, OpenReview, ACM DL, publisher, or
   an official project page).
3. **Attribute.** Summaries should describe what the benchmark *measures and
   reports*, phrased so credit stays with the original authors.
4. **Responsible content.** Do **not** add raw jailbreak prompts, attack code,
   poisoned models, or other harmful payloads. Link to the official repository or
   dataset instead. See [SECURITY.md](SECURITY.md).
5. **Pick an existing category** where one fits. Propose a new category only in
   an issue first, so we can agree on scope.

---

## Adding or correcting an entry

### Option A — edit the JSON directly (fastest)

1. Open [`data/benchmarks.json`](data/benchmarks.json).
2. Add a new object to the `benchmarks` array (or fix an existing one) using the
   schema below. Give it the next `id` (1-based, unique).
3. If you add a brand-new category, also add it to the `categories` array with a
   `name`, URL-safe `slug`, an `emoji`, and a `count` (the build recomputes
   counts, but keep the array in display order).
4. Regenerate all derived files:

   ```bash
   python3 scripts/build.py
   ```

5. Commit **both** `data/benchmarks.json` and the regenerated files
   (`README.md`, `docs/*.md`, `data/benchmarks.csv`, `data/benchmarks.yaml`).

### Option B — update the source workbook (for bulk edits)

If you are changing many rows at once, edit a copy of the spreadsheet under
[`data/source/`](data/source/) and re-run the parser, then the builder:

```bash
python3 scripts/parse_source_xlsx.py   # xlsx  -> data/benchmarks.json
python3 scripts/build.py               # json  -> README, docs, CSV, YAML
```

> Note: `parse_source_xlsx.py` applies only the conservative normalizations
> documented in the README's **Provenance & Data Notes** (separator tidy-ups and
> a few obvious typo fixes in the free-text `Year · Venue / Origin` column). It
> copies `Details`, `Security Type Targeted`, names, categories, and hyperlink
> targets **verbatim**. If you need a per-row cleanup that the parser does not
> cover, prefer Option A so the intent is explicit in the committed JSON.

---

## Record schema

```jsonc
{
  "id": 42,                         // unique 1-based integer
  "name": "ExampleBench",           // benchmark / dataset / framework name
  "category": "Prompt Injection",   // must match an entry in `categories`
  "category_slug": "prompt-injection",
  "year": "2025",                   // display year (or a range like "2020–2024")
  "year_sort": 2025,                // integer for sorting (range start if a range)
  "year_venue_origin": "2025 · NeurIPS · A. Author et al.",   // cleaned
  "year_venue_origin_source": "2025 NeurIPS A. Author et al.",// verbatim source (optional but preferred)
  "website": { "label": "github.com/org/ExampleBench", "url": "https://github.com/org/ExampleBench" },
  "paper":   { "label": "arXiv 2501.00000",            "url": "https://arxiv.org/abs/2501.00000" },
  "details": "One-paragraph, factual summary of what it measures and its headline findings.",
  "security_type": "Short phrase(s) naming the risk(s) targeted."
}
```

Field-by-field meaning is documented in the README under
[Data Files & Schema](README.md#data-files--schema).

---

## Validation checklist before you open a PR

- [ ] `python3 scripts/build.py` runs without errors.
- [ ] `data/benchmarks.json` is valid JSON and the new/edited record has a unique `id`.
- [ ] The regenerated `README.md`, `docs/*.md`, `data/benchmarks.csv`, and
      `data/benchmarks.yaml` are all included in the commit.
- [ ] Both the **Website / Code** and **Paper** links resolve.
- [ ] The summary is factual and attributable; no invented statistics.
- [ ] No harmful payloads were added (links only).
- [ ] You chose an existing category, or discussed a new one in an issue first.

---

## Pull request process

1. Fork the repo and create a topic branch.
2. Make your data change and run `python3 scripts/build.py`.
3. Open a PR describing **what** you added/changed and **the primary source** for
   any new factual claims (a link to the paper is ideal).
4. A maintainer will review for accuracy, sourcing, and scope.

Small corrections (typos, dead links, a clearer sentence) are very welcome. When
in doubt, open an issue first.

---

## Ideas that are especially welcome

- Fixing dead or redirected links.
- Adding missing official code/dataset URLs.
- Correcting a venue, year, or author list against the published paper.
- New high-quality benchmarks in under-represented categories (e.g. multimodal
  safety, over-refusal, privacy/membership inference, watermarking, agentic
  misalignment).

Thank you for keeping this catalog accurate and useful! 🛡️
