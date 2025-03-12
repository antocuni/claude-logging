# Claude Logging

Automatically keep logs of "claude code" sessions, and convert them to HTML.

## Features

- Automatically log `claude` sessions in `~/.claude/logs`
- Convert logged session into HTML files
- Strips control characters and preserves text formatting
- Converts terminal output to styled HTML
- Supports syntax highlighting, bold text, and colors
- Includes line numbering and theme toggling in the HTML output

**NOTE**: this tool has largely been written by claude itself. The quality of
the code is a direct consequence of it.

## Installation

The easiest way is to run it without need of installation through [`uxv`](https://docs.astral.sh/uv/guides/tools/):
```
uvx claude-logging
```

This will start a normal `claude` session, but will record the log in `~/.claude/logs`.

For automatic logging of _every_ invocation of `claude`, you can put an alias
in your `~/.bashrc` or equivalent:

```
alias claude="uxv claude-logging"
```

If you prefer a more classical installation method, you can use `pip`:
```bash
pip install claude-logging
```

## Usage

### Default Mode: Record Claude Sessions

When you run the command `claude-logging`, it will:

1. Create a log directory at `~/.claude/logs/` if it doesn't exist
2. Generate a unique log filename based on your current directory and timestamp
3. Run the `claude` command with all provided arguments
4. Record the entire session to the log file

All the arguments are directly passed to the underyling `claude` program.

### HTML Conversion Mode

Convert existing log files to HTML:

```bash
# Convert a log file to HTML
claude-logging dump ~/.claude/logs/my.log

# Bulk convert multiple files
claude-logging dump ~/.claude/logs/my*.log

# Output to a specific file
claude-logging dump ~/.claude/logs/my.log -o my.html

# Use stdin/stdout
cat logfile.log | claude-logging dump - > output.html
```

## Example logs

These are some of the sessions in which I used `claude` to write `claude-logging`:

  - [create ansi2html.py](https://antocuni.github.io/files/claude-code/claude-logging/claude-logging-2.2025-03-11.0.html),
    which converts a terminal dump into a HTML page with proper colors and
    permalinks

  - [write the pytermdump C extension and setup CI to build/publish wheels](https://antocuni.github.io/files/claude-code/claude-logging/claude-logging-2.2025-03-11.1.html)

  - [tweaks and refinements on the claude-logging script](https://antocuni.github.io/files/claude-code/claude-logging/claude-logging-2.2025-03-12.2.html)

You can click on a line or shift-click on a range of lines to generate a
permalink to a specific part of the log. For example, this is
[when I asked claude not to build windows wheels](https://antocuni.github.io/files/claude-code/claude-logging/claude-logging-2.2025-03-11.1.html#L4414-L4457).


## How it works

Unfortunately `claude` doesn't seem to offer a way to get a structured log of
the conversation, so the only possible way is to get a dump of the terminal.

This is doable using the `script` program in linux, which records all
characters sent to a TTY:
```
script --flush --quiet --return --command "claude $*" "$LOG_FILE"
```

However, the resulting file is not directly usable, because `claude` is a rich
terminal application and it constantly redraws parts of the screen. The raw
log includes *all* characters ever sent to the TTY, including the ones which
are responsible to erase one or more lines, and the ones which are responsible
to redraw.

For example, for each key pressed by the user, `claude` erases and redraws the
whole input box. If you inspect a raw log files using `less -R` you can see it
clearly. This is part of the log generated by typing `hello` in the input box:

```
╭──────────────────────────────────────────────────────────────────────────────╮
│ >                                                                            │
╰──────────────────────────────────────────────────────────────────────────────╯
  ! for bash mode · / for commands                              \⏎ for newline



╭──────────────────────────────────────────────────────────────────────────────╮
│ > Try "how do I log an error?"                                               │
╰──────────────────────────────────────────────────────────────────────────────╯
  ! for bash mode · / for commands                              \⏎ for newline



╭──────────────────────────────────────────────────────────────────────────────╮
│ > h                                                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
  ! for bash mode · / for commands                              \⏎ for newline



╭──────────────────────────────────────────────────────────────────────────────╮
│ > he                                                                         │
╰──────────────────────────────────────────────────────────────────────────────╯
  ! for bash mode · / for commands                              \⏎ for newline



╭──────────────────────────────────────────────────────────────────────────────╮
│ > hel                                                                        │
╰──────────────────────────────────────────────────────────────────────────────╯
  ! for bash mode · / for commands                              \⏎ for newline



╭──────────────────────────────────────────────────────────────────────────────╮
│ > hell                                                                       │
╰──────────────────────────────────────────────────────────────────────────────╯
  ! for bash mode · / for commands                              \⏎ for newline



╭──────────────────────────────────────────────────────────────────────────────╮
│ > hello                                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
  ! for bash mode · / for commands                              \⏎ for newline
```

The solution is to "replay" all the commands sent to the terminal, in order to
get the final state of the screen. For doing that we need to write a basic
version of a terminal emulator: fortunately, we just need to support a handful
number of ANSI escape sequences. This is the job of
[termdump.c](claude_logging/termdump.c) and [pytermdump.c](claude_logging/pytermdump.c)

The core logic is in `termdump.c`, which takes a raw log file and produces the
"final state" of the terminal. Ironically, claude itself was not able to
produce a working version of `termdump.c`,
[which was written by chatgpt](https://chatgpt.com/share/67d1b341-9168-8002-a0a9-4935a5b796f3).

Once we have the "dumped" version of the screen, we can convert it into HTML
using [ansi2html.py](claude_logging/ansi2html.py).



## License

MIT License
