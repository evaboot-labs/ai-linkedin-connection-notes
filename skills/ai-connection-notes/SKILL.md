---
name: ai-connection-notes
description: Write personalised LinkedIn connection notes with AI, safely - build a Sales Navigator search with an intent signal (changed jobs, posted recently), export the leads with Evaboot, write one note under 300 characters per lead from real profile and company data, check them, and queue them in a sheet for the user to approve and send. The agent never sends anything on LinkedIn. Use when the user asks to automate LinkedIn prospecting, write connection requests or notes with AI, or build a daily LinkedIn outreach queue.
---

# AI connection notes

This skill runs inside a clone of https://github.com/evaboot-labs/ai-linkedin-connection-notes: it uses the repo's `notes.py`, `NOTES.md` and `docs/`. If `notes.py` is not in the working directory, clone the repo and work from there.

You do the Sales Navigator and Evaboot work through the Evaboot MCP server (`https://mcp.evaboot.com/mcp`). Every tool named below is an Evaboot MCP tool. You write the notes yourself. `notes.py` makes no network calls: it adds filters to the search URL, turns the export into facts, checks the notes and builds the sheet.

## Rules

- **Never send anything on LinkedIn**, and never drive LinkedIn in the user's browser. The user sends the approved notes by hand or through their outreach tool. This keeps their account safe.
- Confirm with the user before every call that writes to their seat or spends credits: `export_sn_search_or_list`, `save_search`, `create_recurring_export`. Show the count and the cost (1 credit per lead), then wait for a yes.
- Write each note only from that lead's facts in `queue/facts.json`. Never add a fact from memory or the web.
- Print every Sales Navigator URL as a Markdown link with the URL in angle brackets: `[Open in Sales Navigator](<url>)`.

## Step 0: check the setup

1. If the Evaboot MCP tools are not in this session, walk the user through `docs/connect-your-agent.md`, then ask them to restart the agent from this folder: `EVABOOT_API_KEY` is read only when the agent starts.
2. Otherwise call `verify_token` and `get_daily_export_quota`. If `has_valid_salesnav` is false, ask the user to sign in to Evaboot in Chrome, open any Sales Navigator search with the Evaboot extension, and click Export with Evaboot (opening the export page is enough), then call the quota again.
3. Run `mkdir -p data queue`. Both folders are git-ignored.
4. Read `NOTES.md`. If it says `Status: EXAMPLE`, ask the user who they target, which signal, how many a day, and who they are. Rewrite the file and set `Status: yours`.

## Step 1: build the search

1. Call `build_sn_search_from_prompt` with **people only**: titles, seniority, geography and the signal in plain words, for example `Heads of Sales and VPs of Sales in the United Kingdom who changed jobs recently`. Pass `max_results` = the daily number from `NOTES.md`. Never put an industry or company size in this request: that starts a company-first crawl.
2. Poll `get_search_build` until the status is not `building`. Check `filters_used` carries the signal (`recently_changed_jobs: true`, or `posted_on_linkedin: true`). With the posted signal, ask the builder to exclude marketing titles: marketing leaders post more and fill the list.
3. If `NOTES.md` names an industry or a company size, add them: `python3 notes.py lead-url "<url>" --industry 4 --headcount D E`. Codes are in the `lead_url` docstring.
4. Call `search_sn_leads` on the final URL with `count: 25`. It is free. Show the total and the first titles and companies. If the list is noisy (coaches, consultants, unrelated industries), tighten the filters and preview again.

## Step 2: export

If the preview total is below the daily number, export what there is. On a yes, call `export_sn_search_or_list` on the search URL with `max_results` = the daily number and a clear `search_name`. Poll `get_export` until the status is `EXECUTED`. Save the JSON to `data/export.json`, then:

```bash
python3 notes.py facts data/export.json > queue/facts.json
```

## Step 3: write the notes

Read `NOTES.md` again, then write `queue/notes.json`: a list with one entry per lead in `facts.json`, either `{"id", "hook", "note"}` or `{"id", "skip": true, "reason"}`.

- The hook is the fact the note rests on, in a few words ("New role, team up 117% in a year").
- Good hooks, strongest first: a new role (`new_in_role`, `months_in_role`), company growth (`company_growth_1y_pct`), one concrete line of the lead's own `headline` or `summary`. `posts` is usually "Low": do not mention posts unless it is not.
- Skip a lead who is not new in role and whose profile has nothing concrete ("NA" summary, a bare headline).

Then check:

```bash
python3 notes.py check queue/facts.json queue/notes.json
```

Fix every `FAIL` and run it again.

## Step 4: queue for approval

```bash
python3 notes.py sheet queue/facts.json queue/notes.json > queue/queue.csv
```

Put it where the user reviews: a Google Sheet when the session has a Google Drive tool, otherwise give them the path of the CSV to open in any spreadsheet app. Ask them to read the notes, edit any they want, and mark the `Send` column.

## Step 5: sending, by the user

Tell the user the two ways to send, and do neither yourself:

- **By hand:** open each LinkedIn URL, click Connect, Add a note, paste. Twenty a day takes about ten minutes.
- **With an outreach tool** that has a LinkedIn step (lemlist, or any other): import `queue/queue.csv` and map the `Connection note` column to the note field of the invite step.

Remind them to stay at the daily number in `NOTES.md` and to raise it only if their acceptance rate holds.

## Step 6 (optional): every day or week

Offer to repeat the search: `save_search`, then `create_recurring_export` on it (daily or weekly). Each run returns only new people, so the queue refills with fresh leads. Each run spends credits; say so before creating it. Then run steps 2 to 4 on each new export.
