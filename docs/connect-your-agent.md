# Connect your agent by hand

The prompt in the README does all of this for you. These are the same steps, for when you want to do them yourself.

1. **Create your Evaboot account** at [dash.evaboot.com](https://dash.evaboot.com/accounts/signup/?last_click_origin=ai-linkedin-connection-notes-repo) and install the [Chrome extension](https://dash.evaboot.com/install/) to connect Sales Navigator. You need an active Sales Navigator seat.
2. **Get the repo:**
   ```bash
   git clone https://github.com/evaboot-labs/ai-linkedin-connection-notes.git
   cd ai-linkedin-connection-notes
   ```
3. **Connect the Evaboot MCP server.** Copy your API key from
   [dash.evaboot.com/dash/api/](https://dash.evaboot.com/dash/api/), then:
   ```bash
   cp .env.example .env          # paste the key after EVABOOT_API_KEY=
   export EVABOOT_API_KEY=...    # same key, for your agent
   ```
   - **Claude Code** reads `.mcp.json` in this folder and uses `EVABOOT_API_KEY` from your environment. Export the key before you start Claude Code: a session that is already open does not see it.
   - **Codex:** `codex mcp add evaboot --url https://mcp.evaboot.com/mcp --bearer-token-env-var EVABOOT_API_KEY`
   - **Cursor:** add `https://mcp.evaboot.com/mcp` with the header `Authorization: Bearer <your key>`.
   - **Claude or ChatGPT on the web:** add `https://mcp.evaboot.com/mcp` as a custom connector and sign in.
4. **Say who you write to** in [`NOTES.md`](../NOTES.md), or let your agent ask you.
5. **Check** (Python 3.9+, no packages to install):
   ```bash
   python3 notes.py check queue/facts.json queue/notes.json
   ```
   It needs a first export; until then, `python3 notes.py -h` lists the commands.

Then ask your agent: **"Write my LinkedIn connection notes for today."**

Back to the [README](../README.md).
