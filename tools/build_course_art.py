"""Rebuild the original SVG course illustrations. No external image service."""

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "static" / "images" / "courses"
ROOT.mkdir(parents=True, exist_ok=True)
PALETTES = {
    "python": ("#e9edcf", "#5e7652", "PYTHON", "01 / THE FIRST LINE"),
    "django": ("#d4e5d7", "#265447", "DJANGO", "02 / BUILD SOMETHING REAL"),
    "flask": ("#eadccf", "#8c6754", "FLASK", "03 / SMALL & POWERFUL"),
    "machine-learning": ("#e2def0", "#75688e", "MACHINE LEARNING", "04 / FIND THE PATTERN"),
    "data-science": ("#d7e5ec", "#567687", "DATA SCIENCE", "05 / MAKE DATA MEANINGFUL"),
    "nlp": ("#efdcca", "#a47955", "LANGUAGE & AI", "06 / WORDS INTO INSIGHT"),
    "data-mining": ("#dee5d3", "#68815b", "DATA MINING", "07 / DISCOVER WHAT'S HIDDEN"),
    "ai": ("#e6def0", "#7e668d", "ARTIFICIAL INTELLIGENCE", "08 / THINK AHEAD"),
}
SHAPES = {
    "python": '<g transform="translate(205 60) rotate(-8 110 80)"><rect width="165" height="112" rx="14" fill="#314e40"/><path d="M25 28h54m-54 18h82m-82 18h50m-50 18h92" stroke="#b7d39c" stroke-width="6" stroke-linecap="round"/><rect x="86" y="74" width="126" height="88" rx="12" fill="#fbf8e7" stroke="#bbcaa0"/><text x="107" y="132" fill="#446149" font-family="monospace" font-size="37" font-weight="bold">&lt;/&gt;</text></g>',
    "django": '<g transform="translate(190 56) rotate(7 100 80)"><rect width="210" height="135" rx="14" fill="#255346"/><rect x="14" y="15" width="182" height="17" rx="4" fill="#ffffff13"/><circle cx="25" cy="24" r="3" fill="#bbceaf"/><circle cx="36" cy="24" r="3" fill="#e5be87"/><text x="31" y="104" fill="#d6e8c7" font-family="Georgia" font-size="68" font-weight="bold">dj.</text><path d="M124 60h46m-46 16h31m-31 16h42" stroke="#88b196" stroke-width="5" stroke-linecap="round"/></g>',
    "flask": '<g transform="translate(251 36) rotate(-10 60 100)"><path d="M45 22h50M51 22v54L11 150q-9 22 13 24h115q22-2 13-24l-43-74V22" fill="#faf4e9" stroke="#8e725f" stroke-width="5"/><path d="M39 112l-21 43q-4 9 8 9h111q10 0 6-10l-23-42Z" fill="#b58d73"/><circle cx="64" cy="139" r="7" fill="#ecd9bf"/><circle cx="93" cy="123" r="5" fill="#ecd9bf"/><circle cx="81" cy="96" r="4" fill="#b58d73"/></g>',
    "machine-learning": '<g stroke="#9e91b5" stroke-width="3"><path d="M218 66l91 51-91 61m0-112 0 112m91-61 87-51m-87 51 87 61m-178-112 178 112m-178 0 178-112" fill="none"/><circle cx="218" cy="66" r="20" fill="#faf7fd"/><circle cx="218" cy="178" r="20" fill="#faf7fd"/><circle cx="309" cy="117" r="30" fill="#796c94"/><circle cx="396" cy="66" r="20" fill="#c6bbdd"/><circle cx="396" cy="178" r="20" fill="#c6bbdd"/></g><path d="M296 117h26m-13-13v26" stroke="#f1e9fc" stroke-width="4"/>',
    "data-science": '<g transform="translate(196 43) rotate(-6 100 80)"><rect width="218" height="156" rx="13" fill="#f7fafb" stroke="#b4cbd6"/><path d="M30 30v100h160" fill="none" stroke="#acc4d0" stroke-width="2"/><rect x="51" y="89" width="25" height="40" rx="4" fill="#90acb9"/><rect x="89" y="64" width="25" height="65" rx="4" fill="#6c93a4"/><rect x="127" y="39" width="25" height="90" rx="4" fill="#355f70"/><path d="M52 71l48-29 51-19" stroke="#d69e69" stroke-width="4" fill="none"/><circle cx="52" cy="71" r="5" fill="#d69e69"/><circle cx="100" cy="42" r="5" fill="#d69e69"/><circle cx="151" cy="23" r="5" fill="#d69e69"/></g>',
    "nlp": '<g transform="translate(178 51) rotate(-5 115 70)"><path d="M16 0h165q16 0 16 16v81q0 16-16 16H68l-35 23v-23H16Q0 113 0 97V16Q0 0 16 0" fill="#fbf5e8" stroke="#d4b598"/><path d="M27 28h110m-110 21h139m-139 21h81" stroke="#af9173" stroke-width="7" stroke-linecap="round"/><rect x="116" y="73" width="125" height="95" rx="14" fill="#a67a57"/><text x="144" y="138" fill="#fceede" font-family="Georgia" font-size="47">Aa</text></g>',
    "data-mining": '<g transform="translate(233 39)"><path d="M68 4l82 64-82 123L-14 68Z" fill="#a8be8d" stroke="#739363" stroke-width="3"/><path d="M-14 68h164M68 4 34 68l34 123 34-123Z" fill="#c5d5ac" stroke="#739363" stroke-width="3"/><path d="m68 4 34 64-34 123" fill="none" stroke="#edf2df" stroke-width="3"/></g><path d="M177 69h15m-8-8v16M403 165h23m-12-12v24" stroke="#7e986c" stroke-width="3"/>',
    "ai": '<g transform="translate(305 120)"><ellipse rx="100" ry="55" fill="none" stroke="#baa8cb" stroke-width="2"/><ellipse rx="100" ry="55" fill="none" stroke="#baa8cb" stroke-width="2" transform="rotate(60)"/><ellipse rx="100" ry="55" fill="none" stroke="#baa8cb" stroke-width="2" transform="rotate(120)"/><circle r="48" fill="#816a96"/><path d="M-22 0h44M0-22v44M-15-15l30 30M-15 15l30-30" stroke="#eee6f8" stroke-width="6"/><circle cx="100" cy="0" r="8" fill="#c59d71"/><circle cx="-50" cy="-87" r="8" fill="#a18bb6"/><circle cx="-50" cy="87" r="8" fill="#a18bb6"/></g>',
}
for name, (background, ink, title, subtitle) in PALETTES.items():
    title, subtitle = escape(title), escape(subtitle)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360" role="img" aria-label="{title} course illustration">
    <rect width="640" height="360" fill="{background}"/>
    <defs><pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0v32" fill="none" stroke="{ink}" stroke-opacity=".06"/></pattern></defs><rect width="640" height="360" fill="url(#grid)"/>
    <circle cx="306" cy="122" r="126" fill="none" stroke="{ink}" stroke-opacity=".12"/>
    <g transform="translate(2 14)">{SHAPES[name]}</g>
    <text x="32" y="283" font-family="Arial,sans-serif" font-size="11" letter-spacing="2" fill="{ink}" opacity=".8">{subtitle}</text>
    <text x="32" y="322" font-family="Arial,sans-serif" font-size="27" font-weight="bold" letter-spacing="-.5" fill="{ink}">{title}</text>
    <path d="M567 54v32m-16-16h32m-27-11 22 22m-22 0 22-22" stroke="{ink}" stroke-opacity=".6" stroke-width="4"/>
    <text x="556" y="320" font-family="Arial,sans-serif" font-size="12" fill="{ink}" opacity=".5">luma.</text></svg>'''
    (ROOT / f"{name}.svg").write_text(svg, encoding="utf-8")
    compact = svg.replace(
        'width="640" height="360" viewBox="0 0 640 360"',
        'width="320" height="320" viewBox="160 0 300 245"',
    )
    (ROOT / f"{name}-compact.svg").write_text(compact, encoding="utf-8")
print(f"Built {len(PALETTES)} original SVG course covers.")
