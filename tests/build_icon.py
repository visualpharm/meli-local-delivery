#!/usr/bin/env python3
"""Generate the extension icon: a delivery truck whose trailer is the Argentine flag."""
import math, os
import cairosvg

CELESTE = "#74ACDF"
WHITE = "#FFFFFF"
SUN = "#F6B40E"
CAB = "#455A64"
WINDOW = "#BBDEFB"
TIRE = "#263238"
HUB = "#90A4AE"
OUTLINE = "#37474F"

# Sun (Sol de Mayo, simplified): center + 12 rays
scx, scy, r_in, r_out = 47, 63, 7.8, 12.0
rays = []
for i in range(12):
    a = math.radians(i * 30)
    x1, y1 = scx + r_in * math.cos(a), scy + r_in * math.sin(a)
    x2, y2 = scx + r_out * math.cos(a), scy + r_out * math.sin(a)
    rays.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{SUN}" stroke-width="1.7" stroke-linecap="round"/>')
rays = "\n    ".join(rays)

SVG = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <defs>
    <clipPath id="box"><rect x="12" y="34" width="70" height="58" rx="6"/></clipPath>
  </defs>

  <!-- Trailer = Argentine flag -->
  <g clip-path="url(#box)">
    <rect x="12" y="34" width="70" height="20" fill="{CELESTE}"/>
    <rect x="12" y="54" width="70" height="18" fill="{WHITE}"/>
    <rect x="12" y="72" width="70" height="20" fill="{CELESTE}"/>
    <circle cx="{scx}" cy="{scy}" r="6.6" fill="{SUN}"/>
    {rays}
  </g>
  <rect x="12" y="34" width="70" height="58" rx="6" fill="none" stroke="{OUTLINE}" stroke-width="2.6"/>

  <!-- Cab -->
  <path d="M82,92 V58 H92 L102,45 H113 a4,4 0 0 1 4,4 V92 Z" fill="{CAB}"/>
  <path d="M94,58 L101,48 H112 q2,0 2,2 V58 Z" fill="{WINDOW}"/>

  <!-- Wheels -->
  <circle cx="34" cy="97" r="12" fill="{TIRE}"/><circle cx="34" cy="97" r="5" fill="{HUB}"/>
  <circle cx="100" cy="97" r="12" fill="{TIRE}"/><circle cx="100" cy="97" r="5" fill="{HUB}"/>
</svg>'''

here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
icons = os.path.join(here, "icons")
with open(os.path.join(icons, "icon.svg"), "w") as f:
    f.write(SVG)
for size in (16, 48, 128):
    cairosvg.svg2png(bytestring=SVG.encode(), write_to=os.path.join(icons, f"icon{size}.png"),
                     output_width=size, output_height=size)
    print(f"wrote icon{size}.png")
