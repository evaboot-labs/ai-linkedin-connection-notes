# Agent instructions

This repo is an AI connection-note agent for LinkedIn prospecting. It builds a Sales Navigator search with an intent signal, exports the leads with Evaboot, writes one short connection note per lead from real profile and company data, and puts the notes in a sheet for the user to approve. The user sends the notes; the agent never sends anything on LinkedIn. When the user asks for LinkedIn connection notes, a prospecting queue, or personalised connection requests:

1. Follow the skill in `skills/ai-connection-notes/SKILL.md` step by step.
2. Read `NOTES.md` for who to target and the writing rules. If it still holds the example, ask the user and update it.
3. Use `notes.py` for the search filters, the facts, the checks and the sheet. It makes no network calls; the Evaboot MCP server does the Sales Navigator work (`.mcp.json`).
4. If the user is not connected yet, follow `docs/connect-your-agent.md` with them.
5. If the user wants n8n instead, follow `docs/n8n.md` with them one step at a time: you cannot click inside n8n, so say exactly what to do and wait for their confirmation.

Confirm with the user before every call that saves, sends or changes anything, and before every export: it spends 1 Evaboot credit per lead. Never send a LinkedIn message or connection request, and never automate LinkedIn in the user's browser. Never ask for or handle another tool's API key. Never commit `.env`, `data/` or `queue/`: they hold real people's data.
