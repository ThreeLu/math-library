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
- 鼠标停在交叉引用（定理/公式/习题/图的编号、文献、索引条目）上，会弹出目标内容的预览；用手指或笔点时，第一次点显示预览，再点或点“Go to”才跳转（按每次点击的输入方式判断，不按设备判断，接了触控板的平板也一样）。预览由 `head.html` 在浏览器里取目标页面、按 id 截取，构建流程不参与，所以新增的环境只要输出带 id 的元素就能预览。
- 正文右侧的“本页”目录由 `head.html` 根据页内 h2/h3 生成（Quarto 自带的目录看不到 `.yp-body` 里的标题），滚动时高亮当前小节，屏宽不足 1200px 时隐藏。
- 左右两栏目录都可以收起（屏幕边缘的小拉手，或键盘 `[`、`]`），正文随之加宽；选择存在 localStorage 的 `yp:layout` 里，翻页后保持。
- 书的目录页不显示左栏（正文就是目录）；左栏里每讲的“作业”是行尾的小链接，由 `head.html` 从 Quarto 的折叠小节改出来。
- 深色模式跟随系统：整页 `filter: invert(0.92) hue-rotate(180deg)`，TikZ 图随之反色，不必单独配色。
- 点交叉引用（定理/公式编号、文献、索引条目）跳转后，右下角出现“返回”按钮（键盘 `b`），可逐级退回跳转前的位置，跨页面也有效；记录存在 sessionStorage 里，关掉标签页即清空。

## AI 问答（只在作者自己的浏览器里）

- 在任一页网址后加 `#ai` 打开设置，填 DeepSeek API key、GitHub token、记录仓库（默认 `ThreeLu/math-library-notes`，私有）。这些只存在该浏览器的 localStorage `yp:ai` 里；没填 key 的浏览器不加载 `site/assets/ai.js`，读者看不到这个功能。
- 选中正文 → “问 AI” → 右侧面板（窄屏为底部面板）。键盘 `a` 重新打开面板。模型 `deepseek-chat`，浏览器直接调用 API。
- 发给模型的上下文：本页 LaTeX 源码、记号宏、选中部分（公式还原成 TeX）。源码由 `tools/build.py` 的 `write_page_sources` 写到 `books/<slug>/src/<页>.tex`，`src/book.json` 带书名、记号宏和构建时的提交号。
- 每段对话存成记录仓库里的 `<书>/<页>/<日期时间>-<定理名>.md`：front matter 有 book、page、anchor（定理 id 和编号）、commit、note（作者备注）；`<!-- yp:q -->` / `<!-- yp:a -->` 标出问答轮次，面板的“记录”按它读回。改讲义时 clone 这个仓库，按书和页读记录。

## 新增、收纳一本书

1. 复制 `templates/english-book/` 到 `books/<slug>/`（中文书照 `books/advanced-probability/` 的结构）。
2. 在 `library.yml` 里加一条，`status: active`，填 `source` 和 `main`。
3. `make site` 检查。
收纳：把 `status` 改成 `shelved`，书移到首页底部的折叠区，网址不变。

## Git

- `git push` 就是发布网站。AI 只在本地提交，推送由作者决定。
- 参考书籍（有版权）与编译输出不进 git，见 `.gitignore`。
