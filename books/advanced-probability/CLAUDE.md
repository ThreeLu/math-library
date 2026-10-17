@AGENTS.md

## Claude Code 补充说明

- 读 PDF：有文字层的书可以用 Read 工具的 `pages` 参数直接读指定页（一次最多 20 页），或者用 `pdftotext`、PyMuPDF 提取；公式排版乱时，用 PyMuPDF 或 `pdftoppm` 把页面渲染成 PNG，再用 Read 看图。
- 备课手册里给的是 PDF 页码，Read 工具的 `pages` 参数用的也是 PDF 页码，二者一致。
- 这台机器上 Python 的 `urllib` 有证书问题，联网请用 `curl`。
- 抽查版面：`pdftoppm -r 60 -png -f 页 -l 页 build/高等概率论.pdf <scratchpad>/p`，再用 Read 看图。
