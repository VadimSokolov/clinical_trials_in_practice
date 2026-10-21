-- misc/drop-hr-pdf.lua
-- PDF only. A markdown rule (---) between paragraphs is a scene break in the sources. The scrbook class draws it as a
-- long line with blank space around it, so the PDF leaves it out. HTML output is untouched.

if FORMAT:match("latex") or FORMAT:match("pdf") then
  function HorizontalRule()
    return {}
  end
end
