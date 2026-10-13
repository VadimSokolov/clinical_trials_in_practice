-- misc/callout-pdf.lua
-- PDF only. Long callouts are converted to flowing prose (the title becomes a
-- bold run-in paragraph, then the content flows normally) so they never break
-- across a page as a box. Short callouts are left as boxes; combined with the
-- `breakable -> unbreakable` override in misc/preamble.tex they stay on one
-- page. HTML output is unaffected.
--
-- PROSE_THRESHOLD is an approximate count of rendered text characters. Anything
-- longer becomes prose; raise it to keep more content boxed, lower it to box
-- less. Keep it well under a page so the remaining (unbreakable) boxes fit.
--
-- IMPORTANT: callout.content is a Quarto custom-AST node (Lua userdata), NOT a
-- plain pandoc.Blocks list. `ipairs(callout.content)` and `#callout.content`
-- DO NOT WORK on it (ipairs yields nothing, # errors), even though
-- pandoc.utils.stringify walks it fine. Iterating it directly silently drops
-- the entire body and leaves only the title. Use quarto.utils.as_blocks() to
-- materialize it into a real, iterable pandoc.Blocks before touching it.

local PROSE_THRESHOLD = 800

function Callout(callout)
  if not quarto.doc.is_format("pdf") then
    return nil
  end

  local content = quarto.utils.as_blocks(callout.content)
  local text = pandoc.utils.stringify(content or {})
  if #text < PROSE_THRESHOLD then
    return nil  -- short enough to stay a (single-page) box
  end

  -- Convert to prose: bold run-in title (if any) followed by the content blocks.
  local blocks = pandoc.Blocks({})
  local title_text = pandoc.utils.stringify(callout.title or "")
  if #title_text > 0 then
    blocks:insert(pandoc.Para({ pandoc.Strong({ pandoc.Str(title_text) }) }))
  end
  blocks:extend(content)
  return blocks
end
