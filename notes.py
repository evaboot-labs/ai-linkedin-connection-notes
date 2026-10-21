"""Helpers for the AI connection-note agent. No network calls: the agent exports leads through the
Evaboot MCP, writes the notes itself, and uses these commands to keep the facts and the checks the same
on every run.

    python3 notes.py lead-url "<url>" --industry 4 --headcount D E  add industry and company size to a search
        industry 4 = Software Development; headcount B 1-10, C 11-50, D 51-200, E 201-500,
        F 501-1000, G 1001-5000, H 5001-10000, I 10001+
    python3 notes.py facts <export.json> > queue/facts.json        the real hooks per lead
    python3 notes.py check <facts.json> <notes.json>               300-character limit, no invented hooks
    python3 notes.py sheet <facts.json> <notes.json> > queue/queue.csv
"""
import argparse
import csv
import json
import sys

LIMIT = 300  # LinkedIn's limit for a connection note on most plans; free accounts get fewer per month.


def lead_url(url, industries, headcounts):
    """The search builder leaves industry and size out of people searches (asking for them starts a
    company-first crawl); add them to the URL it returns. Codes: industry 4 = Software Development;
    headcount B 1-10, C 11-50, D 51-200, E 201-500, F 501-1000, G 1001-5000, H 5001-10000, I 10001+."""
    def block(kind, ids):
        vals = "%2C".join(f"(id%3A{i}%2CselectionType%3AINCLUDED)" for i in ids)
        return f"%2C(type%3A{kind}%2Cvalues%3AList({vals}))"
    if not url.endswith("))"):
        sys.exit("expected a Sales Navigator people search URL ending in ))")
    extra = (block("INDUSTRY", industries) if industries else "") + (block("COMPANY_HEADCOUNT", headcounts) if headcounts else "")
    return url[:-2] + extra + "))"


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def facts(path):
    """export.json = the Evaboot export (get_export or the API). One entry per lead, only real fields."""
    out = []
    for p in json.load(open(path)).get("prospects") or []:
        months = (num(p.get("Years in Position")) or 0) * 12 + (num(p.get("Months in Position")) or 0)
        out.append({
            "id": p.get("Linkedin URL Unique ID") or p.get("Linkedin URL Public") or p.get("Full Name"),
            "first_name": p.get("First Name") or "",
            "name": p.get("Full Name") or "",
            "title": (p.get("Current Job") or "").strip(),
            "company": p.get("Company Name") or "",
            "months_in_role": months,
            "new_in_role": str(p.get("Has New Position")).lower() in ("true", "yes", "1") or months < 6,
            "months_at_company": (num(p.get("Years in Company")) or 0) * 12 + (num(p.get("Months in Company")) or 0),
            "headline": " ".join((p.get("Profile Headline") or "").split()),
            "summary": " ".join((p.get("Profile Summary") or "").split())[:700],
            "posts": p.get("Posting Frequency") or "",
            "company_description": " ".join((p.get("Company Description") or "").split())[:400],
            "company_growth_1y_pct": num(p.get("Company Employee Growth 1 Year (%)")),
            "linkedin": p.get("Linkedin URL Public") or "",
        })
    return out


def check(facts_path, notes_path):
    """Every lead gets a note or a skip with a reason; no note over the limit."""
    leads = {f["id"]: f for f in json.load(open(facts_path))}
    notes = json.load(open(notes_path))
    problems = []
    for n in notes:
        if n["id"] not in leads:
            problems.append(f"unknown lead {n['id']}")
        elif n.get("skip"):
            if not n.get("reason"):
                problems.append(f"{leads[n['id']]['name']}: skip without a reason")
        elif len(n.get("note", "")) > LIMIT:
            problems.append(f"{leads[n['id']]['name']}: {len(n['note'])} characters, limit {LIMIT}")
        elif not n.get("hook"):
            problems.append(f"{leads[n['id']]['name']}: no hook named")
    endings = {}
    for n in notes:
        if not n.get("skip"):
            last = n.get("note", "").rstrip(".!? ").split(". ")[-1].lower()
            endings[last] = endings.get(last, 0) + 1
    written_count = sum(endings.values())
    for e, c in endings.items():
        if written_count >= 6 and c > written_count / 3:
            problems.append(f'{c} of {written_count} notes end with "{e}": vary the ending')
    missing = set(leads) - {n["id"] for n in notes}
    problems += [f"no note for {leads[i]['name']}" for i in missing]
    for p in problems:
        print("FAIL", p)
    written = sum(1 for n in notes if not n.get("skip"))
    print(f"{written} notes, {len(notes) - written} skipped, {len(problems)} problems")
    return 1 if problems else 0


def sheet(facts_path, notes_path):
    notes = {n["id"]: n for n in json.load(open(notes_path))}
    w = csv.writer(sys.stdout)
    w.writerow(["Name", "Title", "Company", "Hook", "Connection note", "Characters", "LinkedIn", "Send (yes/no)"])
    for f in json.load(open(facts_path)):
        n = notes.get(f["id"], {})
        note = "" if n.get("skip") else n.get("note", "")
        hook = f"SKIP: {n.get('reason', '')}" if n.get("skip") else n.get("hook", "")
        w.writerow([f["name"], f["title"], f["company"], hook, note, len(note) or "", f["linkedin"], ""])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("lead-url"); a.add_argument("url")
    a.add_argument("--industry", nargs="*", default=[]); a.add_argument("--headcount", nargs="*", default=[])
    a = sub.add_parser("facts"); a.add_argument("export")
    a = sub.add_parser("check"); a.add_argument("facts"); a.add_argument("notes")
    a = sub.add_parser("sheet"); a.add_argument("facts"); a.add_argument("notes")
    args = ap.parse_args()
    if args.cmd == "lead-url":
        print(lead_url(args.url, args.industry, args.headcount))
    elif args.cmd == "facts":
        print(json.dumps(facts(args.export), indent=2, ensure_ascii=False))
    elif args.cmd == "check":
        sys.exit(check(args.facts, args.notes))
    else:
        sheet(args.facts, args.notes)


if __name__ == "__main__":
    main()
