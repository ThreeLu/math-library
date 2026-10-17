# Math Library · 仓库约定

一个仓库 = 一个网站首页 + 若干本书。每本书用 LaTeX 写（`yupin-notes` 文档类），`tools/build.py` 把它编译成 PDF，并转成网页；GitHub Actions 在每次推送后发布到 GitHub Pages。

## 目录

```text
library.yml            书目登记表：首页、分类、状态（active / shelved / planned）都由它决定
books/<slug>/          每本书一个目录，各有自己的 AGENTS.md（写作约定）
shared/latex/          全站共用的文档类
  yupin-notes.cls        中文版式（于品式）；\documentclass[english]{yupin-notes} 切换英文
  yupin-notes-en.clo     英文版式（Montgomery 式 article）
templates/english-book/ 新建英文书时复制这个目录
tools/build.py         LaTeX → aux/PDF → pandoc → Quarto 页面；生成侧边栏与首页
tools/yp-filter.lua    pandoc 过滤器：编号、定理框、折叠解答、习题题号、交叉引用
site/assets/           网站样式（library.scss）、字体、head.html（解答折叠、继续阅读、索引筛选的脚本）
site/                  其余内容都是生成的，不进 git
```

## 常用命令（仓库根目录）

```sh
make site      # 编译全部 LaTeX，转换，渲染到 site/_site/
make fast      # 不重新编译 LaTeX，直接用现有的 build/*.aux 和 PDF
make preview   # 本地预览 http://localhost:4200
```

## 转换的原理与约束

- 网页上的每个编号（定理、公式、习题 A1)）都取自该书 `build/*.aux`，与 PDF 一致。过滤器还会按文档顺序自己数一遍，两者不一致时在构建日志里报 `counter says … aux says …`。
- 每个 `\input` 的文件是一页；中文讲义里 `\homework` 之后的部分单独成页。
- 只认 `yupin-notes` 定义的环境与宏。新增环境或宏时，要同时改 `tools/build.py` 的 `preprocess`（或 `THEOREM_ENVS`）和 `tools/yp-filter.lua`，然后 `make fast`，确认没有警告、没有 MathJax 报错。
- 记号宏写在 cls（中文）或 clo（英文）的“记号 / Notation”一节，构建时从那里读取，并由 pandoc 在公式里展开。
- 概率与期望全站统一写 `\P`、`\E`（$\mathbb P$、$\mathbb E$），两种语言的文档类都已定义。
- 定理索引（导航栏 Index，`site/results.qmd`）由过滤器在转换时收集：所有编号的定义、命题、引理、定理、推论、猜想，显示编号、名字（环境的可选参数）和陈述的开头。给定理起名字（`\begin{theorem}[Fatou 引理]`）能让它在索引里更好找。
- 首页与书目录页的“继续阅读”只存在读者自己浏览器的 localStorage 里。
- 点交叉引用（定理/公式编号、文献、索引条目）跳转后，右下角出现“返回”按钮（键盘 `b`），可逐级退回跳转前的位置，跨页面也有效；记录存在 sessionStorage 里，关掉标签页即清空。

## 新增、收纳一本书

1. 复制 `templates/english-book/` 到 `books/<slug>/`（中文书照 `books/advanced-probability/` 的结构）。
2. 在 `library.yml` 里加一条，`status: active`，填 `source` 和 `main`。
3. `make site` 检查。
收纳：把 `status` 改成 `shelved`，书移到首页底部的折叠区，网址不变。

## Git

- `git push` 就是发布网站。AI 只在本地提交，推送由作者决定。
- 参考书籍（有版权）与编译输出不进 git，见 `.gitignore`。
