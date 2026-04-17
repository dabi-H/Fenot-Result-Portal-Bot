# pdf_service.py
# 2-page landscape A4 PDF — 4-panel folded report card
# Minimal palette: navy, white, gold, and warm off-whites only.
# Converted from pdfService.js (PDFKit) → Python (ReportLab)

import os
import math
import time
import glob
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pytz import timezone
from ethiopian_date import EthiopianDateConverter

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))  # root/
TEMP_DIR   = os.path.join(PROJECT_DIR, 'src', 'temp')
FONTS_DIR  = os.path.join(PROJECT_DIR, 'src', 'fonts')
ASSETS_DIR = os.path.join(PROJECT_DIR, 'src', 'assets')

REGULAR_FONT = os.path.join(FONTS_DIR, 'NotoSansEthiopic-Regular.ttf')
BOLD_FONT    = os.path.join(FONTS_DIR, 'NotoSansEthiopic-Bold.ttf')

LEFT_LOGO  = os.path.join(ASSETS_DIR, 'left-top.png')
RIGHT_LOGO = os.path.join(ASSETS_DIR, 'right-top.png')
BACKGROUND = os.path.join(ASSETS_DIR, 'backgroung.png')
CROSS_IMG  = os.path.join(ASSETS_DIR, 'cross.png')

for d in [TEMP_DIR, FONTS_DIR, ASSETS_DIR]:
    os.makedirs(d, exist_ok=True)

if not os.path.exists(REGULAR_FONT):
    raise FileNotFoundError('Missing font: NotoSansEthiopic-Regular.ttf in src/fonts/')

# Register fonts once
pdfmetrics.registerFont(TTFont('Regular', REGULAR_FONT))
pdfmetrics.registerFont(TTFont('Bold', BOLD_FONT if os.path.exists(BOLD_FONT) else REGULAR_FONT))

# ── Palette ───────────────────────────────────────────────────────────────────
C = {
    'navy':       '#1B2A5E',
    'navyMid':    '#2E4499',
    'gold':       '#C9A84C',
    'goldLight':  '#E8C97A',
    'border':     '#5C4033',
    'pageBg':     '#FAF8F3',
    'rowA':       '#F0EEE8',
    'rowB':       '#FFFFFF',
    'fieldBg':    '#EDEAE2',
    'divider':    '#D5CFC0',
    'textDark':   '#1A1A1A',
    'textMid':    '#4A4A4A',
    'textMuted':  '#7A7670',
    'white':      '#FFFFFF',
}

# A4 landscape dimensions (points)
LW, LH = A4[1], A4[0]   # 841.89 x 595.28


# ── Colour helper ─────────────────────────────────────────────────────────────
def hex_to_rgb(h):
    """Convert '#RRGGBB' to (r, g, b) floats 0-1."""
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def set_fill(c, key):
    c.setFillColorRGB(*hex_to_rgb(C[key]))

def set_stroke(c, key):
    c.setStrokeColorRGB(*hex_to_rgb(C[key]))

def set_fill_hex(c, hex_val):
    c.setFillColorRGB(*hex_to_rgb(hex_val))

def set_stroke_hex(c, hex_val):
    c.setStrokeColorRGB(*hex_to_rgb(hex_val))


# ── Ethiopian Calendar ────────────────────────────────────────────────────────
def is_gregorian_leap(y):
    return (y % 400 == 0) or (y % 100 != 0 and y % 4 == 0)

def to_ethiopian_date(dt):
    gY, gM, gD = dt.year, dt.month, dt.day
    def utc_days(y, m, d):
        # days since epoch
        from datetime import date
        return (date(y, m, d) - date(1970, 1, 1)).days

    prev_leap = is_gregorian_leap(gY - 1)
    eth_ny = utc_days(gY, 9, 12 if prev_leap else 11)
    cur    = utc_days(gY, gM, gD)

    if cur >= eth_ny:
        eth_year = gY - 7
        days = cur - eth_ny
    else:
        eth_year = gY - 8
        p_leap = is_gregorian_leap(gY - 2)
        prev_ny = utc_days(gY - 1, 9, 12 if p_leap else 11)
        days = cur - prev_ny

    eth_month = min(days // 30 + 1, 13)
    eth_day   = (days % 30) + 1
    return {'year': eth_year, 'month': eth_month, 'day': eth_day}

def fmt_eth(e):
    return f"{e['day']:02d}/{e['month']:02d}/{e['year']}"


# ── Drawing primitives ────────────────────────────────────────────────────────

def panel_border(c, x, y, w, h):
    """Brown outer + gold inner rounded border."""
    c.saveState()
    set_stroke_hex(c, C['border'])
    c.setLineWidth(3.5)
    c.roundRect(x, y, w, h, 10, stroke=1, fill=0)
    set_stroke_hex(c, C['gold'])
    c.setLineWidth(1)
    c.roundRect(x+5, y+5, w-10, h-10, 7, stroke=1, fill=0)
    c.restoreState()


def rule(c, x1, x2, y, color_key=None, color_hex=None, lw=0.6):
    c.saveState()
    if color_hex:
        set_stroke_hex(c, color_hex)
    else:
        set_stroke_hex(c, C[color_key or 'divider'])
    c.setLineWidth(lw)
    c.line(x1, y, x2, y)
    c.restoreState()


def fill_rect(c, x, y, w, h, fill_hex, stroke_hex=None, lw=0.5, r=0):
    """Draw a filled (optionally rounded) rectangle."""
    c.saveState()
    set_fill_hex(c, fill_hex)
    if stroke_hex:
        set_stroke_hex(c, stroke_hex)
        c.setLineWidth(lw)
        if r > 0:
            c.roundRect(x, y, w, h, r, stroke=1, fill=1)
        else:
            c.rect(x, y, w, h, stroke=1, fill=1)
    else:
        c.setLineWidth(0)
        if r > 0:
            c.roundRect(x, y, w, h, r, stroke=0, fill=1)
        else:
            c.rect(x, y, w, h, stroke=0, fill=1)
    c.restoreState()


def gold_bar(c, cx, y, w):
    bw = w * 0.36
    fill_rect(c, cx - w * 0.18, y, bw, 2.5, C['gold'], r=1)


def draw_text(c, text, x, y, font, size, color_hex, width=None, align='left'):
    """
    Draw text at PDF coordinate (x, y) — note ReportLab y=0 is bottom.
    We work in a flipped coordinate system (y from top), so callers pass
    top-origin y and we convert inside draw_text.
    width/align used for centre-aligned text.
    """
    c.saveState()
    c.setFont(font, size)
    set_fill_hex(c, color_hex)
    if align == 'center' and width:
        c.drawCentredString(x + width / 2, y, text)
    elif align == 'right' and width:
        c.drawRightString(x + width, y, text)
    else:
        c.drawString(x, y, text)
    c.restoreState()


# ReportLab's canvas uses bottom-left origin.
# We use a helper to flip y coordinates (top-origin → bottom-origin).
def fy(y, page_h=LH):
    """Flip y: convert top-origin y to ReportLab bottom-origin y."""
    return page_h - y


def wrap_text(c, text, x, top_y, width, font, size, color_hex, line_gap=1.5, page_h=LH):
    """
    Draw multi-line wrapped text. Returns the bottom y (top-origin) after last line.
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth
    c.saveState()
    c.setFont(font, size)
    set_fill_hex(c, color_hex)

    words = text.split()
    lines = []
    current = ''
    for word in words:
        test = (current + ' ' + word).strip()
        if stringWidth(test, font, size) <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_h = size + line_gap
    y = top_y
    for line in lines:
        c.drawString(x, fy(y + size, page_h), line)
        y += line_h

    c.restoreState()
    return y   # top-origin y after last line


def text_height(text, width, font, size, line_gap=1.5):
    """Estimate height of wrapped text block."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = text.split()
    lines = 0
    current = ''
    for word in words:
        test = (current + ' ' + word).strip()
        if stringWidth(test, font, size) <= width:
            current = test
        else:
            lines += 1
            current = word
    if current:
        lines += 1
    return lines * (size + line_gap)


def field_row(c, label, value, x, top_y, w, ls=8, vs=10, page_h=LH):
    """Label above a filled box. Returns new top_y after field."""
    draw_text(c, label, x, fy(top_y + ls, page_h), 'Regular', ls, C['textMuted'])
    fy_box = top_y + ls + 3
    fill_rect(c, x, fy(fy_box + 20, page_h), w, 20, C['fieldBg'], C['divider'], 0.5, 3)
    if value:
        draw_text(c, value, x + 6, fy(fy_box + 15, page_h), 'Bold', vs, C['navy'])
    return fy_box + 24


def draw_image(c, path, x, top_y, w, h, page_h=LH):
    if os.path.exists(path):
        c.drawImage(path, x, fy(top_y + h, page_h), width=w, height=h, mask='auto')


# ── Utility ───────────────────────────────────────────────────────────────────
def get_grade(s):
    if s >= 85: return 'A'
    if s >= 75: return 'B'
    if s >= 65: return 'C'
    if s >= 50: return 'D'
    return 'F'


# ── PAGE 1 ────────────────────────────────────────────────────────────────────
def draw_page1(c, student, W, H):
    mid = W / 2
    pad = 30
    eth_tz = timezone('Africa/Addis_Ababa')
    now = datetime.now(eth_tz)
    edc = EthiopianDateConverter()
    et_year, et_month, et_day = edc.to_ethiopian(now.year, now.month, now.day)
    ec_date = f"{et_day}/{et_month}/{et_year}"

    # Page background
    fill_rect(c, 0, fy(H, H), W, H, C['pageBg'])

    panel_border(c, 10, fy(H-10, H), mid-15, H-20)
    panel_border(c, mid+5, fy(H-10, H), mid-15, H-20)

    # ── LEFT PANEL ────────────────────────────────────────────────────────────
    lx  = 18 + pad
    lw  = mid - 15 - pad * 2 - 8
    lcx = 18 + (mid - 15) / 2
    y   = 44   # top-origin

    # Grade scale header
    fill_rect(c, lx, fy(y+26, H), lw, 26, C['navy'], r=4)
    draw_text(c, 'የነጥብ አያያዝ', lx, fy(y+17, H), 'Bold', 10, C['white'], width=lw, align='center')
    y += 30

    grades = [
        'ከ100 እስከ 85 — እጅግ በጣም ጥሩ  (A)',
        'ከ84 እስከ 75  — በጣም ጥሩ  (B)',
        'ከ74 እስከ 65  — ደህና  (C)',
        'ከ64 እስከ 50  — መካከለኛ  (D)',
    ]
    for i, g in enumerate(grades):
        gy = y + i * 22
        fill = C['rowA'] if i % 2 == 0 else C['rowB']
        fill_rect(c, lx, fy(gy+20, H), lw, 20, fill, C['divider'], 0.4, 2)
        draw_text(c, g, lx+10, fy(gy+14, H), 'Regular', 9, C['textDark'])
    y += len(grades) * 22 + 20

    # Logo centred
    logo_size = 90
    draw_image(c, LEFT_LOGO, lcx - logo_size/2, y, logo_size, logo_size, H)
    y += logo_size + 8

    draw_text(c, 'ፍኖተ ብርሃን', 18, fy(y+12, H), 'Bold', 12, C['navy'], width=mid-15, align='center')
    y += 15
    draw_text(c, 'ሰ/ት/ቤት', 18, fy(y+9, H), 'Regular', 9, C['textMuted'], width=mid-15, align='center')
    y += 10
    gold_bar(c, lcx, fy(y+2.5, H), lw)
    y += 16

    # Instructions header
    fill_rect(c, lx, fy(y+22, H), lw, 22, C['navy'], r=4)
    draw_text(c, 'ማሳሰቢያ', lx, fy(y+13, H), 'Bold', 9, C['white'], width=lw, align='center')
    y += 28

    bullets = [
        'ይህ የትምህርት ውጤት መግለጫ ካርድ በዓመት አንዴ በትምህርት ማብቂያ ላይ ለተማሪው/ዋ ይሰጣል፡፡',
        'ካርዱ የደብሩ አስተዳዳሪ ፊርማና ማኅተም፣ የሰ/ት/ቤቱ ሊቀ መንበር ፊርማ እና የትምህርት ክፍሉ ተጠሪ ፊርማ ካልሰጠበት ዋጋ አይኖረውም፡፡',
    ]
    for b in bullets:
        # Small square navy bullet
        fill_rect(c, lx, fy(y+4+8, H), 8, 8, C['navy'], r=2)
        bottom_y = wrap_text(c, b, lx+14, y, lw-16, 'Regular', 8.5, C['textMid'], line_gap=1.5, page_h=H)
        y = bottom_y + 12

    # Contact block
    ct_y = H - 115
    rule(c, lx, lx+lw, fy(ct_y, H), color_hex=C['gold'], lw=1.2)
    draw_text(c, 'የሰ/ት/ቤቱ አድራሻ', lx, fy(ct_y+15, H), 'Bold', 8.5, C['navy'])
    draw_text(c, 'ሽገር ከተማ ፣ ቡራዩ ክፍል ከተማ ፣ ገፈርሳ ቡራዩ ወረዳ', lx, fy(ct_y+28, H), 'Regular', 8, C['textMid'])
    for i, contact in enumerate(['ስልክ :', 'ኢሜይል : finotebirhan1021@gmail.com', 'ቴሌግራም : @fenotebrehan']):
        draw_text(c, contact, lx, fy(ct_y+42+i*12, H), 'Regular', 7.5, C['textMuted'])

    # ── RIGHT PANEL ───────────────────────────────────────────────────────────
    rx  = mid + 5 + pad
    rw  = mid - 15 - pad * 2 - 8
    rcx = mid + 5 + (mid - 15) / 2
    y   = 40

    # Cross
    if os.path.exists(CROSS_IMG):
        draw_image(c, CROSS_IMG, rcx-18, y, 36, 36, H)
    else:
        c.saveState()
        set_stroke_hex(c, C['textDark'])
        c.setLineWidth(3.5)
        c.line(rcx, fy(y+4, H), rcx, fy(y+36, H))
        c.line(rcx-14, fy(y+17, H), rcx+14, fy(y+17, H))
        c.restoreState()
    y += 46

    draw_text(c, 'በኢትዮጵያ ኦርቶዶክስ ተዋሕዶ ቤተ ክርስቲያን', mid+5, fy(y+9.5, H), 'Bold', 9.5, C['textDark'], width=mid-10, align='center')
    y += 14
    draw_text(c, 'የሰ/ት/ቤቶች ማደራጃ መምሪያ ሰ/ት/ቤቶች አንድነት', mid+5, fy(y+9, H), 'Regular', 9, C['textMid'], width=mid-10, align='center')
    y += 18
    gold_bar(c, rcx, fy(y+2.5, H), rw)
    y += 12

    # School name band
    fill_rect(c, rx, fy(y+40, H), rw, 40, C['navy'], r=4)
    draw_text(c, 'የሽገር ከተማ ሀገረ ስብከት የቡራዩ ጼደንያ ሰመኝ ቅድስት ድንግል', rx+6, fy(y+17, H), 'Bold', 9.5, C['white'], width=rw-12, align='center')
    draw_text(c, 'ማርያም ገዳም ፍኖተ ብርሃን ሰ/ት/ቤት', rx+6, fy(y+33, H), 'Bold', 9.5, C['goldLight'], width=rw-12, align='center')
    y += 48

    # Two logos
    lg_w = 68
    draw_image(c, LEFT_LOGO,  rx,          y, lg_w, lg_w, H)
    draw_image(c, RIGHT_LOGO, rx+rw-lg_w,  y, lg_w, lg_w, H)
    y += lg_w + 10

    # Bible verse box
    fill_rect(c, rx, fy(y+36, H), rw, 36, C['rowA'], C['divider'], 0.5, 4)
    draw_text(c,
        '"አንተ ግን በተማርክበትና እና በተረዳህበት ነገር ጸንተህ ኑር ፤ ከማን እንደተማርኸው ታወቃለህና::" ፪ጢሞ ፲:፲፩',
        rx+8, fy(y+18, H), 'Regular', 8.5, C['textMid'], width=rw-16, align='center')
    y += 44

    # Card title — gold bar
    fill_rect(c, rx, fy(y+28, H), rw, 28, C['gold'], r=4)
    draw_text(c, 'የትምህርት ውጤት መግለጫ ካርድ', rx, fy(y+16, H), 'Bold', 13, C['navy'], width=rw, align='center')
    y += 36

    # Student fields
    y = field_row(c, 'የተማሪው/ዋ ስም ከነ አያት', student.get('name', ''), rx, y, rw, ls=8, vs=10, page_h=H)
    y += 4
    y = field_row(c, 'የክርስትና ስም', '', rx, y, rw, ls=8, vs=10, page_h=H)
    y += 10

    # Address label block
    y = field_row(c, 'ትምህርቱን የተከታተሉበት አጥቢያ', 'የቡራዩ ጼደንያ ሰመኝ ቅድስት ድንግል ማርያም ገዳም', rx, y, rw, ls=8, vs=8, page_h=H)
    y += 10

    # Address full-width (pre-filled)
    y = field_row(c, 'አድራሻ ከተማ / ወረዳ', 'ሸገር ከተማ, ቡራዩ ክፍል ከተማ', rx, y, rw, ls=8, vs=9, page_h=H)
    y += 4

    # Semester + Class side by side
    hw = (rw - 8) / 2
    field_row(c, 'የትምህርት ዘመን', ec_date,                     rx,       y, hw, ls=8, vs=9, page_h=H)
    field_row(c, 'የክፍሉ ደረጃ',   student.get('class', ''),  rx+hw+8,  y, hw, ls=8, vs=9, page_h=H)


# ── PAGE 2 ────────────────────────────────────────────────────────────────────
def draw_page2(c, student, W, H):
    mid = W / 2
    pad = 28

    # Page background
    fill_rect(c, 0, fy(H, H), W, H, C['pageBg'])

    panel_border(c, 10,    fy(H-10, H), mid-15, H-20)
    panel_border(c, mid+5, fy(H-10, H), mid-15, H-20)

    # ── LEFT PANEL — subject table ────────────────────────────────────────────
    lx      = 18 + pad
    panel_w = mid - 15 - pad * 2 - 8
    col_no  = 34
    col_scr = 66
    col_sub = panel_w - col_no - col_scr
    row_h   = 24
    y       = 32   # top-origin

    # Table header
    fill_rect(c, lx, fy(y+row_h+2, H), panel_w, row_h+2, C['navy'], r=4)
    draw_text(c, 'ተ.ቁ',            lx,                fy(y+row_h-3, H), 'Bold', 8.5, C['white'], width=col_no,  align='center')
    draw_text(c, 'የትምህርት ዓይነት', lx+col_no+4,       fy(y+row_h-3, H), 'Bold', 8.5, C['white'], width=col_sub-8)
    draw_text(c, 'ውጤት ከ100',    lx+col_no+col_sub,  fy(y+row_h-3, H), 'Bold', 8.5, C['white'], width=col_scr,  align='center')
    y += row_h + 4

    entries = list(student.get('subjects', {}).items())
    total       = 0
    valid_count = 0

    for i, (subject, score) in enumerate(entries):
        ry   = y + i * row_h
        fill = C['rowA'] if i % 2 == 0 else C['rowB']
        fill_rect(c, lx, fy(ry+row_h, H), panel_w, row_h, fill, C['divider'], 0.4)

        # Row number
        draw_text(c, str(i+1), lx, fy(ry+row_h-8, H), 'Bold', 9, C['navy'], width=col_no, align='center')

        # Subject name
        draw_text(c, subject, lx+col_no+5, fy(ry+row_h-8, H), 'Regular', 9, C['textDark'])

        # Score cell
        sx = lx + col_no + col_sub + 6
        sw = col_scr - 12
        fill_rect(c, sx, fy(ry+4+row_h-8, H), sw, row_h-8, C['white'], C['divider'], 0.5, 3)
        if score is not None and score != '':
            try:
                s = float(score)
                total += s
                valid_count += 1
            except (ValueError, TypeError):
                pass
            draw_text(c, str(score), sx, fy(ry+row_h-9, H), 'Bold', 10, C['navy'], width=sw, align='center')

    y += len(entries) * row_h + 14

    # Gold rule
    rule(c, lx, lx+panel_w, fy(y, H), color_hex=C['gold'], lw=1.5)
    y += 10

    # Grade logic
    avg = round(total / valid_count, 1) if valid_count > 0 else 0.0
    raw_grade = student.get('grade')
    if raw_grade is not None and str(raw_grade).strip() != '':
        grade = str(raw_grade)
    elif valid_count > 0:
        grade = get_grade(avg)
    else:
        grade = None

    avg_str = f"{avg:.1f}"

    # Summary rows
    sum_h = 26
    val_w = 80
    lbl_w = panel_w - val_w
    summary = [
        {'label': 'ጠቅላላ ውጤት',   'value': str(int(total)),     'size': 10},
        {'label': 'አማካይ ውጤት',  'value': f'{avg_str}%',       'size': 10},
        {'label': 'ደረጃ',        'value': grade or '—',         'size': 14},
    ]
    for i, row in enumerate(summary):
        sy   = y + i * (sum_h + 4)
        fill = C['rowA'] if i % 2 == 0 else C['rowB']
        fill_rect(c, lx,       fy(sy+sum_h, H), lbl_w, sum_h, fill, C['divider'], 0.4, 3)
        fill_rect(c, lx+lbl_w, fy(sy+sum_h, H), val_w, sum_h, C['navy'], r=3)
        draw_text(c, row['label'], lx+8, fy(sy+sum_h-9, H), 'Bold', 9, C['textDark'])
        offset = 5 if i == 2 else 8
        draw_text(c, row['value'], lx+lbl_w, fy(sy+offset+row['size'], H), 'Bold', row['size'], C['white'], width=val_w, align='center')
    y += (sum_h + 4) * 3 + 20

    # Signatures
    sig_base_y = H - 95
    sig_w      = (panel_w - 10) / 2
    rule(c, lx,           lx+sig_w-4,  fy(sig_base_y, H), color_hex=C['textMuted'], lw=0.8)
    rule(c, lx+sig_w+6,   lx+panel_w,  fy(sig_base_y, H), color_hex=C['textMuted'], lw=0.8)
    draw_text(c, 'የሰ/ት/ቤቱ ሊቀ መንበር ስምና ፊርማ',  lx,         fy(sig_base_y+12, H), 'Regular', 7.5, C['textMuted'], width=sig_w-4,  align='center')
    draw_text(c, 'የሰ/ት/ቤቱ ትምህርት ክፍል ተጠሪ ስምና ፊርማ', lx+sig_w+6, fy(sig_base_y+12, H), 'Regular', 7.5, C['textMuted'], width=sig_w-4,  align='center')

    # ── RIGHT PANEL ───────────────────────────────────────────────────────────
    rx  = mid + 5 + pad
    rw  = mid - 15 - pad * 2 - 8
    rcx = mid + 5 + (mid - 15) / 2
    ry  = 32   # top-origin

    # Photo box
    ph_w, ph_h = 88, 108
    ph_x = rx + rw - ph_w
    fill_rect(c, ph_x, fy(ry+ph_h, H), ph_w, ph_h, C['rowA'], C['divider'], 0.8, 4)
    # Dashed inner border
    c.saveState()
    set_stroke_hex(c, C['textMuted'])
    c.setLineWidth(0.5)
    c.setDash(3, 3)
    c.rect(ph_x+6, fy(ry+6+ph_h-12, H), ph_w-12, ph_h-12, stroke=1, fill=0)
    c.restoreState()
    draw_text(c, 'ፎቶ', ph_x, fy(ry+ph_h/2+4, H), 'Regular', 7, C['textMuted'], width=ph_w, align='center')
    ry += ph_h + 22

    # Grade badge — navy circle with gold ring
    badge_sz = 72
    bx = rcx - badge_sz / 2
    fill_rect(c, bx, fy(ry+badge_sz, H), badge_sz, badge_sz, C['navy'], r=badge_sz/2)
    c.saveState()
    set_stroke_hex(c, C['gold'])
    c.setLineWidth(1.5)
    c.circle(rcx, fy(ry+badge_sz/2, H), badge_sz/2+3, stroke=1, fill=0)
    c.restoreState()
    draw_text(c, grade or '—', bx, fy(ry+badge_sz-18, H), 'Bold', 30, C['white'], width=badge_sz, align='center')
    ry += badge_sz + 6

    draw_text(c, 'ደረጃ', rx, fy(ry+8, H), 'Regular', 8, C['textMuted'], width=rw, align='center')
    ry += 18

    # Average
    draw_text(c, f'{avg_str}%', rx, fy(ry+22, H), 'Bold', 22, C['navy'], width=rw, align='center')
    ry += 26
    draw_text(c, 'አማካይ ውጤት', rx, fy(ry+8, H), 'Regular', 8, C['textMuted'], width=rw, align='center')
    ry += 22
    gold_bar(c, rcx, fy(ry+2.5, H), rw * 0.65)
    ry += 16

    # Director & seal signatures
    sp = 20
    rule(c, rx+sp, rx+rw-sp, fy(H-100, H), color_hex=C['textMuted'], lw=0.8)
    draw_text(c, 'የደብሩ አስተዳዳሪ ስምና ፊርማ', rx, fy(H-100+12, H), 'Regular', 8, C['textMuted'], width=rw, align='center')
    rule(c, rx+sp, rx+rw-sp, fy(H-58, H), color_hex=C['textMuted'], lw=0.8)
    draw_text(c, 'የደብሩ ማኅተም', rx, fy(H-58+12, H), 'Regular', 8, C['textMuted'], width=rw, align='center')


# ── Main generator ────────────────────────────────────────────────────────────
def generate_result_pdf(student: dict) -> str:
    """
    Generate a 2-page landscape A4 report card PDF.

    student dict keys:
        id       (str)  — used in filename
        name     (str)  — student full name
        class    (str)  — class/grade level
        address  (str, optional)
        grade    (str/None, optional) — from Excel; auto-calculated if missing
        subjects (dict) — {subject_name: score, ...}

    Returns the file path of the generated PDF.
    """
    safe_id  = student['id'].replace('/', '_')
    filename = f"Result_{safe_id}.pdf"
    file_path = os.path.join(TEMP_DIR, filename)

    c = canvas.Canvas(file_path, pagesize=(LW, LH))
    c.setTitle(f"Student Result – {student.get('name', '')}")

    # Page 1
    draw_page1(c, student, LW, LH)
    c.showPage()

    # Page 2
    draw_page2(c, student, LW, LH)
    c.save()

    return file_path


# ── Cleanup helpers ───────────────────────────────────────────────────────────
def delete_pdf(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f'Error deleting PDF: {e}')


def clean_old_pdfs():
    """Remove PDFs older than 1 hour from TEMP_DIR."""
    try:
        cutoff = time.time() - 3600
        for fp in glob.glob(os.path.join(TEMP_DIR, '*.pdf')):
            if os.path.getmtime(fp) < cutoff:
                os.remove(fp)
    except Exception as e:
        print(f'Error cleaning PDFs: {e}')

