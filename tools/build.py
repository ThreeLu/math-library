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
import html
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
    index_path = out / ".index.jsonl"
    index_path.write_text("", encoding="utf-8")
    thm_offset = sec_offset = 0
    lecture_no = 0
    for p in pages:
        clean = strip_comments(p["tex"])
        row = progress.get(p["unit"], {})
        p["topic"] = row.get("主题", "")
        meta = {"yp-labels": labels_path, "yp-page": p["file"], "yp-lang": lang,
                "yp-numbering": numbering, "yp-thm-offset": thm_offset,
                "yp-sec-offset": sec_offset, "yp-pdf": pdf_name if pdf.exists() else "",
                "yp-index": index_path, "yp-book": slug, "yp-book-title": book["title"]}
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
        if p["topic"]:
            meta["yp-crumb"] = short_label(p, lang == "zh") + ("（作业）" if p["kind"] == "homework" else "")
        md = run_pandoc(macros + brace_macros(preprocess(p["tex"], lang), macros), meta)
        (out / f"{p['file']}.qmd").write_text(md, encoding="utf-8")
        p["title"] = page_title(md)
        thm_offset += len(re.findall(r"\\begin\{(" + "|".join(NUMBERED_ENVS) + r")\}", clean))
        sec_offset += len(re.findall(r"\\section\{", clean))

    write_book_index(book, pages, out, pdf_name if pdf.exists() else None, progress)
    write_dir_metadata(book, out)
    entries = [json.loads(l) for l in index_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    index_path.unlink()
    labels_path.unlink()
    return pages, entries


def short_label(p, zh):
    """Sidebar / index label: "1. 集合系" from the progress-table topic, else the title."""
    if p.get("topic"):
        name = re.split(r"[，：；（(]", p["topic"])[0].strip()
        return f"{p['no']}. {name}" if zh else name
    return plain_title(p.get("title", ""))


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
         "Omega": "Ω", "varepsilon": "ε", "alpha": "α", "beta": "β", "delta": "δ",
         "varphi": "φ", "phi": "φ", "xi": "ξ", "eta": "η", "theta": "θ", "rho": "ρ",
         "tau": "τ", "kappa": "κ", "gamma": "γ", "Lambda": "Λ", "Phi": "Φ", "chi": "χ"}


def tex_to_unicode(s):
    s = re.sub(r"\\([A-Za-z]+)", lambda m: GREEK.get(m.group(1), m.group(1)), s)
    return re.sub(r"[{}^_]", "", s)


def tex_to_unicode_text(s):
    """Search text for the index: \\sigma -> σ etc., other commands dropped."""
    return re.sub(r"\\([A-Za-z]+)", lambda m: GREEK.get(m.group(1), " "), s)


def write_dir_metadata(book, out):
    meta = {"lang": "zh" if book.get("lang") == "zh" else "en"}
    bib = ROOT / book["source"] / "refs.bib"
    if bib.exists():
        shutil.copy(bib, out / "refs.bib")
        meta["bibliography"] = "refs.bib"
        # numeric [1] citations, as in math papers
        meta["csl"] = "../../assets/csl/american-mathematical-society-numeric.csl"
    (out / "_metadata.yml").write_text(yaml.safe_dump(meta, allow_unicode=True), encoding="utf-8")


def esc(t):
    return html.escape(t, quote=True)


CATEGORY_WORD = {"courses": "Course", "research": "Research notes", "surveys": "Survey"}
LANG_WORD = {"zh": "中文", "en": "English"}


def write_book_index(book, pages, out, pdf_name, progress):
    zh = book.get("lang") == "zh"
    lectures = [p for p in pages if p["kind"] == "lecture"]
    front = [p for p in pages if p["kind"] == "front"]
    first = lectures[0]["file"] + ".html" if lectures else None
    eyebrow = f'{CATEGORY_WORD.get(book.get("category"), "")} · {LANG_WORD.get(book.get("lang"), "")}'
    actions = []
    if first:
        actions.append(f'<a class="yp-btn" href="{first}">{"从第 1 讲开始" if zh else "Start reading"}</a>')
    if pdf_name:
        actions.append(f'<a class="yp-btn yp-btn-ghost" href="{pdf_name}">PDF</a>')
    updated = last_updated(book)
    if updated:
        actions.append(f'<span class="yp-quiet">{"更新于" if zh else "Updated"} {updated}</span>')
    h = [f'<header class="yp-hero yp-hero-book" data-book="{book["slug"]}">',
         f'<div class="yp-eyebrow">{esc(eyebrow)}</div>',
         f'<h1 class="yp-hero-title">{esc(book["title"])}</h1>']
    if book.get("subtitle"):
        h.append(f'<p class="yp-hero-sub">{esc(book["subtitle"])}</p>')
    h.append(f'<div class="yp-actions">{"".join(actions)}</div>')
    h.append(f'<a class="yp-continue" id="yp-continue-book" data-book="{book["slug"]}" '
             f'data-word="{"继续阅读" if zh else "Continue reading"}" hidden></a>')
    h.append("</header>")
    if front:
        links = " ".join(f'<a href="{p["file"]}.html">{esc(plain_title(p["title"]))}</a>' for p in front)
        h.append(f'<nav class="yp-front">{links}</nav>')
    h.append('<ol class="yp-toc">')
    for p in lectures:
        hw = next((q for q in pages if q["kind"] == "homework" and q["unit"] == p["unit"]), None)
        name = p["topic"] or plain_title(p["title"])
        num = p["no"] if zh else re.match(r"\[?(\d+)", plain_title(p["title"]) or "0").group(1)
        if not zh:
            name = re.sub(r"^\d+\s*", "", plain_title(p["title"]))
        aux = (f'<a class="yp-toc-aux" href="{hw["file"]}.html">{"作业" if zh else "Exercises"}</a>'
               if hw else "")
        h.append(f'<li><a class="yp-toc-main" href="{p["file"]}.html"><span class="yp-toc-num">{num}</span>'
                 f'<span class="yp-toc-title">{esc(name)}</span></a>{aux}</li>')
    done = {p["unit"] for p in lectures}
    for f, row in progress.items():
        if f not in done and row.get("正文") == "未开始":
            h.append(f'<li class="yp-toc-todo"><span class="yp-toc-main"><span class="yp-toc-num">'
                     f'{esc(row.get("讲", ""))}</span><span class="yp-toc-title">{esc(row.get("主题", f))}'
                     f'</span></span></li>')
    h.append("</ol>")
    lines = ["---", f"pagetitle: {json.dumps(book['title'], ensure_ascii=False)}", "toc: false", "---", "",
             "```{=html}", "\n".join(h), "```", ""]
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
        text = short_label(p, zh)
        hw = [q for q in pages if q["kind"] == "homework" and q["unit"] == p["unit"]]
        if hw:
            contents.append({"section": text, "href": f"{base}/{p['file']}.qmd",
                             "contents": [{"href": f"{base}/{hw[0]['file']}.qmd",
                                           "text": "作业与解答" if zh else "Exercises"}]})
        else:
            contents.append({"href": f"{base}/{p['file']}.qmd", "text": text})
    return {"id": book["slug"], "title": book["title"], "style": "floating",
            "collapse-level": 1, "contents": contents}


def write_quarto_yml(lib, sidebars):
    cfg = lib["site"]
    site_url = f"https://{cfg['github']}.github.io/{cfg['repo']}/"
    repo = f"https://github.com/{cfg['github']}/{cfg['repo']}"
    q = {
        "project": {"type": "website", "output-dir": "_site",
                    "resources": ["books/*/*.pdf"]},
        "website": {
            "title": cfg["title"],
            "description": cfg.get("description", ""),
            "site-url": site_url,
            "repo-url": repo,
            "search": {"location": "navbar", "type": "overlay"},
            "page-navigation": True,
            "navbar": {"left": [{"href": "index.qmd", "text": "Library"},
                                {"href": "results.qmd", "text": "Index"}],
                       "right": [{"icon": "github", "href": repo}]},
            "sidebar": sidebars,
            "page-footer": {"left": f"© {cfg.get('author', '')}",
                            "right": "Written in LaTeX · read on the web"},
        },
        "format": {"html": {
            "theme": ["cosmo", "assets/library.scss"],
            "html-math-method": "mathjax",
            "include-in-header": "assets/head.html",
            "toc": True, "toc-depth": 2, "toc-title": " ",
            "number-sections": False,
            "anchor-sections": True,
        }},
    }
    (SITE / "_quarto.yml").write_text(
        "# Generated by tools/build.py from library.yml — do not edit by hand.\n"
        + yaml.safe_dump(q, allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_home(lib, built):
    cfg = lib["site"]
    books = lib["books"]

    def row(b):
        slug = b["slug"]
        meta = [LANG_WORD.get(b.get("lang", "en"), "")]
        prog = progress_summary(b)
        if prog:
            meta.append(prog)
        upd = last_updated(b)
        if upd:
            meta.append(upd)
        pdf = (GENERATED / slug / f"{slug}.pdf").exists()
        sub = f'<span class="yp-book-sub">{esc(b["subtitle"])}</span>' if b.get("subtitle") else ""
        return (f'<li class="yp-book"><a class="yp-book-main" href="books/{slug}/index.html">'
                f'<span class="yp-book-title">{esc(b["title"])}</span>{sub}</a>'
                f'<span class="yp-book-meta">{" · ".join(esc(m) for m in meta if m)}</span>'
                + (f'<a class="yp-book-pdf" href="books/{slug}/{slug}.pdf">PDF</a>' if pdf else '<span></span>')
                + '</li>')

    h = ['<header class="yp-hero yp-hero-home">',
         f'<div class="yp-eyebrow">{esc(cfg.get("author", ""))}</div>',
         f'<h1 class="yp-hero-title">{esc(cfg["title"])}</h1>',
         f'<p class="yp-hero-sub">{esc(cfg.get("description", ""))}</p>',
         '<a class="yp-continue" id="yp-continue" data-word="Continue reading" hidden></a>',
         '</header>']
    for c in lib["categories"]:
        shelf = [b for b in books if b.get("category") == c["id"]
                 and b.get("status") == "active" and b["slug"] in built]
        planned = [b for b in books if b.get("category") == c["id"]
                   and (b.get("status") == "planned" or (b.get("status") == "active" and b["slug"] not in built))]
        h.append(f'<section class="yp-shelf"><div class="yp-shelf-head"><h2>{esc(c["title"])}</h2>'
                 f'<p>{esc(c.get("blurb", ""))}</p></div><div class="yp-shelf-body">')
        if shelf:
            h.append('<ul class="yp-books">' + "".join(row(b) for b in shelf) + "</ul>")
        if planned:
            h.append('<p class="yp-planned"><span>In preparation</span>'
                     + "".join(f"<em>{esc(b['title'])}</em>" for b in planned) + "</p>")
        if not shelf and not planned:
            h.append('<p class="yp-planned"><span>Nothing here yet</span></p>')
        h.append("</div></section>")
    shelved = [b for b in books if b.get("status") == "shelved" and b["slug"] in built]
    if shelved:
        h.append(f'<details class="yp-shelved"><summary>Shelved · {len(shelved)}</summary>'
                 '<ul class="yp-books">' + "".join(row(b) for b in shelved) + "</ul></details>")
    lines = ["---", f"pagetitle: {json.dumps(cfg['title'])}", "toc: false", "sidebar: false", "---", "",
             "```{=html}", "\n".join(h), "```", ""]
    (SITE / "index.qmd").write_text("\n".join(lines), encoding="utf-8")


KIND_WORD = {"theorem": "Theorems", "proposition": "Propositions", "lemma": "Lemmas",
             "corollary": "Corollaries", "definition": "Definitions", "conjecture": "Conjectures"}


def write_results(lib, results):
    """results: list of (book, pages, entries) in library order."""
    total = sum(len(e) for _, _, e in results)
    h = ['<header class="yp-hero yp-hero-index">',
         '<div class="yp-eyebrow">Index</div>',
         '<h1 class="yp-hero-title">Results</h1>',
         f'<p class="yp-hero-sub">Every numbered definition and statement across the library — {total} in all.</p>',
         '<div class="yp-idx-controls">',
         '<input id="yp-idx-q" type="search" autocomplete="off" '
         'placeholder="Search by name, number or words — e.g. Fatou, 定理 18, π-λ">',
         '<div class="yp-idx-chips"><button type="button" data-kind="" class="on">All</button>'
         + "".join(f'<button type="button" data-kind="{k}">{w}</button>' for k, w in KIND_WORD.items()
                   if any(x["kind"] == k for _, _, es in results for x in es))
         + "</div>",
         '<p class="yp-idx-count" id="yp-idx-count"></p>',
         "</div></header>"]
    md = ["---", 'pagetitle: "Index of results"', "toc: false", "sidebar: false", "---", "",
          "```{=html}", "\n".join(h), "```", ""]
    for book, pages, entries in results:
        if not entries:
            continue
        zh = book.get("lang") == "zh"
        md += [f'::: {{.yp-idx-book data-book="{book["slug"]}"}}', "",
               f'## {book["title"]} {{.unnumbered .unlisted}}', ""]
        by_page = {}
        for e in entries:
            by_page.setdefault(e["page"], []).append(e)
        for p in pages:
            es = by_page.get(p["file"])
            if not es:
                continue
            label = short_label(p, zh) if p["kind"] != "front" else plain_title(p["title"])
            if p["kind"] == "homework":
                label += "（作业）" if zh else " — exercises"
            md += ['::: {.yp-idx-group}', "", f"### {label} {{.unnumbered .unlisted}}", ""]
            for e in es:
                link = f"books/{book['slug']}/{e['page']}.qmd" + (f"#{e['id']}" if e.get("id") else "")
                text = re.sub(r"\s+", " ", tex_to_unicode_text(e["text"])).replace('"', "'")
                name = f" [{e['note']}]{{.yp-idx-name}}" if e["note"] else ""
                md += [f'::: {{.yp-idx-item data-kind="{e["kind"]}" data-text="{esc(text)}"}}',
                       f"[{e['label']}]({link}){{.yp-idx-label}}{name} [{e['snippet']}]{{.yp-idx-snippet}}",
                       ":::", ""]
            md += [":::", ""]
        md += [":::", ""]
    (SITE / "results.qmd").write_text("\n".join(md), encoding="utf-8")


def progress_summary(book):
    if not book.get("progress"):
        return ""
    rows = parse_progress(ROOT / book["progress"])
    if not rows:
        return ""
    written = sum(1 for r in rows.values() if r.get("正文") not in ("未开始", ""))
    return f"{written} / {len(rows)} lectures"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-latex", action="store_true", help="reuse existing .aux/.pdf")
    ap.add_argument("--render", action="store_true", help="run quarto render afterwards")
    a = ap.parse_args()

    lib = yaml.safe_load((ROOT / "library.yml").read_text(encoding="utf-8"))
    sidebars, built, results = [], set(), []
    for b in lib["books"]:
        if not b.get("source") or b.get("status") == "planned":
            continue
        log(f"book {b['slug']}")
        pages, entries = build_book(b, a.no_latex)
        sidebars.append(sidebar_for(b, pages))
        built.add(b["slug"])
        results.append((b, pages, entries))
    write_quarto_yml(lib, sidebars)
    write_home(lib, built)
    write_results(lib, results)
    if a.render:
        subprocess.run([QUARTO, "render"], cwd=SITE, check=True)


if __name__ == "__main__":
    main()
