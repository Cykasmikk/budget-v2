/**
 * Simple markdown parser for chat messages.
 * Converts basic markdown syntax to HTML.
 */

/**
 * Converts markdown text to HTML with basic formatting support.
 * Handles: bold (**text**), italic (*text*), lists (- or *), and line breaks.
 */
export function markdownToHtml(text: string): string {
  if (!text) return '';

  // Escape existing HTML to prevent XSS
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Split into lines for processing
  const lines = html.split('\n');
  const processedLines: string[] = [];
  let inList = false;

  for (let i = 0; i < lines.length; i++) {
    const originalLine = lines[i];
    const trimmedLine = originalLine.trim();
    
    // Check for list items (starting with * or - followed by space)
    // Match pattern: "* " or "- " at start of line
    const listMatch = trimmedLine.match(/^([-*])\s+(.+)$/);

    if (listMatch) {
      if (!inList) {
        processedLines.push('<ul>');
        inList = true;
      }
      // Process the list item content (will process bold/italic later)
      const itemContent = listMatch[2];
      processedLines.push(`<li>${itemContent}</li>`);
    } else {
      if (inList) {
        processedLines.push('</ul>');
        inList = false;
      }
      if (trimmedLine) {
        processedLines.push(`<p>${trimmedLine}</p>`);
      } else if (i < lines.length - 1) {
        // Empty line between paragraphs
        processedLines.push('<br>');
      }
    }
  }

  if (inList) {
    processedLines.push('</ul>');
  }

  html = processedLines.join('');

  // Convert **bold** text (process after lists to handle bold in list items)
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Convert *italic* text (but not if it's part of **)
  // Match *text* but avoid matching list markers or bold markers
  html = html.replace(/(?<!\*)\*([^*\s][^*]*?[^*\s])\*(?!\*)/g, '<em>$1</em>');

  return html;
}
