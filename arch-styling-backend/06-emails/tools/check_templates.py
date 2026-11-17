#!/usr/bin/env python3
"""Template checks for the ARCH emails. Standard library only.
Run from the package folder:  python3 tools/check_templates.py
Exits with 1 if any check fails."""
import re, glob, os, sys, csv
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
def lum(h):
    c = [int(h[i:i+2], 16)/255 for i in (1, 3, 5)]
    c = [x/12.92 if x <= 0.03928 else ((x+0.055)/1.055)**2.4 for x in c]
    return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
def ratio(a, b):
    x, y = sorted((lum(a), lum(b)), reverse=True); return (x+0.05)/(y+0.05)
GROUND, MUTED = '#FAF6F0', '#666666'
fails = []
def check(ok, id, msg):
    if not ok: fails.append((id, msg))
check(ratio(MUTED, GROUND) >= 5.3, 'colour', 'muted on ground below 5.3:1')
tok = lambda s: set(re.findall(r'\{\{(\w+)\}\}', s))
with open(os.path.join(PKG, 'ARCH_Email_Variables.csv'), encoding='utf-8') as f:
    known = {r['Token'] for r in csv.DictReader(f)}
files = sorted(glob.glob(os.path.join(PKG, 'emails', 'html', '*.html')))
for f in files:
    id = os.path.basename(f)[:-5]; h = open(f, encoding='utf-8').read()
    tp = os.path.join(PKG, 'emails', 'text', id + '.txt')
    check(os.path.exists(tp), id, 'no plain-text version')
    t = open(tp, encoding='utf-8').read() if os.path.exists(tp) else ''
    hb = re.sub(r'<title>.*?</title>', '', h, flags=re.S)   # the title repeats the subject line, which is not part of the text body
    th, tt = tok(hb) - {'asset_base_url'}, tok(t)
    check(th <= tt, id, 'tokens in HTML missing from text: %s' % sorted(th - tt))
    check(tt <= tok(hb) | {'privacy_url'}, id, 'tokens in text missing from HTML: %s' % sorted(tt - tok(h)))
    check((tok(h) | tt) <= {k.strip('{}') for k in known}, id, 'token not in the variables reference')
    hrefs = set(re.findall(r'href="((?:https?://|mailto:|\{\{)[^"]+)"', h))
    for u in hrefs:
        u2 = u.replace('mailto:', '')
        check(u2 in t, id, 'link missing from text version: ' + u)
    check(not re.search(r'<[a-z/][^>]*>|&nbsp;|&amp;', t), id, 'HTML left in text version')
    check(all(len(l) <= 78 for l in t.splitlines()), id, 'text line over 78 characters')
    check(not re.search(r'display\s*:\s*(inline-)?(flex|grid)|\bflex-|\bgrid-', h), id, 'flexbox or grid used')
    check(not re.search(r'float\s*:|position\s*:\s*(absolute|fixed)', h), id, 'float or absolute positioning used')
    check(all(int(w) <= 600 for w in re.findall(r'(?:max-)?width\s*[:=]\s*"?(\d+)(?:px)?', h)), id, 'a width above 600')
    check('<table' in h and h.count('<table') >= 2, id, 'layout is not table based')
    check(len(h.encode()) < 102400, id, 'HTML over 100 KB (Gmail clips at 102 KB)')
    # #888888 and the dark ground may appear only inside the dark-mode rules
    body = re.sub(r'<style type="text/css">.*?</style>', '', h, flags=re.S)
    check('#888888' not in body.upper(), id, '#888888 used outside the dark-mode rules')
    style = re.search(r'<style type="text/css">(.*?)</style>', h, re.S)
    css = style.group(1) if style else ''
    dark = re.search(r'@media \(prefers-color-scheme: dark\)\{.*?\n  \}\n', css, re.S)
    check('#888888' not in (css.replace(dark.group(0), '') if dark else css).upper(), id, '#888888 in a rule that is not inside the dark-mode media query')
    # light-lock: color-scheme and supported-color-schemes declared light, Outlook pins hold the light colours
    check(re.search(r'<meta name="color-scheme" content="light">', h) is not None, id, 'meta color-scheme is not exactly "light"')
    check(re.search(r'<meta name="supported-color-schemes" content="light">', h) is not None, id, 'meta supported-color-schemes is not exactly "light"')
    check(':root{color-scheme:light;supported-color-schemes:light;}' in css, id, 'no :root color-scheme light rule')
    for sel, val in (('[data-ogsb] body,[data-ogsb] .arch-bg', '#FAF6F0'), ('[data-ogsc] .arch-ink,[data-ogsc] .arch-ink a', '#0A0A0A'), ('[data-ogsc] .arch-muted,[data-ogsc] .arch-muted a', '#666666'), ('[data-ogsb] .arch-btn a', '#C9A84C')):
        check(re.search(re.escape(sel) + r'\{[^}]*' + val, css, re.I) is not None, id, 'Outlook override missing or not light: ' + sel)
    check(re.search(r'color\s*:\s*#666666', h) is not None and not re.search(r'color\s*:\s*#(?:777777|888888|999999|AAAAAA)', body, re.I), id, 'muted text colour is not #666666')
    check('prefers-color-scheme: dark' in h, id, 'no dark-mode media query')
    check(re.search(r'<title>.+</title>', h) is not None, id, 'no title')
print('Templates checked: %d' % len(files))
print('Muted #666666 on #FAF6F0: %.2f:1' % ratio(MUTED, GROUND))
if fails:
    for id, m in fails: print('FAIL', id, '-', m)
    sys.exit(1)
print('All checks passed.')
