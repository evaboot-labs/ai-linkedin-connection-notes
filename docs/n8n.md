# Run it in n8n

[`n8n/ai-linkedin-connection-notes.json`](../n8n/ai-linkedin-connection-notes.json) is the same agent for n8n. You paste a Sales Navigator search into a form, and the notes land in your Google Sheet.

## What runs

1. **Search to work** (form): a Sales Navigator people search URL with an intent filter, and how many leads to export.
2. **Export with Evaboot** (MCP Client): exports that many leads with their profile and company data. 1 credit per lead.
3. **Lead facts** (Code): the same facts as `notes.py`.
4. **Write the notes** (AI Agent with Claude): one note per lead, or a skip with a reason, by the rules in `NOTES.md`.
5. **Check each note** (Code): the 300-character limit and a named hook; anything else becomes a skip.
6. **Add to the notes sheet** (Google Sheets): one row per lead, ready for you to approve and send.

## Set it up

1. **Build the search** in Sales Navigator, or ask your AI Agent to build it with the skill (step 1). Use one intent filter: *Changed jobs* or *Posted on LinkedIn*. Copy the URL.
2. **Make the sheet:** a Google Sheet with this header row:
   `Name, Title, Company, Hook, Connection note, Characters, LinkedIn, Send (yes/no)`
3. **Import** the JSON in n8n: *Workflows > Import from file*.
4. **Add three credentials:**
   - **Bearer Auth** named `Evaboot MCP (Bearer)`: your key from [dash.evaboot.com/dash/api/](https://dash.evaboot.com/dash/api/). Select it on both MCP Client nodes.
   - **Anthropic** on the Claude node.
   - **Google Sheets** on **Add to the notes sheet**.
5. **Fill in Your settings:** `sheet_url` is your sheet's URL with its `gid` (open the tab, copy the address bar).
6. **Test:** click *Execute workflow*, paste your search, ask for 5 leads, and read the notes in the sheet.

## Good to know

- Each run exports the top of the search again. Run it on a fresh search, or move to a recurring export in Evaboot once you are happy with the notes.
- The AI step retries up to 3 times: Claude sometimes returns an empty answer.
- With the *Posted on LinkedIn* signal, add `NOT Marketing` to the title filter: marketing leaders post more and fill the list.
- Nothing is sent on LinkedIn. You send the approved notes by hand or through your outreach tool.

Back to the [README](../README.md).
