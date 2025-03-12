# Claude Logging

Automatically keep logs of "claude code" sessions, and convert them to HTML.

## Features

- Automatically log `claude` sessions in `~/.claude/logs`
- Convert logged session into HTML files
- Strips control characters and preserves text formatting
- Converts terminal output to styled HTML
- Supports syntax highlighting, bold text, and colors
- Includes line numbering and theme toggling in the HTML output

## Installation

```bash
pip install claude-logging
```

It is also possible to run it directly using [`uxv`](https://docs.astral.sh/uv/guides/tools/):
```
uvx claude-logging
```

For automatic logging of _every_ invocation of `claude`, you can put an alias
in your `~/.bashrc` or equivalent:

```
alias claude="uxv claude-logging"
```

## Usage

### Default Mode: Record Claude Sessions

When you run the command `claude-logging`, it will:

1. Create a log directory at `~/.claude/logs/` if it doesn't exist
2. Generate a unique log filename based on your current directory and timestamp
3. Run the `claude` command with all provided arguments
4. Record the entire session to the log file

```bash
# Run claude with logging
claude-logging

# Pass arguments to claude
claude-logging --help
claude-logging path/to/your/file.py
```

### HTML Conversion Mode

Convert existing log files to HTML:

```bash
# Convert a log file to HTML
claude-logging dump path/to/logfile.log

# Output to a specific file
claude-logging dump path/to/logfile.log -o output.html

# Use stdin/stdout
cat logfile.log | claude-logging dump - > output.html
```

## License

MIT License
