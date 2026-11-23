/*
 * COMEL — teclado USB (relatório HID boot) → matriz 8×8 do C64. GPL-3.0.
 *
 * O mapeamento é "simbólico": o caractere impresso na tecla do teclado USB
 * (ABNT2 ou US) vira a tecla do C64 que produz o mesmo caractere, ligando ou
 * desligando o SHIFT do C64 quando preciso. Ex.: no ABNT2, Shift+' dá aspas
 * duplas, que no C64 é Shift+2.
 *
 * Teclas especiais:
 *   Esc = RUN/STOP          Tab = CTRL            Ctrl / Win = C=
 *   Backspace / Delete = DEL   Insert = INST       Home = CLR/HOME   End = CLR
 *   setas = cursores        F1–F8 = F1–F8 do C64 (F2 = Shift+F1, ...)
 *   Page Up = RESTORE       F9 = LOAD"$",8 + LIST  Shift+F9 = LOAD"*",8,1 + RUN
 *   F10 = troca o joystick de porta    F12 = reset
 *   Num Lock = liga/desliga o joystick no teclado numérico (8 4 6 2, 0/5 = tiro)
 */
#include <string.h>
#include "keyboard.h"
#include "comel_board.h"

#define K(c, r) (uint8_t)(((c) << 3) | (r))
#define NOKEY   0xFF

enum { SH_PASS = 0, SH_ON = 1, SH_OFF = 2 };
typedef struct { uint8_t key, shift; } c64key_t;

/* Matriz do C64 (coluna = PA, linha = PB) */
enum {
    C_DEL = K(0,0), C_RET = K(0,1), C_RIGHT = K(0,2), C_F7 = K(0,3), C_F1 = K(0,4), C_F3 = K(0,5), C_F5 = K(0,6), C_DOWN = K(0,7),
    C_3 = K(1,0), C_W = K(1,1), C_A = K(1,2), C_4 = K(1,3), C_Z = K(1,4), C_S = K(1,5), C_E = K(1,6), C_LSHIFT = K(1,7),
    C_5 = K(2,0), C_R = K(2,1), C_D = K(2,2), C_6 = K(2,3), C_C = K(2,4), C_F = K(2,5), C_T = K(2,6), C_X = K(2,7),
    C_7 = K(3,0), C_Y = K(3,1), C_G = K(3,2), C_8 = K(3,3), C_B = K(3,4), C_H = K(3,5), C_U = K(3,6), C_V = K(3,7),
    C_9 = K(4,0), C_I = K(4,1), C_J = K(4,2), C_0 = K(4,3), C_M = K(4,4), C_K = K(4,5), C_O = K(4,6), C_N = K(4,7),
    C_PLUS = K(5,0), C_P = K(5,1), C_L = K(5,2), C_MINUS = K(5,3), C_DOT = K(5,4), C_COLON = K(5,5), C_AT = K(5,6), C_COMMA = K(5,7),
    C_POUND = K(6,0), C_STAR = K(6,1), C_SEMI = K(6,2), C_HOME = K(6,3), C_RSHIFT = K(6,4), C_EQUAL = K(6,5), C_UPARROW = K(6,6), C_SLASH = K(6,7),
    C_1 = K(7,0), C_LARROW = K(7,1), C_CTRL = K(7,2), C_2 = K(7,3), C_SPACE = K(7,4), C_CBM = K(7,5), C_Q = K(7,6), C_STOP = K(7,7),
};

static const uint8_t letter_key[26] = {
    C_A, C_B, C_C, C_D, C_E, C_F, C_G, C_H, C_I, C_J, C_K, C_L, C_M,
    C_N, C_O, C_P, C_Q, C_R, C_S, C_T, C_U, C_V, C_W, C_X, C_Y, C_Z,
};
static const uint8_t digit_key[10] = { C_0, C_1, C_2, C_3, C_4, C_5, C_6, C_7, C_8, C_9 };

/* Caractere ASCII → tecla do C64 */
static c64key_t c64_for_char(char ch) {
    c64key_t k = { NOKEY, SH_PASS };
    if (ch >= 'a' && ch <= 'z') { k.key = letter_key[ch - 'a']; k.shift = SH_OFF; return k; }
    if (ch >= 'A' && ch <= 'Z') { k.key = letter_key[ch - 'A']; k.shift = SH_ON; return k; }
    if (ch >= '0' && ch <= '9') { k.key = digit_key[ch - '0']; k.shift = SH_OFF; return k; }
    static const char shifted_digits[] = "!\"#$%&'()";   /* Shift+1 … Shift+9 no C64 */
    const char *p = strchr(shifted_digits, ch);
    if (ch && p) { k.key = digit_key[1 + (p - shifted_digits)]; k.shift = SH_ON; return k; }
    switch (ch) {
    case ' ':  k.key = C_SPACE; break;
    case '\r': case '\n': k.key = C_RET; break;
    case '+':  k.key = C_PLUS;  k.shift = SH_OFF; break;
    case '-':  k.key = C_MINUS; k.shift = SH_OFF; break;
    case '.':  k.key = C_DOT;   k.shift = SH_OFF; break;
    case ',':  k.key = C_COMMA; k.shift = SH_OFF; break;
    case ':':  k.key = C_COLON; k.shift = SH_OFF; break;
    case '@':  k.key = C_AT;    k.shift = SH_OFF; break;
    case '*':  k.key = C_STAR;  k.shift = SH_OFF; break;
    case ';':  k.key = C_SEMI;  k.shift = SH_OFF; break;
    case '=':  k.key = C_EQUAL; k.shift = SH_OFF; break;
    case '/':  k.key = C_SLASH; k.shift = SH_OFF; break;
    case '<':  k.key = C_COMMA; k.shift = SH_ON;  break;
    case '>':  k.key = C_DOT;   k.shift = SH_ON;  break;
    case '?':  k.key = C_SLASH; k.shift = SH_ON;  break;
    case '[':  k.key = C_COLON; k.shift = SH_ON;  break;
    case ']':  k.key = C_SEMI;  k.shift = SH_ON;  break;
    case '^':  k.key = C_UPARROW; k.shift = SH_OFF; break;
    case '~':  k.key = C_UPARROW; k.shift = SH_ON;  break;   /* π */
    case '_':  case '`': k.key = C_LARROW; k.shift = SH_OFF; break;
    case '\\': case '|': k.key = C_POUND;  k.shift = SH_OFF; break;
    default: break;
    }
    return k;
}

/* Uso HID → caractere, conforme o layout */
static char layout_char(uint8_t u, bool shift, bool altgr) {
    if (u >= 0x04 && u <= 0x1D) {
#if KBD_LAYOUT == KBD_LAYOUT_ABNT2
        if (altgr && u == 0x14) return '/';           /* AltGr+Q */
        if (altgr && u == 0x1A) return '?';           /* AltGr+W */
#endif
        return (char)((shift ? 'A' : 'a') + (u - 0x04));
    }
    if (u >= 0x1E && u <= 0x27) {
        static const char plain[] = "1234567890";
#if KBD_LAYOUT == KBD_LAYOUT_ABNT2
        static const char shifted[] = "!@#$%\0&*()";  /* Shift+6 é o trema (tecla morta) */
#else
        static const char shifted[] = "!@#$%^&*()";
#endif
        return shift ? shifted[u - 0x1E] : plain[u - 0x1E];
    }
    if (u >= 0x59 && u <= 0x62) return "1234567890"[u - 0x59];   /* teclado numérico */
    switch (u) {
    case 0x54: return '/';
    case 0x55: return '*';
    case 0x56: return '-';
    case 0x57: return '+';
    case 0x63: return '.';
    case 0x85: return ',';
    default: break;
    }
#if KBD_LAYOUT == KBD_LAYOUT_ABNT2
    switch (u) {
    case 0x2D: return shift ? '_' : '-';
    case 0x2E: return shift ? '+' : '=';
    case 0x2F: return shift ? '`' : '\'';             /* acento agudo / crase */
    case 0x30: return shift ? '{' : '[';
    case 0x31: case 0x32: return shift ? '}' : ']';
    case 0x34: return shift ? '^' : '~';
    case 0x35: return shift ? '"' : '\'';
    case 0x36: return shift ? '<' : ',';
    case 0x37: return shift ? '>' : '.';
    case 0x38: return shift ? ':' : ';';
    case 0x87: return shift ? '?' : '/';
    case 0x64: return shift ? '|' : '\\';
    default: return 0;                                 /* Ç e afins não existem no C64 */
    }
#else
    switch (u) {
    case 0x2D: return shift ? '_' : '-';
    case 0x2E: return shift ? '+' : '=';
    case 0x2F: return shift ? '{' : '[';
    case 0x30: return shift ? '}' : ']';
    case 0x31: case 0x32: case 0x64: return shift ? '|' : '\\';
    case 0x33: return shift ? ':' : ';';
    case 0x34: return shift ? '"' : '\'';
    case 0x35: return shift ? '~' : '`';
    case 0x36: return shift ? '<' : ',';
    case 0x37: return shift ? '>' : '.';
    case 0x38: return shift ? '?' : '/';
    default: return 0;
    }
#endif
}

/* Teclas que não são caracteres */
static c64key_t special_key(uint8_t u) {
    c64key_t k = { NOKEY, SH_PASS };
    switch (u) {
    case 0x28: case 0x58: k.key = C_RET; break;
    case 0x29: k.key = C_STOP; break;
    case 0x2A: k.key = C_DEL; break;
    case 0x2B: k.key = C_CTRL; break;
    case 0x2C: k.key = C_SPACE; break;
    case 0x3A: k.key = C_F1; k.shift = SH_OFF; break;
    case 0x3B: k.key = C_F1; k.shift = SH_ON;  break;
    case 0x3C: k.key = C_F3; k.shift = SH_OFF; break;
    case 0x3D: k.key = C_F3; k.shift = SH_ON;  break;
    case 0x3E: k.key = C_F5; k.shift = SH_OFF; break;
    case 0x3F: k.key = C_F5; k.shift = SH_ON;  break;
    case 0x40: k.key = C_F7; k.shift = SH_OFF; break;
    case 0x41: k.key = C_F7; k.shift = SH_ON;  break;
    case 0x49: k.key = C_DEL; k.shift = SH_ON; break;    /* Insert = INST */
    case 0x4A: k.key = C_HOME; break;
    case 0x4C: k.key = C_DEL; k.shift = SH_OFF; break;
    case 0x4D: k.key = C_HOME; k.shift = SH_ON; break;   /* End = CLR */
    case 0x4F: k.key = C_RIGHT; break;
    case 0x50: k.key = C_RIGHT; k.shift = SH_ON; break;
    case 0x51: k.key = C_DOWN; break;
    case 0x52: k.key = C_DOWN; k.shift = SH_ON; break;
    default: break;
    }
    return k;
}

/* ------------------------------------------------------------------------- */

#define SLOTS 8
static uint8_t reports[SLOTS][8];
static bool slot_used[SLOTS];
static uint8_t prev_keys[SLOTS * 6];
static int prev_n;
static bool keypad_joy;

volatile uint8_t kbd_matrix[8];
volatile uint8_t kbd_inject[8];
volatile uint8_t kbd_joystick;
static volatile uint8_t actions;

uint8_t kbd_take_actions(void) {
    uint8_t a = actions;
    actions = 0;
    return a;
}

static bool was_down(uint8_t u) {
    for (int i = 0; i < prev_n; i++) if (prev_keys[i] == u) return true;
    return false;
}

static void press(uint8_t m[8], uint8_t key) {
    if (key != NOKEY) m[key >> 3] |= (uint8_t)(1u << (key & 7));
}

static void recompute(void) {
    uint8_t m[8] = {0}, joy = 0, mods = 0, keys[SLOTS * 6];
    int n = 0;
    for (int s = 0; s < SLOTS; s++) {
        if (!slot_used[s]) continue;
        mods |= reports[s][0];
        for (int i = 2; i < 8; i++) {
            uint8_t u = reports[s][i];
            if (u > 3 && n < (int)sizeof keys) keys[n++] = u;   /* 1–3 = erro/rollover */
        }
    }
    bool shift = mods & 0x22, altgr = mods & 0x40;
    int forced = SH_PASS;

    for (int i = 0; i < n; i++) {
        uint8_t u = keys[i];
        bool fresh = !was_down(u);
        switch (u) {                                   /* ações */
        case 0x42: if (fresh) actions |= shift ? KBD_ACT_LOADRUN : KBD_ACT_LOADDIR; continue;
        case 0x43: if (fresh) actions |= KBD_ACT_SWAPJOY; continue;
        case 0x45: if (fresh) actions |= KBD_ACT_RESET; continue;
        case 0x4B: if (fresh) actions |= KBD_ACT_RESTORE; continue;
        case 0x53: if (fresh) keypad_joy = !keypad_joy; continue;
        default: break;
        }
        if (keypad_joy && ((u >= 0x59 && u <= 0x62) || u == 0x58)) {   /* joystick no numérico */
            switch (u) {
            case 0x60: joy |= JOY_MASK_UP; break;                        /* 8 */
            case 0x5A: joy |= JOY_MASK_DOWN; break;                      /* 2 */
            case 0x5C: joy |= JOY_MASK_LEFT; break;                      /* 4 */
            case 0x5E: joy |= JOY_MASK_RIGHT; break;                     /* 6 */
            case 0x5F: joy |= JOY_MASK_UP | JOY_MASK_LEFT; break;        /* 7 */
            case 0x61: joy |= JOY_MASK_UP | JOY_MASK_RIGHT; break;       /* 9 */
            case 0x59: joy |= JOY_MASK_DOWN | JOY_MASK_LEFT; break;      /* 1 */
            case 0x5B: joy |= JOY_MASK_DOWN | JOY_MASK_RIGHT; break;     /* 3 */
            default: joy |= JOY_MASK_FIRE; break;                        /* 0, 5, Enter */
            }
            continue;
        }
        c64key_t k = special_key(u);
        if (k.key == NOKEY) {
            char ch = layout_char(u, shift, altgr);
            if (ch) k = c64_for_char(ch);
        }
        if (k.key == NOKEY) continue;
        press(m, k.key);
        if (k.shift != SH_PASS) forced = k.shift;
    }

    if (mods & 0x99) press(m, C_CBM);                  /* Ctrl e Win/GUI = C= */
    if (forced == SH_ON) press(m, C_LSHIFT);
    else if (forced == SH_PASS) {
        if (mods & 0x02) press(m, C_LSHIFT);
        if (mods & 0x20) press(m, C_RSHIFT);
    }

    for (int c = 0; c < 8; c++) kbd_matrix[c] = m[c];
    kbd_joystick = joy;
    memcpy(prev_keys, keys, (size_t)n);
    prev_n = n;
}

void kbd_report(uint8_t slot, const uint8_t *report) {
    if (slot >= SLOTS) return;
    memcpy(reports[slot], report, 8);
    slot_used[slot] = true;
    recompute();
}

void kbd_release(uint8_t slot) {
    if (slot >= SLOTS) return;
    slot_used[slot] = false;
    memset(reports[slot], 0, 8);
    recompute();
}

/* ------------------------------------------------------------------------- */
/* Digitação automática: cada caractere fica 2 quadros pressionado e 2 solto. */

static char type_buf[96];
static int type_pos = -1, type_phase;

void kbd_type(const char *text) {
    strncpy(type_buf, text, sizeof type_buf - 1);
    type_buf[sizeof type_buf - 1] = 0;
    type_pos = 0;
    type_phase = 0;
}

void kbd_type_tick(void) {
    if (type_pos < 0) return;
    uint8_t m[8] = {0};
    if (type_phase < 2) {
        char ch = type_buf[type_pos];
        if (!ch) { type_pos = -1; for (int c = 0; c < 8; c++) kbd_inject[c] = 0; return; }
        if (ch >= 'A' && ch <= 'Z') ch = (char)(ch - 'A' + 'a');   /* texto em maiúsculas = letras normais do C64 */
        c64key_t k = c64_for_char(ch);
        press(m, k.key);
        if (k.shift == SH_ON) press(m, C_LSHIFT);
    }
    for (int c = 0; c < 8; c++) kbd_inject[c] = m[c];
    if (++type_phase == 4) { type_phase = 0; type_pos++; }
}
