#!/usr/bin/env python3
"""
packflow easter egg.
"""

import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# -- config ----------------------------------------------------------

LEFT_PAD = 1  # 0 = auto-center, or set explicit column
TOP_PAD = 1  # extra blank lines above
MARGIN = 1  # gap between text and box

KERNING = 1
FONT_SIZE = 400  # large render, then downsample
FONT_STROKE_WIDTH = 2
TEXT_THRESHOLD = 45  # pixel brightness threshold for text binarization
LETTER_RESAMPLING = Image.Resampling.LANCZOS


TEXT_HEIGHT_CHARS = 8  # how tall "pack"/"flow" are in terminal rows
# Originally a constant, but each character needed tweaking to look better with
# other rasterization args.
CHAR_ASPECT = lambda ch: {  # noqa: E731
    "p": 0.48,
    "c": 0.4,
    "k": 0.475,
    "f": 0.4,
}.get(ch, 0.435)

BOX_ASPECT = 0.4

BOX_CHARS = 10  # box sprite width in chars

ANIM_HEIGHT = 6  # lines for animation area
TERM_WIDTH = 74

FPS = 30
ROLL_DURATION = 1.8
FADE_FRAMES = 10

TOTAL_ANGLE = -360  # negative = rolls right


SHADES = "⣿░▒▓█"

ARROW_START_COL = 4
ARROW_COLOR_LEFT = "\033[37m"  # white/gray left half
ARROW_COLOR_RIGHT = "\033[36m"  # cyan right half
BOX_RIPPLE_COLOR = "\033[38;5;180m"  # warm tan/cardboard ripple


def draw_shaft(buf, col_buf, y, x_from, x_to, color):
    """Draw ▄ shaft from x_from to x_to on row y."""
    for x in range(x_from, x_to):
        if 0 <= x < TERM_WIDTH:
            buf[y][x] = "▄"
            col_buf[y][x] = color


def draw_arrowhead(buf, col_buf, tip_x, y, color):
    """Draw arrowhead tip at tip_x on shaft row y.
    row y-1:  ▄          (at tip_x-3)
    row y:    █████▙▄    (█×3 at tip_x-3..-1; ▙ at tip_x-2; ▄ at tip_x)
    row y+1:  █▀▘        (at tip_x-3, tip_x-2, tip_x-1)
    """
    hx = tip_x - 3
    for dx, ch in [(0, "█"), (1, "█"), (2, "▙"), (3, "▄")]:
        if 0 <= hx + dx < TERM_WIDTH:
            buf[y][hx + dx] = ch
            col_buf[y][hx + dx] = color
    if y - 1 >= 0:
        if 0 <= hx < TERM_WIDTH:
            buf[y - 1][hx] = "▄"
            col_buf[y - 1][hx] = color
    if y + 1 < ANIM_HEIGHT:
        for dx, ch in [(0, "█"), (1, "▀"), (2, "▘")]:
            if 0 <= hx + dx < TERM_WIDTH:
                buf[y + 1][hx + dx] = ch
                col_buf[y + 1][hx + dx] = color


# -- quadrant block lookup: (tl, tr, bl, br) → char -----------------

QUAD = {
    (0, 0, 0, 0): " ",
    (1, 0, 0, 0): "▘",
    (0, 1, 0, 0): "▝",
    (0, 0, 1, 0): "▖",
    (0, 0, 0, 1): "▗",
    (1, 1, 0, 0): "▀",
    (0, 0, 1, 1): "▄",
    (1, 0, 1, 0): "▌",
    (0, 1, 0, 1): "▐",
    (1, 0, 0, 1): "▚",
    (0, 1, 1, 0): "▞",
    (1, 1, 1, 0): "▛",
    (1, 1, 0, 1): "▜",
    (1, 0, 1, 1): "▙",
    (0, 1, 1, 1): "▟",
    (1, 1, 1, 1): "█",
}


# -- text rendering with quadrant blocks -----------------------------


def _render_letter(ch: str, font, target_h: int) -> list[str]:
    """Render one letter → list of strings (quadrant blocks)."""
    bbox = font.getbbox(ch)
    tw = bbox[2] - bbox[0]
    ascent, descent = font.getmetrics()
    full_h = ascent + descent

    img = Image.new("L", (tw + 20, full_h + 20), 0)
    ImageDraw.Draw(img).text(
        (-bbox[0] + 10, 10), ch, fill=255, font=font, stroke_width=FONT_STROKE_WIDTH
    )

    px_h = target_h * 2
    px_w = int(tw / full_h * px_h / CHAR_ASPECT(ch))
    px_w += px_w % 2
    if px_w < 2:
        px_w = 2

    small = img.resize((px_w, px_h), LETTER_RESAMPLING)
    bits = (np.array(small) > TEXT_THRESHOLD).astype(int)

    lines = []
    for y in range(0, px_h, 2):
        row = []
        for x in range(0, px_w, 2):
            tl = bits[y, x]
            tr = bits[y, x + 1] if x + 1 < px_w else 0
            bl = bits[y + 1, x] if y + 1 < px_h else 0
            br = bits[y + 1, x + 1] if y + 1 < px_h and x + 1 < px_w else 0
            row.append(QUAD[(tl, tr, bl, br)])
        lines.append("".join(row))
    return lines


def _trim_letter(lines: list[str]) -> list[str]:
    """Strip empty leading/trailing columns from a rendered letter."""
    if not lines:
        return lines
    # trailing
    max_col = max((len(r.rstrip()) for r in lines), default=0)
    lines = [r[:max_col] for r in lines]
    # leading
    min_lead = min((len(r) - len(r.lstrip()) for r in lines if r.strip()), default=0)
    return [r[min_lead:] for r in lines]


def render_text(text: str, target_h: int, font_path: str) -> list[str]:
    """Render text → list of strings. Each letter rendered individually
    then stitched together for clean strokes."""
    font = ImageFont.truetype(font_path, FONT_SIZE)
    letters = [_trim_letter(_render_letter(ch, font, target_h)) for ch in text]
    h = target_h
    result = []
    for y in range(h):
        row = ""
        for i, let in enumerate(letters):
            if i > 0:
                row += " " * KERNING
            row += let[y] if y < len(let) else ""
        result.append(row)
    return result


# -- box sprite rendering --------------------------------------------


def render_box(path: str, width: int) -> list[str]:
    """Render box image as ASCII using SHADES ramp."""
    img = Image.open(path).convert("RGBA")
    char_h = max(1, int(img.size[1] / img.size[0] * width * BOX_ASPECT))
    small = img.resize((width, char_h), Image.Resampling.LANCZOS)
    px = np.array(small)
    alpha, gray = (
        px[:, :, 3],
        (0.299 * px[:, :, 0] + 0.587 * px[:, :, 1] + 0.114 * px[:, :, 2]),
    )
    mask = alpha >= 128
    lo = float(gray[mask].min()) if mask.any() else 0
    hi = float(gray[mask].max()) if mask.any() else 255
    rng = max(hi - lo, 1)
    n = len(SHADES)
    lines = []
    for y in range(char_h):
        row = []
        for x in range(width):
            if alpha[y, x] < 128:
                row.append(" ")
            else:
                b = (gray[y, x] - lo) / rng
                row.append(SHADES[min(n - 1, max(0, int(b * n)))])
        lines.append("".join(row))
    return lines


# -- box rotation for roll animation ---------------------------------


def render_box_rotated(img_rgba, angle_deg: float, width: int) -> list[str]:
    """Rotate box image, convert to ASCII."""
    rotated = img_rgba.rotate(
        -angle_deg,
        expand=True,
        fillcolor=(0, 0, 0, 0),
        resample=Image.Resampling.BICUBIC,
    )
    rw, rh = rotated.size
    ow = img_rgba.size[0]
    scale = rw / ow
    char_w = max(1, int(width * scale))
    char_h = max(1, int(rh / ow * width * BOX_ASPECT))
    small = rotated.resize((char_w, char_h), Image.Resampling.LANCZOS)
    px = np.array(small)
    alpha, gray = (
        px[:, :, 3],
        (0.299 * px[:, :, 0] + 0.587 * px[:, :, 1] + 0.114 * px[:, :, 2]),
    )
    mask = alpha >= 128
    lo = float(gray[mask].min()) if mask.any() else 0
    hi = float(gray[mask].max()) if mask.any() else 255
    rng = max(hi - lo, 1)
    n = len(SHADES)
    lines = []
    for y in range(char_h):
        row = []
        for x in range(char_w):
            if alpha[y, x] < 128:
                row.append(" ")
            else:
                b = (gray[y, x] - lo) / rng
                row.append(SHADES[min(n - 1, max(0, int(b * n)))])
        lines.append("".join(row))
    return lines


# -- compositing -----------------------------------------------------


def blank():
    buf = [[" "] * TERM_WIDTH for _ in range(ANIM_HEIGHT)]
    col = [[None] * TERM_WIDTH for _ in range(ANIM_HEIGHT)]
    return buf, col


def blit(buf, sprite, x, y, col_buf=None, color=None):
    for ry, line in enumerate(sprite):
        sy = y + ry
        if sy < 0 or sy >= ANIM_HEIGHT:
            continue
        for rx, ch in enumerate(line):
            sx = x + rx
            if sx < 0 or sx >= TERM_WIDTH or ch == " ":
                continue
            buf[sy][sx] = ch
            if col_buf is not None and color is not None:
                col_buf[sy][sx] = color


def show(buf, col=None):
    sys.stdout.write(f"\033[{ANIM_HEIGHT}A")
    for y, row in enumerate(buf):
        line = ""
        cur_color = None
        for x, ch in enumerate(row):
            c = col[y][x] if col else None
            if c != cur_color:
                if c is None:
                    line += "\033[0m"
                else:
                    line += c
                cur_color = c
            line += ch
        if cur_color is not None:
            line += "\033[0m"
        sys.stdout.write(line + "\n")
    sys.stdout.flush()


def ease_out(t):
    return 1 - (1 - t) ** 3


# -- main ------------------------------------------------------------


def roll_in(box_path: str, font_path: str, term_width: int = 80):
    global TERM_WIDTH, ANIM_HEIGHT
    TERM_WIDTH = term_width

    # pre-render everything
    box_img = Image.open(box_path).convert("RGBA")
    box_final = render_box(box_path, BOX_CHARS)
    box_h = len(box_final)

    pack_lines = render_text("pack", TEXT_HEIGHT_CHARS, font_path)
    flow_lines = render_text("flow", TEXT_HEIGHT_CHARS, font_path)
    pack_w = len(pack_lines[0]) if pack_lines else 0
    flow_w = len(flow_lines[0]) if flow_lines else 0
    text_h = len(pack_lines)

    # layout: [pack][margin][box][margin][flow] centred
    total_w = pack_w + MARGIN + BOX_CHARS + MARGIN + flow_w
    left_edge = LEFT_PAD if LEFT_PAD else (TERM_WIDTH - total_w) // 2
    pack_x = left_edge
    box_x = left_edge + pack_w + MARGIN
    flow_x = box_x + BOX_CHARS + MARGIN

    ANIM_HEIGHT = max(ANIM_HEIGHT, text_h + TOP_PAD, box_h + TOP_PAD)
    box_y = ANIM_HEIGHT - box_h - 2
    text_y = ANIM_HEIGHT - text_h

    # reserve lines + hide cursor
    sys.stdout.write("\n" * ANIM_HEIGHT)
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    roll_dist = -TOTAL_ANGLE / 90 * BOX_CHARS
    start_x = box_x - int(roll_dist)
    roll_frames = int(ROLL_DURATION * FPS)

    try:
        shaft_row = ANIM_HEIGHT - 2
        arrow_tip = TERM_WIDTH - 3
        shaft_speed = 3  # columns per frame

        # -- phase 1: box rolls in -------------------------------
        for f in range(roll_frames + 1):
            t = f / roll_frames
            p = ease_out(t)
            angle = (1 - p) * TOTAL_ANGLE
            cur_x = start_x + int(p * roll_dist)

            sprite = render_box_rotated(box_img, angle, BOX_CHARS)
            sp_h = len(sprite)
            sp_w = len(sprite[0]) if sprite else 0
            nudge = (sp_w - BOX_CHARS) // 2

            buf, col = blank()
            blit(buf, sprite, cur_x - nudge, ANIM_HEIGHT - sp_h - 2)
            show(buf, col)
            time.sleep(1.0 / FPS)

        # -- phase 2: text fades in ------------------------------
        for f in range(1, FADE_FRAMES + 1):
            frac = f / FADE_FRAMES
            buf, col = blank()
            blit(buf, box_final, box_x, box_y)
            for lines, x, _ in [
                (pack_lines, pack_x, pack_w),
                (flow_lines, flow_x, flow_w),
            ]:
                for ry, line in enumerate(lines):
                    for rx, ch in enumerate(line):
                        if ch == " ":
                            continue
                        weight = 0
                        if ch == "█":
                            weight = 0.0
                        elif ch in "▀▄▌▐":
                            weight = 0.3
                        elif ch in "▛▜▙▟":
                            weight = 0.5
                        elif ch in "▘▝▖▗▚▞":
                            weight = 0.7
                        else:
                            weight = 0.9
                        if frac >= weight:
                            sx = x + rx
                            sy = text_y + ry
                            if 0 <= sy < ANIM_HEIGHT and 0 <= sx < TERM_WIDTH:
                                buf[sy][sx] = ch
            show(buf, col)
            time.sleep(0.06)

        # helper to redraw settled text+box into a buf
        def blit_settled(buf, col, ripple_radius=-1):
            blit(buf, box_final, box_x, box_y)
            # radial ripple from center-bottom of box, cardboard color
            if ripple_radius >= 0:
                cx = BOX_CHARS // 2
                cy = box_h - 1
                for ry in range(box_h):
                    sy = box_y + ry
                    for rx in range(BOX_CHARS):
                        dist = ((rx - cx) ** 2 + (ry - cy) ** 2) ** 0.5
                        if dist <= ripple_radius:
                            sx = box_x + rx
                            if 0 <= sy < ANIM_HEIGHT and 0 <= sx < TERM_WIDTH:
                                col[sy][sx] = BOX_RIPPLE_COLOR
            # text (fully revealed)
            for lines, x, _ in [
                (pack_lines, pack_x, pack_w),
                (flow_lines, flow_x, flow_w),
            ]:
                for ry, line in enumerate(lines):
                    for rx, ch in enumerate(line):
                        if ch != " ":
                            sx = x + rx
                            sy = text_y + ry
                            if 0 <= sy < ANIM_HEIGHT and 0 <= sx < TERM_WIDTH:
                                buf[sy][sx] = ch

        # -- phase 3: arrow draws continuously; ▟ printed at box center -
        # shaft passes under the box (shaft_row is below box sprite rows)
        nub_x = box_x + BOX_CHARS // 2 - 1  # center of box at shaft level

        x_cur = ARROW_START_COL
        while x_cur < nub_x:
            x_cur = min(x_cur + shaft_speed, nub_x)
            buf, col = blank()
            draw_shaft(buf, col, shaft_row, ARROW_START_COL, x_cur, ARROW_COLOR_LEFT)
            blit_settled(buf, col)
            show(buf, col)
            time.sleep(1.0 / FPS)

        # ▟ drawn at box center — triggers ripple
        buf, col = blank()
        draw_shaft(buf, col, shaft_row, ARROW_START_COL, nub_x, ARROW_COLOR_LEFT)
        buf[shaft_row][nub_x] = "▟"
        col[shaft_row][nub_x] = ARROW_COLOR_LEFT
        blit_settled(buf, col)
        show(buf, col)
        time.sleep(1.0 / FPS)

        # -- phase 4: ripple through box (radial from center-bottom) -
        max_radius = int(((BOX_CHARS // 2) ** 2 + (box_h - 1) ** 2) ** 0.5) + 1
        for r in range(max_radius + 1):
            buf, col = blank()
            draw_shaft(buf, col, shaft_row, ARROW_START_COL, nub_x, ARROW_COLOR_LEFT)
            buf[shaft_row][nub_x] = "▟"
            col[shaft_row][nub_x] = ARROW_COLOR_LEFT
            blit_settled(buf, col, ripple_radius=r)
            show(buf, col)
            time.sleep(0.04)

        # -- phase 5: ▙ immediately after ▟, cyan builds rightward ---
        # continuous shaft: white left half, nub ▟▙ at center, cyan right half
        def draw_full_shaft(buf, col, x_cur_cyan):
            draw_shaft(buf, col, shaft_row, ARROW_START_COL, nub_x, ARROW_COLOR_LEFT)
            buf[shaft_row][nub_x] = "▟"
            col[shaft_row][nub_x] = ARROW_COLOR_LEFT
            if 0 <= nub_x + 1 < TERM_WIDTH:
                buf[shaft_row][nub_x + 1] = "▙"
                col[shaft_row][nub_x + 1] = ARROW_COLOR_RIGHT
            draw_shaft(buf, col, shaft_row, nub_x + 2, x_cur_cyan, ARROW_COLOR_RIGHT)

        x_cur = nub_x + 2
        while x_cur < arrow_tip:
            x_cur = min(x_cur + shaft_speed, arrow_tip)
            buf, col = blank()
            draw_full_shaft(buf, col, x_cur)
            blit_settled(buf, col, ripple_radius=max_radius)
            show(buf, col)
            time.sleep(1.0 / FPS)

        # draw arrowhead
        buf, col = blank()
        draw_full_shaft(buf, col, arrow_tip)
        blit_settled(buf, col, ripple_radius=max_radius)
        draw_arrowhead(buf, col, arrow_tip, shaft_row, ARROW_COLOR_RIGHT)
        show(buf, col)

        time.sleep(1.2)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("box", help="path to packflow-logo-32px.png")
    ap.add_argument("font", help="path to JosefinSans-VariableFont_wght.ttf")
    ap.add_argument("-W", "--width", type=int, default=TERM_WIDTH)
    args = ap.parse_args()
    roll_in(args.box, args.font, args.width)
