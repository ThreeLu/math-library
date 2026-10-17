# 于品式课堂笔记模版 · 使用说明

## 文件

| 文件 | 作用 |
|---|---|
| `yupin-notes.cls` | 文档类。版式仿照于品《数学分析之课程讲义》，末尾定义了概率论记号宏。 |
| `高等概率论.tex` | 主文件：封面、前言、参考书目、目录，按顺序 `\input` 各讲。 |
| `课程设置.tex` | 书名、副标题、学年、作者、单位、作业框标题栏。 |
| `front/preface.tex`、`front/references.tex` | 前言与参考书目。 |
| `lectures/<slug>.tex` | 每讲一个文件，文件名是主题英文短名，讲次只由主文件中的引入顺序决定。 |
| `figures/` | TikZ 图与图片；`cover-emblem.tex` 为封面装饰（二项分布直方图与正态曲线）。 |
| `模版示例.tex` / `build/模版示例.pdf` | 每个环境都用一遍的示例，不确定怎么写时照着抄。 |

## 编译

```sh
cd 讲义
xelatex -output-directory=build 高等概率论.tex   # 两遍
```

## 新建一讲

```tex
% !TEX root = ../高等概率论.tex
\lecture{σ-代数与生成的 σ-代数，Borel σ-代数，π-类、λ-类与 π-λ 定理}
\label{lec:sigma-algebras}

导入正文……

\topic{σ-代数}
……

\homework{π-λ 定理的应用}
……
```

然后在 `高等概率论.tex` 中按顺序加一行 `\input{lectures/sigma-algebras}`。

## 接口速查

```tex
% ---- 一讲 ----
\lecture{罗列本讲知识点的标题，可以很长}      % 另起一页，编号 1, 2, 3, ...
\topic{讲内小标题}                            % 不编号、不进目录
% summary 方框导语环境仍保留在模版中，但本讲义不使用

% ---- 数学陈述：定义、命题、引理、定理、推论共用全书连续编号，正文为楷体 ----
\begin{definition}[名称]\label{def:slug:xxx} ... \end{definition}
\begin{theorem}[名称]\label{thm:slug:xxx} ... \end{theorem}
\begin{proposition} \begin{lemma} \begin{corollary}
\begin{theorem*}[Carathéodory 扩张定理] ... \end{theorem*}   % 带 * 不编号
\begin{proof} ... \end{proof}                                % 小号楷体“证明:”，结尾 □
\appendixstatements   % 附录 \section 之后：改排“定理 A.1”，从 1 重新计数

% ---- 不编号的段落（楷体）----
\begin{example}[可选标题]\label{ex:slug:xxx} 例子 \end{example}   % 排作“例子.”，与于品一致
\egref{ex:slug:xxx}                             % 引用不编号的例子：“第 N 页的例子”
\begin{workedexample}[可选标题]\label{we:slug:xxx} 题目 \end{workedexample}   % 例题，排作“例题.”
\begin{solution} 完整解答 \end{solution}       % 解答：绿色细线方框，“解答:”起头，可跨页
\wegref{we:slug:xxx}                            % 引用例题：“第 N 页的例题”
\showsolutionsfalse                             % 写在主文件导言区：隐去全部解答，编自测版
\begin{remark} 注记 \end{remark}
\begin{practice} 练习 \end{practice}
\begin{question} 问题 \end{question}
\begin{thinking} 思考题 \end{thinking}
\begin{historynote} 历史注记 \end{historynote}

% ---- 强调 ----
\term{加黑的术语}  \blueterm{蓝色的对象名}  \red{红色提醒}  \uline{下划线}
\marginterm{σ-代数}  \marginnote{(\ref{thm:slug:xxx})}      % 页边标注（可选）

% ---- 作业（讲下的编号小节，另起一页，带绿色标题栏的框）----
\homework{作业的大结果}[目录短标题]                 % N.1 作业：……
\homework*{自定作业标题}                             % 不加“作业：”
\exercisepart{基本习题}
\begin{exercises}{A}{课堂内容的补充}                % 习题 A：……，题号 A1) A2) ...
  \item\label{ex:slug:A1} ...                        % \exref{ex:slug:A1} 得到“A1)”
  \begin{solution} 每道题、每一小问后面紧跟解答 \end{solution}
\end{exercises}
\begin{probleme}{B}{Kolmogorov 三级数定理}           % 法式大题，题号 B1) B2) ...
  引导语
  \begin{questions} \item ... \begin{questions} \item 子问 B2-1) \end{questions} \end{questions}
  过渡文字
  \begin{questions}[resume] \item ... \end{questions}
\end{probleme}
\thinkingpart                                        % 小节标题“思考题”
\begin{probleme}[问题]{D}{……}                        % 问题 D：……
\begin{probleme}*[问题]{E}{……}                       % 问题 E*：难题
\exercisepart{课外知识：……}
```

## 概率论记号宏

| 宏 | 效果 | 宏 | 效果 |
|---|---|---|---|
| `\R \N \Z \Q \C` | 黑板粗体 | `\cA \cB \cC \cD \cF \cG \cH \cL \cP \cS \cT` | 花体字母 |
| `\Var \Cov \sgn \esssup` | 算子 | `\one_A` | $1_A$ |
| `\as` | a.s. | `\aeverywhere` | a.e. |
| `\iid` | i.i.d. | `\eqd` | 同分布 $\stackrel{d}{=}$ |
| `\toas` | $\xrightarrow{\text{a.s.}}$ | `\toP` | $\xrightarrow{P}$ |
| `\toLp`、`\toLp[2]` | $\xrightarrow{L^p}$ | `\dd` | 积分中的 $\,\mathrm d$ |
| `\abs{x}` `\norm{x}` `\set{x}` | 绝对值、范数、花括号 | `\given` | 条件竖线 |

弱收敛直接写 `\Rightarrow`。

## 于品作业的三部分

**基本习题**（习题 A 课堂内容的补充；习题 B、C…… 法式大题），**思考题**（问题的字母接着往下排，难题加 *），**课外知识**（课堂之外的一个完整结果，同样用法式大题）。每道题（法式大题的每一小问）后面紧跟详细解答（`solution` 环境）。
