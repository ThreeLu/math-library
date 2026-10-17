% =====================================================================
%  yupin-notes.cls —— 于品式课堂笔记模版（高等概率论）
%
%  版式仿照于品《数学分析之课程讲义》（清华大学，2020）：
%    * ctexart，12pt，宋体正文 / 黑体粗体 / 楷体“斜体”，西文 Latin Modern，数学 CM；
%    * 每一讲是一个 \section，另起一页，标题罗列本讲知识点；讲内小标题不编号（\topic）；
%    * 方框导语（summary 环境）；
%    * 定义、命题、引理、定理、推论共用一个贯穿全书的计数器，正文用楷体；
%    * 例子、注记、练习、问题不编号（与于品一致）；证明用小号楷体“证明:”起头，结尾 □；
%    * 作业是讲下的编号小节“N.1 作业：……”，另起一页，带深绿标题栏的灰底圆角框；
%      “基本习题 / 习题 A：… / 习题 B：…（法式大题）/ 思考题 / 课外知识”，题号 A1) B7-1)；
%    * 目录与交叉引用使用 hyperref 默认的红色链接框；页码在页底居中，无页眉。
%
%  类选项：
%    letterpaper 改用 Letter 纸（于品原版的纸型）；缺省为 A4。
% =====================================================================
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{yupin-notes}[2026/09/15 v2.0 Yu Pin style course notes (probability)]

\newif\ifyp@letter    \yp@letterfalse
\DeclareOption{letterpaper}{\yp@lettertrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{ctexart}}
\ProcessOptions\relax

\LoadClass[UTF8,12pt,fontset=none]{ctexart}

% ---------------------------------------------------------------------
%  版面
% ---------------------------------------------------------------------
\ifyp@letter
  \RequirePackage[letterpaper,textwidth=16.3cm,hcentering,top=2.6cm,bottom=2.9cm,marginparwidth=2cm,marginparsep=2.5mm]{geometry}
\else
  \RequirePackage[a4paper,textwidth=16.3cm,hcentering,top=2.6cm,bottom=2.9cm,marginparwidth=2cm,marginparsep=2.5mm]{geometry}
\fi
\pagestyle{plain}
\setlength{\emergencystretch}{3em}

% ---------------------------------------------------------------------
%  字体：宋体 / 黑体（粗体）/ 楷体（斜体），缺字体时依次回退
% ---------------------------------------------------------------------
\IfFontExistsTF{Songti SC}{%
  \IfFontExistsTF{Kaiti SC}{%
    \setCJKmainfont{Songti SC}[BoldFont=Heiti SC,ItalicFont=Kaiti SC,BoldItalicFont=Heiti SC]%
  }{%
    \setCJKmainfont{Songti SC}[BoldFont=Heiti SC,ItalicFont=FandolKai-Regular.otf,BoldItalicFont=Heiti SC]%
  }%
  \setCJKsansfont{Heiti SC}%
}{\IfFontExistsTF{STSong}{%
  \setCJKmainfont{STSong}[BoldFont=STHeiti,ItalicFont=STKaiti,BoldItalicFont=STHeiti]%
  \setCJKsansfont{STHeiti}%
  \IfFontExistsTF{STFangsong}{\setCJKmonofont{STFangsong}}{}%
}{\IfFontExistsTF{SimSun}{%
  \setCJKmainfont{SimSun}[BoldFont=SimHei,ItalicFont=KaiTi,BoldItalicFont=SimHei]%
  \setCJKsansfont{SimHei}\setCJKmonofont{FangSong}%
}{%
  \setCJKmainfont{FandolSong-Regular.otf}[BoldFont=FandolHei-Regular.otf,ItalicFont=FandolKai-Regular.otf,BoldItalicFont=FandolHei-Regular.otf]%
  \setCJKsansfont{FandolHei-Regular.otf}\setCJKmonofont{FandolFang-Regular.otf}%
}}}
% 西文保持 fontspec 默认的 Latin Modern；数学保持 Computer Modern。

% ---------------------------------------------------------------------
%  宏包
% ---------------------------------------------------------------------
\RequirePackage{amsmath,amssymb,amsthm,mathtools}
\RequirePackage{graphicx}
\RequirePackage[dvipsnames,svgnames]{xcolor}
\RequirePackage{enumitem}
\RequirePackage{booktabs,array}
\RequirePackage{tikz}
\usetikzlibrary{cd,arrows.meta,calc,positioning,decorations.pathreplacing}
\RequirePackage{xeCJKfntef}          % \CJKunderline：中西文混排下划线
\RequirePackage[most]{tcolorbox}
\RequirePackage{environ}
\RequirePackage{etoolbox}
\RequirePackage{xparse}
\RequirePackage{newunicodechar}
% 选读标记 ★：第一遍可以跳过的小节、定理或证明
\newunicodechar{★}{\ensuremath{^{\bigstar}}}
\RequirePackage[unicode,bookmarksnumbered,bookmarksopen]{hyperref}
% 与于品原版一致：不给链接上色，保留 hyperref 默认的红色链接框。
\hypersetup{pdfborder={0 0 1}}

% 前置内容用小写罗马页码，目录独立用大写罗马页码，正文从 1 开始。
\AddToHook{cmd/tableofcontents/before}{\clearpage\pagenumbering{Roman}}
\AddToHook{cmd/tableofcontents/after}{\clearpage\pagenumbering{arabic}}

% 比较符号统一写成 \leqslant、\geqslant 的样子
\let\leq\leqslant \let\geq\geqslant \let\le\leqslant \let\ge\geqslant

% ---------------------------------------------------------------------
%  标题：讲 = section（另起一页），讲下小节 = subsection（作业、考试等）
% ---------------------------------------------------------------------
\ctexset{
  section = {
    format      = \Large\bfseries\raggedright,
    name        = {,},
    number      = \arabic{section},
    aftername   = \hspace{0.9em},
    hang        = true,
    beforeskip  = 0.5ex plus .2ex,
    afterskip   = 2.2ex plus .2ex,
    indent      = 0pt,
  },
  subsection = {
    format      = \large\bfseries\raggedright,
    aftername   = \hspace{0.9em},
    hang        = true,
    beforeskip  = 3.2ex plus 1ex minus .2ex,
    afterskip   = 1.6ex plus .2ex,
    indent      = 0pt,
  },
  subsubsection = {
    format      = \normalsize\bfseries\raggedright,
    beforeskip  = 2.2ex plus .5ex,
    afterskip   = 1ex,
    indent      = 0pt,
  },
}
\setcounter{secnumdepth}{2}
\setcounter{tocdepth}{2}

% 一讲：另起一页，标题罗列本讲的知识点（可以很长）
\NewDocumentCommand{\lecture}{o m}{%
  \clearpage
  \IfValueTF{#1}{\section[#1]{#2}}{\section{#2}}}

% 讲内小标题：不编号、不进目录
\newcommand{\topic}[1]{\subsection*{#1}}

% ---------------------------------------------------------------------
%  文字强调
% ---------------------------------------------------------------------
\definecolor{ypred}{rgb}{1,0,0}
\definecolor{ypblue}{rgb}{0,0,1}
\definecolor{ypgreen}{rgb}{0.0,0.26,0.0}
\newcommand{\term}[1]{\textbf{#1}}                 % 新术语：加黑（黑体）
\newcommand{\blueterm}[1]{\textcolor{ypblue}{#1}}  % 蓝色标出的对象名
\newcommand{\red}[1]{\textcolor{ypred}{#1}}        % 红色提醒
\newcommand{\blue}[1]{\textcolor{ypblue}{#1}}
\renewcommand{\uline}[1]{\CJKunderline{#1}}        % 下划线强调（ulem 的 \uline 不认中文，改用 xeCJKfntef）

% 页边标注（可选）：术语第一次出现时把它印在页边，引用旧结果时把编号印在页边
%   \marginterm{σ-代数}               正文加黑，页边同时印出“σ-代数”
%   \marginterm[σ-代数]{sigma 代数}   正文与页边的写法不同
%   \marginnote{(\ref{thm:pi-lambda})} 页边只印一条小注
\RequirePackage{marginnote}
\renewcommand*{\marginfont}{\footnotesize\itshape\raggedright}
\NewDocumentCommand{\marginterm}{o m}{\textbf{#2}\marginnote{\IfValueTF{#1}{#1}{#2}}}

% ---------------------------------------------------------------------
%  方框导语（于品每节开头的细线方框）
% ---------------------------------------------------------------------
\newtcolorbox{summary}{
  enhanced, breakable, sharp corners,
  colback=white, colframe=black, boxrule=0.5pt,
  left=3pt, right=3pt, top=1pt, bottom=1pt,
  before skip=1ex, after skip=1.6ex,
  parbox=false, before upper={\parindent=0pt}}

% ---------------------------------------------------------------------
%  数学陈述
%  定义、命题、引理、定理、推论共用一个贯穿全书的计数器（不按讲重置）；
%  带 * 的版本不编号（于品常写“定义 (序关系).”“定理 (Schroeder-Bernstein).”）。
%  例子、注记、练习、问题、思考题不编号（于品原版如此）。正文为楷体。
% ---------------------------------------------------------------------
\newtheoremstyle{yupin}%
  {1.2ex plus .4ex}{1.2ex plus .4ex}%
  {\itshape}{0pt}%
  {\bfseries}{.}{0.5em}%
  {\thmname{#1}\thmnumber{ #2}\thmnote{ {\normalfont\upshape(#3)}}}
\theoremstyle{yupin}
\newtheorem{definition}{定义}
\newtheorem{proposition}[definition]{命题}
\newtheorem{lemma}[definition]{引理}
\newtheorem{theorem}[definition]{定理}
\newtheorem{corollary}[definition]{推论}
\newtheorem*{definition*}{定义}
\newtheorem*{proposition*}{命题}
\newtheorem*{lemma*}{引理}
\newtheorem*{theorem*}{定理}
\newtheorem*{corollary*}{推论}
\newtheorem*{remark}{注记}
\newtheorem*{example}{例子}
\newtheorem*{practice}{练习}
\newtheorem*{question}{问题}
\newtheorem*{thinking}{思考题}
\newtheorem*{historynote}{历史注记}
% 不编号的环境没有自己的锚点；在开头放 \phantomsection，使 \label 指向正确位置。
\AtBeginEnvironment{example}{\phantomsection}
\AtBeginEnvironment{remark}{\phantomsection}
\AtBeginEnvironment{practice}{\phantomsection}
% 引用不编号的例子：\egref{标签} 排作“第 N 页的例子”并带链接；\egref[文字]{标签} 自定文字
\NewDocumentCommand{\egref}{o m}{\hyperref[#2]{\IfValueTF{#1}{#1}{第~\pageref*{#2}~页的例子}}}

% 例题（不编号，排作“例题.”），后面紧跟 solution 环境给出解答；
% 引用例题：\wegref{标签} 排作“第 N 页的例题”
\newtheorem*{workedexample}{例题}
\AtBeginEnvironment{workedexample}{\phantomsection}
\NewDocumentCommand{\wegref}{o m}{\hyperref[#2]{\IfValueTF{#1}{#1}{第~\pageref*{#2}~页的例题}}}

% 解答：左侧绿色细线、浅底色的可跨页方框，小号楷体“解答:”起头。
% 用于例题之后与作业每道题（每一小问）之后。
% 在导言区或主文件中写 \showsolutionsfalse 可以隐去全部解答，编出自测用的版本。
\newif\ifshowsolutions \showsolutionstrue
\newtcolorbox{yp@solutionbox}{
  breakable, enhanced, frame hidden, boxrule=0pt, arc=0pt,
  colback=ypgreen!4,
  borderline west={1.2pt}{0pt}{ypgreen!70},
  left=2.2mm, right=1.2mm, top=.8mm, bottom=.8mm,
  before skip=.8ex plus .2ex, after skip=1.2ex plus .3ex,
  parbox=false, before upper={\parindent=2em}}
\NewDocumentEnvironment{solution}{O{解答} +b}{%
  \ifshowsolutions
    \begin{yp@solutionbox}\normalfont\noindent{\small\itshape #1:}\ \ignorespaces#2\hfill$\square$\end{yp@solutionbox}%
  \fi}{}

% 附录内的定义、命题、引理、定理、推论另起编号，排作“定理 A.1”；
% 在附录的 \section 之后使用，不影响正文各讲的连续编号。
\newcommand{\appendixstatements}{%
  \setcounter{definition}{0}%
  \renewcommand{\thedefinition}{\thesection.\arabic{definition}}%
  \def\theHdefinition{appendix.\thesection.\arabic{definition}}}

% 证明：小号楷体“证明:”起头，正文宋体，结尾 □
\renewenvironment{proof}[1][证明]{%
  \par\addvspace{1ex plus .3ex}\pushQED{\qed}%
  \normalfont\noindent{\small\itshape #1:}\ \ignorespaces}%
  {\popQED\par\addvspace{1ex plus .3ex}}

% 列表：1) 2) 3)；嵌套 a) b)；无序列表 • 与 –
\setlist[enumerate,1]{label=\arabic*),leftmargin=2.2em,itemsep=.3ex,topsep=.8ex}
\setlist[enumerate,2]{label=\alph*),itemsep=.2ex}
\setlist[itemize]{itemsep=.3ex,topsep=.8ex}

% ---------------------------------------------------------------------
%  作业
%    \homework{作业的大结果}
%    \exercisepart{基本习题}  /  \exercisepart{课外知识：……}
%    \begin{exercises}{A}{课堂内容的补充}[可选的红色说明] \item ... \end{exercises}
%    \begin{probleme}{B}{Kolmogorov 三级数定理}  引导语
%       \begin{questions} \item ... \end{questions}
%       中间的过渡文字……
%       \begin{questions}[resume] \item ... \end{questions}
%    \end{probleme}
% ---------------------------------------------------------------------
\newcounter{homework}
% 作业框标题栏；在导言区用 \homeworkheader{……} 修改，#1 处放作业序号
\newcommand{\yp@hwheader}[1]{高等概率论，作业 #1}
\newcommand{\homeworkheader}[1]{\renewcommand{\yp@hwheader}[1]{#1}}
% 作业说明文字；可在导言区用 \homeworkrules{……} 修改
\newcommand{\yp@hwrules}{作业供课后自学使用，不提交。每道题与每个小问后面紧跟解答，建议先自己想几分钟再读。法式大题请按顺序完成：后一问可以直接使用前面各问的结论。}
\newcommand{\homeworkrules}[1]{\renewcommand{\yp@hwrules}{#1}}

\newtcolorbox{hwbox}[1]{
  enhanced, arc=1.6mm, boxrule=1.1pt,
  colframe=black!75, colback=black!6,
  colbacktitle=ypgreen, coltitle=white,
  fonttitle=\bfseries, title={\hspace{0.8em}#1},
  toptitle=0.6mm, bottomtitle=0.6mm,
  left=3.2mm, right=3.2mm, top=1.4mm, bottom=1.6mm,
  before skip=1.2ex, after skip=3ex,
  parbox=false, before upper={\parindent=0pt}}

% \homework*[提交时间]{自定标题}[目录短标题]：带星号时小节标题不加“作业：”前缀
\NewDocumentCommand{\homework}{s o m o}{%
  \clearpage
  \stepcounter{homework}%
  \IfBooleanTF{#1}{%
    \IfValueTF{#4}{\subsection[#4]{#3}}{\subsection{#3}}}{%
    \if\relax\detokenize{#3}\relax
      \subsection{作业}%
    \else
      \IfValueTF{#4}{\subsection[作业：#4]{作业：#3}}{\subsection{作业：#3}}%
    \fi}%
  \begin{hwbox}{\yp@hwheader{\thehomework}}
    \yp@hwrules
    \IfValueT{#2}{本次作业的提交时间和地点为\textbf{#2}，逾期视作零分。}
  \end{hwbox}}

\newcommand{\exercisepart}[1]{\subsection*{#1}}

\def\yp@group{A}
\newlist{questions}{enumerate}{2}
\setlist[questions,1]{label=\upshape\yp@group\arabic*),ref=\yp@group\arabic*,
  leftmargin=2.9em,labelsep=0.45em,align=right,itemsep=1.1ex,topsep=1.2ex}
\setlist[questions,2]{label=\upshape\yp@group\arabic{questionsi}-\arabic*),
  ref=\yp@group\arabic{questionsi}-\arabic*,
  leftmargin=3.6em,labelsep=0.45em,align=right,itemsep=.6ex,topsep=.6ex}

% 习题 A、B：自动开出题目列表
\NewDocumentEnvironment{exercises}{m m o}{%
  \par\addvspace{1.6ex}\noindent\textbf{习题 #1：#2}\par
  \IfValueT{#3}{\noindent\red{（#3）}}%
  \gdef\yp@group{#1}%
  \begin{questions}}
  {\end{questions}\par\addvspace{1ex}}

% 习题 C、D……：法式大题；标题后可写引导语，题目用 questions 列表
%   \begin{probleme}{C}{Schroeder-Bernstein 定理}        → 习题 C：Schroeder-Bernstein 定理
%   \begin{probleme}[问题]{G}{Banach-Mazur 游戏}         → 问题 G：Banach-Mazur 游戏（思考题里用）
%   \begin{probleme}*[问题]{J}{……}                       → 问题 J*：……（带星号表示难题）
%   标题留空 {} 时只排“习题 C”
\NewDocumentEnvironment{probleme}{s O{习题} m m}{%
  \par\addvspace{1.6ex}\noindent
  \textbf{#2 #3\IfBooleanT{#1}{*}\if\relax\detokenize{#4}\relax\else：#4\fi}\par
  \gdef\yp@group{#3}\ignorespaces}
  {\par\addvspace{1ex}}

% 于品作业的三部分：
%   \exercisepart{基本习题}                习题 A（课堂内容的补充）、习题 B、C……
%   \thinkingpart                          思考题，问题字母接着往下排（问题 G、H……）
%   \exercisepart{课外知识：……}            课堂之外的一个完整结果，或者选做、阅读材料
\newcommand{\thinkingpart}[1][思考题]{\subsection*{#1}}

% 引用习题：\ref{label} 给出 A4、B7-1 一类题号
\newcommand{\exref}[1]{\ref{#1})}

% ---------------------------------------------------------------------
%  封面与前置部分
% ---------------------------------------------------------------------
% 封面：标题、副标题、学年；页面下方为作者、单位、日期（留空的项不排）
\newcommand{\yp@title}{高等概率论}
\newcommand{\yp@subtitle}{}
\newcommand{\yp@year}{}
\newcommand{\yp@author}{}
\newcommand{\yp@inst}{}
\newcommand{\yp@date}{}
\newcommand{\coursetitle}[1]{\renewcommand{\yp@title}{#1}}
\newcommand{\coursesubtitle}[1]{\renewcommand{\yp@subtitle}{#1}}
\newcommand{\courseyear}[1]{\renewcommand{\yp@year}{#1}}
\newcommand{\courseauthor}[1]{\renewcommand{\yp@author}{#1}}
\newcommand{\courseinstitution}[1]{\renewcommand{\yp@inst}{#1}}
\newcommand{\coursedate}[1]{\renewcommand{\yp@date}{#1}}
\newcommand{\yp@ifset}[2]{\if\relax\detokenize\expandafter{#1}\relax\else#2\fi}

% 封面中部的装饰图（figures/cover-emblem.tex）；不想要时在主文件里写 \renewcommand{\coveremblem}{}。
\IfFileExists{figures/cover-emblem.tex}
  {\input{figures/cover-emblem}}
  {\newcommand{\coveremblem}{}}

% 书名后缀：封面排作“高等概率论 之 课堂笔记”
\newcommand{\yp@kind}{课堂笔记}
\newcommand{\coursekind}[1]{\renewcommand{\yp@kind}{#1}}

\newcommand{\makecoursetitle}{%
  \hypersetup{pdftitle={\yp@title 之\yp@kind},pdfauthor={\yp@author}}%
  \hypersetup{pageanchor=false}%
  \pagenumbering{gobble}%
  \begin{titlepage}\thispagestyle{empty}\centering
    \vspace*{2.2cm}
    {\Large \yp@title\ {\small 之}\ \yp@kind\par}
    \vspace{1.2ex}
    \yp@ifset{\yp@subtitle}{{\small \yp@subtitle\par}}
    \vspace{4.5ex}
    \yp@ifset{\yp@year}{{\normalsize \yp@year\par}}
    \vfill
    \coveremblem\par
    \vfill
    \yp@ifset{\yp@author}{{\large \yp@author\par}\vspace{3ex}}
    \yp@ifset{\yp@inst}{{\large \yp@inst\par}\vspace{3ex}}
    \yp@ifset{\yp@date}{{\normalsize \yp@date\par}}
    \vspace*{1.6cm}
  \end{titlepage}%
  \pagenumbering{roman}%
  \hypersetup{pageanchor=true}}

% 前言、声明、参考书目等：不编号、不进目录
\newcommand{\frontsection}[1]{\clearpage\section*{#1}}

% ---------------------------------------------------------------------
%  概率论记号（约定见 AGENTS.md 第六节）
% ---------------------------------------------------------------------
\RequirePackage{bm}
\newcommand{\R}{\mathbb{R}}
\newcommand{\N}{\mathbb{N}}
\newcommand{\Z}{\mathbb{Z}}
\newcommand{\Q}{\mathbb{Q}}
\newcommand{\C}{\mathbb{C}}
% 花体字母 \cA … \cZ
\newcommand{\cA}{\mathcal{A}}
\newcommand{\cB}{\mathcal{B}}
\newcommand{\cC}{\mathcal{C}}
\newcommand{\cD}{\mathcal{D}}
\newcommand{\cE}{\mathcal{E}}
\newcommand{\cF}{\mathcal{F}}
\newcommand{\cG}{\mathcal{G}}
\newcommand{\cH}{\mathcal{H}}
\newcommand{\cI}{\mathcal{I}}
\newcommand{\cJ}{\mathcal{J}}
\newcommand{\cK}{\mathcal{K}}
\newcommand{\cL}{\mathcal{L}}
\newcommand{\cM}{\mathcal{M}}
\newcommand{\cN}{\mathcal{N}}
\newcommand{\cO}{\mathcal{O}}
\newcommand{\cP}{\mathcal{P}}
\newcommand{\cQ}{\mathcal{Q}}
\newcommand{\cR}{\mathcal{R}}
\newcommand{\cS}{\mathcal{S}}
\newcommand{\cT}{\mathcal{T}}
\newcommand{\cU}{\mathcal{U}}
\newcommand{\cV}{\mathcal{V}}
\newcommand{\cW}{\mathcal{W}}
\newcommand{\cX}{\mathcal{X}}
\newcommand{\cY}{\mathcal{Y}}
\newcommand{\cZ}{\mathcal{Z}}
\newcommand{\one}{1}                                  % 示性函数 \one_A，排作 1_A（与 Durrett 一致）
\DeclareMathOperator{\Var}{Var}
\DeclareMathOperator{\Cov}{Cov}
\DeclareMathOperator{\sgn}{sgn}
\DeclareMathOperator*{\esssup}{ess\,sup}
\newcommand{\as}{\text{a.s.}}                        % 几乎必然
\newcommand{\aeverywhere}{\text{a.e.}}                % 几乎处处（\ae 是 æ，不能占用）
\newcommand{\iid}{i.i.d.}
\newcommand{\eqd}{\stackrel{d}{=}}                   % 同分布
\newcommand{\toas}{\xrightarrow{\text{a.s.}}}
\newcommand{\toP}{\xrightarrow{P}}
\newcommand{\toLp}[1][p]{\xrightarrow{L^{#1}}}
\newcommand{\dd}{\,\mathrm{d}}                       % 积分中的 d：\int f\dd\mu
\newcommand{\abs}[1]{\lvert #1\rvert}
\newcommand{\norm}[1]{\lVert #1\rVert}
\newcommand{\set}[1]{\{#1\}}
\newcommand{\given}{\mid}

\endinput
