#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

#define ESC '\x1b'
#define MAX_COLS 1024

typedef struct Line {
    char *data;
    struct Line *next;
} Line;

typedef struct {
    Line *head;
    Line *tail;
    Line *cursor;
    int cursor_col;
} Screen;

void die(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    exit(1);
}

Line* make_line() {
    Line *line = malloc(sizeof(Line));
    line->data = calloc(MAX_COLS, 1);
    line->next = NULL;
    return line;
}

void screen_init(Screen *s) {
    s->head = s->tail = s->cursor = make_line();
    s->cursor_col = 0;
}

void screen_clear(Screen *s) {
    Line *line = s->head;
    while (line) {
        Line *next = line->next;
        free(line->data);
        free(line);
        line = next;
    }
    screen_init(s);
}

void screen_newline(Screen *s) {
    if (s->cursor->next == NULL) {
        Line *new_line = make_line();
        s->cursor->next = new_line;
        s->tail = new_line;
    }
    s->cursor = s->cursor->next;
    s->cursor_col = 0;
}

void screen_cursor_up(Screen *s) {
    if (s->cursor == s->head) return;
    Line *line = s->head;
    while (line && line->next != s->cursor) line = line->next;
    if (line) s->cursor = line;
}

void screen_cursor_to_home(Screen *s) {
    s->cursor = s->head;
    s->cursor_col = 0;
}

void screen_cursor_to_bol(Screen *s) {
    s->cursor_col = 0;
}

void screen_putc(Screen *s, char c) {
    if (c == '\n') {
        screen_newline(s);
        return;
    }
    if (s->cursor_col >= MAX_COLS - 1) return;
    s->cursor->data[s->cursor_col++] = c;
}

void handle_escape_sequence(Screen *s, FILE *in, char first_char) {
    if (first_char == '[') {
        char buf[8] = {0};
        int i = 0;
        while (i < 7) {
            int c = fgetc(in);
            if (c == EOF) break;
            buf[i++] = c;
            if ((c >= '@' && c <= '~')) break; // CSI end
        }
        buf[i] = '\0';

        if (strcmp(buf, "1A") == 0) {
            screen_cursor_up(s);
        } else if (strcmp(buf, "2J") == 0) {
            screen_clear(s);
        } else if (strcmp(buf, "2K") == 0) {
            memset(s->cursor->data, 0, MAX_COLS);
        } else if (strcmp(buf, "3J") == 0) {
            screen_clear(s);
        } else if (strcmp(buf, "F") == 0) {
            screen_cursor_up(s);
            screen_cursor_to_bol(s);
        } else if (strcmp(buf, "G") == 0) {
            screen_cursor_to_bol(s);
        } else if (strcmp(buf, "H") == 0) {
            screen_cursor_to_home(s);
        } else {
            // unknown sequence: print it raw
            screen_putc(s, ESC);
            screen_putc(s, '[');
            for (int j = 0; j < i; j++)
                screen_putc(s, buf[j]);
        }
    } else {
        // unknown non-CSI sequence
        screen_putc(s, ESC);
        screen_putc(s, first_char);
    }
}

void process_input(Screen *screen, FILE *in) {
    int c;
    while ((c = fgetc(in)) != EOF) {
        if (c == ESC) {
            int next = fgetc(in);
            if (next == EOF) break;
            handle_escape_sequence(screen, in, next);
        } else {
            screen_putc(screen, c);
        }
    }
}

void dump_output(Screen *s, FILE *out) {
    for (Line *line = s->head; line != NULL; line = line->next)
        fprintf(out, "%s\n", line->data);
}

int main(int argc, char **argv) {
    FILE *in = stdin;
    FILE *out = stdout;
    char *outfile = NULL;

    // CLI parsing
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "-o")) {
            if (++i >= argc) die("Missing argument for -o\n");
            outfile = argv[i];
        } else if (!in || in == stdin) {
            in = fopen(argv[i], "r");
            if (!in) die("Failed to open %s\n", argv[i]);
        }
    }

    if (outfile) {
        out = fopen(outfile, "w");
        if (!out) die("Failed to open %s for writing\n", outfile);
    }

    Screen screen;
    screen_init(&screen);
    process_input(&screen, in);
    dump_output(&screen, out);

    // cleanup
    if (in && in != stdin) fclose(in);
    if (out && out != stdout) fclose(out);
    screen_clear(&screen);
    return 0;
}
