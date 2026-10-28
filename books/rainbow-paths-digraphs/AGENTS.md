# 论文稿（Research Topics）

这是作者未发表的论文稿，原稿是单个文件 `~/Desktop/main.tex`，这里已按节拆开；原稿中行内的 `\refstepcounter{equation}…\textup{(\theequation)}` 改成了 `\textup{(\ref{…})}`，`\1`、`\sig` 改成了 `\one`、`\sigma`。网页与 PDF 都由这里的 `main.tex` 和 `sections/` 生成。

- 一节一个文件，按 `main.tex` 里 `\input` 的顺序；`sections/abstract.tex` 是摘要，显示在书的目录页上。
- 文档类是 `\documentclass[english]{yupin-notes}`；只属于这篇论文的记号写在 `notation.tex`（如果有）。
- 原稿更新后，把改动同步到对应的节文件；节标题和 `\label` 写在每个节文件的第一行。
- 不改动数学内容，除非作者要求。
