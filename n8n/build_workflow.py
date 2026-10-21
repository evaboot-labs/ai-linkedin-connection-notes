"""Builds n8n/ai-linkedin-connection-notes.json. Run: python3 n8n/build_workflow.py

A form takes a Sales Navigator search URL and a lead count. Evaboot exports the leads, Claude writes one
note per lead from the same facts as notes.py, a Code node applies the same checks, and the notes land in
your Google Sheet for you to approve and send. Nothing is sent on LinkedIn.
"""
import json
import uuid
from pathlib import Path

MCP = "https://mcp.evaboot.com/mcp"
EVABOOT_CRED = {"httpBearerAuth": {"id": "", "name": "Evaboot MCP (Bearer)"}}
ANTHROPIC_CRED = {"anthropicApi": {"id": "", "name": "Anthropic"}}
SHEETS_CRED = {"googleSheetsOAuth2Api": {"id": "", "name": "Google Sheets account"}}
MODEL = "claude-sonnet-5-5"

nodes, connections = [], {}


def node(name, type_, version, params, pos, creds=None, **extra):
    n = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": type_,
         "typeVersion": version, "position": pos, **extra}
    if creds:
        n["credentials"] = creds
    nodes.append(n)


def link(a, b, kind="main", out=0):
    connections.setdefault(a, {}).setdefault(kind, [])
    while len(connections[a][kind]) <= out:
        connections[a][kind].append([])
    connections[a][kind][out].append({"node": b, "type": kind, "index": 0})


def mcp_call(name, tool, json_expr, pos):
    node(name, "@n8n/n8n-nodes-langchain.mcpClient", 1.1, {
        "endpointUrl": MCP, "authentication": "bearerAuth",
        "tool": {"__rl": True, "mode": "list", "value": tool, "cachedResultName": tool},
        "inputMode": "json", "jsonInput": json_expr, "options": {"timeout": 120000},
    }, pos, EVABOOT_CRED)


def code(name, js, pos):
    node(name, "n8n-nodes-base.code", 2, {"jsCode": js}, pos)


FACTS_JS = r"""
// Same as notes.py facts: one entry per lead, real fields only, tenure = years * 12 + months.
const num = v => { const n = parseFloat(String(v ?? '').replace(/,/g, '')); return isNaN(n) ? null : n; };
const words = s => String(s || '').split(/\s+/).join(' ').trim();
const prospects = $json.structuredContent.result.prospects || [];
if (!prospects.length) throw new Error('The export returned no leads. Check the search in Sales Navigator.');
const leads = prospects.map(p => {
  const months = (num(p['Years in Position']) || 0) * 12 + (num(p['Months in Position']) || 0);
  return {
    id: p['Linkedin URL Unique ID'] || p['Linkedin URL Public'] || p['Full Name'],
    first_name: p['First Name'] || '', name: p['Full Name'] || '',
    title: String(p['Current Job'] || '').trim(), company: p['Company Name'] || '',
    months_in_role: months,
    new_in_role: ['true', 'yes', '1'].includes(String(p['Has New Position']).toLowerCase()) || months < 6,
    headline: words(p['Profile Headline']), summary: words(p['Profile Summary']).slice(0, 700),
    posts: p['Posting Frequency'] || '',
    company_description: words(p['Company Description']).slice(0, 400),
    company_growth_1y_pct: num(p['Company Employee Growth 1 Year (%)']),
    linkedin: p['Linkedin URL Public'] || '',
  };
});
return [{ json: { leads } }];
"""

ROWS_JS = r"""
// Same checks as notes.py check: 300 characters, a named hook, a reason for every skip.
const LIMIT = 300;
const leads = $('Lead facts').first().json.leads;
const notes = Object.fromEntries($json.output.notes.map(n => [n.id, n]));
return leads.map(l => {
  const n = notes[l.id] || { skip: true, reason: 'no note returned' };
  let note = n.skip ? '' : (n.note || '');
  let hook = n.skip ? `SKIP: ${n.reason || 'no reason given'}` : (n.hook || '');
  if (note.length > LIMIT) { hook = `SKIP: note was ${note.length} characters`; note = ''; }
  if (!n.skip && !n.hook) { hook = 'SKIP: no hook named'; note = ''; }
  return { json: {
    'Name': l.name, 'Title': l.title, 'Company': l.company, 'Hook': hook,
    'Connection note': note, 'Characters': note.length || '', 'LinkedIn': l.linkedin, 'Send (yes/no)': '',
  } };
});
"""

NOTES_SYSTEM = """You write LinkedIn connection notes for a salesperson, from the JSON leads you are given. Use only those facts: never add anything from memory.

For each lead, return either {id, hook, note} or {id, skip: true, reason}.
Rules:
1. 300 characters at most, ideally 150 to 220. Start with "Hi <first_name>,".
2. One real hook per note, named in "hook": a new role (new_in_role, months_in_role), company growth (company_growth_1y_pct, always with "in a year"), or one concrete line of the lead's own headline or summary. Do not mention posts if posts is "Low".
3. No pitch, no link, no product name, no meeting request. No flattery beyond a short congratulation on a new role.
4. Vary the ending: no ending phrase on more than a third of the notes.
5. Skip a lead who is not new in role and whose profile has nothing concrete ("NA" summary, a bare headline), with the reason."""

node("Search to work", "n8n-nodes-base.formTrigger", 2.2, {
    "formTitle": "Write LinkedIn connection notes",
    "formDescription": "Paste a Sales Navigator people search with an intent filter (changed jobs, posted on LinkedIn). Evaboot exports the leads (1 credit per lead) and Claude writes one note per lead into your sheet. Nothing is sent on LinkedIn.",
    "formFields": {"values": [
        {"fieldLabel": "Sales Navigator search URL", "fieldType": "textarea", "requiredField": True},
        {"fieldLabel": "Leads to export", "fieldType": "number", "requiredField": True, "placeholder": "20"},
    ]},
    "responseMode": "lastNode", "options": {},
}, [0, 0])
node("Your settings", "n8n-nodes-base.set", 3.4, {"assignments": {"assignments": [
    {"id": str(uuid.uuid4()), "name": "sheet_url", "type": "string", "value": "PASTE_YOUR_GOOGLE_SHEET_URL_WITH_GID"},
]}, "includeOtherFields": True, "options": {}}, [220, 0])
mcp_call("Export with Evaboot", "export_sn_search_or_list",
         "={{ JSON.stringify({ linkedin_url: $('Search to work').first().json['Sales Navigator search URL'].trim(), "
         "max_results: Number($('Search to work').first().json['Leads to export']) || 20, "
         "search_name: 'Connection notes ' + $now.toFormat('yyyy-MM-dd') }) }}", [440, 0])
node("Wait 30 s", "n8n-nodes-base.wait", 1.1, {"amount": 30}, [660, 0])
mcp_call("Check the export", "get_export",
         "={{ JSON.stringify({ extraction_id: $('Export with Evaboot').first().json.structuredContent.result.extraction_id }) }}",
         [880, 0])
node("Done?", "n8n-nodes-base.if", 2.2, {"conditions": {
    "options": {"caseSensitive": True, "typeValidation": "loose", "version": 2},
    "conditions": [{"id": str(uuid.uuid4()), "leftValue": "={{ $json.structuredContent.result.status }}",
                    "rightValue": "EXECUTED", "operator": {"type": "string", "operation": "equals"}}],
    "combinator": "and"}, "options": {}}, [1100, 0])
code("Lead facts", FACTS_JS, [1320, -100])
node("Write the notes", "@n8n/n8n-nodes-langchain.agent", 2.2, {
    "promptType": "define", "text": "={{ JSON.stringify($json.leads) }}", "hasOutputParser": True,
    "options": {"systemMessage": NOTES_SYSTEM, "maxIterations": 3},
}, [1560, -100], retryOnFail=True, maxTries=3, waitBetweenTries=2000)
node("Claude", "@n8n/n8n-nodes-langchain.lmChatAnthropic", 1.3, {
    "model": {"__rl": True, "mode": "list", "value": MODEL, "cachedResultName": MODEL},
    "options": {"maxTokensToSample": 8000},
}, [1520, 120], ANTHROPIC_CRED)
node("Notes", "@n8n/n8n-nodes-langchain.outputParserStructured", 1.3, {
    "schemaType": "manual",
    "inputSchema": json.dumps({"type": "object", "required": ["notes"], "properties": {"notes": {
        "type": "array", "items": {"type": "object", "required": ["id"], "properties": {
            "id": {"type": "string"}, "hook": {"type": "string"}, "note": {"type": "string"},
            "skip": {"type": "boolean"}, "reason": {"type": "string"}}}}}}, indent=2),
}, [1680, 120])
code("Check each note", ROWS_JS, [1880, -100])
node("Add to the notes sheet", "n8n-nodes-base.googleSheets", 4.7, {
    "operation": "append",
    "documentId": {"__rl": True, "mode": "url", "value": "={{ $('Your settings').first().json.sheet_url }}"},
    "sheetName": {"__rl": True, "mode": "url", "value": "={{ $('Your settings').first().json.sheet_url }}"},
    "columns": {"mappingMode": "autoMapInputData", "value": {}, "matchingColumns": [], "schema": []},
    "options": {},
}, [2100, -100], SHEETS_CRED)
node("Notes ready", "n8n-nodes-base.form", 2.3, {
    "operation": "completion", "completionTitle": "Your notes are in the sheet",
    "completionMessage": "Read them, edit any you want, and send the ones you approve by hand or through your outreach tool.",
    "options": {}}, [2320, -100], executeOnce=True)

for a, b in [("Search to work", "Your settings"), ("Your settings", "Export with Evaboot"),
             ("Export with Evaboot", "Wait 30 s"), ("Wait 30 s", "Check the export"), ("Check the export", "Done?"),
             ("Lead facts", "Write the notes"), ("Write the notes", "Check each note"),
             ("Check each note", "Add to the notes sheet"), ("Add to the notes sheet", "Notes ready")]:
    link(a, b)
link("Done?", "Lead facts", out=0)
link("Done?", "Wait 30 s", out=1)
link("Claude", "Write the notes", "ai_languageModel")
link("Notes", "Write the notes", "ai_outputParser")

workflow = {"name": "AI LinkedIn connection notes (Evaboot MCP + Claude)", "nodes": nodes,
            "connections": connections, "settings": {"executionOrder": "v1"}, "pinData": {}}
out = Path(__file__).with_name("ai-linkedin-connection-notes.json")
out.write_text(json.dumps(workflow, indent=2, ensure_ascii=False) + "\n")
print(out, len(nodes), "nodes")
