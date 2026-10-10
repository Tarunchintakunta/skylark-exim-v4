// Tiny renderer for docs/LICENSES.md: headings, paragraphs and pipe tables only (the file uses nothing else).
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
const inline = (s: string) =>
  esc(s)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/(https?:\/\/[^\s|)]+)/g, '<a href="$1" rel="noopener">$1</a>')

export function renderMarkdown(md: string) {
  const out: string[] = []
  const lines = md.split('\n')
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i]
    if (l.startsWith('# ')) out.push(`<h1>${inline(l.slice(2))}</h1>`)
    else if (l.startsWith('## ')) out.push(`<h2>${inline(l.slice(3))}</h2>`)
    else if (l.startsWith('|')) {
      const rows: string[][] = []
      while (i < lines.length && lines[i].startsWith('|')) {
        if (!/^\|[\s|:-]+\|$/.test(lines[i]))
          rows.push(
            lines[i]
              .slice(1, -1)
              .split('|')
              .map((c) => c.trim()),
          )
        i++
      }
      i--
      const [head, ...body] = rows
      out.push(
        `<div class="table-wrap"><table><thead><tr>${head.map((h) => `<th scope="col">${inline(h)}</th>`).join('')}</tr></thead><tbody>${body
          .map((r) => `<tr>${r.map((c) => `<td>${inline(c)}</td>`).join('')}</tr>`)
          .join('')}</tbody></table></div>`,
      )
    } else if (l.trim()) out.push(`<p>${inline(l)}</p>`)
  }
  return out.join('\n')
}
