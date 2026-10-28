"""Classify forum comments as acceptable, toxic or spam with Cloudflare's Clef model,
then write an HTML page that shows each comment with its label.

Usage:
    python3 classify.py        # comments.json    with clef-flash -> results.html
    python3 classify.py v2     # comments-v2.json with clef       -> results-v2.html

Needs cloud-flare.local.sh (account ID and API token) in the same folder.
Uses only the Python standard library.
"""

import html
import json
import re
import sys
import time
import urllib.error
import urllib.request

RUNS = {
    "v1": {"model": "clef-flash", "comments": "comments.json",
           "results": "results.json", "html": "results.html"},
    "v2": {"model": "clef", "comments": "comments-v2.json",
           "results": "results-v2.json", "html": "results-v2.html"},
}
RUN = sys.argv[1] if len(sys.argv) > 1 else "v1"
if RUN not in RUNS:
    sys.exit("Usage: python3 classify.py [v1|v2]")
MODEL = RUNS[RUN]["model"]
COMMENTS_FILE = RUNS[RUN]["comments"]
RESULTS_FILE = RUNS[RUN]["results"]
HTML_FILE = RUNS[RUN]["html"]

INSTRUCTIONS = (
    "Classify `comment`, a post on the discussion forum of an online college course on "
    "applied AI. Students ask questions, share their work, give feedback and chat about the "
    "course. Informal language, frustration, criticism of the course and mild slang are normal "
    "and acceptable. Judge the comment by what it does, not by its tone alone."
)

CRITERIA = {
    "acceptable": (
        "A genuine post related to the course or the forum: a question, an answer, shared work, "
        "feedback, criticism of the course or tools, or friendly chat. It may be informal, "
        "frustrated or blunt, as long as it does not attack or demean people."
    ),
    "toxic": (
        "Insults, harasses, threatens, demeans or mocks a person or group (students, teachers or "
        "others), uses abusive or hateful language aimed at someone, or tries to humiliate someone."
    ),
    "spam": (
        "Unrelated promotion or advertising, selling services (including paid assignment help or "
        "answers), links or contact details pushed for someone's own gain, scams, or repeated "
        "or meaningless content posted to get attention rather than to take part."
    ),
}

COLOURS = {"acceptable": "#2f7d4a", "toxic": "#b3261e", "spam": "#a86400"}
UNSURE_BELOW = 0.5


def load_credentials(path="cloud-flare.local.sh"):
    text = open(path, encoding="utf-8").read()
    creds = dict(re.findall(r'export (\w+)="([^"]*)"', text))
    return creds["CLOUDFLARE_ACCOUNT_ID"], creds["CLOUDFLARE_API_TOKEN"]


def classify(comment, account, token):
    payload = {
        "state": {"comment": comment},
        "questions": {
            "label": {
                "type": "choice",
                "instructions": INSTRUCTIONS,
                "criteria": CRITERIA,
            }
        },
    }
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/cloudflare/{MODEL}"
    body = json.dumps(payload).encode("utf-8")
    for attempt in range(6):
        request = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.load(response)
        except urllib.error.HTTPError as err:
            if err.code == 429 or err.code >= 500:  # busy or temporary error: wait, try again
                time.sleep(2 ** attempt)
                continue
            if err.code in (401, 403):
                sys.exit("Cloudflare refused the request: check the account ID and API token "
                         "in cloud-flare.local.sh.")
            sys.exit(f"Cloudflare returned HTTP {err.code}: {err.read().decode('utf-8', 'replace')}")
        if not data.get("success"):
            sys.exit(f"Cloudflare error: {data.get('errors')}")
        return data["result"]["answers"]["label"]
    sys.exit("Gave up after repeated 'too many requests' or server errors. Try again later.")


def write_html(course, forum, rows):
    counts = {k: sum(1 for r in rows if r["label"] == k) for k in CRITERIA}
    unsure = sum(1 for r in rows if r["confidence"] < UNSURE_BELOW)

    def row_html(r):
        low = r["confidence"] < UNSURE_BELOW
        probs = " · ".join(f"{k} {v:.2f}" for k, v in r["probabilities"].items())
        flag = ' <span class="unsure">check</span>' if low else ""
        colour = COLOURS.get(r["label"], "#555")
        return (
            f'<tr data-label="{html.escape(r["label"])}" data-unsure="{int(low)}">'
            f'<td class="num">{r["id"]}</td>'
            f'<td><span class="tag" style="background:{colour}">{html.escape(r["label"])}</span>{flag}</td>'
            f'<td class="num">{r["confidence"]:.2f}</td>'
            f'<td>{html.escape(r["comment"])}<div class="meta">{html.escape(r["author"])} · '
            f'{html.escape(r["thread"])} · {probs}</div></td></tr>'
        )

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clef classification: {html.escape(forum)}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 24px; color: #1d2422; background: #fafaf8; }}
h1 {{ font-size: 22px; margin: 0 0 4px; }}
.sub {{ color: #5d6a66; margin: 0 0 16px; }}
.filters button {{ margin: 0 6px 12px 0; padding: 4px 10px; border: 1px solid #ccc; background: #fff; border-radius: 6px; cursor: pointer; }}
.filters button.on {{ border-color: #1d2422; font-weight: 600; }}
table {{ border-collapse: collapse; width: 100%; background: #fff; }}
th, td {{ text-align: left; vertical-align: top; padding: 8px; border-bottom: 1px solid #e3e3e0; }}
th {{ position: sticky; top: 0; background: #f0f0ec; }}
.num {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}
.tag {{ color: #fff; padding: 2px 8px; border-radius: 10px; font-size: 13px; }}
.unsure {{ font-size: 12px; color: #a86400; border: 1px solid #a86400; border-radius: 8px; padding: 0 6px; margin-left: 4px; }}
.meta {{ color: #6b7280; font-size: 12px; margin-top: 4px; }}
</style></head><body>
<h1>{html.escape(forum)}</h1>
<p class="sub">{html.escape(course)} · model: {MODEL} · {len(rows)} comments ·
acceptable {counts['acceptable']}, toxic {counts['toxic']}, spam {counts['spam']} ·
{unsure} marked "check" (confidence below {UNSURE_BELOW})</p>
<div class="filters">
<button class="on" data-f="all">All</button><button data-f="acceptable">Acceptable</button>
<button data-f="toxic">Toxic</button><button data-f="spam">Spam</button>
<button data-f="unsure">Low confidence</button>
</div>
<table><thead><tr><th>ID</th><th>Clef label</th><th>Confidence</th><th>Comment</th></tr></thead>
<tbody>{''.join(row_html(r) for r in rows)}</tbody></table>
<script>
document.querySelectorAll('.filters button').forEach(b => b.onclick = () => {{
  document.querySelectorAll('.filters button').forEach(x => x.classList.toggle('on', x === b));
  const f = b.dataset.f;
  document.querySelectorAll('tbody tr').forEach(tr => {{
    tr.hidden = !(f === 'all' || tr.dataset.label === f || (f === 'unsure' && tr.dataset.unsure === '1'));
  }});
}});
</script>
</body></html>"""
    with open(HTML_FILE, "w", encoding="utf-8") as out:
        out.write(page)


def main():
    account, token = load_credentials()
    data = json.load(open(COMMENTS_FILE, encoding="utf-8"))
    print(f"Classifying {len(data['comments'])} comments from {COMMENTS_FILE} with {MODEL}...")
    rows = []
    for c in data["comments"]:
        answer = classify(c["comment"], account, token)
        rows.append({**c, "label": answer["choice"],
                     "confidence": answer.get("confidence", 0.0),
                     "probabilities": answer.get("probabilities", {})})
        print(f'{c["id"]:>3}  {answer["choice"]:<10}  {answer.get("confidence", 0):.2f}')
    with open(RESULTS_FILE, "w", encoding="utf-8") as out:
        json.dump(rows, out, indent=2, ensure_ascii=False)
    write_html(data.get("course", ""), data.get("forum", ""), rows)
    print(f"Done. Open {HTML_FILE} to see the results.")


if __name__ == "__main__":
    main()
