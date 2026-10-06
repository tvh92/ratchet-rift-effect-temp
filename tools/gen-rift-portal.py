"""Generate assets/rift-portal.svg: connected unequal fracture cells around the fixed opening.

Usage: python tools/gen-rift-portal.py [seed] [output]
Seed 4 produces the committed asset. The opening path must stay identical to
assets/rift-aperture.svg; both SVGs share the viewBox -30 -30 380 380.
"""
import math
import os
import random
import sys

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 4
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "assets", "rift-portal.svg"
)
rnd = random.Random(SEED)

CX, CY = 159, 162
OPENING_D = (
    "M139 61 L160 65 Q177 72 194 62 L207 86 L230 90 L235 118 Q253 133 253 152 "
    "L242 166 L251 182 Q249 209 233 224 L218 227 L207 249 Q190 264 169 260 "
    "L155 254 L135 262 Q115 259 99 245 L96 229 L78 224 Q64 209 66 187 L58 174 "
    "L64 154 Q56 134 67 113 L82 106 L91 85 Q111 70 127 72 Z"
)
RIM = [
    (139, 61), (160, 65), (194, 62), (207, 86), (230, 90), (235, 118),
    (253, 152), (242, 166), (251, 182), (233, 224), (218, 227), (207, 249),
    (169, 260), (155, 254), (135, 262), (99, 245), (96, 229), (78, 224),
    (66, 187), (58, 174), (64, 154), (67, 113), (82, 106), (91, 85), (127, 72),
]
N = len(RIM)


def polar(p):
    dx, dy = p[0] - CX, p[1] - CY
    return math.atan2(dy, dx), math.hypot(dx, dy)


def at(ang, r):
    return (CX + math.cos(ang) * r, CY + math.sin(ang) * r)


def fmt(p):
    return f"{p[0]:.0f} {p[1]:.0f}"


# Ring 1: irregular attachment points on the rim, pushed outward by unequal amounts.
attach1 = []
i = rnd.randrange(2)
while i < N:
    attach1.append(i)
    i += rnd.choice([1, 2, 2, 2, 3, 3])
if N - attach1[-1] + attach1[0] < 2:
    attach1.pop()

ring1 = []
for idx in attach1:
    a, r = polar(RIM[idx])
    a += rnd.uniform(-0.12, 0.12)
    ring1.append(at(a, r + rnd.uniform(20, 44)))

# Ring 2: a subset of ring-1 points extends further, making large, unequal outer panes.
attach2 = [k for k in range(len(ring1)) if rnd.random() < 0.55]
ring2 = []
for k in attach2:
    a, r = polar(ring1[k])
    a += rnd.uniform(-0.15, 0.15)
    ring2.append(at(a, r + rnd.uniform(22, 46)))

edges = []
cells1 = []
for j, idx in enumerate(attach1):
    nj = (j + 1) % len(attach1)
    nidx = attach1[nj]
    edges.append([RIM[idx], ring1[j]])
    # Outer edge of the cell, bent once so the panes are never regular quads.
    p, q = ring1[j], ring1[nj]
    mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    ma, mr = polar(mid)
    bend = at(ma, mr + rnd.uniform(-6, 9))
    edges.append([p, bend, q])
    rim_run = []
    k = idx
    while True:
        rim_run.append(RIM[k])
        if k == nidx:
            break
        k = (k + 1) % N
    cells1.append(rim_run + [q, bend, p])

cells2 = []
for j, k in enumerate(attach2):
    nj = (j + 1) % len(attach2)
    nk = attach2[nj]
    edges.append([ring1[k], ring2[j]])
    p, q = ring2[j], ring2[nj]
    mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    ma, mr = polar(mid)
    bend = at(ma, mr + rnd.uniform(-4, 14))
    # Leave most outer edges open so the outside never reads as a closed polygon.
    if rnd.random() < 0.35:
        edges.append([p, bend, q])
    else:
        t1, t2 = rnd.uniform(0.25, 0.5), rnd.uniform(0.15, 0.4)
        edges.append([p, (p[0] + (bend[0] - p[0]) * t1, p[1] + (bend[1] - p[1]) * t1)])
        edges.append([q, (q[0] + (bend[0] - q[0]) * t2, q[1] + (bend[1] - q[1]) * t2)])
    run = []
    m = k
    while True:
        run.append(ring1[m])
        if m == nk:
            break
        m = (m + 1) % len(ring1)
    cells2.append(run + [q, bend, p])

# Cracks run outward from the outer corners and fork before fading out.
cracks = []


def crack(start, ang, length, depth):
    pts = [start]
    p = start
    a = ang
    remaining = length
    while remaining > 0:
        seg = rnd.uniform(10, 20)
        a += rnd.uniform(-0.35, 0.35)
        a = ang + max(-0.6, min(0.6, a - ang))
        p = (p[0] + math.cos(a) * seg, p[1] + math.sin(a) * seg)
        pts.append(p)
        remaining -= seg
        if depth < 2 and rnd.random() < 0.3:
            crack(p, a + rnd.choice([-1, 1]) * rnd.uniform(0.45, 0.8), remaining * 0.6, depth + 1)
    cracks.append(pts)


for p in ring2:
    a, r = polar(p)
    crack(p, a, rnd.uniform(28, 60), 0)
for k, p in enumerate(ring1):
    if k not in attach2 and rnd.random() < 0.7:
        a, r = polar(p)
        crack(p, a, rnd.uniform(18, 50), 1)


def jag(poly):
    """Kink long straight segments so fracture lines are never ruler-straight."""
    out = [poly[0]]
    for a, b in zip(poly, poly[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        if ln > 14:
            off = rnd.uniform(-0.13, 0.13) * ln
            t = rnd.uniform(0.35, 0.65)
            out.append((a[0] + dx * t - dy / ln * off, a[1] + dy * t + dx / ln * off))
        out.append(b)
    return out


edges = [jag(e) for e in edges]


def path_d(polys, closed=False):
    out = []
    for poly in polys:
        s = "M" + " L".join(fmt(p) for p in poly)
        out.append(s + (" Z" if closed else ""))
    return " ".join(out)


def pane_fills(cells, lo, hi, chance):
    rows = []
    for c in cells:
        if rnd.random() < chance:
            op = rnd.uniform(lo, hi)
            rows.append(f'    <path d="{path_d([c], True)}" opacity="{op:.2f}"/>')
    return "\n".join(rows)


hot_spots = []
for p in rnd.sample(ring1, 3):
    hot_spots.append(p)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-30 -30 380 380">
  <defs>
    <!-- Geometry only: each use supplies its own stroke, opacity and blur. Generated (seed {SEED}). -->
    <path id="opening" d="{OPENING_D}"/>
    <path id="cells" d="{path_d(edges)}"/>
    <path id="cracks" d="{path_d(cracks)}"/>
    <linearGradient id="hot" x1="0" y1="0" x2="1" y2="1">
      <stop stop-color="#ffc4ff"/><stop offset=".3" stop-color="#fff4ff"/>
      <stop offset=".54" stop-color="#ff8cf3"/><stop offset=".8" stop-color="#ffe0ff"/><stop offset="1" stop-color="#ff9cff"/>
    </linearGradient>
    <linearGradient id="pane" x1="0" y1="0" x2="1" y2="1">
      <stop stop-color="#ffd0ff" stop-opacity=".95"/><stop offset=".45" stop-color="#c040ff" stop-opacity=".4"/><stop offset="1" stop-color="#ff7af4" stop-opacity=".85"/>
    </linearGradient>
    <linearGradient id="sliver" x1="0" y1="0" x2="1" y2="1">
      <stop stop-color="#e7b8ff" stop-opacity=".42"/><stop offset=".5" stop-color="#6f3cff" stop-opacity=".12"/><stop offset="1" stop-color="#d06bff" stop-opacity=".3"/>
    </linearGradient>
    <radialGradient id="haze" gradientUnits="userSpaceOnUse" cx="{CX}" cy="{CY}" r="190">
      <stop offset=".34" stop-color="#ff2ef2" stop-opacity="0"/>
      <stop offset=".5" stop-color="#ff2ef2" stop-opacity=".8"/>
      <stop offset=".62" stop-color="#e01cf5" stop-opacity=".5"/>
      <stop offset=".8" stop-color="#a514e8" stop-opacity=".16"/>
      <stop offset="1" stop-color="#a514e8" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="fade" gradientUnits="userSpaceOnUse" cx="{CX}" cy="{CY}" r="190">
      <stop offset=".5" stop-color="white"/><stop offset=".64" stop-color="white" stop-opacity=".6"/><stop offset=".82" stop-color="white" stop-opacity=".15"/><stop offset=".95" stop-color="white" stop-opacity="0"/>
    </radialGradient>
    <mask id="falloff" maskUnits="userSpaceOnUse" x="-30" y="-30" width="380" height="380"><rect x="-30" y="-30" width="380" height="380" fill="url(#fade)"/></mask>
    <filter id="bloom" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="12"/></filter>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="3.5"/></filter>
    <filter id="fine" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="1.1"/></filter>
  </defs>
  <!-- Broad saturated bloom that peaks at the rim and fades softly outward. -->
  <rect x="-30" y="-30" width="380" height="380" fill="url(#haze)"/>
  <use href="#opening" fill="none" stroke="#f21cfa" stroke-width="38" opacity=".7" filter="url(#bloom)"/>
  <!-- Translucent glass panes: unequal cells of the fractured surface. -->
  <g mask="url(#falloff)" fill="url(#pane)">
{pane_fills(cells1, 0.35, 0.8, 0.8)}
{pane_fills(cells2, 0.12, 0.32, 0.6)}
  </g>
  <!-- Cracks continue outward from the outer cell corners. -->
  <g mask="url(#falloff)">
    <use href="#cracks" fill="none" stroke="#f02cfb" stroke-width="5" stroke-linejoin="round" opacity=".75" filter="url(#glow)"/>
    <use href="#cracks" fill="none" stroke="#ffc6fc" stroke-width="1.3" stroke-linejoin="round"/>
  </g>
  <use mask="url(#falloff)" href="#cells" fill="none" stroke="#f22afa" stroke-width="11" stroke-linejoin="round" opacity=".7" filter="url(#glow)"/>
  <!-- Refracted slivers intrude into the opening, leaving the center clear. -->
  <g fill="url(#sliver)" stroke="#d27bff" stroke-width="1.1" stroke-linejoin="round">
    <path d="M82 106 L104 101 L117 135 L107 161 L66 187 L64 154 L67 113 Z"/>
    <path d="M194 62 L185 91 L204 120 L235 118 L230 90 L207 86 Z"/>
    <path d="M253 152 L224 155 L215 176 L230 190 L251 182 L242 166 Z"/>
    <path d="M218 227 L191 224 L177 242 L169 260 L190 258 L207 249 Z"/>
    <path d="M96 229 L118 219 L139 239 L135 262 L113 252 L99 245 Z"/>
  </g>
  <use mask="url(#falloff)" href="#cells" fill="none" stroke="#ff8ff9" stroke-width="3.4" stroke-linejoin="round" opacity=".85" filter="url(#fine)"/>
  <use mask="url(#falloff)" href="#cells" fill="none" stroke="url(#hot)" stroke-width="1.5" stroke-linejoin="round" opacity=".95"/>
  <!-- Rim: glow, uneven thick segments, then a sharp white-pink core. -->
  <use href="#opening" fill="none" stroke="#ff3ff4" stroke-width="15" opacity=".9" filter="url(#glow)"/>
  <use href="#opening" fill="none" stroke="#ff7af6" stroke-width="9" stroke-linecap="round" stroke-dasharray="70 22 34 46 18 30" opacity=".9" filter="url(#fine)"/>
  <use href="#opening" fill="none" stroke="#ffa6fa" stroke-width="5" stroke-linejoin="round" opacity=".95"/>
  <use href="#opening" fill="none" stroke="url(#hot)" stroke-width="2" stroke-linejoin="round"/>
  <!-- White-pink hotspots where fractures meet the rim. -->
  <g fill="#ffe8ff" filter="url(#glow)">
    <ellipse cx="202" cy="72" rx="9" ry="15" opacity=".75"/>
    <ellipse cx="66" cy="126" rx="8" ry="12" opacity=".6"/>
    <ellipse cx="109" cy="249" rx="13" ry="6" opacity=".6"/>
{chr(10).join(f'    <circle cx="{p[0]:.0f}" cy="{p[1]:.0f}" r="4" opacity=".55"/>' for p in hot_spots)}
  </g>
</svg>
'''
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(svg)
print("cells1", len(cells1), "cells2", len(cells2), "cracks", len(cracks))
