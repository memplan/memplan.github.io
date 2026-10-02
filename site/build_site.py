#!/usr/bin/env python3
"""Assemble the static site into `_site/`.

Reads the per-job metadata from `data/jobs.json`, renders the landing page and
one folder per job (`/<CODE>/index.html`), detects the PDFs that actually exist
in `pdf/output/`, and copies all shared assets.

Usage:
  python3 site/build_site.py            # writes ./_site
  python3 site/build_site.py --out dist # custom output directory
"""

import argparse
import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

SITE_DIR = Path(__file__).resolve().parent
REPO_DIR = SITE_DIR.parent
TEMPLATE_DIR = SITE_DIR / "templates"

# Suffix (after `Lernziele_<short>`) -> label shown in the PDF dropdown.
PDF_LABELS = [
    ("_Berufsschule.pdf", "Berufsschule"),
    ("_Betrieb.pdf", "Betrieb"),
    ("_Ueberbetriebliche_Kurse.pdf", "Überbetriebliche Kurse"),
]


def load_jobs():
    with open(REPO_DIR / "data" / "jobs.json", encoding="utf-8") as f:
        return json.load(f)


def pdf_links_for(job):
    links = []
    for suffix, label in PDF_LABELS:
        name = f"Lernziele_{job['short']}{suffix}"
        if (REPO_DIR / "pdf" / "output" / name).exists():
            links.append({"label": label, "href": f"pdf/output/{name}"})
    return links


def count_stats():
    """Total Lernziele and Leistungskriterien across all per-job files."""
    lz = lk = 0
    for path in (REPO_DIR / "data").glob("lehrplan_*.json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        bpl = next(iter(data))
        for hkb in data[bpl]["handlungskompetenzbereiche"]:
            for hk in hkb["handlungskompetenzen"]:
                lk += len(hk["lernkriterien"])
                for k in hk["lernkriterien"]:
                    lz += len(k["lernziele"])
    return {"jobs": len(load_jobs()), "lernziele": lz, "lernkriterien": lk}


def render(env, template_name, **context):
    return env.get_template(template_name).render(**context)


def build(out_dir):
    jobs = load_jobs()
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(enabled_extensions=("html", "j2")),
    )

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    # Landing page
    (out_dir / "index.html").write_text(
        render(env, "index.html.j2", jobs=jobs, stats=count_stats()), encoding="utf-8")

    # One folder per job
    for code, job in jobs.items():
        job_dir = out_dir / code
        job_dir.mkdir()
        (job_dir / "index.html").write_text(
            render(env, "job.html.j2", code=code, job=job, jobs=jobs,
                   pdf_links=pdf_links_for(job)),
            encoding="utf-8")

    # Shared assets
    shutil.copy2(REPO_DIR / "style.css", out_dir / "style.css")
    shutil.copy2(REPO_DIR / "script.js", out_dir / "script.js")

    img_out = out_dir / "img"
    img_out.mkdir()
    for f in (REPO_DIR / "img").iterdir():
        if f.is_file():
            shutil.copy2(f, img_out / f.name)
    jobs_img_out = img_out / "jobs"
    jobs_img_out.mkdir()
    for f in (REPO_DIR / "img" / "jobs").iterdir():
        if f.is_file() and not f.name.startswith("_"):
            shutil.copy2(f, jobs_img_out / f.name)

    data_out = out_dir / "data"
    data_out.mkdir()
    for f in (REPO_DIR / "data").glob("lehrplan_*.json"):
        shutil.copy2(f, data_out / f.name)

    pdf_out = out_dir / "pdf" / "output"
    pdf_out.mkdir(parents=True)
    for f in (REPO_DIR / "pdf" / "output").glob("*.pdf"):
        shutil.copy2(f, pdf_out / f.name)

    print(f"Built {len(jobs)} job pages + landing page into {out_dir}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(REPO_DIR / "_site"),
                    help="Output directory (default: <repo>/_site).")
    args = ap.parse_args()
    build(Path(args.out).resolve())


if __name__ == "__main__":
    main()
