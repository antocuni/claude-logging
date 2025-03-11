#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

#define ESC '\x1b'
#define MAX_COLS 1024

// Define TERMDUMP_MAIN when compiling as a standalone program
#ifdef TERMDUMP_MAIN
#define TERMDUMP_API
#else
#define TERMDUMP_API extern
#endif

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

TERMDUMP_API void die(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    exit(1);
}

TERMDUMP_API Line* make_line() {
    Line *line = malloc(sizeof(Line));
    line->data = calloc(MAX_COLS, 1);
    line->next = NULL;
    return line;
}

TERMDUMP_API void screen_init(Screen *s) {
    s->head = s->tail = s->cursor = make_line();
    s->cursor_col = 0;
}

TERMDUMP_API void screen_clear(Screen *s) {
    Line *line = s->head;
    while (line) {
        Line *next = line->next;
        free(line->data);
        free(line);
        line = next;
    }
    screen_init(s);
}

TERMDUMP_API void screen_newline(Screen *s) {
    if (s->cursor->next == NULL) {
        Line *new_line = make_line();
        s->cursor->next = new_line;
        s->tail = new_line;
    }
    s->cursor = s->cursor->next;
    s->cursor_col = 0;
}

TERMDUMP_API void screen_cursor_up(Screen *s) {
    if (s->cursor == s->head) return;
    Line *line = s->head;
    while (line && line->next != s->cursor) line = line->next;
    if (line) s->cursor = line;
}

TERMDUMP_API void screen_cursor_to_home(Screen *s) {
    s->cursor = s->head;
    s->cursor_col = 0;
}

TERMDUMP_API void screen_cursor_to_bol(Screen *s) {
    s->cursor_col = 0;
}

TERMDUMP_API void screen_putc(Screen *s, char c) {
    if (c == '\n') {
        screen_newline(s);
        return;
    }
    if (s->cursor_col >= MAX_COLS - 1) return;
    s->cursor->data[s->cursor_col++] = c;
}

// Forward declaration
TERMDUMP_API void handle_escape_sequence_mem(Screen *s, const unsigned char **data, size_t *len, char first_char);

TERMDUMP_API void handle_escape_sequence(Screen *s, FILE *in, char first_char) {
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

/* Process escape sequence from memory buffer */
TERMDUMP_API void handle_escape_sequence_mem(Screen *s, const unsigned char **data, size_t *len, char first_char) {
    if (first_char == '[') {
        char buf[8] = {0};
        int i = 0;
        
        while (i < 7 && *len > 0) {
            char c = **data;
            (*data)++;
            (*len)--;
            
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

TERMDUMP_API void process_input(Screen *screen, FILE *in) {
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

/* Process input from memory buffer */
TERMDUMP_API void process_input_mem(Screen *screen, const unsigned char *data, size_t len) {
    while (len > 0) {
        unsigned char c = *data++;
        len--;
        
        if (c == ESC && len > 0) {
            unsigned char next = *data++;
            len--;
            handle_escape_sequence_mem(screen, &data, &len, next);
        } else {
            screen_putc(screen, c);
        }
    }
}

/* Write output to memory buffer */
TERMDUMP_API size_t get_output_size(Screen *s) {
    size_t size = 0;
    for (Line *line = s->head; line != NULL; line = line->next) {
        size += strlen(line->data) + 1; // +1 for newline
    }
    return size;
}

TERMDUMP_API size_t dump_output_mem(Screen *s, char *buffer, size_t buffer_size) {
    size_t pos = 0;
    for (Line *line = s->head; line != NULL; line = line->next) {
        size_t len = strlen(line->data);
        if (pos + len + 1 > buffer_size) {
            break; // Buffer too small
        }
        memcpy(buffer + pos, line->data, len);
        pos += len;
        buffer[pos++] = '\n';
    }
    return pos;
}

TERMDUMP_API void dump_output(Screen *s, FILE *out) {
    for (Line *line = s->head; line != NULL; line = line->next)
        fprintf(out, "%s\n", line->data);
}

/* Process a memory buffer and return a new processed buffer */
TERMDUMP_API char* process_buffer(const unsigned char *input, size_t input_len, size_t *output_len) {
    Screen screen;
    screen_init(&screen);
    
    process_input_mem(&screen, input, input_len);
    
    size_t size = get_output_size(&screen);
    char *output = malloc(size);
    if (!output) {
        *output_len = 0;
        screen_clear(&screen);
        return NULL;
    }
    
    *output_len = dump_output_mem(&screen, output, size);
    screen_clear(&screen);
    return output;
}

#ifdef TERMDUMP_MAIN
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
#endif
