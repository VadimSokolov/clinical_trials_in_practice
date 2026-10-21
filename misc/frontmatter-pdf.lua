-- misc/frontmatter-pdf.lua
-- PDF only. Puts a copyright page after the title page and drops the date from the title page.
-- The year and DOI come from the metadata; the ISBN is set only in the print build (book-has-isbn true).
-- For any other format the filter returns no handlers, so HTML output is untouched.

local function stringify(v)
  if v == nil then
    return ""
  end
  return pandoc.utils.stringify(v)
end

-- Escape LaTeX special characters in text taken from metadata.
local special = {
  ["\\"] = "\\textbackslash{}",
  ["{"] = "\\{",
  ["}"] = "\\}",
  ["$"] = "\\$",
  ["&"] = "\\&",
  ["#"] = "\\#",
  ["^"] = "\\textasciicircum{}",
  ["_"] = "\\_",
  ["%"] = "\\%",
  ["~"] = "\\textasciitilde{}",
}

local function esc(s)
  return (s:gsub("[\\{}$&#%^_%%~]", special))
end

local function add_header(meta, tex)
  local hi = meta['header-includes']
  if hi == nil then
    hi = pandoc.MetaList({})
  elseif hi.t ~= 'MetaList' then
    hi = pandoc.MetaList({hi})
  end
  table.insert(hi, pandoc.MetaBlocks({pandoc.RawBlock('latex', tex)}))
  meta['header-includes'] = hi
end

local tex_template = [==[
\newcommand{\ctpYear}{@YEAR@}
\newcommand{\ctpDOI}{@DOI@}
\newcommand{\ctpISBN}{@ISBN@}
\newcommand{\CopyrightPage}{%
  \clearpage
  \thispagestyle{empty}%
  \vspace*{\fill}%
  \noindent Clinical Trials in Practice\par
  \vspace{0.8em}
  \noindent Copyright \textcopyright{} \ctpYear{} Alexandra Sokolova and Vadim Sokolov\par
  \vspace{0.8em}
  \noindent License: the text, figures and PDF are distributed under the Creative Commons Attribution 4.0 International License (CC BY 4.0), \texttt{https:\allowbreak//creativecommons.org\allowbreak/licenses\allowbreak/by\allowbreak/4.0/}. You may copy, share and adapt them for any purpose, provided you credit the authors. The code is released under the MIT License.\par
  \vspace{0.8em}
  \noindent Source: \texttt{https:\allowbreak//github.com\allowbreak/VadimSokolov\allowbreak/clinical\_trials\_in\_practice}\par
  \vspace{0.8em}
  \noindent First edition, \ctpYear{}\par
  \ifx\ctpISBN\empty\else
  \vspace{0.8em}
  \noindent Paperback ISBN: \ctpISBN\par
  \fi
  \vspace{0.8em}
  \noindent Digital Object Identifier (DOI): \texttt{\ctpDOI}\par
  \vspace{0.8em}
  \noindent Typeset with Quarto and LaTeX.\par
  \clearpage
}
\AtBeginDocument{\let\ctpoldmaketitle\maketitle \renewcommand*{\maketitle}{\ctpoldmaketitle\CopyrightPage}}
]==]

function Meta(meta)
  meta.date = nil

  local year = esc(stringify(meta['book-year']))
  local doi = esc(stringify(meta['book-doi']))
  local isbn = ""
  if stringify(meta['book-has-isbn']) == "true" then
    isbn = esc(stringify(meta['book-isbn']))
  end

  local tex = tex_template
    :gsub("@YEAR@", function() return year end)
    :gsub("@DOI@", function() return doi end)
    :gsub("@ISBN@", function() return isbn end)

  add_header(meta, tex)
  return meta
end

if FORMAT:match("latex") or FORMAT:match("pdf") then
  return { { Meta = Meta } }
end
return {}
