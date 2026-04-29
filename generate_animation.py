"""
Generate a looping GIF of a cute star avatar with a smooth eye movement
animation as if it is reading a book (gentle left-to-right scan).
"""

import math
from PIL import Image, ImageDraw

# ── canvas & palette ──────────────────────────────────────────────────────────
SIZE        = 240          # square canvas (px)
BG_COLOR    = (255, 255, 255, 0)   # transparent background
STAR_FILL   = (255, 215, 0)        # gold star body
STAR_OUTLINE= (230, 180, 0)        # slightly darker outline
CHEEK_COLOR = (255, 160, 120, 120) # soft blush (semi-transparent)
EYE_WHITE   = (255, 255, 255)
EYE_OUTLINE = (50, 30, 10)
IRIS_COLOR  = (60, 100, 200)
PUPIL_COLOR = (20, 20, 20)
SHINE_COLOR = (255, 255, 255)
MOUTH_COLOR = (200, 80, 80)

CENTER   = SIZE // 2           # 120
STAR_R   = 88                  # outer radius of star
STAR_r   = 40                  # inner radius of star
STAR_PTS = 5

# ── star polygon ──────────────────────────────────────────────────────────────

def star_polygon(cx, cy, r_outer, r_inner, n=5):
    """Return a list of (x, y) vertices for a regular n-pointed star."""
    pts = []
    for i in range(2 * n):
        angle = math.pi / n * i - math.pi / 2   # start pointing up
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts

STAR_VERTS = star_polygon(CENTER, CENTER, STAR_R, STAR_r)

# ── eye geometry (reference, centred on face) ─────────────────────────────────
# The eye socket is an ellipse; the iris/pupil slide horizontally inside it.
EYE_CX   = CENTER          # horizontal centre of the eye socket
EYE_CY   = CENTER - 8      # slightly above the star centre
EYE_W    = 34              # full width of white area
EYE_H    = 22              # full height of white area
IRIS_R   = 8               # iris circle radius
PUPIL_R  = 4               # pupil circle radius
SHINE_R  = 2               # highlight dot radius

# How far the iris travels left / right inside the socket
EYE_TRAVEL = 7

# ── mouth ─────────────────────────────────────────────────────────────────────
MOUTH_CX  = CENTER
MOUTH_CY  = CENTER + 22
MOUTH_W   = 28
MOUTH_H   = 10

# ── cheek blush ───────────────────────────────────────────────────────────────
BLUSH_OFFSET = 28
BLUSH_RX     = 14
BLUSH_RY     = 8


def draw_frame(iris_x_offset: float) -> Image.Image:
    """
    Render one frame of the avatar.
    iris_x_offset: horizontal shift of the iris inside the eye socket (-1 … +1
                   maps to full left … full right travel).
    """
    img  = Image.new("RGBA", (SIZE, SIZE), BG_COLOR)
    draw = ImageDraw.Draw(img, "RGBA")

    # 1. Star body
    draw.polygon(STAR_VERTS, fill=STAR_FILL, outline=STAR_OUTLINE)

    # 2. Cheek blushes
    lx = CENTER - BLUSH_OFFSET
    rx = CENTER + BLUSH_OFFSET
    cy = CENTER + 14
    draw.ellipse([lx - BLUSH_RX, cy - BLUSH_RY,
                  lx + BLUSH_RX, cy + BLUSH_RY], fill=CHEEK_COLOR)
    draw.ellipse([rx - BLUSH_RX, cy - BLUSH_RY,
                  rx + BLUSH_RX, cy + BLUSH_RY], fill=CHEEK_COLOR)

    # 3. Eye white (ellipse)
    ex0 = EYE_CX - EYE_W // 2
    ey0 = EYE_CY - EYE_H // 2
    ex1 = EYE_CX + EYE_W // 2
    ey1 = EYE_CY + EYE_H // 2
    draw.ellipse([ex0, ey0, ex1, ey1], fill=EYE_WHITE, outline=EYE_OUTLINE, width=2)

    # 4. Iris (blue circle, clipped to eye white area)
    iris_cx = EYE_CX + iris_x_offset * EYE_TRAVEL
    iris_cy = float(EYE_CY)
    # Draw iris
    draw.ellipse([iris_cx - IRIS_R, iris_cy - IRIS_R,
                  iris_cx + IRIS_R, iris_cy + IRIS_R], fill=IRIS_COLOR)

    # 5. Pupil
    draw.ellipse([iris_cx - PUPIL_R, iris_cy - PUPIL_R,
                  iris_cx + PUPIL_R, iris_cy + PUPIL_R], fill=PUPIL_COLOR)

    # 6. Shine highlight
    sx = iris_cx - IRIS_R * 0.35
    sy = iris_cy - IRIS_R * 0.35
    draw.ellipse([sx - SHINE_R, sy - SHINE_R,
                  sx + SHINE_R, sy + SHINE_R], fill=SHINE_COLOR)

    # 7. Eye outline re-draw (top arc) to keep the lid natural
    draw.arc([ex0, ey0, ex1, ey1], start=200, end=340,
             fill=EYE_OUTLINE, width=2)

    # 8. Mouth (small arc smile)
    draw.arc([MOUTH_CX - MOUTH_W // 2, MOUTH_CY,
              MOUTH_CX + MOUTH_W // 2, MOUTH_CY + MOUTH_H],
             start=10, end=170, fill=MOUTH_COLOR, width=3)

    return img.convert("P", palette=Image.ADAPTIVE, colors=256)


def eased_positions(steps: int) -> list:
    """
    Return a list of `steps` iris x-offsets in [-1, +1] that simulate a
    reading scan: slow from left → right, brief pause at right, then
    quick snap back to the left, pause, repeat.

    The motion uses a smooth sine-based ease so it feels natural.
    """
    positions = []

    # Phase 1: slow drift left → right  (60 % of frames)
    scan_steps = int(steps * 0.60)
    for i in range(scan_steps):
        t = i / max(scan_steps - 1, 1)
        # ease-in-out: 3t²-2t³
        t_ease = 3 * t**2 - 2 * t**3
        positions.append(-1.0 + 2.0 * t_ease)   # -1 → +1

    # Phase 2: hold at right  (15 % of frames)
    hold_steps = int(steps * 0.15)
    for _ in range(hold_steps):
        positions.append(1.0)

    # Phase 3: quick return right → left  (15 % of frames)
    return_steps = int(steps * 0.15)
    for i in range(return_steps):
        t = i / max(return_steps - 1, 1)
        t_ease = 3 * t**2 - 2 * t**3
        positions.append(1.0 - 2.0 * t_ease)    # +1 → -1

    # Phase 4: hold at left  (remaining frames)
    while len(positions) < steps:
        positions.append(-1.0)

    return positions


def main():
    # Total frames and per-frame delay (ms) → controls playback speed
    TOTAL_FRAMES = 60
    FRAME_DELAY  = 60    # ms per frame  →  ~16.7 fps

    positions = eased_positions(TOTAL_FRAMES)
    frames    = [draw_frame(p) for p in positions]

    out_path = "FUN-ANIMATION/star_avatar_reading.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        loop=0,           # loop forever
        duration=FRAME_DELAY,
        optimize=False,
    )
    print(f"Saved {out_path}  ({TOTAL_FRAMES} frames, {FRAME_DELAY} ms/frame)")


if __name__ == "__main__":
    main()
