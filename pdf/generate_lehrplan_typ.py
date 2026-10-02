#!/usr/bin/env python3
"""Generate a printable Typst goal sheet from a Swissmem ET lehrplan JSON subset.

Usage examples:
  # All goals for the Lernort Betrieb, no semester split
  python3 generate_lehrplan_typ.py data/lehrplan_ET.json --lernort BE -o output/Lernziele_Elektroniker_Betrieb.typ

  # All goals for the Berufsschule, one chapter per semester
  python3 generate_lehrplan_typ.py data/lehrplan_ET.json --lernort BFS --by-semester -o output/Lernziele_Elektroniker_Berufsschule.typ

  # Hide the long HK descriptions, signatures only on LK rows
  python3 generate_lehrplan_typ.py data/lehrplan_ET.json --no-descriptions --signature lk -o output/Lernziele_Elektroniker.typ

The input may be the full data/lehrplan_<BPL>.json or any subset sharing its schema
({"ET": {"handlungskompetenzbereiche": [...]}} or directly {"handlungskompetenzbereiche": [...]}).

The Typst layout lives in the Jinja2 templates under templates/:
  base.typ.j2         entry point + DESIGN block + content loops
  title_page.typ.j2   title page
  toc.typ.j2          table of contents + page numbering reset
  table.typ.j2        LK/LZ table macros (lk_row, lz_row, lk_table)
"""

import argparse
import datetime
import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

JOBS_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.json"

LERNORT_NAMES = {
    "BE": "Betrieb (BE)",
    "BFS": "Berufsschule (BFS)",
    "üK": "Überbetriebliche Kurse (üK)",
    "ÜK": "Überbetriebliche Kurse (üK)",
}

# Defaults matching the ET/neutral web palette; per-job values come from jobs.json.
DEFAULT_ACCENT = "#16213e"
DEFAULT_ACCENT_SOFT = "#e9edf5"


def load_jobs():
    with open(JOBS_PATH, encoding="utf-8") as f:
        return json.load(f)


def job_for_input(path):
    """Look up the job metadata for a lehrplan_<CODE>.json input (or {} fallback)."""
    m = re.search(r"lehrplan_([A-Z]{2})\.json$", str(path))
    if not m:
        return {}, ""
    code = m.group(1)
    return load_jobs().get(code, {}), code


def job_name_of(job, code):
    return job.get("title") or (f"Lernziele {code} EFZ" if code else "Lernziele")

OUTPUT_NAMES = {
    "BE": "Lernziele_Elektroniker_Betrieb",
    "BFS": "Lernziele_Elektroniker_Berufsschule",
    "üK": "Lernziele_Elektroniker_Ueberbetriebliche_Kurse",
    "ÜK": "Lernziele_Elektroniker_Ueberbetriebliche_Kurse",
}

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def t(s):
    """Typst literal text from a Python string (no markup parsing)."""
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'#("{s}")'


def tstr(s):
    """Typst string literal from a Python string (for e.g. #set document(title: ...))."""
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def min_sem(obj):
    sems = [int(x) for x in as_list(obj.get("Semester")) if str(x).strip().isdigit()]
    return min(sems) if sems else 999


def fmt_semesters(arr):
    nums = sorted({int(x) for x in as_list(arr) if str(x).strip().isdigit()})
    if not nums:
        return ""
    parts = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
        else:
            parts.append((start, prev))
            start = prev = n
    parts.append((start, prev))
    return ", ".join(f"{a}\u2013{b}" if a != b else str(a) for a, b in parts)


def get_hkbs(data):
    if isinstance(data, dict):
        if "handlungskompetenzbereiche" in data:
            return data["handlungskompetenzbereiche"]
        for v in data.values():
            if isinstance(v, dict) and "handlungskompetenzbereiche" in v:
                return v["handlungskompetenzbereiche"]
    return []


def build_tree(hkbs, lernorte):
    """Sort/group like script.js: HKB by ID, HK by ID, LK by (min sem, ID), LZ by min sem."""
    tree = []
    for hkb in sorted(hkbs, key=lambda h: h.get("ID HKB", "")):
        hks = []
        for hk in sorted(hkb.get("handlungskompetenzen", []), key=lambda h: h.get("ID HK", "")):
            lks = []
            for lk in hk.get("lernkriterien", []):
                if lernorte and lk.get("Lernort") not in lernorte:
                    continue
                lzs = sorted(lk.get("lernziele", []), key=min_sem)
                lks.append({"lk": lk, "lzs": lzs})
            if lks:
                hks.append({"hk": hk, "lks": lks})
        if hks:
            tree.append({"hkb": hkb, "hks": hks})
    return tree


def sems_of(obj):
    return {int(x) for x in as_list(obj.get("Semester")) if str(x).strip().isdigit()}


def semester_chapters(tree):
    """Split the tree into one chapter per semester.

    A goal appears in every semester it is active:
      - with Lernziele (BFS/üK): driven by the Lernziel semesters,
      - without (BE): driven by the Leistungskriterium semester list.
    """
    sems = set()
    for hkb in tree:
        for hk in hkb["hks"]:
            for item in hk["lks"]:
                lk, lzs = item["lk"], item["lzs"]
                if lzs:
                    for lz in lzs:
                        sems.update(sems_of(lz))
                else:
                    sems.update(sems_of(lk))

    chapters = []
    for s in sorted(sems):
        items = []
        for entry in tree:
            hks = []
            for hk in entry["hks"]:
                lks = []
                for item in hk["lks"]:
                    lk, lzs = item["lk"], item["lzs"]
                    if lzs:
                        active = [lz for lz in lzs if s in sems_of(lz)]
                        if active:
                            lks.append({"lk": lk, "lzs": active})
                    elif s in sems_of(lk):
                        lks.append({"lk": lk, "lzs": []})
                if lks:
                    hks.append({"hk": hk["hk"], "lks": lks})
            if hks:
                items.append({"hkb": entry["hkb"], "hks": hks})
        chapters.append({"sem": s, "items": items})
    return chapters


def renderable_lz(lz):
    return {
        "lz_id": lz.get("ID LZ") or "",
        "desc": lz.get("Beschreibung LZ") or "",
        "sem": fmt_semesters(lz.get("Semester")),
    }


def renderable_lk(item):
    lk = item["lk"]
    return {
        "lk_id": lk.get("ID LK") or "",
        "desc": lk.get("Beschreibung LK") or "",
        "sem": fmt_semesters(lk.get("Semester")),
        "lzs": [renderable_lz(lz) for lz in item["lzs"]],
    }


def renderable_hk(hk):
    return {
        "hk_id": hk["hk"].get("ID HK") or "",
        "name": hk["hk"].get("Name") or "",
        "desc": hk["hk"].get("Beschreibung") or "",
        "pw": hk["hk"].get("P/W", ""),
        "lks": [renderable_lk(item) for item in hk["lks"]],
    }


def renderable_hkb(hkb):
    return {
        "name": hkb["hkb"].get("Name") or "",
        "id": hkb["hkb"].get("ID HKB") or "",
        "hks": [renderable_hk(hk) for hk in hkb["hks"]],
    }


def hk_code(hk_id):
    """Derive the short code (e.g. '9999 a.01' -> 'a1') for an HK id.

    The questionnaire overview transposes the HKB/HK list into a grid
    (columns = HKB, rows = HK level), like the Qualifikationsprofil page.
    Each HK cell is headed by its short code, followed by the full id."""
    s = str(hk_id)
    for token in s.split():
        letters = "".join(c for c in token if c.isalpha())
        digits = "".join(c for c in token if c.isdigit())
        if letters and digits:
            return f"{letters}{int(digits)}"
    return s


def build_overview(hkbs):
    """All HKB/HK for the overview chapter, rendered as a transposed grid.

    Matches the Qualifikationsprofil table on skills.futuremem.swiss:
    columns are the HKB, the first row names each HKB, then a full-width
    'Handlungskompetenzen' subheader, and below one HK per row (the nth HK
    of each HKB), padded with empty cells where a column runs out of HKs."""
    cols = []
    for hkb in sorted(hkbs, key=lambda h: h.get("ID HKB", "")):
        hks = []
        for hk in sorted(hkb.get("handlungskompetenzen", []),
                         key=lambda h: h.get("ID HK", "")):
            hk_id = hk.get("ID HK") or ""
            pw = hk.get("P/W", "")
            hks.append({
                "code": hk_code(hk_id),
                "id": hk_id,
                "name": hk.get("Name") or "",
                "pw": pw,
                "text": "Pflicht" if pw == "P" else ("Wahl" if pw == "W" else ""),
            })
        cols.append({
            "id": hkb.get("ID HKB") or "",
            "name": hkb.get("Name") or "",
            "hks": hks,
        })

    n_rows = max((len(c["hks"]) for c in cols), default=0)
    rows = [
        [c["hks"][i] if i < len(c["hks"]) else None for c in cols]
        for i in range(n_rows)
    ]
    return {"cols": cols, "rows": rows, "n_rows": n_rows}


def build_context(args):
    data = json.load(open(args.input, encoding="utf-8"))
    job, code = job_for_input(args.input)
    name = job_name_of(job, code)
    tree = build_tree(get_hkbs(data), args.lernort or None)
    has_lz = any(item["lzs"] for h in tree for hk in h["hks"] for item in hk["lks"])

    chapters = None
    if args.by_semester:
        chapters = [
            {"sem": c["sem"], "items": [renderable_hkb(e) for e in c["items"]]}
            for c in semester_chapters(tree)
        ]
        tree = None
    else:
        tree = [renderable_hkb(e) for e in tree]

    fields = []
    for label, key, length in (("Name", "name", 38),
                               ("Jahr Lehrstart", "start_year", 18),
                               ("Firma", "company", 38)):
        fields.append({
            "label": label,
            "value": getattr(args, key) or "",
            "length": length,
        })

    beruf = job.get("name") or name
    return {
        "title": name,
        "doc_title": doc_title_for(args, name),
        "subtitle": subtitle_for(args),
        "job_name": beruf,
        "accent": job.get("accent", DEFAULT_ACCENT),
        "accent_soft": job.get("accentSoft", DEFAULT_ACCENT_SOFT),
        "today": datetime.date.today().strftime("%d.%m.%Y"),
        "footer": f"Lernziele gemäss Bildungsplan {beruf}",
        "fields": fields,
        "by_semester": args.by_semester,
        "show_desc": args.descriptions,
        "signature": args.signature,
        "has_lz": has_lz,
        "tree": tree,
        "chapters": chapters,
        "overview": build_overview(get_hkbs(data)),
    }


def render(context, template_dir=TEMPLATE_DIR):
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(disabled_extensions=("j2",)),
    )
    env.filters["typ"] = t
    env.filters["tstr"] = tstr
    return env.get_template("base.typ.j2").render(**context)


def doc_title_for(args, name="Lernziele"):
    return f"{name} \u2013 " + subtitle_for(args)


def subtitle_for(args):
    los = args.lernort
    if not los:
        part = "Alle Lernorte"
    else:
        part = "Lernort " + " / ".join(LERNORT_NAMES[l] for l in los)
    if args.by_semester:
        part += " · nach Semestern"
    return part


def main():
    ap = argparse.ArgumentParser(
        description="Generate a printable Typst goal sheet (Lernziele) from a lehrplan.json subset.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("input", help="Path to the lehrplan JSON (full file or subset).")
    ap.add_argument("--lernort", action="append", choices=["BE", "BFS", "üK", "ÜK"],
                    help="Only include goals for this Lernort. May be repeated (default: all).")
    ap.add_argument("--by-semester", action="store_true",
                    help="Group the goals into one chapter per semester.")
    ap.add_argument("--show-descriptions", dest="descriptions", action="store_true", default=True,
                    help="Show the long HK descriptions (default).")
    ap.add_argument("--no-descriptions", dest="descriptions", action="store_false",
                    help="Hide the long HK descriptions.")
    ap.add_argument("--signature", choices=["both", "lk", "lz", "none"], default="both",
                    help="Where to place the signature checkbox (default: both).")
    ap.add_argument("--name", default="", help="Pre-fill the student name field.")
    ap.add_argument("--start-year", default="", help="Pre-fill the apprenticeship start year field.")
    ap.add_argument("--company", default="", help="Pre-fill the company field.")
    ap.add_argument("-o", "--output", help="Output .typ path (default: output/lehrplan_<lernort>.typ).")
    args = ap.parse_args()

    if args.output is None:
        if args.lernort and len(args.lernort) == 1:
            args.output = f"output/{OUTPUT_NAMES[args.lernort[0]]}.typ"
        else:
            args.output = "output/Lernziele_Elektroniker.typ"

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(build_context(args)) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
