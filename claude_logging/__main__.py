#!/usr/bin/env python3

import argparse
import datetime
import os
import subprocess
import sys
from pathlib import Path

# Import our local modules
try:
    from claude_logging import pytermdump
    from claude_logging.ansi2html import generate_html
except ImportError:
    print("Error: Required modules not found. Make sure the claude_logging package is properly installed.")
    sys.exit(1)

def dump_command(args):
    """
    Process a file with termdump and convert it to HTML.
    This command:
    1. Reads input file
    2. Processes terminal escape sequences with pytermdump
    3. Converts the processed output to HTML with ansi2html
    4. Writes the HTML to the output file
    """
    # Determine input source
    if args.input_file == '-':
        input_data = sys.stdin.buffer.read()
    else:
        try:
            with open(args.input_file, 'rb') as f:
                input_data = f.read()
        except Exception as e:
            print(f"Error reading input file: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Process with pytermdump
    try:
        processed_data = pytermdump.termdump(input_data)
        processed_text = processed_data.decode('utf-8', errors='replace')
    except Exception as e:
        print(f"Error processing with pytermdump: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Convert to HTML
    try:
        html_output = generate_html(processed_text)
    except Exception as e:
        print(f"Error converting to HTML: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Determine output destination
    if args.output_file == '-':
        sys.stdout.write(html_output)
    else:
        try:
            with open(args.output_file, 'w') as f:
                f.write(html_output)
            print(f"HTML output written to {args.output_file}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)

def get_default_output_path(input_file):
    """Generate a default output filename in the current directory with .html extension"""
    if input_file == '-':
        return '-'  # Use stdout for stdin input
        
    input_path = Path(input_file)
    # Use just the filename without directory, and replace extension with .html
    filename = input_path.name
    return str(Path(filename).with_suffix('.html'))

def claude_command(args):
    """
    Execute the claude command and log the session.
    This is the default mode that:
    1. Creates a log directory if needed
    2. Generates a unique log filename based on current directory and timestamp
    3. Uses script command to record the session
    4. Passes all command line arguments to the claude command
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.expanduser("~/.claude/logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Get current directory path, strip home directory prefix
    home = os.path.expanduser("~")
    current_dir = os.getcwd()
    if current_dir.startswith(home):
        current_dir = current_dir[len(home)+1:]  # +1 to remove the leading /
    
    # Replace slashes with underscores for filename
    dir_name = current_dir.replace('/', '_')
    
    # Get current date and time
    datetime_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create log filename
    log_file = os.path.join(log_dir, f"{dir_name}_{datetime_str}.log")
    
    # Combine all remaining args into command string
    claude_args = args.claude_args if hasattr(args, 'claude_args') else []
    
    try:
        # Build the claude command including all arguments
        claude_cmd = ["claude"] + claude_args
        
        # Use script to record the session
        # We need to pass the command as a single string to script
        cmd = ["script", "--flush", "--quiet", "--return", "--command", 
               " ".join(claude_cmd), log_file]
            
        # Execute command
        subprocess.run(cmd)
    except Exception as e:
        print(f"Error executing claude command: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Main entry point for the claude-logging CLI"""
    # Check if first arg is 'dump' to decide which mode to run
    if len(sys.argv) > 1 and sys.argv[1] == 'dump':
        # 'dump' subcommand mode
        parser = argparse.ArgumentParser(description='Claude logging utilities')
        subparsers = parser.add_subparsers(dest='command')
        
        # 'dump' subcommand
        dump_parser = subparsers.add_parser('dump', 
                                          help='Process a file with terminal escape sequences and convert to HTML')
        dump_parser.add_argument('input_file', 
                              help='Input file (use "-" for stdin)')
        dump_parser.add_argument('-o', '--output', dest='output_file',
                              help='Output file (default: <input_file>.html or stdout for stdin)')
        
        # Parse the arguments
        args = parser.parse_args()
        
        # If no output file is specified, use default naming
        if args.output_file is None:
            args.output_file = get_default_output_path(args.input_file)
        dump_command(args)
    else:
        # Default mode: Run claude with logging
        # Don't use argparse since we want to pass all args directly to claude
        claude_args = sys.argv[1:]
        args = argparse.Namespace(claude_args=claude_args)
        claude_command(args)

if __name__ == '__main__':
    main()