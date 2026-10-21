-- misc/table-longtoken-wrap.lua
-- PDF only. Long unbreakable tokens in table cells (notably e-mail addresses
-- such as CDERBiomarkerQualificationProgram@fda.hhs.gov) have no hyphenation
-- points, so on the narrow trim they overrun their column and overlap
-- the neighbouring one. Wrap such tokens in \seqsplit{} (seqsplit package,
-- loaded in misc/preamble.tex) so xelatex may break them at any character when
-- a line would otherwise overflow. Only tokens containing '@' are touched, so
-- ordinary words (which LaTeX can already hyphenate) are left alone. HTML output
-- is untouched.

local function wrap_token(el)
  if el.text:find("@") and #el.text >= 12 then
    return pandoc.RawInline("latex", "\\seqsplit{" .. el.text .. "}")
  end
  return nil
end

function Table(tbl)
  if not quarto.doc.is_format("pdf") then
    return nil
  end
  return pandoc.walk_block(tbl, { Str = wrap_token })
end
