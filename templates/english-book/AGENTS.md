# Writing conventions for English books

These notes are read on the web and as a PDF. The source is LaTeX with `\documentclass[english]{yupin-notes}`; see the repository `AGENTS.md` for how pages are built.

## 1. Model: Richard Montgomery's papers

Write the way Richard Montgomery writes his arXiv papers (e.g. *Spanning trees in random graphs*, *A proof of Ringel's conjecture* with Pokrovskiy and Sudakov):

- **Structure of a topic.** Introduction (the problem, its history with precise attributions, the results covered) → *Proof outline* or *Overview* before any technical section → *Preliminaries* (notation, probabilistic tools, known lemmas with citations) → technical sections, each built around one or two lemmas → *Concluding remarks* with open problems.
- **Explain the idea before the proof.** Before a long proof, say in a paragraph what the proof does and why it should work. Name the key objects (absorbers, switchers, templates, …) and keep the names fixed.
- **Voice.** First person plural ("we show", "we will use"). Plain declarative sentences. No rhetorical questions, no "it is worth noting", no "crucially", no summaries that repeat what was just said.
- **Constants.** State hierarchies as $1/n \ll \varepsilon \ll \alpha$ and say once, in the notation section, what $\ll$ means.
- **Citations.** Every result not proved here gets a reference with \cite. Attribute precisely ("Keevash, Pokrovskiy, Sudakov and Yepremyan~\cite{...} proved ...").

## 2. Statements

- Environments: `theorem`, `lemma`, `proposition`, `corollary`, `claim`, `conjecture`, `observation` (italic body); `definition`, `remark`, `example`, `question` (upright body). All share one counter numbered within the section: Lemma 2.1, Definition 2.2, …
- Name a statement with its optional argument only when it has a standard name: `\begin{theorem}[Hall]`.
- Inside long proofs, isolate steps as `claim`s with their own short proofs.
- Every statement that is referred to gets `\label{type:slug:name}`, e.g. `lem:greedy:extend`; refer with `Lemma~\ref{...}`, equations with `\eqref{...}`.
- Exercises (course notes only) use `\homework`, `exercises`, `probleme`, `questions`, `solution` exactly as in the Chinese books; solutions are collapsed on the web.

## 3. Files

- One `\section` per file in `sections/`, file name = English slug; order is the `\input` order in `main.tex`. Each file becomes one web page.
- New notation macros go in `shared/latex/yupin-notes-en.clo` under *Notation*, not in section files.
- References in `refs.bib` next to `main.tex`. Check every bibliographic detail; never invent volume or page numbers. Leave a field out if unsure.

## 4. Correctness

- Every proof must be complete and checked. If an argument is only sketched, say "sketch" explicitly.
- A statement whose truth you have not verified (a claimed bound, an attribution, a year) is not written down until it is checked against the source.
