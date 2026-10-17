#!/usr/bin/env python3
"""Build the website from library.yml.

    python3 tools/build.py              compile LaTeX, convert, write site/
    python3 tools/build.py --no-latex   reuse existing build/*.aux and PDFs
    python3 tools/build.py --render     also run `quarto render site`

For every book with a `source`, the LaTeX is compiled first: the .aux file
is the authority for every number on the web page (statements, equations,
exercises), so web and PDF always agree. Each \\input file becomes a page;
a lecture's \\homework part becomes a separate page.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
TOOLS = ROOT / "tools"
SHARED_TEX = ROOT / "shared" / "latex"
GENERATED = SITE / "books"

QUARTO = shutil.which("quarto") or str(Path.home() / ".local/quarto/bin/quarto")

THEOREM_ENVS = [
    "definition", "proposition", "lemma", "theorem", "corollary", "claim",
    "conjecture", "observation", "remark", "example", "practice", "question",
    "thinking", "historynote", "workedexample",
]
NUMBERED_ENVS = ["definition", "proposition", "lemma", "theorem", "corollary",
                 "claim", "conjecture", "observation"]

def log(msg):
    print(f"[build] {msg}", file=sys.stderr)


# ---------------------------------------------------------------------
#  Small LaTeX scanning helpers
# ---------------------------------------------------------------------
def read_group(s, i, open_="{", close="}"):
    """s[i] is `open_`; return (content, index after the matching `close`).
    Inside [...] a {...} group is skipped whole, so ] in braces is safe."""
    assert s[i] == open_, (s[i:i + 20], open_)
    depth, j = 0, i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if open_ == "[" and c == "{":
            _, j = read_group(s, j)
            continue
        if c == open_:
            depth += 1
        elif c == close:
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError("unbalanced group near: " + s[i:i + 60])


def skip_ws(s, i):
    while i < len(s) and s[i] in " \t\n":
        i += 1
    return i


def replace_command(s, name, spec, fn):
    """Replace every \\name with fn(args). spec: s=star, o=optional, m=mandatory.
    Missing optional args are passed as None, star as bool."""
    out, i = [], 0
    pat = re.compile(r"\\" + re.escape(name) + r"(?![A-Za-z@])")
    while True:
        m = pat.search(s, i)
        if not m:
            out.append(s[i:])
            return "".join(out)
        out.append(s[i:m.start()])
        j, args = m.end(), []
        for kind in spec:
            if kind == "s":
                if j < len(s) and s[j] == "*":
                    args.append(True)
                    j += 1
                else:
                    args.append(False)
            elif kind == "o":
                k = j
                if k < len(s) and s[k] == "[":
                    content, j = read_group(s, k, "[", "]")
                    args.append(content)
                else:
                    args.append(None)
            else:
                k = skip_ws(s, j)
                if k < len(s) and s[k] == "{":
                    content, j = read_group(s, k)
                else:  # single-token argument
                    content, j = s[k], k + 1
                args.append(content)
        out.append(fn(*args))
        i = j


def strip_comments(s):
    return re.sub(r"(?<!\\)%.*", "", s)


def texorpdf(s, pdf=False):
    return replace_command(s, "texorpdfstring", "mm", lambda a, b: b if pdf else a)


# ---------------------------------------------------------------------
#  .aux and PDF page labels
# ---------------------------------------------------------------------
def parse_aux(path):
    labels = {}
    s = path.read_text(encoding="utf-8")
    for m in re.finditer(r"\\newlabel\{", s):
        try:
            name, j = read_group(s, m.end() - 1)
            body, _ = read_group(s, j)
        except (ValueError, AssertionError, IndexError):
            continue
        if name.endswith("@cref"):
            continue
        fields, k = [], 0
        while k < len(body) and len(fields) < 5:
            if body[k] == "{":
                g, k = read_group(body, k)
                fields.append(g)
            else:
                k += 1
        if len(fields) < 2:
            continue
        num = fields[0].strip("{}").strip()
        labels[name] = {"num": num, "page": fields[1],
                        "title": fields[2] if len(fields) > 2 else ""}
    return labels


def pdf_page_index(pdf):
    """Printed page label -> physical page number (1-based)."""
    try:
        import fitz
    except ImportError:
        log("PyMuPDF not installed; PDF page links fall back to printed numbers")
        return {}
    index = {}
    with fitz.open(pdf) as doc:
        for i, pg in enumerate(doc):
            # the cover can carry the same label as main-matter page 1;
            # later pages win
            index[pg.get_label() or str(i + 1)] = i + 1
    return index


# ---------------------------------------------------------------------
#  Rewriting cls syntax into pandoc-friendly LaTeX
# ---------------------------------------------------------------------
def href(kind, text):
    return r"\href{yp:" + kind + "}{" + text + "}"


def preprocess(s, lang):
    s = strip_comments(s)
    s = texorpdf(s)
    for cmd in ["phantomsection", "clearpage", "newpage", "qedhere", "noindent",
                "appendixstatements", "medskip", "bigskip", "smallskip"]:
        s = re.sub(r"\\" + cmd + r"(?![A-Za-z])", "", s)

    # headings
    s = replace_command(s, "lecture", "om", lambda short, long: r"\section{" + long + "}")
    s = replace_command(s, "topic", "m", lambda t: r"\subsection*{" + t + "}")
    s = replace_command(s, "frontsection", "m", lambda t: r"\section{" + t + "}")
    s = replace_command(s, "exercisepart", "m", lambda t: r"\subsection*{" + t + "}")
    default_thinking = "思考题" if lang == "zh" else "Problems"
    s = replace_command(s, "thinkingpart", "o",
                        lambda t: r"\subsection*{" + (t or default_thinking) + "}")

    # text styling
    term = r"\textbf{" if lang == "zh" else r"\emph{"
    s = replace_command(s, "term", "m", lambda t: term + t + "}")
    s = replace_command(s, "marginterm", "om", lambda o, t: r"\textbf{" + t + "}")
    s = replace_command(s, "marginnote", "m", lambda t: "")
    s = replace_command(s, "blueterm", "m", lambda t: href("blue", t))
    s = replace_command(s, "blue", "m", lambda t: href("blue", t))
    s = replace_command(s, "red", "m", lambda t: href("red", t))
    s = replace_command(s, "uline", "m", lambda t: r"\underline{" + t + "}")

    # page-based references have no meaning on the web
    here = "此处" if lang == "zh" else "here"
    s = re.sub(r"第\s*~?\s*\\pageref\*?\{([^}]*)\}\s*~?\s*页",
               lambda m: href("at:" + m.group(1), here), s)
    s = re.sub(r"(?:page|p\.)\s*~?\s*\\pageref\*?\{([^}]*)\}",
               lambda m: href("at:" + m.group(1), here), s)
    s = replace_command(s, "pageref", "sm", lambda st, l: href("at:" + l, here))
    s = replace_command(s, "egref", "om", lambda t, l: href("egref:" + l, t or "@"))
    s = replace_command(s, "wegref", "om", lambda t, l: href("wegref:" + l, t or "@"))
    s = replace_command(s, "exref", "m", lambda l: r"\ref{" + l + "})")
    s = replace_command(s, "hyperref", "om", lambda l, t: href("at:" + (l or ""), t))

    # theorem-like environments: starred names and optional titles
    def env_opt(m):
        env, star = m.group(1), m.group(2)
        name = env + ("star" if star else "")
        return r"\begin{" + name + "}" + "\x00OPT\x00"

    envs = "|".join(THEOREM_ENVS + ["proof", "solution"])
    s = re.sub(r"\\begin\{(" + envs + r")(\*?)\}", env_opt, s)
    s = re.sub(r"\\end\{(" + "|".join(THEOREM_ENVS) + r")\*\}", r"\\end{\1star}", s)
    out, i = [], 0
    while True:
        k = s.find("\x00OPT\x00", i)
        if k < 0:
            out.append(s[i:])
            break
        out.append(s[i:k])
        j = k + 5
        if j < len(s) and s[j] == "[":
            content, j = read_group(s, j, "[", "]")
            out.append(href("note", content))
        i = j
    s = "".join(out)

    # exercises / probleme / questions
    def exercises(group, title, note):
        sep = "：" if lang == "zh" else ": "
        word = "习题" if lang == "zh" else "Exercises"
        head = href("group", group) + href("title", f"{word} {group}{sep}{title}")
        if note:
            head += href("note", note)
        return r"\begin{ypexercises}" + head + r"\begin{enumerate}"

    s = replace_command(s, "begin{exercises}", "mmo", exercises)
    s = s.replace(r"\end{exercises}", r"\end{enumerate}\end{ypexercises}")

    def probleme(star, word, group, title):
        word = word or ("习题" if lang == "zh" else "Problem")
        sep = "：" if lang == "zh" else ": "
        head = f"{word} {group}{'*' if star else ''}" + (f"{sep}{title}" if title.strip() else "")
        return r"\begin{ypprobleme}" + href("group", group) + href("title", head)

    s = replace_command(s, "begin{probleme}", "somm", probleme)
    s = s.replace(r"\end{probleme}", r"\end{ypprobleme}")

    s = replace_command(s, "begin{questions}", "o", lambda o: r"\begin{ypquestions}"
                        + (href("resume", "x") if o and "resume" in o else "")
                        + r"\begin{enumerate}")
    s = s.replace(r"\end{questions}", r"\end{enumerate}\end{ypquestions}")
    return s


def split_homework(s):
    """Return (lecture part, homework part or None, homework title)."""
    m = re.search(r"\\homework(?![A-Za-z])", s)
    if not m:
        return s, None, None
    title = {}

    def grab(star, when, t, short):
        title["t"] = t
        return "\x00HW\x00"

    rest = replace_command(s[m.start():], "homework", "somo", grab)
    return s[:m.start()], rest.replace("\x00HW\x00", ""), title.get("t", "")


def math_macros(cls_path):
    """Notation macros from the class file (everything after the notation banner)."""
    text = cls_path.read_text(encoding="utf-8")
    m = re.search(r"^%.*(记号|[Nn]otation).*$", text, re.M)
    section = text[m.end():] if m else ""
    keep = []
    for line in section.splitlines():
        line = strip_comments(line).strip()
        if re.match(r"\\(newcommand|renewcommand|DeclareMathOperator)", line) and "@" not in line:
            keep.append(line)
    return "\n".join(keep) + "\n"


def brace_macros(s, macros):
    """Wrap argument-free notation macros in braces: \\overline\\R must become
    \\overline{\\mathbb{R}}, not \\overline\\mathbb{R}, after pandoc expands it."""
    # only letter-like macros (\\mathbb{R}, \\mathcal{F}); bracing a relation
    # such as \\given or \\toP would change its spacing
    names = re.findall(r"\\(?:re)?newcommand\{\\([A-Za-z]+)\}\{\\math(?:bb|cal|bf|frak|scr)\{\w\}\}", macros)
    if not names:
        return s
    pat = re.compile(r"(?<!\{)\\(" + "|".join(sorted(names, key=len, reverse=True)) + r")(?![A-Za-z])")
    return pat.sub(lambda m: "{\\" + m.group(1) + "}", s)


# ---------------------------------------------------------------------
#  Progress table (进度.md)
# ---------------------------------------------------------------------
def parse_progress(path):
    rows = {}
    if not path or not path.exists():
        return rows
    header = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            header = None if not line.strip() else header
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        row = dict(zip(header, cells))
        f = row.get("文件", "").strip("`")
        if f:
            rows[f] = row
    return rows


# ---------------------------------------------------------------------
#  Building one book
# ---------------------------------------------------------------------
def compile_latex(src, main):
    env = dict(os.environ)
    env["TEXINPUTS"] = f".:{SHARED_TEX}//:" + env.get("TEXINPUTS", "")
    cmd = ["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error",
           "-outdir=build", main]
    log(f"latexmk {src.relative_to(ROOT)}/{main}")
    r = subprocess.run(cmd, cwd=src, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout[-3000:])
        raise SystemExit(f"LaTeX failed for {src}")


def find_units(src, main):
    text = strip_comments((src / main).read_text(encoding="utf-8"))
    body = text.split(r"\begin{document}", 1)[-1]
    return [m.group(1) for m in re.finditer(r"\\(?:input|include)\{([^}]+)\}", body)]


def run_pandoc(tex, meta):
    args = ["pandoc", "-f", "latex", "-t", "markdown-smart", "--wrap=none", "-s",
            "--lua-filter", str(TOOLS / "yp-filter.lua")]
    for k, v in meta.items():
        args += ["-M", f"{k}={v}"]
    r = subprocess.run(args, input=tex, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        raise SystemExit("pandoc failed")
    for line in r.stderr.splitlines():
        if line.strip():
            log(line)
    return r.stdout


def build_book(book, no_latex):
    slug, lang = book["slug"], book.get("lang", "en")
    src = ROOT / book["source"]
    main = book["main"]
    stem = Path(main).stem
    numbering = "global" if lang == "zh" else "section"
    if not no_latex:
        compile_latex(src, main)
    aux = src / "build" / f"{stem}.aux"
    pdf = src / "build" / f"{stem}.pdf"
    labels = parse_aux(aux)
    pageidx = pdf_page_index(pdf) if pdf.exists() else {}
    for v in labels.values():
        v["pdfpage"] = str(pageidx.get(v["page"], v["page"]))

    out = GENERATED / slug
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    pdf_name = f"{slug}.pdf"
    if pdf.exists():
        shutil.copy(pdf, out / pdf_name)

    cls = src / "yupin-notes.cls"
    if not cls.exists():
        cls = SHARED_TEX / "yupin-notes.cls"
    macros = math_macros(cls if lang == "zh" else cls.with_name("yupin-notes-en.clo"))
    progress = parse_progress(ROOT / book["progress"]) if book.get("progress") else {}

    # ---- collect pages -------------------------------------------------
    pages = []  # dicts: file, kind, tex, unit
    hw_no = 0
    for unit in find_units(src, main):
        path = src / (unit if unit.endswith(".tex") else unit + ".tex")
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        if raw.lstrip().startswith(r"\documentclass") or "makecoursetitle" in raw:
            continue
        uname = Path(unit).stem
        front = unit.startswith("front/")
        if front and "tableofcontents" in raw:
            continue
        lecture, hw, hw_title = split_homework(raw)
        pages.append({"file": ("front-" if front else "") + uname, "kind": "front" if front else "lecture",
                      "tex": lecture, "unit": uname})
        if hw is not None:
            hw_no += 1
            # the PDF's homework box (title bar and rules) is left out on the web
            word = "作业" if lang == "zh" else "Exercises"
            sep = "：" if lang == "zh" else ": "
            hw_tex = r"\section{" + word + (sep + hw_title if hw_title.strip() else "") + "}\n" + hw
            pages.append({"file": uname + "-hw", "kind": "homework", "tex": hw_tex, "unit": uname})

    # label -> page file
    for p in pages:
        for m in re.finditer(r"\\label\{([^}]+)\}", strip_comments(p["tex"])):
            labels.setdefault(m.group(1), {"num": "??", "page": "", "title": ""})["file"] = p["file"]

    labels_path = out / ".labels.json"
    labels_path.write_text(json.dumps(labels, ensure_ascii=False), encoding="utf-8")

    # ---- convert -------------------------------------------------------
    thm_offset = sec_offset = 0
    lecture_no = 0
    for p in pages:
        clean = strip_comments(p["tex"])
        meta = {"yp-labels": labels_path, "yp-page": p["file"], "yp-lang": lang,
                "yp-numbering": numbering, "yp-thm-offset": thm_offset,
                "yp-sec-offset": sec_offset, "yp-pdf": pdf_name if pdf.exists() else ""}
        row = progress.get(p["unit"], {})
        if p["kind"] == "lecture":
            lecture_no += 1
            p["no"] = lecture_no
            if lang == "zh":
                meta["yp-kicker"] = f"第 {lecture_no} 讲"
            lec = labels.get(f"lec:{p['unit']}")
            if lec:
                meta["yp-pdf-page"] = lec["pdfpage"]
        elif p["kind"] == "homework":
            p["no"] = lecture_no
            if lang == "zh":
                meta["yp-kicker"] = f"第 {lecture_no} 讲 · 作业"
            hw = labels.get(f"hw:{p['unit']}")
            if hw:
                meta["yp-pdf-page"] = hw["pdfpage"]
        p["topic"] = row.get("主题", "")
        md = run_pandoc(macros + brace_macros(preprocess(p["tex"], lang), macros), meta)
        (out / f"{p['file']}.qmd").write_text(md, encoding="utf-8")
        p["title"] = page_title(md)
        thm_offset += len(re.findall(r"\\begin\{(" + "|".join(NUMBERED_ENVS) + r")\}", clean))
        sec_offset += len(re.findall(r"\\section\{", clean))

    write_book_index(book, pages, out, pdf_name if pdf.exists() else None, progress)
    write_dir_metadata(book, out)
    return pages


def page_title(md):
    m = re.search(r"^title:\s*(.*)$", md, re.M)
    if not m:
        return ""
    t = m.group(1).strip()
    if t in ("|", ">"):
        nxt = md[m.end():].lstrip("\n").splitlines()
        t = nxt[0].strip() if nxt else ""
    return t.strip("'\"")


def plain_title(t):
    """Sidebar text: strip $...$ math to its letters and [x]{.class} spans to x."""
    t = re.sub(r"\[([^\]]*)\]\{[^}]*\}", r"\1", t)
    t = re.sub(r"\$([^$]*)\$", lambda m: tex_to_unicode(m.group(1)), t)
    return t.replace("\\", "")


GREEK = {"sigma": "σ", "pi": "π", "lambda": "λ", "mu": "μ", "nu": "ν", "omega": "ω",
         "Omega": "Ω", "varepsilon": "ε", "alpha": "α", "beta": "β", "delta": "δ"}


def tex_to_unicode(s):
    s = re.sub(r"\\([A-Za-z]+)", lambda m: GREEK.get(m.group(1), m.group(1)), s)
    return re.sub(r"[{}^_]", "", s)


def write_dir_metadata(book, out):
    meta = {"lang": "zh" if book.get("lang") == "zh" else "en"}
    bib = ROOT / book["source"] / "refs.bib"
    if bib.exists():
        shutil.copy(bib, out / "refs.bib")
        meta["bibliography"] = "refs.bib"
        # numeric [1] citations, as in math papers
        meta["csl"] = "../../assets/csl/american-mathematical-society-numeric.csl"
    (out / "_metadata.yml").write_text(yaml.safe_dump(meta, allow_unicode=True), encoding="utf-8")


def write_book_index(book, pages, out, pdf_name, progress):
    zh = book.get("lang") == "zh"
    lines = ["---", f"title: {json.dumps(book['title'], ensure_ascii=False)}"]
    if book.get("subtitle"):
        lines.append(f"subtitle: {json.dumps(book['subtitle'], ensure_ascii=False)}")
    lines += ["toc: false", "---", ""]
    buttons = []
    if pdf_name:
        buttons.append(f'<a class="yp-button" href="{pdf_name}">'
                       + ("下载整本 PDF" if zh else "Download PDF") + "</a>")
    updated = last_updated(book)
    if updated:
        buttons.append(f'<span class="yp-updated">{"最后更新" if zh else "Updated"} {updated}</span>')
    lines += ['<div class="yp-book-actions">' + " ".join(buttons) + "</div>", ""]

    lectures = [p for p in pages if p["kind"] == "lecture"]
    rows_md = []
    head = ("| 讲 | 内容 | 作业 |" if zh else "| § | Contents | Exercises |")
    rows_md += [head, "|---|---|---|"]
    for p in lectures:
        hw = next((q for q in pages if q["kind"] == "homework" and q["unit"] == p["unit"]), None)
        name = p["topic"] or plain_title(p["title"])
        hw_cell = f"[{'作业' if zh else 'Exercises'}]({hw['file']}.qmd)" if hw else ""
        rows_md.append(f"| {p['no']} | [{name}]({p['file']}.qmd) | {hw_cell} |")
    # planned lectures from the progress table
    done = {p["unit"] for p in lectures}
    n = len(lectures)
    for f, row in progress.items():
        if f not in done and row.get("正文") == "未开始":
            n += 1
            rows_md.append(f"| {row.get('讲', n)} | <span class=\"yp-todo\">{row.get('主题', f)}</span> | |")
    lines += ["## " + ("目录" if zh else "Contents"), "", "::: {.yp-book-index}"] + rows_md + [":::", ""]
    (out / "index.qmd").write_text("\n".join(lines), encoding="utf-8")


def last_updated(book):
    if not book.get("source"):
        return ""
    r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", book["source"]],
                       cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip() or datetime.date.today().isoformat()


# ---------------------------------------------------------------------
#  Site-level files
# ---------------------------------------------------------------------
def sidebar_for(book, pages):
    zh = book.get("lang") == "zh"
    base = f"books/{book['slug']}"
    contents = [{"href": f"{base}/index.qmd", "text": "目录" if zh else "Contents"}]
    front = [p for p in pages if p["kind"] == "front"]
    if front:
        contents.append({"section": "前言与导读" if zh else "Front matter",
                         "contents": [{"href": f"{base}/{p['file']}.qmd",
                                       "text": plain_title(p["title"])} for p in front]})
    for p in pages:
        if p["kind"] != "lecture":
            continue
        # sidebar: first phrase of the progress-table topic ("集合系，π-λ 定理" -> "集合系")
        name = re.split(r"[，：；（(]", p["topic"])[0].strip() if p["topic"] else plain_title(p["title"])
        text = f"{p['no']}. {name}" if zh else plain_title(p["title"])
        hw = [q for q in pages if q["kind"] == "homework" and q["unit"] == p["unit"]]
        if hw:
            contents.append({"section": text, "href": f"{base}/{p['file']}.qmd",
                             "contents": [{"href": f"{base}/{hw[0]['file']}.qmd",
                                           "text": "作业与解答" if zh else "Exercises"}]})
        else:
            contents.append({"href": f"{base}/{p['file']}.qmd", "text": text})
    return {"id": book["slug"], "title": book["title"], "style": "docked",
            "collapse-level": 1, "contents": contents}


def write_quarto_yml(lib, sidebars):
    cfg = lib["site"]
    site_url = f"https://{cfg['github']}.github.io/{cfg['repo']}/"
    q = {
        "project": {"type": "website", "output-dir": "_site",
                    "resources": ["books/*/*.pdf"]},
        "website": {
            "title": cfg["title"],
            "description": cfg.get("description", ""),
            "site-url": site_url,
            "repo-url": f"https://github.com/{cfg['github']}/{cfg['repo']}",
            "search": {"location": "navbar", "type": "overlay"},
            "page-navigation": True,
            "navbar": {"left": [{"href": "index.qmd", "text": "Library"}],
                       "right": [{"icon": "github",
                                  "href": f"https://github.com/{cfg['github']}/{cfg['repo']}"}]},
            "sidebar": sidebars,
        },
        "format": {"html": {
            "theme": ["cosmo", "assets/library.scss"],
            "html-math-method": "mathjax",
            "include-in-header": "assets/head.html",
            "toc": True, "toc-depth": 2,
            "number-sections": False,
            "anchor-sections": True,
        }},
    }
    (SITE / "_quarto.yml").write_text(
        "# Generated by tools/build.py from library.yml — do not edit by hand.\n"
        + yaml.safe_dump(q, allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_home(lib, built):
    cats = lib["categories"]
    books = lib["books"]
    parts = ["---", f"title: {json.dumps(lib['site']['title'])}",
             f"subtitle: {json.dumps(lib['site'].get('description', ''))}",
             "page-layout: full", "toc: false", "sidebar: false", "---", ""]

    def card(b):
        planned = b.get("status") == "planned" or b["slug"] not in built
        href = f"books/{b['slug']}/index.qmd"
        meta = [{"zh": "中文", "en": "English"}.get(b.get("lang", "en"), "")]
        prog = progress_summary(b)
        if prog:
            meta.append(prog)
        upd = last_updated(b)
        if upd and not planned:
            meta.append(f"updated {upd}")
        links = ""
        if not planned:
            links = f'<a class="yp-card-link" href="books/{b["slug"]}/index.html">Read</a>'
            if (GENERATED / b["slug"] / f"{b['slug']}.pdf").exists():
                links += f' <a class="yp-card-link" href="books/{b["slug"]}/{b["slug"]}.pdf">PDF</a>'
        else:
            links = '<span class="yp-card-planned">In preparation</span>'
        sub = f'<div class="yp-card-sub">{b["subtitle"]}</div>' if b.get("subtitle") else ""
        title = (f'<a href="books/{b["slug"]}/index.html">{b["title"]}</a>'
                 if not planned else b["title"])
        return (f'<div class="yp-card{" yp-card-muted" if planned else ""}">'
                f'<div class="yp-card-title">{title}</div>{sub}'
                f'<div class="yp-card-meta">{" · ".join(m for m in meta if m)}</div>'
                f'<div class="yp-card-links">{links}</div></div>')

    for c in cats:
        shelf = [b for b in books if b.get("category") == c["id"] and b.get("status") != "shelved"]
        parts.append(f"## {c['title']}\n")
        parts.append(f'<p class="yp-shelf-blurb">{c.get("blurb", "")}</p>\n')
        if shelf:
            parts.append('<div class="yp-shelf">' + "".join(card(b) for b in shelf) + "</div>\n")
        else:
            parts.append('<p class="yp-empty">Nothing here yet.</p>\n')
    shelved = [b for b in books if b.get("status") == "shelved"]
    if shelved:
        parts.append(f'<details class="yp-shelved"><summary>Shelved ({len(shelved)})</summary>'
                     '<div class="yp-shelf">' + "".join(card(b) for b in shelved) + "</div></details>\n")
    (SITE / "index.qmd").write_text("\n".join(parts), encoding="utf-8")


def progress_summary(book):
    if not book.get("progress"):
        return ""
    rows = parse_progress(ROOT / book["progress"])
    if not rows:
        return ""
    written = sum(1 for r in rows.values() if r.get("正文") not in ("未开始", ""))
    return f"{written}/{len(rows)} lectures"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-latex", action="store_true", help="reuse existing .aux/.pdf")
    ap.add_argument("--render", action="store_true", help="run quarto render afterwards")
    a = ap.parse_args()

    lib = yaml.safe_load((ROOT / "library.yml").read_text(encoding="utf-8"))
    sidebars, built = [], set()
    for b in lib["books"]:
        if not b.get("source") or b.get("status") == "planned":
            continue
        log(f"book {b['slug']}")
        pages = build_book(b, a.no_latex)
        sidebars.append(sidebar_for(b, pages))
        built.add(b["slug"])
    write_quarto_yml(lib, sidebars)
    write_home(lib, built)
    if a.render:
        subprocess.run([QUARTO, "render"], cwd=SITE, check=True)


if __name__ == "__main__":
    main()
