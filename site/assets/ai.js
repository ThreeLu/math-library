// AI questions on the notes: select a passage, ask DeepSeek about it, and each
// conversation is saved as a Markdown file in a private GitHub repository.
// head.html loads this file only in a browser whose settings hold an API key,
// or when the address ends in #ai (which opens the settings). Nothing here is
// secret: the keys live in this browser's localStorage only.
(() => {
  const SETTINGS = "yp:ai", PENDING = "yp:ai:pending";
  const API = "https://api.deepseek.com/chat/completions", MODEL = "deepseek-chat";
  const GITHUB = "https://api.github.com";
  const MARKED = "https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js";
  const DEFAULT_REPO = "ThreeLu/math-library-notes";
  const zh = (document.documentElement.lang || "").startsWith("zh");
  const T = zh ? {
    ask: "问 AI", title: "问 AI", history: "记录", settings: "设置", close: "关闭",
    placeholder: "问点什么……（Enter 发送，Shift+Enter 换行）", send: "发送", stop: "停止",
    note: "备注（可选）：这里哪里没讲清楚、该补哪句话",
    quick: [["解释这一步", "请解释这段内容：每一步为什么成立，用到了前面哪些定义或结论。"],
            ["给个提示", "请只给我思路提示和下一步该想什么，先不要给出完整解答。"],
            ["举个例子", "请举一两个具体的例子（需要时也给反例），帮助我理解这段内容。"],
            ["完整证明", "请给出完整、严谨的证明或解答，每一步写清理由。"]],
    saved: "已保存到", saving: "保存中……", unsaved: "没有保存：设置里还没填 GitHub token",
    saveFailed: "保存失败，已留在本机，下次打开网页时重试：", thinking: "思考中……",
    failed: "请求失败：", noHistory: "这一页还没有问答记录。", loading: "读取中……",
    historyTitle: "本页的问答记录", back: "← 回到对话",
    sKey: "DeepSeek API key", sGh: "GitHub token（只授权记录仓库的读写）", sRepo: "记录仓库",
    sSave: "保存", sCancel: "取消", sOff: "停用并清除",
    sHelp: "这些只存在这台设备的浏览器里，不会上传到网站。别的设备要各填一次。",
    passage: "选中的原文", you: "问", ai: "答",
  } : {
    ask: "Ask AI", title: "Ask AI", history: "History", settings: "Settings", close: "Close",
    placeholder: "Ask something… (Enter to send, Shift+Enter for a new line)", send: "Send", stop: "Stop",
    note: "Note (optional): what is unclear here, what sentence is missing",
    quick: [["Explain", "Please explain this passage: why each step holds, and which earlier definitions or results it uses."],
            ["Hint", "Please give me only a hint and what to think about next, not a full solution yet."],
            ["Example", "Please give one or two concrete examples (and a counterexample if useful) to illustrate this passage."],
            ["Full proof", "Please give a complete, rigorous proof or solution, with a reason for every step."]],
    saved: "Saved to", saving: "Saving…", unsaved: "Not saved: no GitHub token in the settings",
    saveFailed: "Saving failed; kept in this browser and retried next time: ", thinking: "Thinking…",
    failed: "Request failed: ", noHistory: "No questions on this page yet.", loading: "Loading…",
    historyTitle: "Questions on this page", back: "← Back to the conversation",
    sKey: "DeepSeek API key", sGh: "GitHub token (read/write on the notes repository only)", sRepo: "Notes repository",
    sSave: "Save", sCancel: "Cancel", sOff: "Turn off and clear",
    sHelp: "Stored in this browser only, never uploaded to the site. Other devices need their own copy.",
    passage: "Selected passage", you: "Question", ai: "Answer",
  };

  const load = k => { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } };
  const store = (k, v) => {
    try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, JSON.stringify(v)); } catch (e) {}
  };
  let cfg = load(SETTINGS) || {};
  const el = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  };
  const button = (cls, text, onclick) => {
    const b = el("button", cls, text);
    b.type = "button";
    if (onclick) b.onclick = onclick;
    return b;
  };
  const esc = s => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  // ---------------------------------------------------------------------
  //  Settings (#ai)
  // ---------------------------------------------------------------------
  function openSettings() {
    const shade = el("div", "yp-ai-modal");
    const form = el("form", "yp-ai-settings");
    const field = (label, value, type) => {
      const l = el("label", null, label);
      const i = el("input");
      i.type = type;
      i.value = value || "";
      i.autocomplete = "off";
      i.spellcheck = false;
      l.append(i);
      form.append(l);
      return i;
    };
    form.append(el("p", "yp-ai-settings-title", T.title + " · " + T.settings));
    const key = field(T.sKey, cfg.key, "password");
    const gh = field(T.sGh, cfg.gh, "password");
    const repo = field(T.sRepo, cfg.repo || DEFAULT_REPO, "text");
    form.append(el("p", "yp-ai-settings-help", T.sHelp));
    const row = el("div", "yp-ai-settings-row");
    const done = () => shade.remove();
    const off = button("yp-ai-off", T.sOff, () => { store(SETTINGS, null); cfg = {}; done(); location.reload(); });
    const save = el("button", "yp-ai-primary", T.sSave);
    save.type = "submit";
    row.append(off, button("", T.sCancel, done), save);
    form.append(row);
    form.onsubmit = e => {
      e.preventDefault();
      const was = !!cfg.key;
      cfg = { key: key.value.trim(), gh: gh.value.trim(), repo: repo.value.trim() || DEFAULT_REPO };
      store(SETTINGS, cfg.key ? cfg : null);
      done();
      if (cfg.key && !was) start();
    };
    shade.onclick = e => { if (e.target === shade) done(); };
    shade.append(form);
    document.body.append(shade);
    key.focus();
  }
  if (location.hash === "#ai") {
    history.replaceState(null, "", location.pathname + location.search);
    openSettings();
  }

  // ---------------------------------------------------------------------
  //  Everything else needs a key and a page of notes
  // ---------------------------------------------------------------------
  const body = document.querySelector(".yp-body[data-book]");
  let started = false;
  if (cfg.key) start();

  function start() {
    if (started) return;
    started = true;
    flushPending();
    if (!body) return;
    const page = {
      book: body.dataset.book,
      bookTitle: body.dataset.bookTitle || "",
      page: location.pathname.split("/").pop().replace(/\.html$/, "") || "index",
      crumb: body.dataset.crumb || ((document.querySelector("h1.title") || {}).textContent || document.title).trim(),
      lang: body.classList.contains("yp-zh") ? "zh" : "en",
    };

    // ---- The page's LaTeX source, the book's notation and version (build.py)
    const cache = {};
    const fetchText = url => cache[url] || (cache[url] = fetch(url)
      .then(r => r.ok ? r.text() : Promise.reject(new Error(r.status)))
      .catch(e => { delete cache[url]; throw e; }));
    let macrosDefined = false;
    async function sources() {
      const [tex, info] = await Promise.all([
        fetchText(`src/${page.page}.tex`).catch(() => ""),
        fetchText("src/book.json").then(JSON.parse).catch(() => ({})),
      ]);
      if (!macrosDefined && info.macros) {
        macrosDefined = true;
        defineMacros(info.macros);
      }
      return { tex, info };
    }
    // the notation macros, so that MathJax can show them in answers too
    function defineMacros(macros) {
      const defs = macros.split("\n")
        .map(l => l.replace(/^\\DeclareMathOperator(\*?)\{(\\[A-Za-z]+)\}\{(.*)\}$/,
                            (m, star, name, text) => `\\newcommand{${name}}{\\operatorname${star}{${text}}}`)
                   .replace(/^\\renewcommand/, "\\newcommand"))
        .filter(l => l.startsWith("\\newcommand"));
      const box = el("div", null, defs.map(d => `\\(${d}\\)`).join(" "));
      box.hidden = true;
      document.body.append(box);
      typeset(box);
    }

    // ---- Selection -> TeX: formulas back to their source
    function markMath() {
      const doc = window.MathJax && MathJax.startup && MathJax.startup.document;
      if (!doc || !doc.getMathItemsWithin) return;
      try {
        for (const m of doc.getMathItemsWithin(body)) {
          if (!m.typesetRoot) continue;
          m.typesetRoot.dataset.tex = m.math;
          if (m.display) m.typesetRoot.dataset.display = "1";
        }
      } catch (e) {}
    }
    const elementOf = n => n && (n.nodeType === 1 ? n : n.parentElement);
    // never cut a formula in half
    function widen(r) {
      r = r.cloneRange();
      const a = elementOf(r.startContainer).closest("mjx-container");
      if (a) r.setStartBefore(a);
      const b = elementOf(r.endContainer).closest("mjx-container");
      if (b) r.setEndAfter(b);
      return r;
    }
    const BLOCK = /^(P|DIV|LI|H[1-6]|SECTION|DETAILS|SUMMARY|BLOCKQUOTE|OL|UL|FIGURE|FIGCAPTION)$/;
    function toTex(node) {
      let out = "";
      node.childNodes.forEach(n => {
        if (n.nodeType === 3) { out += n.data; return; }
        if (n.nodeType !== 1 || n.matches(".yp-thm-pdf, .anchorjs-link, script, style")) return;
        if (n.tagName === "MJX-CONTAINER") {
          const t = n.dataset.tex;
          out += t == null ? n.textContent : n.dataset.display ? `\n$$${t}$$\n` : `$${t}$`;
          return;
        }
        const t = toTex(n);
        out += BLOCK.test(n.tagName) ? `\n${t}\n` : t;
      });
      return out;
    }
    const tidy = s => s.replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
    const labelOf = n => tidy(toTex(n.cloneNode(true))).replace(/\s+/g, " ").replace(/[.．。]$/, "");

    // where the selection is: the statement, proof, exercise or section around it
    function where(r) {
      const n = elementOf(r.startContainer);
      const head = thm => { const h = thm.querySelector(".yp-thm-head"); return h ? labelOf(h) : ""; };
      const q = n.closest(".yp-qitem");
      if (q) {
        const mark = q.querySelector(":scope > p [data-label]");
        const lab = q.querySelector(":scope > p > .yp-qlabel");
        const word = page.lang === "zh" ? "习题 " : "Exercise ";
        const sol = n.closest(".yp-solution") ? (page.lang === "zh" ? " 的解答" : " — solution") : "";
        return { id: mark ? mark.id : "", label: word + (lab ? lab.textContent.trim() : "") + sol };
      }
      const thm = n.closest(".yp-thm[id]");
      if (thm) return { id: thm.id, label: head(thm) };
      const proof = n.closest(".yp-proof");
      if (proof) {
        let p = proof.previousElementSibling;
        while (p && !p.matches(".yp-thm[id]")) p = p.previousElementSibling;
        if (p) return { id: p.id, label: head(p) + (page.lang === "zh" ? " 的证明" : " — proof") };
      }
      const eq = n.closest(".yp-eq[id]");
      if (eq) {
        const mj = eq.querySelector("mjx-container");
        const tag = mj && (mj.dataset.tex || "").match(/\\tag\*?\{([^}]*)\}/);
        return { id: eq.id, label: (page.lang === "zh" ? "公式 " : "Equation ") + (tag ? `(${tag[1]})` : eq.id) };
      }
      const sec = n.closest("section[id]");
      const h = sec && sec.querySelector(":scope > h2, :scope > h3");
      if (h) return { id: sec.id, label: labelOf(h) };
      return { id: "", label: page.crumb };
    }

    // ---- The "Ask AI" button next to a selection
    const askBtn = button("yp-ai-ask", T.ask);
    askBtn.hidden = true;
    document.body.append(askBtn);
    let picked = null, mouseDown = false, selTimer = 0;
    // keep the selection when the button is pressed
    askBtn.addEventListener("pointerdown", e => e.preventDefault());
    askBtn.addEventListener("mousedown", e => e.preventDefault());
    askBtn.onclick = () => { if (picked) ask(picked); askBtn.hidden = true; };
    // while the mouse drags out a selection, wait for it to be released;
    // fingers and pens select with the system handles and are caught by selectionchange
    document.addEventListener("pointerdown", e => {
      if (e.pointerType === "mouse" && e.target !== askBtn) mouseDown = true;
    });
    document.addEventListener("mouseup", () => { mouseDown = false; setTimeout(checkSelection, 0); });
    document.addEventListener("selectionchange", () => {
      clearTimeout(selTimer);
      selTimer = setTimeout(() => { if (!mouseDown) checkSelection(); }, 250);
    });
    addEventListener("resize", () => { askBtn.hidden = true; });
    function checkSelection() {
      const sel = getSelection();
      if (!sel.rangeCount || sel.isCollapsed) { askBtn.hidden = true; return; }
      const r = sel.getRangeAt(0);
      if (!body.contains(r.startContainer) || !body.contains(r.endContainer) || !r.toString().trim()) {
        askBtn.hidden = true;
        return;
      }
      picked = r.cloneRange();
      // below the end of the selection: the system menu on touch screens sits above it
      const rects = [...r.getClientRects()].filter(x => x.width || x.height);
      const last = rects[rects.length - 1] || r.getBoundingClientRect();
      askBtn.hidden = false;
      const vw = document.documentElement.clientWidth, w = askBtn.offsetWidth;
      askBtn.style.left = Math.max(12, Math.min(last.right - w / 2, vw - w - 12)) + scrollX + "px";
      askBtn.style.top = last.bottom + 10 + scrollY + "px";
    }

    // ---- The panel
    const panel = el("aside", "yp-ai");
    panel.setAttribute("aria-label", T.title);
    panel.hidden = true;
    const head = el("header", "yp-ai-head");
    const whereEl = el("span", "yp-ai-where", page.crumb);
    head.append(el("span", "yp-ai-title", T.title), whereEl,
                button("yp-ai-tool", T.history, showHistory),
                button("yp-ai-tool", T.settings, openSettings),
                button("yp-ai-close", "×", closePanel));
    head.lastChild.setAttribute("aria-label", T.close);
    const scroller = el("div", "yp-ai-scroll");
    const quote = el("div", "yp-ai-quote");
    const msgs = el("div", "yp-ai-msgs");
    const hist = el("div", "yp-ai-history");
    hist.hidden = true;
    scroller.append(quote, msgs, hist);
    const foot = el("div", "yp-ai-foot");
    const quick = el("div", "yp-ai-quick");
    T.quick.forEach(([label, prompt]) => quick.append(button("", label, () => send(prompt, label))));
    const input = el("textarea", "yp-ai-input");
    input.rows = 2;
    input.placeholder = T.placeholder;
    const note = el("input", "yp-ai-note");
    note.placeholder = T.note;
    const sendBtn = button("yp-ai-send", T.send, () => (streaming ? streaming.abort() : send(input.value)));
    const row = el("div", "yp-ai-row");
    row.append(note, sendBtn);
    const status = el("p", "yp-ai-status");
    foot.append(quick, input, row, status);
    panel.append(head, scroller, foot);
    document.body.append(panel);

    input.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing && e.keyCode !== 229) {
        e.preventDefault();
        if (!streaming) send(input.value);
      }
    });
    note.addEventListener("change", () => {
      if (!conv) return;
      conv.note = note.value.trim();
      if (conv.messages.length) persist(conv);
    });
    document.addEventListener("keydown", e => {
      if (e.key === "Escape" && !panel.hidden && !document.querySelector(".yp-ai-modal")) closePanel();
      // "a" opens the panel again (or this page's history when nothing was asked yet)
      if (e.key === "a" && !e.metaKey && !e.ctrlKey && !e.altKey &&
          !/input|textarea/i.test(document.activeElement.tagName)) {
        if (!panel.hidden) closePanel(); else if (conv) openPanel(); else { openPanel(); showHistory(); }
      }
    });

    function openPanel() {
      panel.hidden = false;
      document.documentElement.classList.add("yp-ai-open");
    }
    function closePanel() {
      panel.hidden = true;
      document.documentElement.classList.remove("yp-ai-open");
    }
    const setStatus = (text, cls) => { status.textContent = text || ""; status.className = "yp-ai-status " + (cls || ""); };
    const nearBottom = () => scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight < 80;

    // ---- A conversation
    let conv = null, streaming = null;
    function stamp(d) {
      const p = n => String(n).padStart(2, "0");
      return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`;
    }
    // local time with its offset, as in the file name: 2026-10-25T14:03:00+08:00
    function localISO(d) {
      const off = -d.getTimezoneOffset(), p = n => String(Math.abs(n)).padStart(2, "0");
      return new Date(d.getTime() + off * 60000).toISOString().slice(0, 19) +
             (off < 0 ? "-" : "+") + p(Math.trunc(off / 60)) + ":" + p(off % 60);
    }
    const fileSafe = s => s.replace(/\$|\\[A-Za-z]+|[{}^_]/g, "").replace(/[\s\/\\:*?"<>|#%&~]+/g, "-")
      .replace(/^-+|-+$/g, "").slice(0, 60);

    function ask(range) {
      markMath();
      const r = widen(range);
      const frag = r.cloneContents();
      const wrap = el("div");
      wrap.append(frag);
      const anchor = where(r);
      const now = new Date();
      conv = {
        book: page.book, bookTitle: page.bookTitle, page: page.page, crumb: page.crumb,
        url: location.origin + location.pathname + (anchor.id ? "#" + anchor.id : ""),
        anchor, selTex: tidy(toTex(wrap)), messages: [], note: "", commit: "",
        created: localISO(now), updated: localISO(now),
        path: `${page.book}/${page.page}/${stamp(now)}-${fileSafe(anchor.label) || "note"}.md`, sha: "",
      };
      // the quote: the selection as it looks on the page
      wrap.querySelectorAll("[id]").forEach(x => x.removeAttribute("id"));
      wrap.querySelectorAll(".yp-thm-pdf, .anchorjs-link").forEach(x => x.remove());
      showConversation(wrap);
      getSelection().removeAllRanges();
      sources();          // start loading the page source now
      input.focus();
    }

    function showConversation(quoteNode) {
      hist.hidden = true;
      msgs.hidden = quote.hidden = false;
      quote.replaceChildren();
      const lab = el("p", "yp-ai-anchor", conv.anchor.label || T.passage);
      const q = el("div", "yp-ai-quote-body yp-body yp-" + page.lang);
      if (quoteNode) q.append(...quoteNode.childNodes);
      else { render(conv.selTex, q); typeset(q); }
      quote.append(lab, q);
      msgs.replaceChildren();
      conv.messages.forEach(m => addMessage(m.role, m.content));
      note.value = conv.note || "";
      setStatus(conv.sha ? `${T.saved} ${cfg.repo}` : "");
      openPanel();
      scroller.scrollTop = 0;
    }

    function addMessage(role, text, label) {
      const m = el("div", "yp-ai-msg yp-ai-" + (role === "user" ? "q" : "a"));
      if (role === "user") m.textContent = label || text;
      else {
        m.classList.add("yp-body", "yp-" + page.lang);
        render(text, m);
        typeset(m);
      }
      msgs.append(m);
      return m;
    }

    function systemPrompt(src) {
      const title = src.info.title || page.bookTitle;
      if (page.lang === "zh") {
        return [
          `你是一位耐心、严谨的数学助教，正在帮读者读讲义《${title}》的「${page.crumb}」。`,
          "下面先给出讲义自定义的记号宏，再给出这一页的 LaTeX 源码。",
          "",
          "回答时：",
          "- 用中文。先直接回答问题，再按需要展开；不要复述整段原文。",
          "- 沿用讲义的记号；引用前文时说出编号或名字（如“由定理 3”）。",
          "- 公式用 $…$（行内）和 $$…$$（单独成行）书写；只用标准 LaTeX 命令，例如写 \\mathbb{P}、\\mathbb{E}、\\mathbb{R}，不要用讲义自定义的宏。",
          "- 如果讲义这里有错误、跳步或说得不清楚，直接指出，并说明应该怎样补。",
          "",
          "=== 记号宏 ===", src.info.macros || "（无）",
          "=== 本页源码 ===", src.tex || "（没有取到源码）",
        ].join("\n");
      }
      return [
        `You are a patient, rigorous mathematics tutor helping a reader with the notes "${title}", page "${page.crumb}".`,
        "Below are the notation macros of the notes, then the LaTeX source of this page.",
        "",
        "When answering:",
        "- Answer in English. Answer the question directly first, then expand as needed; do not restate the passage.",
        "- Keep the notation of the notes; when using earlier results, cite their number or name.",
        "- Write formulas as $…$ (inline) and $$…$$ (display), using standard LaTeX only (\\mathbb{P}, \\mathbb{E}, \\mathbb{R}), not the macros of the notes.",
        "- If the notes contain an error, a gap, or an unclear step here, say so and say how to fix it.",
        "",
        "=== Notation macros ===", src.info.macros || "(none)",
        "=== Source of this page ===", src.tex || "(source not available)",
      ].join("\n");
    }
    function firstQuestion(c, question) {
      return page.lang === "zh"
        ? `我在读「${c.anchor.label}」。选中的原文：\n\n~~~latex\n${c.selTex}\n~~~\n\n${question}`
        : `I am reading "${c.anchor.label}". The selected passage:\n\n~~~latex\n${c.selTex}\n~~~\n\n${question}`;
    }

    async function send(text, label) {
      text = (text || "").trim();
      if (!text || !conv || streaming) return;
      const c = conv;
      input.value = "";
      c.messages.push({ role: "user", content: text });
      addMessage("user", text, label);
      const out = addMessage("assistant", "");
      out.classList.add("yp-ai-pending");
      out.textContent = T.thinking;
      scroller.scrollTop = scroller.scrollHeight;
      setStatus("");
      const ctrl = new AbortController();
      streaming = ctrl;
      sendBtn.textContent = T.stop;
      let answer = "";
      try {
        const src = await sources();
        c.commit = src.info.commit || "";
        const messages = [{ role: "system", content: systemPrompt(src) },
          ...c.messages.map((m, i) => i === 0 ? { role: "user", content: firstQuestion(c, m.content) } : m)];
        const live = liveRender(out);
        answer = await complete(messages, t => {
          const stick = nearBottom();
          out.classList.remove("yp-ai-pending");
          live.set(t);
          if (stick) scroller.scrollTop = scroller.scrollHeight;
        }, ctrl.signal);
        await live.flush();
      } catch (e) {
        if (e.name !== "AbortError") {
          out.classList.remove("yp-ai-pending");
          if (!answer) out.textContent = "";
          out.append(el("p", "yp-ai-error", T.failed + (e.message || e)));
        }
      } finally {
        streaming = null;
        sendBtn.textContent = T.send;
      }
      if (answer.trim()) {
        c.messages.push({ role: "assistant", content: answer });
        c.updated = localISO(new Date());
        if (c === conv) c.note = note.value.trim();
        persist(c);
      } else {
        // nothing came back: forget the question, so the next one is asked afresh
        c.messages.pop();
      }
    }

    async function complete(messages, onText, signal) {
      const res = await fetch(API, {
        method: "POST", signal,
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${cfg.key}` },
        body: JSON.stringify({ model: MODEL, messages, stream: true }),
      });
      if (!res.ok) {
        let msg = String(res.status);
        try { msg += " " + ((await res.json()).error || {}).message; } catch (e) {}
        throw new Error(msg);
      }
      const reader = res.body.getReader(), dec = new TextDecoder();
      let buf = "", text = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        let i;
        while ((i = buf.indexOf("\n")) >= 0) {
          const line = buf.slice(0, i).trim();
          buf = buf.slice(i + 1);
          if (!line.startsWith("data:")) continue;
          const data = line.slice(5).trim();
          if (data === "[DONE]") return text;
          try {
            const d = JSON.parse(data).choices[0].delta.content;
            if (d) { text += d; onText(text); }
          } catch (e) {}
        }
      }
      return text;
    }

    // ---- History: the files saved for this page
    async function showHistory() {
      openPanel();
      quote.hidden = msgs.hidden = true;
      hist.hidden = false;
      hist.replaceChildren(el("p", "yp-ai-hist-title", T.historyTitle));
      if (conv) hist.firstChild.append(button("yp-ai-back", T.back, () => showConversation(null)));
      if (!cfg.gh) { hist.append(el("p", "yp-ai-muted", T.unsaved)); return; }
      const wait = el("p", "yp-ai-muted", T.loading);
      hist.append(wait);
      try {
        const list = (await github(`${page.book}/${page.page}`)) || [];
        wait.remove();
        const files = list.filter(f => f.type === "file" && f.name.endsWith(".md"))
          .sort((a, b) => b.name.localeCompare(a.name));
        if (!files.length) { hist.append(el("p", "yp-ai-muted", T.noHistory)); return; }
        const ul = el("ul", "yp-ai-hist-list");
        files.forEach(f => {
          const m = f.name.match(/^(\d{4}-\d\d-\d\d)-(\d\d)(\d\d)-(.*)\.md$/);
          const li = el("li");
          const b = button("", null, () => openSaved(f.path));
          b.append(el("span", "yp-ai-hist-date", m ? `${m[1]} ${m[2]}:${m[3]}` : ""),
                   el("span", "yp-ai-hist-name", m ? m[4].replace(/-/g, " ") : f.name));
          li.append(b);
          ul.append(li);
        });
        hist.append(ul);
      } catch (e) {
        wait.textContent = T.failed + e.message;
      }
    }
    async function openSaved(path) {
      try {
        const f = await github(path);
        const saved = fromMarkdown(unbase64(f.content));
        const fm = saved.fm;
        conv = {
          book: page.book, bookTitle: page.bookTitle, page: page.page, crumb: page.crumb,
          url: fm.url || "", anchor: { id: fm.anchor || "", label: fm.anchor_label || "" },
          selTex: saved.selTex, messages: saved.messages, note: fm.note || "", commit: fm.commit || "",
          created: fm.created || "", updated: fm.updated || "", path, sha: f.sha,
        };
        showConversation(null);
      } catch (e) {
        setStatus(T.failed + e.message, "yp-ai-bad");
      }
    }

    // ---- Saving
    async function persist(c) {
      if (!cfg.gh) { if (c === conv) setStatus(T.unsaved, "yp-ai-bad"); return; }
      if (c === conv) setStatus(T.saving);
      try {
        await upload(c);
        if (c === conv) setStatus(`${T.saved} ${cfg.repo}/${c.path}`, "yp-ai-ok");
      } catch (e) {
        keepPending(c);
        if (c === conv) setStatus(T.saveFailed + e.message, "yp-ai-bad");
      }
    }
  }

  // ---------------------------------------------------------------------
  //  GitHub: one Markdown file per conversation
  // ---------------------------------------------------------------------
  async function github(path, opts = {}) {
    const url = `${GITHUB}/repos/${cfg.repo}/contents/` + path.split("/").map(encodeURIComponent).join("/");
    const res = await fetch(url, {
      ...opts, cache: "no-store",
      headers: { Authorization: `Bearer ${cfg.gh}`, Accept: "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28" },
    });
    if (res.status === 404 && !opts.method) return null;
    if (!res.ok) {
      const err = new Error(`GitHub ${res.status} ${((await res.json().catch(() => ({}))).message || "")}`);
      err.status = res.status;
      throw err;
    }
    return res.json();
  }
  async function upload(c) {
    const put = sha => github(c.path, { method: "PUT", body: JSON.stringify({
      message: `${c.book}/${c.page}: ${c.anchor.label || c.crumb}`,
      content: base64(toMarkdown(c)), ...(sha ? { sha } : {}) }) });
    let r;
    try {
      r = await put(c.sha);
    } catch (e) {
      // changed on another device, or saved before without our knowing: take its version
      if (e.status !== 409 && e.status !== 422) throw e;
      const now = await github(c.path);
      r = await put(now && now.sha);
    }
    c.sha = r.content.sha;
  }
  function keepPending(c) {
    const p = load(PENDING) || {};
    p[c.path] = c;
    store(PENDING, p);
  }
  async function flushPending() {
    const p = load(PENDING);
    if (!p || !cfg.gh) return;
    for (const [path, c] of Object.entries(p)) {
      try { await upload(c); delete p[path]; } catch (e) {}
    }
    store(PENDING, Object.keys(p).length ? p : null);
  }

  function base64(s) {
    const bytes = new TextEncoder().encode(s);
    let bin = "";
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    return btoa(bin);
  }
  const unbase64 = s => new TextDecoder().decode(Uint8Array.from(atob(s.replace(/\s/g, "")), ch => ch.charCodeAt(0)));

  // The file: front matter for filtering, the passage, then the conversation.
  // <!-- yp:q --> / <!-- yp:a --> mark the turns so the page can read it back.
  function toMarkdown(c) {
    const y = v => JSON.stringify(v == null ? "" : v);
    const lines = ["---",
      `book: ${c.book}`, `book_title: ${y(c.bookTitle)}`, `page: ${c.page}`, `page_title: ${y(c.crumb)}`,
      `anchor: ${y(c.anchor.id)}`, `anchor_label: ${y(c.anchor.label)}`, `url: ${y(c.url)}`,
      `commit: ${y(c.commit)}`, `model: ${MODEL}`, `created: ${c.created}`, `updated: ${c.updated}`,
      `note: ${y(c.note)}`, "---", "",
      `## ${T.passage}`, "", "~~~latex", c.selTex, "~~~", ""];
    for (const m of c.messages) {
      const q = m.role === "user";
      lines.push(q ? "<!-- yp:q -->" : "<!-- yp:a -->", `### ${q ? T.you : T.ai}`, "", m.content.trim(), "");
    }
    return lines.join("\n");
  }
  function fromMarkdown(md) {
    const fm = {};
    const head = md.match(/^---\n([\s\S]*?)\n---\n/);
    if (head) head[1].split("\n").forEach(line => {
      const k = line.indexOf(":");
      if (k < 0) return;
      const v = line.slice(k + 1).trim();
      try { fm[line.slice(0, k).trim()] = JSON.parse(v); } catch (e) { fm[line.slice(0, k).trim()] = v; }
    });
    const sel = md.match(/~~~latex\n([\s\S]*?)\n~~~/);
    const parts = md.split(/<!-- yp:(q|a) -->\n/);
    const messages = [];
    for (let i = 1; i < parts.length; i += 2) {
      messages.push({ role: parts[i] === "q" ? "user" : "assistant",
                      content: parts[i + 1].replace(/^### .*\n\n?/, "").trim() });
    }
    return { fm, selTex: sel ? sel[1] : "", messages };
  }

  // ---------------------------------------------------------------------
  //  Answers: Markdown with formulas, typeset by the page's MathJax
  // ---------------------------------------------------------------------
  let markedReady = null;
  function loadMarked() {
    return markedReady || (markedReady = new Promise((ok, fail) => {
      const s = el("script");
      s.src = MARKED;
      s.onload = () => {
        // raw HTML in an answer is shown as text
        marked.use({ renderer: { html: t => esc(typeof t === "string" ? t : t.text || "") } });
        ok();
      };
      s.onerror = fail;
      document.head.append(s);
    }));
  }
  loadMarked().catch(() => {});
  function render(md, into) {
    // formulas out of the way of Markdown, then back as \( \) and \[ \]
    const math = [];
    const keep = (tex, display) => `@@M${math.push([tex, display]) - 1}@@`;
    const s = md.replace(/\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]|\\\(([\s\S]+?)\\\)|\$([^$\n]+?)\$/g,
      (m, a, b, c, d) => a != null ? keep(a, true) : b != null ? keep(b, true) : keep(c != null ? c : d, false));
    let html = window.marked ? marked.parse(s) : esc(s).replace(/\n/g, "<br>");
    html = html.replace(/@@M(\d+)@@/g, (m, i) => {
      const [tex, display] = math[i];
      return esc(display ? `\\[${tex}\\]` : `\\(${tex}\\)`);
    });
    if (window.MathJax && MathJax.typesetClear) MathJax.typesetClear([into]);
    into.innerHTML = html;
  }
  // MathJax's queue can stall (seen in WebKit); then typeset synchronously from
  // there on, so that an answer never stops updating
  let stalled = false;
  async function typeset(node) {
    if (!window.MathJax) return;
    if (!stalled && MathJax.typesetPromise) {
      const wait = new Promise(ok => setTimeout(() => ok(false), 1500));
      if (await Promise.race([MathJax.typesetPromise([node]).then(() => true, () => true), wait])) return;
      stalled = true;
    }
    try { MathJax.typeset([node]); } catch (e) {}
  }
  // while an answer streams in: render and typeset the latest text, one pass at a time
  function liveRender(node) {
    let text = "", busy = null, dirty = false;
    const run = async () => {
      do {
        dirty = false;
        render(text, node);
        await typeset(node);
      } while (dirty);
      busy = null;
    };
    return {
      set(t) { text = t; if (busy) dirty = true; else busy = run(); },
      flush: () => busy || Promise.resolve(),
    };
  }
})();
