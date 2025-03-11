#!/usr/bin/env python3
import re
import sys
import argparse
from html import escape


# ANSI color codes
RESET = 0
BOLD = 1
FG_BLACK = 30
FG_RED = 31
FG_GREEN = 32
FG_YELLOW = 33
FG_BLUE = 34
FG_MAGENTA = 35
FG_CYAN = 36
FG_WHITE = 37
BG_BLACK = 40
BG_RED = 41
BG_GREEN = 42
BG_YELLOW = 43
BG_BLUE = 44
BG_MAGENTA = 45
BG_CYAN = 46
BG_WHITE = 47

# True color indicators
FG_TRUE_COLOR = 38
BG_TRUE_COLOR = 48

# Regular expression to find ANSI escape sequences
ANSI_ESCAPE_RE = re.compile(r'\x1b\[((?:\d+;)*\d*)m')


def parse_ansi_code(code_str):
    """Parse ANSI code into a list of integers."""
    if not code_str:
        return [0]  # Default to reset
    return [int(c) for c in code_str.split(';') if c]


def ansi_to_css(ansi_codes):
    """Convert ANSI codes to CSS styles."""
    styles = []
    fg_color = None
    bg_color = None
    bold = False
    
    i = 0
    while i < len(ansi_codes):
        code = ansi_codes[i]
        
        if code == RESET:
            return []  # Reset all styles
        elif code == BOLD:
            bold = True
        # Handle true color (24-bit) foreground: ESC[38;2;r;g;bm
        elif code == FG_TRUE_COLOR and i + 4 < len(ansi_codes) and ansi_codes[i+1] == 2:
            r, g, b = ansi_codes[i+2], ansi_codes[i+3], ansi_codes[i+4]
            styles.append(f"fg-true-color")
            styles.append(f"fg-rgb-{r}-{g}-{b}")
            i += 4  # Skip the parameters we just processed
        # Handle true color (24-bit) background: ESC[48;2;r;g;bm
        elif code == BG_TRUE_COLOR and i + 4 < len(ansi_codes) and ansi_codes[i+1] == 2:
            r, g, b = ansi_codes[i+2], ansi_codes[i+3], ansi_codes[i+4]
            styles.append(f"bg-true-color")
            styles.append(f"bg-rgb-{r}-{g}-{b}")
            i += 4  # Skip the parameters we just processed
        # Handle standard foreground colors
        elif FG_BLACK <= code <= FG_WHITE:
            fg_color = code - FG_BLACK
            styles.append(f"c{fg_color}")
        # Handle standard background colors
        elif BG_BLACK <= code <= BG_WHITE:
            bg_color = code - BG_BLACK
            styles.append(f"bg{bg_color}")
        
        i += 1

    if bold:
        styles.append("bold")

    return styles


def ansi_to_html(text):
    """Convert ANSI colored text to HTML with CSS classes."""
    result = []
    pos = 0
    active_styles = []

    # Process all ANSI escape sequences
    for match in ANSI_ESCAPE_RE.finditer(text):
        # Add text before the escape sequence
        if pos < match.start():
            if active_styles:
                css_class = " ".join(active_styles)
                result.append(f'<span class="{css_class}">{escape(text[pos:match.start()])}</span>')
            else:
                result.append(escape(text[pos:match.start()]))

        # Process the escape sequence
        ansi_codes = parse_ansi_code(match.group(1))
        if 0 in ansi_codes:  # Reset
            active_styles = []
        else:
            active_styles = ansi_to_css(ansi_codes)

        pos = match.end()

    # Add any remaining text
    if pos < len(text):
        if active_styles:
            css_class = " ".join(active_styles)
            result.append(f'<span class="{css_class}">{escape(text[pos:])}</span>')
        else:
            result.append(escape(text[pos:]))

    return ''.join(result)


def generate_html(input_text):
    """Generate complete HTML with the converted content."""
    lines = input_text.split('\n')
    html_lines = []
    
    for i, line in enumerate(lines, 1):
        html_content = ansi_to_html(line)
        html_lines.append(
            f'<div id="L{i}" class="line" data-line-number="{i}">'
            f'<span class="line-number">{i}</span>'
            f'<span class="line-content">{html_content}</span>'
            f'</div>'
        )
    
    html_content = '\n'.join(html_lines)
    
    # Create the full HTML document
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terminal Output</title>
    <style>
        :root {{
            /* Dark theme (default) */
            --bg-color: #1e1e1e;
            --text-color: #f0f0f0;
            --line-number-color: #888;
            --line-highlight-color: rgba(255, 255, 100, 0.1);
            --border-color: #444;
            
            /* ANSI colors - Dark theme */
            --c0-color: #a0a0a0; /* black (gray in dark mode) */
            --c1-color: #f44336; /* red */
            --c2-color: #4caf50; /* green */
            --c3-color: #ffeb3b; /* yellow */
            --c4-color: #2196f3; /* blue */
            --c5-color: #9c27b0; /* magenta */
            --c6-color: #00bcd4; /* cyan */
            --c7-color: #ffffff; /* white */
            
            /* Background colors - Dark theme */
            --bg0-color: #000000; /* black */
            --bg1-color: #f44336; /* red */
            --bg2-color: #4caf50; /* green */
            --bg3-color: #ffeb3b; /* yellow */
            --bg4-color: #2196f3; /* blue */
            --bg5-color: #9c27b0; /* magenta */
            --bg6-color: #00bcd4; /* cyan */
            --bg7-color: #ffffff; /* white */
        }}

        [data-theme="light"] {{
            --bg-color: #f8f8f8;
            --text-color: #333;
            --line-number-color: #999;
            --line-highlight-color: rgba(255, 220, 0, 0.2);
            --border-color: #ddd;
            
            /* ANSI colors - Light theme */
            --c0-color: #6a6a6a; /* black */
            --c1-color: #d32f2f; /* red */
            --c2-color: #388e3c; /* green */
            --c3-color: #f57f17; /* yellow */
            --c4-color: #1976d2; /* blue */
            --c5-color: #7b1fa2; /* magenta */
            --c6-color: #0097a7; /* cyan */
            --c7-color: #333333; /* white (dark in light mode) */
            
            /* Background colors - Light theme */
            --bg0-color: #f0f0f0; /* black */
            --bg1-color: #ffcdd2; /* red */
            --bg2-color: #c8e6c9; /* green */
            --bg3-color: #fff9c4; /* yellow */
            --bg4-color: #bbdefb; /* blue */
            --bg5-color: #e1bee7; /* magenta */
            --bg6-color: #b2ebf2; /* cyan */
            --bg7-color: #ffffff; /* white */
        }}
        
        body {{
            font-family: 'Courier New', monospace;
            line-height: 1.2;
            margin: 0;
            padding: 0;
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: all 0.3s ease;
        }}
        
        #controls {{
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 100;
            background-color: var(--bg-color);
            padding: 5px 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
        }}
        
        #theme-toggle {{
            padding: 5px 10px;
            background-color: var(--text-color);
            color: var(--bg-color);
            border: none;
            border-radius: 3px;
            cursor: pointer;
        }}
        
        #container {{
            padding: 10px 0;
        }}
        
        .line {{
            display: flex;
            white-space: pre;
            position: relative;
            padding: 0 10px;
            cursor: pointer;
        }}
        
        .line:hover {{
            background-color: rgba(128, 128, 128, 0.1);
        }}
        
        .line-number {{
            display: inline-block;
            width: 40px;
            padding-right: 10px;
            color: var(--line-number-color);
            text-align: right;
            user-select: none;
        }}
        
        .line-content {{
            flex-grow: 1;
            padding-left: 10px;
            border-left: 1px solid var(--border-color);
        }}
        
        .line.highlighted {{
            background-color: var(--line-highlight-color);
        }}
        
        /* ANSI colors */
        .c0 {{ color: var(--c0-color); }}  /* black */
        .c1 {{ color: var(--c1-color); }}  /* red */
        .c2 {{ color: var(--c2-color); }}  /* green */
        .c3 {{ color: var(--c3-color); }}  /* yellow */
        .c4 {{ color: var(--c4-color); }}  /* blue */
        .c5 {{ color: var(--c5-color); }}  /* magenta */
        .c6 {{ color: var(--c6-color); }}  /* cyan */
        .c7 {{ color: var(--c7-color); }}  /* white */
        
        /* Background colors */
        .bg0 {{ background-color: var(--bg0-color); }}
        .bg1 {{ background-color: var(--bg1-color); }}
        .bg2 {{ background-color: var(--bg2-color); }}
        .bg3 {{ background-color: var(--bg3-color); }}
        .bg4 {{ background-color: var(--bg4-color); }}
        .bg5 {{ background-color: var(--bg5-color); }}
        .bg6 {{ background-color: var(--bg6-color); }}
        .bg7 {{ background-color: var(--bg7-color); }}
        
        /* True colors */
        .fg-true-color {{ }}  /* Base class for true color foreground */
        .bg-true-color {{ }}  /* Base class for true color background */
        
        /* Generated dynamically for true colors */
        [class*="fg-rgb-"] {{ color: rgb(var(--rgb-values)); }}
        [class*="bg-rgb-"] {{ background-color: rgb(var(--rgb-values)); }}
        
        /* Text styles */
        .bold {{ font-weight: bold; }}
    </style>
</head>
<body>
    <div id="controls">
        <button id="theme-toggle">Switch to Light Theme</button>
    </div>
    <div id="container">
{html_content}
    </div>
    
    <script>
        // Theme toggling
        const themeToggle = document.getElementById('theme-toggle');
        const body = document.body;
        
        themeToggle.addEventListener('click', () => {{
            const isLightTheme = body.getAttribute('data-theme') === 'light';
            body.setAttribute('data-theme', isLightTheme ? 'dark' : 'light');
            themeToggle.textContent = isLightTheme ? 'Switch to Light Theme' : 'Switch to Dark Theme';
        }});
        
        // Process RGB true color classes
        function processRgbColors() {{
            // Process foreground RGB colors
            document.querySelectorAll('[class*="fg-rgb-"]').forEach(el => {{
                const classList = Array.from(el.classList);
                const rgbClass = classList.find(cls => cls.startsWith('fg-rgb-'));
                if (rgbClass) {{
                    const [_, __, r, g, b] = rgbClass.split('-');
                    el.style.setProperty('--rgb-values', `${{r}},${{g}},${{b}}`);
                }}
            }});
            
            // Process background RGB colors
            document.querySelectorAll('[class*="bg-rgb-"]').forEach(el => {{
                const classList = Array.from(el.classList);
                const rgbClass = classList.find(cls => cls.startsWith('bg-rgb-'));
                if (rgbClass) {{
                    const [_, __, r, g, b] = rgbClass.split('-');
                    el.style.setProperty('--rgb-values', `${{r}},${{g}},${{b}}`);
                }}
            }});
        }}
        
        // Line highlighting and permalinks
        let firstSelectedLine = null;
        const lines = document.querySelectorAll('.line');
        
        function clearHighlights() {{
            lines.forEach(line => line.classList.remove('highlighted'));
        }}
        
        function highlightLine(lineNum) {{
            document.getElementById(`L${{lineNum}}`).classList.add('highlighted');
            setPermalink(lineNum);
        }}
        
        function highlightRange(start, end) {{
            if (start > end) {{
                [start, end] = [end, start]; // Swap if needed
            }}
            
            for (let i = start; i <= end; i++) {{
                document.getElementById(`L${{i}}`).classList.add('highlighted');
            }}
            
            setPermalink(start, end);
        }}
        
        function setPermalink(start, end) {{
            const hash = end ? `L${{start}}-L${{end}}` : `L${{start}}`;
            window.history.replaceState(null, '', `#${{hash}}`);
        }}
        
        lines.forEach(line => {{
            line.addEventListener('click', (event) => {{
                const lineNum = parseInt(line.getAttribute('data-line-number'));
                
                if (event.shiftKey && firstSelectedLine) {{
                    clearHighlights();
                    highlightRange(firstSelectedLine, lineNum);
                    firstSelectedLine = null;
                }} else {{
                    clearHighlights();
                    highlightLine(lineNum);
                    firstSelectedLine = lineNum;
                }}
            }});
        }});
        
        // Handle initial hash (permalink)
        function handlePermalink() {{
            const hash = window.location.hash;
            if (!hash) return;
            
            if (hash.includes('-')) {{
                const [start, end] = hash.slice(1).split('-').map(id => parseInt(id.slice(1)));
                if (!isNaN(start) && !isNaN(end)) {{
                    clearHighlights();
                    highlightRange(start, end);
                    firstSelectedLine = null;
                }}
            }} else {{
                const lineNum = parseInt(hash.slice(2));
                if (!isNaN(lineNum)) {{
                    clearHighlights();
                    highlightLine(lineNum);
                    firstSelectedLine = lineNum;
                }}
            }}
        }}
        
        // Handle permalink on page load and when hash changes
        window.addEventListener('hashchange', handlePermalink);
        document.addEventListener('DOMContentLoaded', () => {{
            handlePermalink();
            processRgbColors();
        }});
        
        // Process colors immediately
        processRgbColors();
    </script>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description='Convert ANSI terminal output to HTML')
    parser.add_argument('input_file', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help='Input file (default: stdin)')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout,
                        help='Output file (default: stdout)')
    args = parser.parse_args()

    # Read input
    input_text = args.input_file.read()
    
    # Generate HTML
    html = generate_html(input_text)
    
    # Write output
    args.output.write(html)
    
    # Close files if not stdin/stdout
    if args.input_file is not sys.stdin:
        args.input_file.close()
    if args.output is not sys.stdout:
        args.output.close()


if __name__ == "__main__":
    main()