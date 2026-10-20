"""The stickers this app adds to the original sticker set: the boys' section (16 squishies drawn here, Fluent Emoji pictures, 9 Star
Friends) and more for the girls' section. Run once; the export script (talk-cards repo, scripts/export_maths.py) builds
the two books from the original stickers plus stickers/extra.json, which this writes.

Usage: python3 tools/make_stickers.py RAW_DIR
RAW_DIR holds the Fluent Emoji 3D pictures (github.com/microsoft/fluentui-emoji, MIT), named like racing-car.png.
"""
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = sys.argv[1] if len(sys.argv) > 1 else ''
OUT = os.path.join(APP, 'stickers')
SIZE, INNER, K = 300, 262, 4          # sticker canvas, picture inside it, drawing scale

# ---------- the die-cut look of the original stickers: a white edge and a soft shadow ----------
def diecut(pic, size=SIZE, inner=INNER, edge=8, k=K):
    big = Image.new('RGBA', (size * k, size * k), (0, 0, 0, 0))
    p = pic.convert('RGBA').resize((inner * k, inner * k), Image.LANCZOS)
    off = ((size - inner) * k // 2, (size - inner) * k // 2 - 3 * k)
    big.alpha_composite(p, off)
    a = big.split()[3].point(lambda v: 255 if v > 60 else 0)
    grow = a.filter(ImageFilter.GaussianBlur(edge * k * .55)).point(lambda v: 255 if v > 18 else 0).filter(ImageFilter.GaussianBlur(k * .7))
    shadow = Image.new('RGBA', big.size, (60, 30, 60, 0))
    shadow.putalpha(grow.filter(ImageFilter.GaussianBlur(5 * k)).point(lambda v: int(v * .28)))
    out = Image.new('RGBA', big.size, (0, 0, 0, 0))
    out.alpha_composite(shadow, (2 * k, 5 * k))
    white = Image.new('RGBA', big.size, (255, 255, 255, 0)); white.putalpha(grow)
    out.alpha_composite(white)
    out.alpha_composite(big)
    return out.resize((size, size), Image.LANCZOS)


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, 'WEBP', quality=88, method=6)


# ---------- squishies: see-through jelly, glitter, a shiny face ----------
W = INNER * K
def hexc(h, a=255): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)
def mix(c1, c2, t): return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,)

def jelly(mask, base, rnd, glitter=None, star_glitter=False, gloss=True):
    """Fill a shape with a jelly gradient, an inner glow, glitter and a highlight."""
    b = hexc(base)
    light, dark = mix(b, (255, 255, 255), .55), mix(b, (40, 30, 70), .28)
    bb = mask.getbbox() or (0, 0, W, W)
    cx, cy = bb[0] + (bb[2] - bb[0]) * .4, bb[1] + (bb[3] - bb[1]) * .35
    R = max(bb[2] - bb[0], bb[3] - bb[1]) * .8
    grad = Image.new('RGBA', (W, W))
    gd = ImageDraw.Draw(grad)
    for i in range(60, -1, -1):
        t = i / 60
        col = mix(light, b, min(1, t * 1.6)) if t < .62 else mix(b, dark, (t - .62) / .38)
        r = R * t
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    grad = grad.filter(ImageFilter.GaussianBlur(10))
    # a darker rim and a light inner glow at the bottom, like light through jelly
    inner = mask.filter(ImageFilter.GaussianBlur(40))
    rim = ImageChops.subtract(mask, inner).point(lambda v: int(v * .9))
    rimc = Image.new('RGBA', (W, W), dark[:3] + (0,)); rimc.putalpha(rim)
    grad.alpha_composite(rimc)
    glow = Image.new('L', (W, W), 0)
    ImageDraw.Draw(glow).ellipse([bb[0] + (bb[2] - bb[0]) * .2, bb[3] - (bb[3] - bb[1]) * .32, bb[2] - (bb[2] - bb[0]) * .2, bb[3] - (bb[3] - bb[1]) * .06], fill=110)
    glow = ImageChops.multiply(glow.filter(ImageFilter.GaussianBlur(30)), mask)
    gl = Image.new('RGBA', (W, W), (255, 255, 255, 0)); gl.putalpha(glow)
    grad.alpha_composite(gl)
    # glitter: little squares, diamonds and dots, most of them in the upper middle
    if glitter:
        g = Image.new('RGBA', (W, W), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
        gx, gy = (bb[0] + bb[2]) / 2, bb[1] + (bb[3] - bb[1]) * .42
        for _ in range(300):
            a, r = rnd.random() * math.tau, abs(rnd.gauss(0, .17)) * (bb[2] - bb[0])
            x, y = gx + math.cos(a) * r, gy + math.sin(a) * r * .7
            s = rnd.uniform(7, 19)
            col = hexc(rnd.choice(glitter), rnd.randint(170, 255))
            kind = rnd.random()
            if star_glitter and kind < .35:
                pts = [(x + math.cos(k * math.pi / 4) * (s * 1.3 if k % 2 == 0 else s * .45), y + math.sin(k * math.pi / 4) * (s * 1.3 if k % 2 == 0 else s * .45)) for k in range(8)]
                d.polygon(pts, fill=col)
            elif kind < .55: d.polygon([(x, y - s), (x + s * .7, y), (x, y + s), (x - s * .7, y)], fill=col)
            elif kind < .8: d.rectangle([x - s / 2, y - s / 2, x + s / 2, y + s / 2], fill=col)
            else: d.ellipse([x - s / 3, y - s / 3, x + s / 3, y + s / 3], fill=col)
        g.putalpha(ImageChops.multiply(g.split()[3], mask.filter(ImageFilter.GaussianBlur(4))))
        grad.alpha_composite(g)
    if gloss:   # the shine, top left
        hl = Image.new('L', (W, W), 0); hd = ImageDraw.Draw(hl)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        hd.ellipse([bb[0] + w * .16, bb[1] + h * .1, bb[0] + w * .38, bb[1] + h * .24], fill=235)
        hd.ellipse([bb[0] + w * .42, bb[1] + h * .1, bb[0] + w * .48, bb[1] + h * .15], fill=200)
        hl = ImageChops.multiply(hl.filter(ImageFilter.GaussianBlur(6)), mask)
        hc = Image.new('RGBA', (W, W), (255, 255, 255, 0)); hc.putalpha(hl)
        grad.alpha_composite(hc)
    grad.putalpha(ImageChops.multiply(grad.split()[3], mask))
    return grad

def face(img, cx, cy, s=1.0, blush='#FF8FB8', mouth='smile'):
    s *= 1.5
    d = ImageDraw.Draw(img)
    ex, er = 66 * s, 25 * s
    for sx in (-1, 1):
        x = cx + sx * ex
        d.ellipse([x - er, cy - er * 1.15, x + er, cy + er * 1.15], fill=(25, 20, 35, 255))
        d.ellipse([x - er * .55, cy - er * .85, x - er * .05, cy - er * .3], fill=(255, 255, 255, 255))
        d.ellipse([x + er * .15, cy + er * .25, x + er * .45, cy + er * .55], fill=(255, 255, 255, 220))
    bl = Image.new('RGBA', img.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(bl)
    for sx in (-1, 1):
        x = cx + sx * (ex + 44 * s)
        bd.ellipse([x - 26 * s, cy + 22 * s, x + 26 * s, cy + 40 * s], fill=hexc(blush, 150))
    img.alpha_composite(bl.filter(ImageFilter.GaussianBlur(6)))
    if mouth == 'smile':
        d.arc([cx - 22 * s, cy + 2 * s, cx + 22 * s, cy + 34 * s], 20, 160, fill=(25, 20, 35, 255), width=round(7 * s))
    elif mouth == 'open':
        d.chord([cx - 20 * s, cy + 8 * s, cx + 20 * s, cy + 40 * s], 0, 180, fill=(120, 30, 50, 255))
    elif mouth == 'tooth':
        d.arc([cx - 24 * s, cy + 2 * s, cx + 24 * s, cy + 34 * s], 20, 160, fill=(25, 20, 35, 255), width=round(7 * s))
        d.polygon([(cx - 10 * s, cy + 31 * s), (cx + 2 * s, cy + 31 * s), (cx - 4 * s, cy + 44 * s)], fill=(255, 255, 255, 255))

def smooth(mask, r=10):
    return mask.filter(ImageFilter.GaussianBlur(r)).point(lambda v: 255 if v > 127 else 0).filter(ImageFilter.GaussianBlur(2))

def m_new(): return Image.new('L', (W, W), 0)
def ell(m, box, v=255): ImageDraw.Draw(m).ellipse(box, fill=v); return m
def poly(m, pts, v=255): ImageDraw.Draw(m).polygon(pts, fill=v); return m
def rrect(m, box, r, v=255): ImageDraw.Draw(m).rounded_rectangle(box, r, fill=v); return m
def layer(img, mask, color):
    c = Image.new('RGBA', (W, W), hexc(color)); c.putalpha(mask); img.alpha_composite(c)

C = W / 2
GLIT = ['#FFB3DD', '#C9B6FF', '#9FE6C9', '#9FD2FF', '#FFE98A', '#FFFFFF']
GLIT_B = ['#9FD2FF', '#FFFFFF', '#FFE98A', '#8FF0D8', '#C9D8FF']

def sq_round(base, glit=GLIT_B, box=(130, 170, W - 130, W - 120), star=False):
    def draw(rnd):
        m = smooth(ell(m_new(), box))
        img = jelly(m, base, rnd, glit, star)
        face(img, C, box[1] + (box[3] - box[1]) * .6)
        return img
    return draw

def sq_dino(rnd):
    m = m_new(); ell(m, (140, 300, W - 140, W - 110)); rrect(m, (140, 600, W - 140, W - 110), 120)
    spikes = m_new()
    for i, x in enumerate([330, 470, 610, 740]):
        poly(spikes, [(x - 62, 340 + (i in (0, 3)) * 40), (x, 175 + (i in (0, 3)) * 50), (x + 62, 340 + (i in (0, 3)) * 40)])
    spikes = smooth(spikes, 8)
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    img.alpha_composite(jelly(spikes, '#FF9F43', rnd, None, gloss=False))
    img.alpha_composite(jelly(smooth(m), '#4CC96B', rnd, GLIT_B))
    face(img, C, 660)
    return img

def sq_shark(rnd):
    body = smooth(ell(m_new(), (110, 290, W - 110, W - 140)))
    fin = smooth(poly(m_new(), [(380, 330), (560, 120), (640, 330)]), 12)
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    img.alpha_composite(jelly(fin, '#5C8DD6', rnd, None, gloss=False))
    img.alpha_composite(jelly(body, '#6FA3E8', rnd, GLIT_B))
    belly = ImageChops.multiply(smooth(ell(m_new(), (210, 600, W - 210, W - 150))), body)
    bl = Image.new('RGBA', (W, W), (240, 248, 255, 0)); bl.putalpha(belly.point(lambda v: int(v * .75))); img.alpha_composite(bl)
    face(img, C, 560, mouth='tooth')
    return img

def sq_robot(rnd):
    m = smooth(rrect(m_new(), (170, 260, W - 170, W - 130), 150))
    ear = smooth(rrect(rrect(m_new(), (110, 470, 200, 640), 30), (W - 200, 470, W - 110, 640), 30))
    ant = smooth(rrect(m_new(), (C - 14, 140, C + 14, 290), 12), 4)
    ball = smooth(ell(m_new(), (C - 48, 90, C + 48, 186)))
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    layer(img, ant, '#7C8796')
    img.alpha_composite(jelly(ball, '#FF5D73', rnd, None))
    img.alpha_composite(jelly(ear, '#8E9AAF', rnd, None, gloss=False))
    img.alpha_composite(jelly(m, '#B8C4D6', rnd, ['#9FD2FF', '#FFFFFF', '#8FF0D8']))
    face(img, C, 590, blush='#7FD0FF')
    return img

def sq_football(rnd):
    m = smooth(ell(m_new(), (150, 150, W - 150, W - 150)))
    img = jelly(m, '#F4F7FB', rnd, ['#C9D8FF', '#9FD2FF', '#FFFFFF'])
    p = m_new()
    def pent(cx, cy, r, rot=-90): return [(cx + r * math.cos(math.radians(rot + k * 72)), cy + r * math.sin(math.radians(rot + k * 72))) for k in range(5)]
    poly(p, pent(C, 330, 70))
    for cx, cy, rot in [(250, 450, -54), (W - 250, 450, -126), (300, 760, 18), (W - 300, 760, 162)]:
        poly(p, pent(cx, cy, 62, rot))
    p = ImageChops.multiply(smooth(p, 6), m)
    layer(img, p.point(lambda v: int(v * .85)), '#3A4256')
    face(img, C, 590)
    return img

def sq_monster(rnd):
    m = smooth(ell(m_new(), (140, 240, W - 140, W - 120)))
    horns = smooth(poly(poly(m_new(), [(290, 320), (330, 130), (420, 290)]), [(W - 290, 320), (W - 330, 130), (W - 420, 290)]), 10)
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    img.alpha_composite(jelly(horns, '#FFD34D', rnd, None, gloss=False))
    img.alpha_composite(jelly(m, '#9B6BF2', rnd, GLIT))
    face(img, C, 600, mouth='tooth')
    return img

def sq_planet(rnd):
    ball = smooth(ell(m_new(), (230, 200, W - 230, W - 230)))
    ring_back = m_new(); ImageDraw.Draw(ring_back).ellipse((70, 440, W - 70, 700), outline=255, width=44)
    ring_front = ImageChops.multiply(ring_back, smooth(rrect(m_new(), (0, 570, W, W), 0), 2))
    ring_back = ImageChops.subtract(ring_back, ring_front)
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    img.alpha_composite(jelly(smooth(ring_back, 3), '#7FD0FF', rnd, None, gloss=False))
    img.alpha_composite(jelly(ball, '#FF9F43', rnd, GLIT, True))
    img.alpha_composite(jelly(smooth(ring_front, 3), '#8FE0FF', rnd, ['#FFFFFF', '#FFE98A'], gloss=False))
    face(img, C, 490, s=.8)
    return img

def sq_bolt(rnd):
    m = smooth(poly(m_new(), [(560, 90), (230, 560), (470, 560), (380, W - 80), (W - 220, 430), (560, 430), (690, 90)]), 26)
    img = jelly(m, '#FFC93C', rnd, ['#FFFFFF', '#FFF2A8', '#FFB3DD'], True)
    face(img, 500, 480, s=.6)
    return img

def sq_star(rnd):
    pts = [(C + (430 if k % 2 == 0 else 190) * math.cos(math.radians(-90 + k * 36)), 560 + (430 if k % 2 == 0 else 190) * math.sin(math.radians(-90 + k * 36))) for k in range(10)]
    m = smooth(poly(m_new(), pts), 30)
    img = jelly(m, '#6CB6FF', rnd, ['#FFE98A', '#FFFFFF', '#FFD34D'], True)
    face(img, C, 600, s=.75)
    return img

def sq_whale(rnd):
    body = smooth(ell(m_new(), (110, 360, W - 230, W - 130)))
    tail = smooth(poly(poly(m_new(), [(W - 300, 600), (W - 90, 430), (W - 140, 640)]), [(W - 300, 640), (W - 80, 760), (W - 160, 600)]), 14)
    spout = m_new()
    for x, y, r in [(400, 230, 44), (330, 170, 30), (470, 160, 32), (400, 110, 26)]: ell(spout, (x - r, y - r, x + r, y + r))
    spout = smooth(spout, 6)
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    img.alpha_composite(jelly(tail, '#3D7FE0', rnd, None, gloss=False))
    img.alpha_composite(jelly(spout, '#A6E3FF', rnd, None))
    img.alpha_composite(jelly(body, '#4A90E8', rnd, GLIT_B))
    face(img, 420, 630, s=.9)
    return img

def sq_tiger(rnd):
    m = m_new(); ell(m, (150, 230, W - 150, W - 130))
    ell(m, (170, 170, 360, 360)); ell(m, (W - 360, 170, W - 170, 360))
    m = smooth(m)
    img = jelly(m, '#FF9A3C', rnd, ['#FFE98A', '#FFFFFF', '#FFD34D'])
    st = m_new()
    for pts in [[(C - 30, 250), (C + 30, 250), (C, 380)], [(C - 120, 260), (C - 70, 260), (C - 95, 350)], [(C + 70, 260), (C + 120, 260), (C + 95, 350)],
                [(150, 520), (270, 545), (150, 580)], [(W - 150, 520), (W - 270, 545), (W - 150, 580)], [(165, 640), (260, 655), (170, 690)], [(W - 165, 640), (W - 260, 655), (W - 170, 690)]]:
        poly(st, pts)
    layer(img, ImageChops.multiply(smooth(st, 5), m).point(lambda v: int(v * .8)), '#3A2A2A')
    muzzle = smooth(ell(m_new(), (C - 120, 610, C + 120, 780)))
    layer(img, muzzle.point(lambda v: int(v * .8)), '#FFF4E6')
    face(img, C, 570)
    return img

def sq_turtle(rnd):
    head = smooth(ell(m_new(), (40, 470, 280, 690)))
    legs = smooth(ell(ell(m_new(), (200, 720, 340, 850)), (W - 340, 720, W - 200, 850)))
    shell = smooth(ell(m_new(), (180, 260, W - 110, W - 170)))
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    img.alpha_composite(jelly(legs, '#7FD67A', rnd, None, gloss=False))
    img.alpha_composite(jelly(head, '#8BE086', rnd, None))
    img.alpha_composite(jelly(shell, '#2FAE6E', rnd, ['#FFE98A', '#FFFFFF', '#B8F5C8']))
    pat = m_new(); d = ImageDraw.Draw(pat)
    cx, cy = 590, 520
    def hexa(x, y, r): return [(x + r * math.cos(math.radians(30 + 60 * k)), y + r * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
    for x, y in [(cx, cy), (cx - 165, cy - 50), (cx + 165, cy - 50), (cx - 165, cy + 110), (cx + 165, cy + 110), (cx, cy - 160)]:
        d.polygon(hexa(x, y, 82), outline=255, width=14)
    layer(img, ImageChops.multiply(smooth(pat, 3), shell).point(lambda v: int(v * .22)), '#14724A')
    face(img, 610, 600, s=.95)
    return img

def sq_car(rnd):
    body = m_new(); rrect(body, (90, 430, W - 90, 760), 150); rrect(body, (250, 250, W - 250, 520), 130)
    body = smooth(body)
    wheels = smooth(ell(ell(m_new(), (190, 640, 400, 850)), (W - 400, 640, W - 190, 850)))
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    img.alpha_composite(jelly(body, '#FF4D5E', rnd, ['#FFE98A', '#FFFFFF', '#FFB3DD']))
    win = ImageChops.multiply(smooth(rrect(m_new(), (310, 300, W - 310, 470), 70)), body)
    layer(img, win.point(lambda v: int(v * .85)), '#BFE6FF')
    img.alpha_composite(jelly(wheels, '#3A3F4F', rnd, None))
    hub = smooth(ell(ell(m_new(), (255, 705, 335, 785)), (W - 335, 705, W - 255, 785)))
    layer(img, hub, '#C8CED8')
    face(img, C, 600, s=.8, blush='#FFB3C6')
    return img

def sq_galaxy(rnd):
    m = smooth(ell(m_new(), (140, 170, W - 140, W - 120)))
    img = jelly(m, '#4B3A9E', rnd, ['#FFFFFF', '#FFE98A', '#9FD2FF', '#FFB3DD'], True)
    face(img, C, 610, blush='#C58BFF')
    return img

def sq_burger(rnd):
    top = smooth(ell(m_new(), (150, 180, W - 150, 560)))
    top = ImageChops.multiply(top, smooth(rrect(m_new(), (0, 0, W, 470), 0), 2))
    lettuce = m_new(); d = ImageDraw.Draw(lettuce)
    for k in range(9): d.ellipse((150 + k * 86, 430, 260 + k * 86, 540), fill=255)
    lettuce = smooth(lettuce, 6)
    patty = smooth(rrect(m_new(), (160, 500, W - 160, 640), 70))
    bottom = smooth(rrect(m_new(), (170, 630, W - 170, 820), 90))
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    img.alpha_composite(jelly(bottom, '#F2A65A', rnd, None))
    img.alpha_composite(jelly(patty, '#8A4B2A', rnd, None, gloss=False))
    img.alpha_composite(jelly(lettuce, '#6DD36B', rnd, None, gloss=False))
    img.alpha_composite(jelly(top, '#F5A84E', rnd, ['#FFF6D6', '#FFFFFF']))
    face(img, C, 330, s=.8)
    return img

# file, English name, Arabic name, sparkly, drawing
SQUISHIES = [
    ('sq-blue.webp', 'Blue glitter squishy', 'سكويشي أزرق لامع', False, sq_round('#5AA9F0')),
    ('sq-dino.webp', 'Dino squishy', 'سكويشي الديناصور', False, sq_dino),
    ('sq-shark.webp', 'Shark squishy', 'سكويشي القرش', False, sq_shark),
    ('sq-planet.webp', 'Planet squishy', 'سكويشي الكوكب', True, sq_planet),
    ('sq-robot.webp', 'Robot squishy', 'سكويشي الروبوت', False, sq_robot),
    ('sq-football.webp', 'Football squishy', 'سكويشي الكرة', False, sq_football),
    ('sq-monster.webp', 'Monster squishy', 'سكويشي الوحش اللطيف', False, sq_monster),
    ('sq-bolt.webp', 'Lightning squishy', 'سكويشي البرق', True, sq_bolt),
    ('sq-green.webp', 'Green glitter squishy', 'سكويشي أخضر لامع', False, sq_round('#3CC79A', box=(120, 330, W - 120, W - 140))),
    ('sq-whale.webp', 'Whale squishy', 'سكويشي الحوت', False, sq_whale),
    ('sq-tiger.webp', 'Tiger squishy', 'سكويشي النمر', False, sq_tiger),
    ('sq-star.webp', 'Blue star squishy', 'سكويشي النجمة الزرقاء', True, sq_star),
    ('sq-turtle.webp', 'Turtle squishy', 'سكويشي السلحفاة', False, sq_turtle),
    ('sq-car.webp', 'Car squishy', 'سكويشي السيارة', False, sq_car),
    ('sq-burger.webp', 'Burger squishy', 'سكويشي البرغر', False, sq_burger),
    ('sq-galaxy.webp', 'Galaxy squishy', 'سكويشي المجرّة', True, sq_galaxy),
]

# ---------- Fluent Emoji pictures: raw name, English, Arabic, kind, sparkly ----------
BOY = [
    ('racing-car', 'Racing car', 'سيارة سباق', 'thing', False), ('soccer-ball', 'Football', 'كرة قدم', 'thing', False),
    ('basketball', 'Basketball', 'كرة سلة', 'thing', False), ('t-rex', 'T-rex', 'تي ركس', 'animal', False),
    ('helicopter', 'Helicopter', 'طائرة مروحية', 'thing', False), ('airplane', 'Aeroplane', 'طائرة', 'thing', False),
    ('fire-engine', 'Fire engine', 'سيارة إطفاء', 'thing', False), ('locomotive', 'Train', 'قطار', 'thing', False),
    ('tractor', 'Tractor', 'جرّار', 'thing', False), ('motorcycle', 'Motorbike', 'درّاجة نارية', 'thing', False),
    ('flying-saucer', 'Flying saucer', 'صحن طائر', 'thing', False), ('satellite', 'Satellite', 'قمر صناعي', 'thing', False),
    ('shark', 'Shark', 'قرش', 'animal', False), ('octopus', 'Octopus', 'أخطبوط', 'animal', False),
    ('crocodile', 'Crocodile', 'تمساح', 'animal', False), ('spouting-whale', 'Whale', 'حوت', 'animal', False),
    ('eagle', 'Eagle', 'نسر', 'animal', False), ('tiger-face', 'Tiger', 'نمر', 'animal', False),
    ('high-voltage', 'Lightning', 'برق', 'sparkly', True), ('volcano', 'Volcano', 'بركان', 'thing', False),
    ('comet', 'Comet', 'مذنّب', 'sparkly', True), ('telescope', 'Telescope', 'تلسكوب', 'thing', False),
    ('compass', 'Compass', 'بوصلة', 'sparkly', True), ('magnet', 'Magnet', 'مغناطيس', 'thing', False),
    ('skateboard', 'Skateboard', 'لوح تزلّج', 'thing', False), ('bicycle', 'Bicycle', 'درّاجة', 'thing', False),
    ('puzzle-piece', 'Puzzle piece', 'قطعة أحجية', 'thing', False), ('sports-medal', 'Medal', 'ميدالية', 'sparkly', True),
    ('police-car', 'Police car', 'سيارة شرطة', 'thing', False), ('ambulance', 'Ambulance', 'سيارة إسعاف', 'thing', False),
    ('bus', 'Bus', 'حافلة', 'thing', False), ('articulated-lorry', 'Lorry', 'شاحنة', 'thing', False),
    ('speedboat', 'Speedboat', 'قارب سريع', 'thing', False), ('ship', 'Ship', 'سفينة', 'thing', False),
    ('parachute', 'Parachute', 'مظلّة هبوط', 'thing', False), ('kick-scooter', 'Scooter', 'سكوتر', 'thing', False),
    ('high-speed-train', 'Fast train', 'قطار سريع', 'thing', False), ('american-football', 'Rugby ball', 'كرة رغبي', 'thing', False),
    ('baseball', 'Baseball', 'كرة بيسبول', 'thing', False), ('ice-hockey', 'Ice hockey', 'هوكي الجليد', 'thing', False),
    ('goal-net', 'Goal', 'مرمى', 'thing', False), ('joystick', 'Joystick', 'عصا ألعاب', 'thing', False),
    ('yo-yo', 'Yo-yo', 'يويو', 'thing', False), ('toolbox', 'Toolbox', 'صندوق العدّة', 'thing', False),
    ('microscope', 'Microscope', 'مجهر', 'thing', False), ('abacus', 'Abacus', 'معداد', 'thing', False),
    ('dragon', 'Dragon', 'تنّين', 'animal', False), ('wolf', 'Wolf', 'ذئب', 'animal', False),
    ('gorilla', 'Gorilla', 'غوريلا', 'animal', False), ('dolphin', 'Dolphin', 'دلفين', 'animal', False),
    ('crab', 'Crab', 'سلطعون', 'animal', False), ('hamburger', 'Burger', 'برغر', 'food', False),
    ('french-fries', 'Chips', 'بطاطس مقلية', 'food', False), ('snowman', 'Snowman', 'رجل الثلج', 'thing', False),
    ('shooting-star', 'Shooting star', 'شهاب', 'sparkly', True), ('sun-with-face', 'Smiling sun', 'شمس مبتسمة', 'sparkly', True),
    ('crescent-moon', 'Crescent moon', 'هلال', 'sparkly', True), ('fire', 'Fire', 'نار', 'sparkly', True),
    ('light-bulb', 'Light bulb', 'مصباح', 'sparkly', True), ('1st-place-medal', 'Gold medal', 'ميدالية ذهبية', 'sparkly', True),
    ('globe-showing-asia-australia', 'Globe', 'الكرة الأرضية', 'sparkly', True), ('milky-way', 'Milky Way', 'درب التبّانة', 'sparkly', True),
    ('bullseye', 'Bullseye', 'إصابة الهدف', 'sparkly', True), ('fireworks', 'Fireworks', 'ألعاب نارية', 'sparkly', True),
    ('snowflake', 'Snowflake', 'ندفة ثلج', 'sparkly', True), ('old-key', 'Golden key', 'مفتاح ذهبي', 'sparkly', True),
]
GIRL = [
    ('cherry-blossom', 'Cherry blossom', 'زهرة الكرز', 'thing', False), ('tulip', 'Tulip', 'توليب', 'thing', False),
    ('sunflower', 'Sunflower', 'عبّاد الشمس', 'thing', False), ('bouquet', 'Bouquet', 'باقة ورد', 'thing', False),
    ('ballet-shoes', 'Ballet shoes', 'حذاء الباليه', 'thing', False), ('dress', 'Dress', 'فستان', 'thing', False),
    ('swan', 'Swan', 'بجعة', 'animal', False), ('peacock', 'Peacock', 'طاووس', 'animal', False),
    ('lollipop', 'Lollipop', 'مصّاصة', 'food', False), ('spiral-shell', 'Seashell', 'صدفة', 'thing', False),
    ('sparkles', 'Sparkles', 'بريق', 'sparkly', True), ('ribbon', 'Ribbon', 'شريطة', 'sparkly', True),
    ('hibiscus', 'Hibiscus', 'كركديه', 'thing', False), ('rose', 'Rose', 'وردة', 'thing', False),
    ('blossom', 'Blossom', 'زهرة', 'thing', False), ('cherries', 'Cherries', 'كرز', 'food', False),
    ('candy', 'Sweet', 'حلوى', 'food', False), ('birthday-cake', 'Birthday cake', 'كعكة عيد الميلاد', 'food', False),
    ('lady-beetle', 'Ladybird', 'دعسوقة', 'animal', False), ('honeybee', 'Bee', 'نحلة', 'animal', False),
    ('hatching-chick', 'Chick', 'كتكوت', 'animal', False), ('handbag', 'Handbag', 'حقيبة يد', 'thing', False),
    ('mushroom', 'Mushroom', 'فطر', 'food', False), ('balloon', 'Balloon', 'بالون', 'thing', False),
    ('bubbles', 'Bubbles', 'فقاعات', 'sparkly', True), ('heart-with-ribbon', 'Gift heart', 'قلب الهدية', 'sparkly', True),
]
FRIENDS_BOY = [   # mirror the girls': Princess, Doctor, Fairy, Astronaut, Cartwheel girl, Scientist, Superwoman, Artist, Pilot
    ('prince', 'Prince', 'الأمير', 'twirl'), ('man-health-worker', 'Doctor', 'الطبيب', 'bounce'), ('man-mage', 'Wizard', 'الساحر', 'fly'),
    ('man-astronaut', 'Astronaut', 'رائد الفضاء', 'fly'), ('man-cartwheeling', 'Cartwheel boy', 'البهلوان', 'spin'),
    ('man-scientist', 'Scientist', 'العالِم', 'sway'), ('man-superhero', 'Superhero', 'البطل الخارق', 'fly'),
    ('man-artist', 'Artist', 'الرسّام', 'sway'), ('man-pilot', 'Pilot', 'الطيّار', 'sway'),
]

if __name__ == '__main__':
    extra = {'boy': [], 'girl': [], 'friendsBoy': []}
    for f, name, ar, sparkle, draw in SQUISHIES:
        save(diecut(draw(random.Random(f))), os.path.join(OUT, 'boy', f))
        extra['boy'].append({'file': f'boy/{f}', 'name': name, 'ar': ar, 'sparkle': sparkle, 'kind': 'glitter'})
    if RAW:
        for section, rows in (('boy', BOY), ('girl', GIRL)):
            for raw, name, ar, kind, sparkle in rows:
                save(diecut(Image.open(os.path.join(RAW, raw + '.png'))), os.path.join(OUT, section, raw + '.webp'))
                extra[section].append({'file': f'{section}/{raw}.webp', 'name': name, 'ar': ar, 'sparkle': sparkle, 'kind': kind})
        for raw, name, ar, dance in FRIENDS_BOY:      # Star Friends are plain, as in the girls' book
            save(Image.open(os.path.join(RAW, raw + '.png')).convert('RGBA'), os.path.join(OUT, 'boy', 'friends', raw + '.webp'))
            extra['friendsBoy'].append({'file': f'boy/friends/{raw}.webp', 'name': name, 'ar': ar, 'dance': dance})
    json.dump(extra, open(os.path.join(OUT, 'extra.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"{len(extra['boy'])} boys' stickers, {len(extra['girl'])} more girls' stickers, {len(extra['friendsBoy'])} boys' Star Friends")
