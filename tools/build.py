import json, math, re, html
import numpy as np
from PIL import Image
from lxml import etree

BASE = '/home/claude/kal'
ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
SW, SH = 9753600, 14630400          # slide size in EMU (2:3)
PT_W = SW / 12700                   # slide width in points (768)

def cqw(pt):                        # points -> % of poster width (container query units)
    return round(pt / PT_W * 100, 4)

J = json.load(open(f'{BASE}/bgpieces.json'))
CX, CY = J['cx'], J['cy']           # mandala centre, fraction of width / height
ASPECT = SH / SW                    # 1.5

rels = {r.get('Id'): r.get('Target') for r in etree.parse(f'{BASE}/src/ppt/slides/_rels/slide1.xml.rels').getroot()}
root = etree.parse(f'{BASE}/src/ppt/slides/slide1.xml').getroot()
tree = root.find('.//p:spTree', ns)

def radial(gx, gy):
    """unit vector from mandala centre to point (in width units), its length, angle (deg, 0 = up, clockwise)"""
    vx, vy = gx - CX, (gy - CY) * ASPECT
    r = math.hypot(vx, vy) or 1e-6
    ang = (math.degrees(math.atan2(vx, -vy)) + 360) % 360
    return vx / r, vy / r, r, ang

def pc(cls, kind, x, y, w, h, src, gx, gy, extra=''):
    dx, dy, r, ang = radial(gx, gy)
    style = f'left:{x*100:.3f}%;top:{y*100:.3f}%;width:{w*100:.3f}%;height:{h*100:.3f}%'
    return (f'<div class="pc {cls}" data-k="{kind}" data-dx="{dx:.4f}" data-dy="{dy:.4f}" data-r="{r:.4f}" '
            f'data-a="{ang:.1f}" data-gx="{gx:.4f}" data-gy="{gy:.4f}"{extra} style="{style}">'
            f'<div class="pr"><div class="pm"><img src="a/{src}" alt="" decoding="async"></div></div></div>')

# ---------- background pieces, grouped by ring ----------
groups = {'core': [], 'ring': [], 'outer': []}
for p in J['pieces']:
    rpx = p['r']                                   # px at 1024-wide scale
    g = 'core' if rpx < 125 else 'ring' if rpx < 265 else 'outer'
    if p['area'] > 30000: kind = 'fig'
    elif p['area'] < 450 and p['dark'] and p['el'] < 2.2: kind = 'dot'
    elif p['gold']: kind = 'gold'
    else: kind = 'shard'
    groups[g].append(pc('bg', kind, p['x'], p['y'], p['w'], p['h'], p['f'], p['gx'], p['gy']))

# ---------- overlay pieces (slide order) and text ----------
ov, txt, T = [], [], {}
FIGS = {'Freeform 11', 'Freeform 13', 'Freeform 19', 'Freeform 61', 'Freeform 63'}
k = 0
for sp in tree.findall('p:sp', ns):
    name = sp.find('.//p:cNvPr', ns).get('name')
    off = sp.find('.//a:xfrm/a:off', ns); ext = sp.find('.//a:xfrm/a:ext', ns)
    X, Y, Wd, Ht = int(off.get('x')), int(off.get('y')), int(ext.get('cx')), int(ext.get('cy'))
    x, y, w, h = X / SW, Y / SH, Wd / SW, Ht / SH
    blip = sp.find('.//a:blip', ns)
    if blip is not None:
        media = rels[blip.get('{%s}embed' % ns['r'])].split('/')[-1]
        if media == 'image1.png':
            continue                                # the background, already cut into pieces
        im = Image.open(f'{BASE}/src/ppt/media/{media}').convert('RGBA')
        a = np.asarray(im)[..., 3].astype(float) / 255
        ys, xs = np.nonzero(a > 0.3)
        if len(xs) == 0:
            ys, xs = np.nonzero(a > 0.02)
        fx, fy = xs.mean() / im.width, ys.mean() / im.height
        gx, gy = x + fx * w, y + fy * h
        rgb = np.asarray(im)[..., :3][a > 0.5]
        mcol = rgb.mean(0) if len(rgb) else np.array([255, 255, 255])
        cover = (a > 0.5).mean()
        fname = f'o{k:02d}.webp'; k += 1
        im.save(f'{BASE}/site/a/{fname}', quality=90, method=6)
        if name == 'Freeform 72': kind = 'rule'
        elif name in FIGS: kind = 'fig'
        elif 4600000 <= X <= 4950000 and Wd <= 400000: kind = 'axis'
        elif mcol.mean() > 225 and cover < 0.5: kind = 'haze'
        elif mcol[0] > mcol[2] + 15: kind = 'gold'
        else: kind = 'shard'
        ov.append(pc('ov', kind, x, y, w, h, fname, gx, gy, f' data-n="{name}"'))
        continue
    body = sp.find('p:txBody', ns)
    if body is None:
        continue
    para = body.find('a:p', ns)
    run = para.find('a:r', ns); rp = run.find('a:rPr', ns)
    t = run.find('a:t', ns).text
    if t == 'KELIDOSCOPE':
        t = 'KALEIDOSCOPE'                      # event renamed
    sz = int(rp.get('sz')) / 100; spc = int(rp.get('spc', '0')) / 100
    col = rp.find('.//a:srgbClr', ns).get('val')
    face = rp.find('a:latin', ns).get('typeface')
    lns = para.find('.//a:lnSpc/a:spcPts', ns)
    lh = int(lns.get('val')) / 100 if lns is not None else sz * 1.2
    weight = 700 if 'Bold' in face else 400
    role = {'FOSA': 'fosa', 'KALEIDOSCOPE': 'title', 'CULTURE IN MOTION': 'tag', 'X': 'x'}.get(t, 'word')
    T.setdefault(role, []).append(dict(t=t, x=x, y=y, w=w, sz=sz, spc=spc, lh=lh, weight=weight, col=col))

# ---- the poster's type as ONE flowing stack (lines push each other instead of overlapping
#      when a phone enlarges small text), placed exactly where the PPT put each line ----
def chars(t):
    return ''.join(f'<span class="ch">{html.escape(c) if c != " " else "&nbsp;"}</span>' for c in t)
def font(d, minpx=None):
    fs = f'{cqw(d["sz"])}cqw' if minpx is None else f'max({cqw(d["sz"])}cqw,{minpx}px)'
    return f'font-size:{fs};letter-spacing:{cqw(d["spc"])}cqw;line-height:{cqw(d["lh"])}cqw;font-weight:{d["weight"]};color:#{d["col"]}'
F, Ti, Tg = T['fosa'][0], T['title'][0], T['tag'][0]
row = sorted(T['word'] + T['x'], key=lambda d: d['x'])
top = lambda d: d['y'] * 150                      # % of poster height -> cqw (poster is 2:3)
gap1 = top(Ti) - (top(F) + cqw(F['lh']))
gap2 = top(Tg) - (top(Ti) + cqw(Ti['lh']))
gap3 = top(row[0]) - (top(Tg) + cqw(Tg['lh']))
cx = (F['x'] + F['w'] / 2) * 100                  # the poster's own centre axis for the type
words = ''.join(
    (f'<span class="tx x" aria-hidden="true">{chars(d["t"])}</span>' if d['t'] == 'X'
     else f'<span class="tx word">{chars(d["t"])}</span>') for d in row)
wd = row[0]
txt.append(
    f'<div class="txstack" style="top:{F["y"]*100:.3f}%;left:0;width:{2*cx:.3f}%">'
    f'<p class="tx fosa" aria-label="FOSA" style="{font(F)}"><span aria-hidden="true">{chars(F["t"])}</span></p>'
    f'<h1 class="tx title" aria-label="{html.escape(Ti["t"].title())}" style="{font(Ti)};margin-top:{gap1:.3f}cqw"><span aria-hidden="true">{chars(Ti["t"])}</span></h1>'
    f'<p class="tx tag" aria-label="{html.escape(Tg["t"].title())}" style="{font(Tg, 9)};margin-top:{gap2:.3f}cqw"><span aria-hidden="true">{chars(Tg["t"])}</span></p>'
    f'<p class="words" aria-label="Performance, exchange, community" style="{font(wd, 8)};margin-top:{gap3:.3f}cqw">{words}</p>'
    f'</div>')

markup = (
    '<div class="L" id="Ldust"><div class="zm"><img class="dust" src="a/dust.webp" alt=""></div></div>\n'
    '<div class="L rot" id="Louter"><div class="zm"><div class="spin">' + '\n'.join(groups['outer']) + '</div></div></div>\n'
    '<div class="L rot" id="Lring"><div class="zm"><div class="spin">' + '\n'.join(groups['ring']) + '</div></div></div>\n'
    '<div class="L rot" id="Lcore"><div class="zm"><div class="spin">' + '\n'.join(groups['core']) + '</div></div></div>\n'
    '<div class="L" id="Lov"><div class="zm">' + '\n'.join(ov) + '</div></div>\n'
    '<div class="L" id="Lwing"><div class="zm"></div></div>\n'
    '<div class="L" id="Ltxt"><div class="zm">' + '\n'.join(txt) + '</div></div>'
)
# rosette for the About section: the same core + ring pieces, re-used as a turnable kaleidoscope
def rp(group):
    out = []
    for p in J['pieces']:
        rpx = p['r']
        g = 'core' if rpx < 125 else 'ring' if rpx < 265 else None
        if g != group: continue
        dx, dy, r, ang = radial(p['gx'], p['gy'])
        out.append(f'<img class="rp" src="a/{p["f"]}" alt="" data-dx="{dx:.3f}" data-dy="{dy:.3f}" data-r="{r:.3f}" '
                   f'style="left:{p["x"]*100:.3f}%;top:{p["y"]*100:.3f}%;width:{p["w"]*100:.3f}%;height:{p["h"]*100:.3f}%">')
    return '\n'.join(out)
CW = 1 / (2 * 0.30)                     # copy width relative to the rosette window
rosette = (f'<div class="rcopy" style="width:{CW*100:.2f}%;height:{CW*150:.2f}%;left:{(0.5-CX*CW)*100:.2f}%;top:{(0.5-CY*CW*1.5)*100:.2f}%">'
           '<div class="rspin" id="rRing">' + rp('ring') + '</div><div class="rspin" id="rCore">' + rp('core') + '</div></div>')
bg = 'rgb({},{},{})'.format(*J['bg'])
tpl = open('/home/claude/template.html').read()
out = (tpl.replace('{{MARKUP}}', markup).replace('{{ROSETTE}}', rosette).replace('{{BG}}', bg).replace('{{CXF}}', f'{CX:.5f}').replace('{{CYF}}', f'{CY:.5f}').replace('{{FORM_TICKET}}', 'https://docs.google.com/forms/d/1T8xE7zlN29RPpQWMausfICLrCpUhzcIcdfh2Johy-vs/viewform').replace('{{FORM_PERFORM}}', 'https://docs.google.com/forms/d/1P8v3C2DItpqaBAdwlAEhp1DGRsNni7nGr9lcNxcrH_w/viewform')
          .replace('{{CX}}', f'{CX*100:.3f}%').replace('{{CY}}', f'{CY*100:.3f}%'))
open(f'{BASE}/site/index.html', 'w').write(out)
print('bg pieces', {g: len(v) for g, v in groups.items()}, 'overlays', len(ov), 'text', len(txt))
kinds = re.findall(r'data-k="(\w+)"', markup)
print({k_: kinds.count(k_) for k_ in set(kinds)})
