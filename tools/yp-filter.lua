-- =====================================================================
--  yp-filter.lua — turns pandoc's reading of a yupin-notes lecture into
--  the web page body.
--
--  build.py first rewrites cls-specific syntax into pandoc-friendly
--  markers (\href{yp:...}{...}, \begin{ypexercises}, ...). This filter:
--    * numbers theorem-like blocks exactly as the PDF does (global
--      counter for zh books, section.counter for en books), checked
--      against the numbers LaTeX wrote into the .aux file;
--    * resolves \ref, \eqref, \pageref, \egref across pages from the
--      .aux labels;
--    * renders solutions as collapsible <details> blocks;
--    * gives exercise lists their A1) / A1-2) labels.
--
--  Metadata (set with -M by build.py):
--    yp-labels      path to labels.json
--    yp-page        basename of the page being built
--    yp-lang        zh | en
--    yp-numbering   global | section
--    yp-thm-offset  numbered statements before this page (global mode)
--    yp-sec-offset  sections before this page (section mode)
--    yp-pdf         URL of the book PDF
--    yp-kicker, yp-pdf-page   banner contents
--    yp-short-title  short page title; the long \lecture heading becomes the lede
--    yp-index       file to append index-of-results entries to (JSON lines)
-- =====================================================================

local stringify = pandoc.utils.stringify

local labels = {}
local page, lang, numbering, pdf_url, index_path
local thm_counter, sec_counter, sub_counter = 0, 0, 0

local NAMES = {
  zh = {
    definition = '定义', proposition = '命题', lemma = '引理', theorem = '定理',
    corollary = '推论', remark = '注记', example = '例子', practice = '练习',
    question = '问题', thinking = '思考题', historynote = '历史注记',
    workedexample = '例题', proof = '证明', solution = '解答',
    claim = '断言', conjecture = '猜想', observation = '观察',
    fact = '事实', problem = '问题',
  },
  en = {
    definition = 'Definition', proposition = 'Proposition', lemma = 'Lemma',
    theorem = 'Theorem', corollary = 'Corollary', remark = 'Remark',
    example = 'Example', practice = 'Exercise', question = 'Question',
    thinking = 'Problem', historynote = 'Historical note',
    workedexample = 'Worked example', proof = 'Proof', solution = 'Solution',
    claim = 'Claim', conjecture = 'Conjecture', observation = 'Observation',
    fact = 'Fact', problem = 'Problem',
  },
}

-- Environments sharing the numbered counter.
local NUMBERED = {
  definition = true, proposition = true, lemma = true, theorem = true,
  corollary = true, claim = true, conjecture = true, observation = true,
}
-- en books follow Montgomery: remarks and examples are numbered too.
local NUMBERED_EN = {remark = true, example = true, question = true, fact = true, problem = true}
-- amsthm "definition" style (upright body) in en books.
local UPRIGHT = {
  definition = true, remark = true, example = true, practice = true,
  question = true, thinking = true, historynote = true, workedexample = true,
  problem = true,
}

local function warn(msg)
  io.stderr:write('[yp-filter] ' .. page .. ': ' .. msg .. '\n')
end

local function read_meta(meta)
  page = stringify(meta['yp-page'] or '')
  lang = stringify(meta['yp-lang'] or 'zh')
  numbering = stringify(meta['yp-numbering'] or 'global')
  pdf_url = stringify(meta['yp-pdf'] or '')
  index_path = stringify(meta['yp-index'] or '')
  thm_counter = tonumber(stringify(meta['yp-thm-offset'] or '0')) or 0
  sec_counter = tonumber(stringify(meta['yp-sec-offset'] or '0')) or 0
  local path = stringify(meta['yp-labels'] or '')
  if path ~= '' then
    local f = io.open(path, 'r')
    labels = pandoc.json.decode(f:read('a'))
    f:close()
  end
end

-- ---------------------------------------------------------------------
--  Label resolution
-- ---------------------------------------------------------------------
local function target(label)
  local l = labels[label]
  if not l or not l.file or l.file == page then return '#' .. label end
  return l.file .. '.qmd#' .. label
end

local function num(label)
  local l = labels[label]
  if l and l.num and l.num ~= '' then return l.num end
  warn('unresolved label ' .. label)
  return '??'
end

-- PDF link to the page a label sits on.
local function pdf_link(label)
  local l = labels[label]
  if pdf_url == '' or not l or not l.page then return nil end
  return pandoc.Link({pandoc.Str('PDF p.' .. l.page)},
    pdf_url .. '#page=' .. l.pdfpage, '', {class = 'yp-pdflink'})
end

local function marker(el)
  if el.t == 'Link' and el.target:match('^yp:') then
    return el.target:sub(4)
  end
end

-- ---------------------------------------------------------------------
--  Inline rewrites
-- ---------------------------------------------------------------------
local function fix_math(m)
  local t = m.text
  -- \let\leq\leqslant etc. in the cls
  t = t:gsub('\\leq(%f[^%a])', '\\leqslant%1'):gsub('\\geq(%f[^%a])', '\\geqslant%1')
  t = t:gsub('\\le(%f[^%a])', '\\leqslant%1'):gsub('\\ge(%f[^%a])', '\\geqslant%1')
  t = t:gsub('\\qedhere', '')
  if m.mathtype == 'DisplayMath' then
    local label = t:match('\\label{([^}]*)}')
    t = t:gsub('\\label{[^}]*}', '')
    t = t:gsub('\\begin{equation%*?}', ''):gsub('\\end{equation%*?}', '')
    t = t:gsub('\\begin{align%*?}', '\\begin{aligned}'):gsub('\\end{align%*?}', '\\end{aligned}')
    -- no leading/trailing or blank lines, or the $$...$$ inside a span breaks
    t = t:gsub('^%s+', ''):gsub('%s+$', ''):gsub('\n%s*\n', '\n')
    if label then
      t = t .. '\\tag{' .. num(label) .. '}'
      m.text = t
      return pandoc.Span({m}, {id = label, class = 'yp-eq'})
    end
  end
  m.text = t
  return m
end

local function fix_link(el)
  local rt = el.attributes['reference-type']
  if rt then
    local label = el.attributes['reference']
    local text = num(label)
    if rt == 'eqref' then text = '(' .. text .. ')' end
    return pandoc.Link({pandoc.Str(text)}, target(label), '', {class = 'yp-ref'})
  end
  local m = marker(el)
  if not m then return nil end
  local kind, label = m:match('^([%w]+):(.+)$')
  kind = kind or m
  if kind == 'blue' then return pandoc.Span(el.content, {class = 'yp-blue'}) end
  if kind == 'red' then return pandoc.Span(el.content, {class = 'yp-red'}) end
  if kind == 'at' then
    return pandoc.Link(el.content, target(label), '', {class = 'yp-ref'})
  end
  if kind == 'egref' or kind == 'wegref' then
    local content = el.content
    if stringify(content) == '@' then
      local name = kind == 'egref' and NAMES[lang].example or NAMES[lang].workedexample
      local title = labels[label] and labels[label].title or ''
      if title ~= '' then
        local inl = pandoc.read(title, 'latex').blocks
        local t = (inl[1] and inl[1].content) or {pandoc.Str(title)}
        content = {pandoc.Str(name), pandoc.Str(lang == 'zh' and '（' or ' (')}
        for _, x in ipairs(t) do content[#content + 1] = x end
        content[#content + 1] = pandoc.Str(lang == 'zh' and '）' or ')')
      else
        content = {pandoc.Str(lang == 'zh' and ('这个' .. name) or ('this ' .. name:lower()))}
      end
    end
    return pandoc.Link(content, target(label), '', {class = 'yp-ref'})
  end
  return nil
end

-- \cite{a,b}[note] -> [1, 4, note], each number linking to the reference list
local function fix_cite(c)
  local out = pandoc.Inlines({pandoc.Str('[')})
  for i, cit in ipairs(c.citations) do
    if i > 1 then out:insert(pandoc.Str(', ')) end
    local key = 'bib:' .. cit.id
    out:insert(pandoc.Link({pandoc.Str(num(key))}, target(key), '', {class = 'yp-cite'}))
    if #cit.suffix > 0 then
      out:insert(pandoc.Str(', '))
      local suf = pandoc.Inlines(cit.suffix)
      if suf[1] and suf[1].t == 'Str' then suf[1].text = suf[1].text:gsub('^,%s*', '') end
      out:extend(suf)
    end
  end
  out:insert(pandoc.Str(']'))
  return out
end

local inline_filter = {Math = fix_math, Link = fix_link, Cite = fix_cite}

-- Keep a formula together with the CJK punctuation right after it (or the
-- opening bracket right before it), so that "(Ω,F,P)，" never breaks before "，".
local CLOSING = {['，']=1, ['。']=1, ['；']=1, ['：']=1, ['、']=1, ['）']=1, ['！']=1, ['？']=1, ['”']=1, ['’']=1, ['》']=1, ['-']=1, ['–']=1}
local OPENING = {['（']=1, ['“']=1, ['‘']=1, ['《']=1}
local function first_char(t) return t:match('^[%z\1-\127\194-\244][\128-\191]*') end
local function last_char(t) return t:match('[%z\1-\127\194-\244][\128-\191]*$') end
local function glue_punct(inlines)
  local out = pandoc.Inlines({})
  local i = 1
  while i <= #inlines do
    local el = inlines[i]
    if el.t == 'Math' and el.mathtype == 'InlineMath' then
      local group = pandoc.Inlines({el})
      local prev = out[#out]
      if prev and prev.t == 'Str' then
        local c = last_char(prev.text)
        if c and OPENING[c] then
          prev.text = prev.text:sub(1, #prev.text - #c)
          if prev.text == '' then out:remove(#out) end
          group:insert(1, pandoc.Str(c))
        end
      end
      local nxt = inlines[i + 1]
      if nxt and nxt.t == 'Str' then
        local c = first_char(nxt.text)
        if c and CLOSING[c] then
          group:insert(pandoc.Str(c))
          nxt.text = nxt.text:sub(#c + 1)
          if nxt.text == '' then i = i + 1 end
        end
      end
      if #group > 1 then out:insert(pandoc.Span(group, {class = 'yp-nobr'})) else out:insert(el) end
    else
      out:insert(el)
    end
    i = i + 1
  end
  return out
end

-- ---------------------------------------------------------------------
--  Block helpers
-- ---------------------------------------------------------------------

-- Pull leading yp: markers and \label spans out of the first paragraph.
local function take_head(blocks)
  local info = {}
  local first = blocks[1]
  if not first or (first.t ~= 'Para' and first.t ~= 'Plain') then return info end
  local keep = {}
  for _, el in ipairs(first.content) do
    local m = marker(el)
    if m and info[m] == nil and (m == 'note' or m == 'group' or m == 'title'
        or m == 'resume' or m == 'bibkey') then
      info[m] = el.content
    elseif el.t == 'Span' and el.attributes['label'] and not info.label then
      info.label = el.attributes['label']
    elseif #keep == 0 and (el.t == 'Space' or el.t == 'SoftBreak') then
      -- drop whitespace left behind by removed markers
    else
      keep[#keep + 1] = el
    end
  end
  if #keep == 0 then table.remove(blocks, 1) else first.content = pandoc.Inlines(keep) end
  return info
end

local function prepend_inlines(blocks, inlines)
  local first = blocks[1]
  if first and (first.t == 'Para' or first.t == 'Plain') then
    local c = pandoc.List(inlines)
    c:insert(pandoc.Space())
    c:extend(first.content)
    first.content = c
  else
    table.insert(blocks, 1, pandoc.Para(inlines))
  end
end

local function append_qed(blocks)
  local qed = pandoc.Span({pandoc.Str('□')}, {class = 'yp-qed'})
  local last = blocks[#blocks]
  if last and (last.t == 'Para' or last.t == 'Plain') then
    local c = pandoc.Inlines(last.content)
    c:insert(qed)
    last.content = c
  else
    table.insert(blocks, pandoc.Para({qed}))
  end
end

local function strip_auto_qed(blocks)
  -- pandoc appends "\160◻" to the last paragraph of a proof
  local last = blocks[#blocks]
  if last and (last.t == 'Para' or last.t == 'Plain') then
    local c = pandoc.Inlines(last.content)
    local n = #c
    if n > 0 and c[n].t == 'Str' then
      c[n].text = c[n].text:gsub('\u{a0}?\u{25fb}$', '')
      if c[n].text == '' then c:remove(n) end
    end
    last.content = c
  end
  -- and prepends Emph "Proof."
  local first = blocks[1]
  if first and first.t == 'Para' and first.content[1] and first.content[1].t == 'Emph'
      and stringify(first.content[1]) == 'Proof.' then
    local c = pandoc.Inlines(first.content)
    c:remove(1)
    if c[1] and c[1].t == 'Space' then c:remove(1) end
    first.content = c
  end
end

local function paren(inlines)
  -- the cls typesets theorem notes as " (note)" with ASCII parentheses
  local open, close = '(', ')'
  local c = pandoc.List({pandoc.Str(open)})
  c:extend(inlines)
  c:insert(pandoc.Str(close))
  return c
end

-- ---------------------------------------------------------------------
--  Exercise lists: A1), A1-2), E3) ...
-- ---------------------------------------------------------------------
local qstate = {group = 'A', count = 0}
local walk_blocks  -- forward declaration

local function labelled_list(list, prefix)
  local items = pandoc.List()
  for i, item in ipairs(list.content) do
    local label = prefix(i)
    local blocks = pandoc.List(item)
    -- nested question lists inside this item get label-<j>
    blocks = walk_blocks(blocks, {qprefix = label})
    prepend_inlines(blocks, {pandoc.Span({pandoc.Str(label .. ')')}, {class = 'yp-qlabel'})})
    items:insert(pandoc.Div(blocks, {class = 'yp-qitem'}))
  end
  return pandoc.Div(items, {class = 'yp-qlist'})
end

local function first_list(blocks)
  for i, b in ipairs(blocks) do
    if b.t == 'OrderedList' then return i end
  end
end

-- ---------------------------------------------------------------------
--  Index of results: one JSON line per numbered statement
-- ---------------------------------------------------------------------
local INDEXED = {
  definition = true, proposition = true, lemma = true, theorem = true,
  corollary = true, conjecture = true, problem = true,
}

-- Plain inlines for the index: links become text, citations are dropped
-- (their numbers only make sense inside the book), nothing page-relative.
local function unlink(inlines)
  return pandoc.Inlines(inlines):walk({
    Cite = function() return {} end,
    Link = function(l) return l.content end,
    Span = function(sp) sp.identifier = ''; sp.attributes = {}; return sp end,
  })
end

-- Rough visible length: characters of text, a formula counts as 3.
local function visible_len(inlines)
  local n = 0
  for _, el in ipairs(inlines) do
    if el.t == 'Str' then n = n + (utf8.len(el.text) or #el.text)
    elseif el.t == 'Math' then n = n + 3 end
  end
  return n
end

-- The statement's opening: its first sentence (up to 。 ； or a full stop),
-- plus the next one when the first is only a set-up such as "设 A⊆Ω。".
-- Stops before display math; at most ~50 inlines.
local function opening_inlines(blocks)
  -- the first paragraph, continued into the next block when it is only a
  -- short set-up ("设 A⊆Ω。" followed by a list of claims)
  local stream = pandoc.Inlines({})
  for k = 1, math.min(#blocks, 2) do
    local b = blocks[k]
    local inl
    if b.t == 'Para' or b.t == 'Plain' then
      inl = b.content
    elseif (b.t == 'OrderedList' or b.t == 'BulletList') and b.content[1] and b.content[1][1]
        and (b.content[1][1].t == 'Para' or b.content[1][1].t == 'Plain') then
      inl = pandoc.Inlines({pandoc.Str(b.t == 'OrderedList' and '1)' or '•'), pandoc.Space()})
      inl:extend(b.content[1][1].content)
    end
    if not inl then break end
    if #stream > 0 then stream:insert(pandoc.Space()) end
    stream:extend(inl)
    if visible_len(stream) >= 16 then break end
  end
  return stream
end

local function first_sentence(blocks)
  local content = opening_inlines(blocks)
  if #content == 0 then return content end
  local out, sentences = pandoc.Inlines({}), 0
  for i, el in ipairs(content) do
    if i > 50 or (el.t == 'Math' and el.mathtype == 'DisplayMath') then
      out:insert(pandoc.Str('…'))
      break
    end
    if el.t == 'Str' then
      local a, b = el.text:find('。'), nil
      if a then b = a + #'。' - 1 else a = el.text:find('；'); if a then b = a + #'；' - 1 end end
      if not a and el.text:match('%.$') and not el.text:match('^%a%.$') then b = #el.text end
      if b then
        out:insert(pandoc.Str(el.text:sub(1, b)))
        sentences = sentences + 1
        if sentences >= 2 or visible_len(out) >= 16 then break end
      else
        out:insert(el)
      end
    elseif el.t ~= 'Note' then
      out:insert(el)
    end
  end
  return out
end

local function to_md(inlines)
  local md = pandoc.write(pandoc.Pandoc({pandoc.Plain(inlines)}), 'markdown-smart')
  md = md:gsub('\n', ' '):gsub('%s+$', '')
  -- spaces left in front of punctuation by a dropped citation
  md = md:gsub('[ \u{a0}]+([,.;:%)])', '%1'):gsub('[ \u{a0}]+$', '')
  return md
end

local function index_entry(env, name, n, id, note, blocks)
  if index_path == '' or not INDEXED[env] then return end
  -- resolve \ref to numbers; build new Math elements so the page's own
  -- elements (labels, tags) are left untouched
  local body = first_sentence(blocks):walk({
    Link = fix_link,
    Math = function(m)
      local t = m.text:gsub('\\label{[^}]*}', ''):gsub('\\qedhere', '')
      return pandoc.Math(m.mathtype, t)
    end,
  })
  body = unlink(body)
  local entry = {
    page = page, id = id, kind = env, label = name .. ' ' .. n,
    note = note and to_md(unlink(note)) or '',
    snippet = to_md(body),
    text = (name .. ' ' .. n .. ' ' .. (note and stringify(note) or '') .. ' ' .. stringify(body)):lower(),
  }
  local f = io.open(index_path, 'a')
  f:write(pandoc.json.encode(entry), '\n')
  f:close()
end

-- ---------------------------------------------------------------------
--  Div handlers
-- ---------------------------------------------------------------------
local function theorem_div(div, env, starred, ctx)
  local blocks = pandoc.List(div.content)
  local info = take_head(blocks)
  blocks = walk_blocks(blocks, ctx)
  local name = NAMES[lang][env] or env
  local head = pandoc.List({pandoc.Str(name)})
  if (NUMBERED[env] or (lang == 'en' and NUMBERED_EN[env])) and not starred then
    thm_counter = thm_counter + 1
    local n = tostring(thm_counter)
    if numbering == 'section' then n = sec_counter .. '.' .. thm_counter end
    if info.label and labels[info.label] and labels[info.label].num ~= n then
      warn(('counter says %s, aux says %s for %s'):format(n, labels[info.label].num, info.label))
      n = labels[info.label].num
    end
    head:insert(pandoc.Str(' ' .. n))
  end
  local number = nil
  if #head > 1 then number = stringify(head[2]):gsub('^ ', '') end
  local id = info.label
  if not id and number then id = 'stmt-' .. number:gsub('%.', '-') end
  if number then
    index_entry(env, name, number, id, info.note, blocks)
  end
  local headspan = pandoc.List({pandoc.Strong(head)})
  if info.note then
    headspan:insert(pandoc.Space())
    headspan:insert(pandoc.Span(paren(info.note), {class = 'yp-thm-note'}))
  end
  headspan:insert(pandoc.Str(lang == 'zh' and '.' or '.'))
  prepend_inlines(blocks, {pandoc.Span(headspan, {class = 'yp-thm-head'})})
  -- zh: every statement uses the cls's single "yupin" style (楷体 body);
  -- en: amsthm plain vs definition style
  local upright = lang == 'en' and UPRIGHT[env]
  local classes = {'yp-thm', 'yp-' .. env, upright and 'yp-upright' or 'yp-slanted'}
  local attrs = {}
  if info.label then
    local link = pdf_link(info.label)
    if link then blocks:insert(1, pandoc.Div({pandoc.Plain({link})}, {class = 'yp-thm-pdf'})) end
  end
  return pandoc.Div(blocks, {id = id or '', class = table.concat(classes, ' ')})
end

local function proof_div(div, ctx)
  local blocks = pandoc.List(div.content)
  strip_auto_qed(blocks)
  local info = take_head(blocks)
  blocks = walk_blocks(blocks, ctx)
  local title = info.note or {pandoc.Str(NAMES[lang].proof)}
  local head = pandoc.List(title)
  head:insert(pandoc.Str(lang == 'zh' and ':' or '.'))
  prepend_inlines(blocks, {pandoc.Span({pandoc.Emph(head)}, {class = 'yp-proof-head'})})
  append_qed(blocks)
  return pandoc.Div(blocks, {class = 'yp-proof'})
end

local function solution_div(div, ctx)
  local blocks = pandoc.List(div.content)
  local info = take_head(blocks)
  blocks = walk_blocks(blocks, ctx)
  append_qed(blocks)
  local title = info.note and stringify(info.note) or NAMES[lang].solution
  local out = pandoc.List({pandoc.RawBlock('html',
    '<details class="yp-solution"><summary>' .. title .. '</summary>')})
  out:insert(pandoc.Div(blocks, {class = 'yp-solution-body'}))
  out:insert(pandoc.RawBlock('html', '</details>'))
  return out
end

local function exercises_div(div, ctx)
  local blocks = pandoc.List(div.content)
  local info = take_head(blocks)
  local group = stringify(info.group or 'A')
  local head = pandoc.List({pandoc.Strong(info.title or {})})
  if info.note then
    head:insert(pandoc.LineBreak())
    -- the cls prints this note as \red{（#3）}
    local note = pandoc.List({pandoc.Str(lang == 'zh' and '（' or '(')})
    note:extend(info.note)
    note:insert(pandoc.Str(lang == 'zh' and '）' or ')'))
    head:insert(pandoc.Span(note, {class = 'yp-red'}))
  end
  local out = pandoc.List({pandoc.Para(head)})
  local i = first_list(blocks)
  for k, b in ipairs(blocks) do
    if k == i then
      out:insert(labelled_list(b, function(n) return group .. n end))
    else
      out:extend(walk_blocks(pandoc.List({b}), ctx))
    end
  end
  return pandoc.Div(out, {class = 'yp-exercises'})
end

local function probleme_div(div, ctx)
  local blocks = pandoc.List(div.content)
  local info = take_head(blocks)
  local group = stringify(info.group or 'A')
  local out = pandoc.List({pandoc.Para({pandoc.Strong(info.title or {})})})
  qstate = {group = group, count = 0}
  out:extend(walk_blocks(blocks, {probleme = group}))
  return pandoc.Div(out, {class = 'yp-probleme'})
end

local function questions_div(div, ctx)
  local blocks = pandoc.List(div.content)
  local info = take_head(blocks)
  local i = first_list(blocks)
  if not i then return walk_blocks(blocks, ctx) end
  local list = blocks[i]
  local out
  if ctx.qprefix then
    -- inside an exercise item: A1-1), A1-2) ...
    local p = ctx.qprefix
    out = labelled_list(list, function(n) return p .. '-' .. n end)
  else
    -- top level of a probleme: E1), E2) ..., continuing with [resume]
    if not info.resume then qstate.count = 0 end
    local base, g = qstate.count, qstate.group
    out = labelled_list(list, function(n) return g .. (base + n) end)
    qstate.count = base + #list.content
  end
  blocks[i] = out
  return blocks
end

local THEOREM_ENVS = {}
for env in pairs(NAMES.zh) do
  if env ~= 'proof' and env ~= 'solution' then THEOREM_ENVS[env] = true end
end

local function handle_div(div, ctx)
  local cls = div.classes[1] or ''
  local starred = false
  local env = cls
  if cls:match('star$') and THEOREM_ENVS[cls:sub(1, -5)] then
    env, starred = cls:sub(1, -5), true
  end
  if THEOREM_ENVS[env] then return theorem_div(div, env, starred, ctx) end
  if cls == 'proof' then return proof_div(div, ctx) end
  if cls == 'solution' then return solution_div(div, ctx) end
  if cls == 'ypexercises' then return exercises_div(div, ctx) end
  if cls == 'ypprobleme' then return probleme_div(div, ctx) end
  if cls == 'ypquestions' then return questions_div(div, ctx) end
  if cls == 'ypbibentry' then
    local blocks = pandoc.List(div.content)
    local info = take_head(blocks)
    local key = 'bib:' .. stringify(info.bibkey or '')
    prepend_inlines(blocks, {pandoc.Span({pandoc.Str('[' .. num(key) .. ']')}, {class = 'yp-biblabel'})})
    return pandoc.Div(blocks, {id = key, class = 'yp-bibentry'})
  end
  if cls == 'summary' then
    return pandoc.Div(walk_blocks(pandoc.List(div.content), ctx), {class = 'yp-summary'})
  end
  div.content = walk_blocks(pandoc.List(div.content), ctx)
  return div
end

-- In-order walk so that statement counters follow document order.
walk_blocks = function(blocks, ctx)
  ctx = ctx or {}
  local out = pandoc.List()
  for _, b in ipairs(blocks) do
    local r
    if b.t == 'Div' then
      r = handle_div(b, ctx)
    elseif b.t == 'Header' then
      if numbering == 'section' and not b.classes:includes('unnumbered') then
        -- number headings as the PDF does: 2, 2.1, ...
        local n
        if b.level == 1 then
          sec_counter, thm_counter, sub_counter = sec_counter + 1, 0, 0
          n = tostring(sec_counter)
        elseif b.level == 2 then
          sub_counter = sub_counter + 1
          n = sec_counter .. '.' .. sub_counter
        end
        if n then
          local c = pandoc.Inlines({pandoc.Span({pandoc.Str(n)}, {class = 'yp-secnum'}), pandoc.Space()})
          c:extend(b.content)
          b.content = c
        end
      end
      r = b
    elseif b.t == 'OrderedList' then
      for k, item in ipairs(b.content) do b.content[k] = walk_blocks(pandoc.List(item), ctx) end
      r = b
    elseif b.t == 'BulletList' then
      for k, item in ipairs(b.content) do b.content[k] = walk_blocks(pandoc.List(item), ctx) end
      r = b
    elseif b.t == 'Figure' then
      -- "Figure 5." in front of the caption, numbered as in the PDF
      local id = b.identifier
      if id ~= '' and labels[id] and b.caption.long[1] then
        local word = lang == 'zh' and '图 ' or 'Figure '
        local cap = b.caption.long[1]
        local c = pandoc.Inlines({pandoc.Span({pandoc.Str(word .. labels[id].num .. '.')}, {class = 'yp-fignum'}), pandoc.Space()})
        c:extend(cap.content)
        cap.content = c
      end
      r = b
    elseif b.t == 'BlockQuote' then
      b.content = walk_blocks(pandoc.List(b.content), ctx)
      r = b
    else
      r = b
    end
    if r.t then out:insert(r) else out:extend(r) end
  end
  return out
end

-- Browser-tab title: formulas as plain characters (\sigma -> σ, \mathbb{R} -> R).
local GREEK = {alpha='α', beta='β', gamma='γ', delta='δ', varepsilon='ε', epsilon='ε', zeta='ζ',
  eta='η', theta='θ', kappa='κ', lambda='λ', mu='μ', nu='ν', xi='ξ', pi='π', rho='ρ',
  sigma='σ', tau='τ', varphi='φ', phi='φ', chi='χ', psi='ψ', omega='ω', Gamma='Γ', Delta='Δ',
  Theta='Θ', Lambda='Λ', Pi='Π', Sigma='Σ', Phi='Φ', Psi='Ψ', Omega='Ω', infty='∞'}
function plain_text(inlines)
  local out = {}
  pandoc.Inlines(inlines):walk({
    Str = function(e) out[#out + 1] = e.text end,
    Space = function() out[#out + 1] = ' ' end,
    Math = function(m)
      local t = m.text:gsub('\\(%a+)', function(c) return GREEK[c] or '' end)
      out[#out + 1] = (t:gsub('[{}^_\\]', ''))
    end,
  })
  return table.concat(out)
end

-- ---------------------------------------------------------------------
--  Page assembly
-- ---------------------------------------------------------------------
function Pandoc(doc)
  -- a bare \includegraphics (a TikZ figure without \caption) has the alt text
  -- "image", which the markdown writer would print under the figure
  doc = doc:walk({Image = function(el)
    if stringify(el.caption) == 'image' then el.caption = {} end
    return el
  end})
  read_meta(doc.meta)
  local blocks = walk_blocks(pandoc.List(doc.blocks))
  blocks = pandoc.Blocks(blocks):walk(inline_filter)
  blocks = blocks:walk({Inlines = glue_punct})

  -- The page title is the first level-1 heading (\lecture or \section).
  -- A lecture with a short title (from the progress table) shows that instead,
  -- and its long heading, a list of the lecture's topics, goes under the banner.
  local short = stringify(doc.meta['yp-short-title'] or '')
  local lede
  for i, b in ipairs(blocks) do
    if b.t == 'Header' and b.level == 1 then
      if short ~= '' then
        doc.meta.title = pandoc.Inlines({pandoc.Str(short)})
        doc.meta.pagetitle = short
        lede = pandoc.Div({pandoc.Para(b.content)}, {class = 'yp-lede'})
      else
        doc.meta.title = b.content
        doc.meta.pagetitle = plain_text(b.content)
      end
      blocks:remove(i)
      break
    end
  end
  if lede then blocks:insert(1, lede) end

  -- Banner: lecture number and a link into the PDF.
  local banner = pandoc.List()
  local kicker = stringify(doc.meta['yp-kicker'] or '')
  if kicker ~= '' then banner:insert(pandoc.Span({pandoc.Str(kicker)}, {class = 'yp-kicker'})) end
  local pdfpage = stringify(doc.meta['yp-pdf-page'] or '')
  if pdf_url ~= '' and pdfpage ~= '' then
    banner:insert(pandoc.Link({pandoc.Str(lang == 'zh' and '在 PDF 中打开' or 'Open in PDF')},
      pdf_url .. '#page=' .. pdfpage, '', {class = 'yp-banner-pdf'}))
  end
  if #banner > 0 then blocks:insert(1, pandoc.Div({pandoc.Plain(banner)}, {class = 'yp-banner'})) end

  -- data-* attributes feed the "continue reading" script in head.html
  local body_attr = {class = 'yp-body yp-' .. lang}
  for _, k in ipairs({'yp-book', 'yp-book-title', 'yp-crumb'}) do
    local v = stringify(doc.meta[k] or '')
    if v ~= '' then body_attr['data-' .. k:sub(4)] = v end
  end
  doc.blocks = {pandoc.Div(blocks, body_attr)}
  for _, k in ipairs({'yp-labels', 'yp-page', 'yp-lang', 'yp-numbering', 'yp-thm-offset',
      'yp-sec-offset', 'yp-pdf', 'yp-kicker', 'yp-pdf-page', 'yp-index',
      'yp-book', 'yp-book-title', 'yp-crumb', 'yp-short-title'}) do
    doc.meta[k] = nil
  end
  return doc
end
