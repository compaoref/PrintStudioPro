"""
PrintStudio Pro v3.0 — Solution d'impression professionnelle
Grand Format (Vinyle / Bâche) + DTF + Suppression de fond
Thème Clair / Sombre — RIP intégré CMJN/TIF/PMN
"""

import streamlit as st
import io, zipfile
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np

try:
    import fitz
    HAS_MUPDF = True
except ImportError:
    HAS_MUPDF = False

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG (doit être en premier)
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="PrintStudio Pro",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════
# THÈME — SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Paramètres Globaux")
    theme = st.radio("Thème d'affichage", ["🌙 Sombre", "☀️ Clair"], index=0, key="theme_choice")
    DARK = theme == "🌙 Sombre"
    st.markdown("---")
    st.markdown("**PrintStudio Pro** v3.0")
    st.markdown("Système RIP intégré")
    st.markdown("`CMJN · TIF · PMN`")

# ═══════════════════════════════════════════════════════════
# VARIABLES THÈME
# ═══════════════════════════════════════════════════════════
if DARK:
    BG        = "#0d0f14"
    SURFACE   = "#161921"
    SURFACE2  = "#1e2330"
    BORDER    = "#2a3045"
    TEXT      = "#e8ecf5"
    MUTED     = "#7a869a"
    ACCENT    = "#ff5c1a"
    GREEN     = "#00c8a0"
    BLUE      = "#4da6ff"
    WARN      = "#ffb020"
    PREV_BG   = "#111520"
    PREV_GRID = "#1a2035"
    CELL_DEF  = "#1e2a3a"
else:
    BG        = "#f5f6fa"
    SURFACE   = "#ffffff"
    SURFACE2  = "#f0f2f8"
    BORDER    = "#d4d8e8"
    TEXT      = "#1a1e2e"
    MUTED     = "#6b7280"
    ACCENT    = "#e64a00"
    GREEN     = "#00a882"
    BLUE      = "#2563eb"
    WARN      = "#d97706"
    PREV_BG   = "#e8eaf0"
    PREV_GRID = "#d0d4e0"
    CELL_DEF  = "#dde0ee"

# ═══════════════════════════════════════════════════════════
# CSS DYNAMIQUE
# ═══════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: 'Inter', sans-serif !important;
    background-color: {BG} !important;
    color: {TEXT} !important;
}}
.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1280px !important;
}}

/* ── HEADER ── */
.psp-header {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 22px 32px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 12px rgba(0,0,0,{".18" if DARK else ".06"});
}}
.psp-logo {{
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: {TEXT};
}}
.psp-logo em {{ color: {ACCENT}; font-style: normal; }}
.psp-sub {{ font-size: 12px; color: {MUTED}; margin-top: 3px; font-weight: 400; }}
.psp-badge {{
    background: {ACCENT};
    color: white;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

/* ── SECTION HEADERS ── */
.sec-hdr {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: {MUTED};
    padding: 14px 0 10px;
    border-bottom: 2px solid {BORDER};
    margin-bottom: 16px;
}}
.sec-num {{
    width: 22px; height: 22px;
    background: {ACCENT};
    color: white;
    border-radius: 50%;
    font-size: 11px;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}}

/* ── STAT CARDS ── */
.stats-row {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin: 20px 0;
}}
.stat-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 16px 12px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,{".12" if DARK else ".04"});
}}
.stat-card .lbl {{
    font-size: 10px;
    font-weight: 600;
    color: {MUTED};
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
}}
.stat-card .val {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 15px;
    font-weight: 700;
    color: {TEXT};
    line-height: 1.2;
}}
.stat-card .val.accent {{ color: {ACCENT}; }}
.stat-card .val.green  {{ color: {GREEN};  }}
.stat-card .val.blue   {{ color: {BLUE};   }}

/* ── RESULT BOX ── */
.result-box {{
    background: {'rgba(0,200,160,0.07)' if DARK else 'rgba(0,168,130,0.07)'};
    border: 1.5px solid {'rgba(0,200,160,0.35)' if DARK else 'rgba(0,168,130,0.3)'};
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 14px;
    color: {GREEN};
    margin: 14px 0;
    line-height: 1.6;
}}
.info-box {{
    background: {'rgba(77,166,255,0.07)' if DARK else 'rgba(37,99,235,0.06)'};
    border: 1.5px solid {'rgba(77,166,255,0.3)' if DARK else 'rgba(37,99,235,0.25)'};
    border-radius: 10px;
    padding: 13px 16px;
    font-size: 13px;
    color: {BLUE};
    margin: 10px 0 16px;
}}
.warn-box {{
    background: {'rgba(255,176,32,0.07)' if DARK else 'rgba(217,119,6,0.06)'};
    border: 1.5px solid {'rgba(255,176,32,0.3)' if DARK else 'rgba(217,119,6,0.25)'};
    border-radius: 10px;
    padding: 13px 16px;
    font-size: 13px;
    color: {WARN};
    margin: 10px 0;
}}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{
    background: {SURFACE};
    border-radius: 12px;
    padding: 5px;
    gap: 4px;
    border: 1px solid {BORDER};
    box-shadow: 0 1px 6px rgba(0,0,0,{".1" if DARK else ".04"});
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 22px !important;
    color: {MUTED} !important;
    background: transparent !important;
    transition: all 0.2s !important;
}}
.stTabs [aria-selected="true"] {{
    background: {ACCENT} !important;
    color: white !important;
}}

/* ── INPUTS ── */
.stNumberInput input, .stSelectbox select, .stTextInput input {{
    background: {SURFACE2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    color: {TEXT} !important;
    font-size: 14px !important;
}}
.stNumberInput input:focus, .stSelectbox select:focus {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px {'rgba(255,92,26,0.15)' if DARK else 'rgba(230,74,0,0.1)'} !important;
}}

/* ── SIDEBAR ── */
.css-1d391kg, [data-testid="stSidebar"] {{
    background: {SURFACE} !important;
    border-right: 1px solid {BORDER} !important;
}}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {{
    background: {SURFACE2} !important;
    border: 2px dashed {BORDER} !important;
    border-radius: 12px !important;
    padding: 8px !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {ACCENT} !important;
}}

/* ── BUTTONS ── */
.stButton > button {{
    background: {ACCENT} !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 12px 28px !important;
    transition: all 0.2s !important;
    box-shadow: 0 2px 8px rgba(255,92,26,0.3) !important;
}}
.stButton > button:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(255,92,26,0.4) !important;
}}
.stDownloadButton > button {{
    background: {GREEN} !important;
    color: {'#0a1a16' if DARK else 'white'} !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 12px 28px !important;
    box-shadow: 0 2px 8px {'rgba(0,200,160,0.3)' if DARK else 'rgba(0,168,130,0.3)'} !important;
}}

/* ── RADIO ── */
.stRadio label {{ font-size: 13px !important; font-weight: 500 !important; color: {TEXT} !important; }}

/* ── DIVIDER ── */
hr {{ border-color: {BORDER} !important; margin: 20px 0 !important; }}

#MainMenu, footer, header {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# CONSTANTES & FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════
INCH_PER_METER = 39.3701
MM_PER_INCH    = 25.4

def sec(num, title):
    st.markdown(f'<div class="sec-hdr"><span class="sec-num">{num}</span>{title}</div>', unsafe_allow_html=True)

def result_box(html):
    st.markdown(f'<div class="result-box">{html}</div>', unsafe_allow_html=True)

def info_box(html):
    st.markdown(f'<div class="info-box">ℹ️ {html}</div>', unsafe_allow_html=True)

def warn_box(html):
    st.markdown(f'<div class="warn-box">⚠️ {html}</div>', unsafe_allow_html=True)

def px_from_m(m, dpi):   return max(1, int(m * INCH_PER_METER * dpi))
def px_from_mm(mm, dpi): return max(1, int((mm / MM_PER_INCH) * dpi))

def estimate_tif(wpx, hpx):
    b = int(wpx * hpx * 4 * 0.38)
    return f"{b/1_048_576:.1f} MB" if b >= 1_048_576 else f"{b/1024:.0f} KB"

def load_image(uploaded) -> Image.Image:
    data = uploaded.read(); uploaded.seek(0)
    if uploaded.name.lower().endswith(".pdf") and HAS_MUPDF:
        doc  = fitz.open(stream=data, filetype="pdf")
        pix  = doc[0].get_pixmap(matrix=fitz.Matrix(4,4), alpha=True)
        img  = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
        doc.close(); return img
    img = Image.open(io.BytesIO(data))
    return img.convert("RGBA") if img.mode != "RGBA" else img

def encode_tif(img: Image.Image, dpi: int, comp: str) -> bytes:
    if img.mode in ("RGBA","RGB"):
        bg = Image.new("RGB", img.size, (255,255,255))
        if img.mode == "RGBA":
            bg.paste(img.convert("RGB"), mask=img.split()[3])
        else:
            bg = img
        img = bg.convert("CMYK")
    buf = io.BytesIO()
    img.save(buf, format="TIFF", dpi=(dpi,dpi), compression=comp)
    return buf.getvalue()

def build_pmn(job: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return "\n".join([
        "; PrintStudio Pro — Job PMN",
        f"; {now}",
        "", "[JobInfo]",
        f"JobName={job.get('name','Job')}",
        f"Created={now}",
        "", "[Media]",
        f"Width={job.get('w_mm',0):.2f}",
        f"Height={job.get('h_mm',0):.2f}",
        "Unit=mm",
        f"Orientation={job.get('orient','portrait')}",
        "", "[Print]",
        f"Copies={job.get('copies',1)}",
        f"DPI={job.get('dpi',300)}",
        "ColorMode=CMYK",
        f"ColorProfile={job.get('icc','ISOcoated_v2')}",
        f"Mirror={1 if job.get('mirror') else 0}",
        f"WhiteBase={1 if job.get('white_base') else 0}",
        f"Bleed={job.get('bleed',0):.1f}",
        "", "[RIP]",
        "Software=MainTap",
        f"Quality={job.get('quality','High')}",
        "RenderIntent=Perceptual",
        "", "[Grid]",
        f"Cols={job.get('cols',1)}",
        f"Rows={job.get('rows',1)}",
        f"GapH={job.get('gap_h',0):.1f}",
        f"GapV={job.get('gap_v',0):.1f}",
        f"Margin={job.get('margin',0):.1f}",
        "", "[Source]",
        f"File={job.get('file','unknown')}",
        f"Mode={job.get('mode','Standard')}",
    ])

# ═══════════════════════════════════════════════════════════
# SUPPRESSION DE FOND
# ═══════════════════════════════════════════════════════════
def remove_background(img: Image.Image, method: str, tolerance: int,
                       color_pick: tuple) -> Image.Image:
    """Supprime le fond d'une image selon la méthode choisie."""
    rgba = img.convert("RGBA")
    arr  = np.array(rgba, dtype=np.uint8)

    if method == "Blanc (fond blanc)":
        # Masque : pixels proches du blanc
        mask = (arr[:,:,0].astype(int) + arr[:,:,1].astype(int) + arr[:,:,2].astype(int)) > (765 - tolerance * 3)
    elif method == "Noir (fond noir)":
        mask = (arr[:,:,0].astype(int) + arr[:,:,1].astype(int) + arr[:,:,2].astype(int)) < (tolerance * 3)
    else:  # Couleur personnalisée
        r0, g0, b0 = color_pick
        dr = arr[:,:,0].astype(int) - r0
        dg = arr[:,:,1].astype(int) - g0
        db = arr[:,:,2].astype(int) - b0
        dist = np.sqrt(dr**2 + dg**2 + db**2)
        mask = dist < tolerance

    arr[mask, 3] = 0
    return Image.fromarray(arr, "RGBA")

# ═══════════════════════════════════════════════════════════
# MOTEUR RIP — GRAND FORMAT
# ═══════════════════════════════════════════════════════════
def rip_grand_format(src: Image.Image, w_m: float, h_m: float,
                     cols: int, rows: int, gap_h: float, gap_v: float,
                     margin: float, bleed: float, dpi: int, rotation: int,
                     icc: str, comp: str, keep_ratio: bool,
                     prog=None) -> tuple[bytes, dict]:
    def p(v,m):
        if prog: prog(v,m)

    p(5, "Calcul des dimensions pixel…")
    wpx = px_from_m(w_m, dpi)
    hpx = px_from_m(h_m, dpi)
    m_px  = px_from_mm(margin, dpi)
    gh_px = px_from_mm(gap_h,  dpi)
    gv_px = px_from_mm(gap_v,  dpi)

    cw = max(1, (wpx - 2*m_px - gh_px*(cols-1)) // cols)
    ch = max(1, (hpx - 2*m_px - gv_px*(rows-1)) // rows)

    p(18, f"Préparation source — rotation {rotation}°…")
    s = src.convert("RGBA")
    if rotation: s = s.rotate(-rotation, expand=True)

    if keep_ratio:
        r = s.width / s.height
        if cw / ch > r: cw2, ch2 = int(ch*r), ch
        else:           cw2, ch2 = cw, int(cw/r)
    else:
        cw2, ch2 = cw, ch

    s = s.resize((cw2, ch2), Image.LANCZOS)

    p(35, "Création de la planche blanche…")
    board = Image.new("RGB", (wpx, hpx), (255,255,255))

    p(50, f"Placement {cols}×{rows} = {cols*rows} éléments…")
    alpha = s.split()[3] if s.mode == "RGBA" else None
    s_rgb = s.convert("RGB")
    for r_ in range(rows):
        for c_ in range(cols):
            x = m_px + c_*(cw + gh_px) + (cw - cw2)//2
            y = m_px + r_*(ch + gv_px) + (ch - ch2)//2
            cell_bg = Image.new("RGB", (cw2, ch2), (255,255,255))
            cell_bg.paste(s_rgb, (0,0), alpha)
            board.paste(cell_bg, (x, y))

    p(75, f"Conversion CMJN — {icc}…")
    board_cmyk = board.convert("CMYK")

    p(90, f"Encodage TIF ({comp})…")
    tif = encode_tif(board_cmyk, dpi, comp)

    p(100, "✅ RIP terminé !")
    return tif, {"wpx": wpx, "hpx": hpx, "cw_mm": (cw/dpi)*MM_PER_INCH,
                 "ch_mm": (ch/dpi)*MM_PER_INCH, "total": cols*rows}

# ═══════════════════════════════════════════════════════════
# MOTEUR RIP — DTF
# ═══════════════════════════════════════════════════════════
def rip_dtf(src: Image.Image, w_mm: float, h_mm: float, dpi: int,
            mirror: bool, white_base: bool, comp: str, prog=None) -> tuple[bytes, dict]:
    def p(v,m):
        if prog: prog(v,m)

    p(5,  "Calcul zone DTF…")
    wpx = px_from_mm(w_mm, dpi)
    hpx = px_from_mm(h_mm, dpi)

    p(20, "Mise en forme de l'image…")
    s = src.convert("RGBA")
    if mirror: s = s.transpose(Image.FLIP_LEFT_RIGHT)

    # Fit centré
    r = s.width / s.height
    t = wpx / hpx
    nw = wpx if r > t else int(hpx*r)
    nh = int(wpx/r) if r > t else hpx
    s = s.resize((nw, nh), Image.LANCZOS)

    p(45, "Composition sur fond…")
    base = Image.new("RGB", (wpx, hpx), (255,255,255))
    ox = (wpx-nw)//2; oy = (hpx-nh)//2
    alpha = s.split()[3]
    base.paste(s.convert("RGB"), (ox, oy), alpha)

    p(70, "Conversion CMJN…")
    cmyk = base.convert("CMYK")

    p(88, f"Encodage TIF…")
    tif = encode_tif(cmyk, dpi, comp)

    p(100, "✅ RIP DTF terminé !")
    return tif, {"wpx": wpx, "hpx": hpx}

# ═══════════════════════════════════════════════════════════
# FONCTIONS D'APERÇU
# ═══════════════════════════════════════════════════════════
def font(size=9):
    try:    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except: return ImageFont.load_default()

def font_mono(size=9):
    try:    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
    except: return ImageFont.load_default()

def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def preview_image_simple(src_img, w_mm, h_mm, rotation, keep_ratio, pw=700):
    aspect = h_mm / w_mm if w_mm > 0 else 1
    ph = min(int(pw * aspect), 520); ph = max(ph, 160)
    board = Image.new("RGB", (pw, ph), hex2rgb(PREV_BG))
    draw  = ImageDraw.Draw(board)

    # Grille de fond
    gc = hex2rgb(PREV_GRID)
    for x in range(0, pw, 28): draw.line([(x,0),(x,ph)], fill=gc, width=1)
    for y in range(0, ph, 28): draw.line([(0,y),(pw,y)], fill=gc, width=1)

    pad = 24
    iw, ih = pw - pad*2, ph - pad*2

    if src_img:
        s = src_img.copy().convert("RGBA")
        if rotation: s = s.rotate(-rotation, expand=True)
        if keep_ratio:
            r = s.width / s.height
            if iw/ih > r: iw2, ih2 = int(ih*r), ih
            else:          iw2, ih2 = iw, int(iw/r)
        else:
            iw2, ih2 = iw, ih
        s = s.resize((iw2, ih2), Image.LANCZOS)
        ox = pad + (iw-iw2)//2; oy = pad + (ih-ih2)//2
        bg = Image.new("RGB",(iw2,ih2), hex2rgb(PREV_BG))
        bg.paste(s.convert("RGB"),(0,0), s.split()[3])
        board.paste(bg,(ox,oy))
        ac = hex2rgb(ACCENT)
        draw.rectangle([ox-2,oy-2,ox+iw2+1,oy+ih2+1], outline=ac, width=2)
        # Cotes
        draw.line([(ox,oy-14),(ox+iw2,oy-14)], fill=ac, width=1)
        draw.line([(ox,oy-18),(ox,oy-10)], fill=ac, width=1)
        draw.line([(ox+iw2,oy-18),(ox+iw2,oy-10)], fill=ac, width=1)
        draw.text(((ox+ox+iw2)//2, oy-14), f"{w_mm:.1f} mm", fill=ac, font=font(9), anchor="mm")
    else:
        draw.rectangle([pad,pad,pw-pad,ph-pad], outline=hex2rgb(BORDER), width=2)
        draw.text((pw//2, ph//2), "Chargez une image", fill=hex2rgb(MUTED), font=font(14), anchor="mm")

    # Barre info bas
    draw.rectangle([0,ph-22,pw,ph], fill=hex2rgb(SURFACE2))
    txt = f"{w_mm:.1f} × {h_mm:.1f} mm  |  {w_mm/10:.1f} × {h_mm/10:.1f} cm  |  {w_mm/1000:.3f} × {h_mm/1000:.3f} m"
    draw.text((pw//2, ph-11), txt, fill=hex2rgb(ACCENT), font=font_mono(9), anchor="mm")
    return board

def preview_grid(src_img, cols, rows, w_m, h_m, gap_h, gap_v, margin, rotation, pw=700):
    aspect = h_m / w_m if w_m > 0 else 1
    ph = min(int(pw*aspect), 520); ph = max(ph, 180)
    board = Image.new("RGB",(pw,ph), hex2rgb(PREV_BG))
    draw  = ImageDraw.Draw(board)

    gc = hex2rgb(PREV_GRID)
    for x in range(0,pw,28): draw.line([(x,0),(x,ph)],fill=gc,width=1)
    for y in range(0,ph,28): draw.line([(0,y),(pw,y)],fill=gc,width=1)

    scale = pw / (w_m*1000)
    mp  = int(margin*scale)
    ghp = int(gap_h*scale)
    gvp = int(gap_v*scale)
    uw  = pw - 2*mp - ghp*(cols-1)
    uh  = ph - 2*mp - gvp*(rows-1)
    cw  = max(2, uw//cols)
    ch  = max(2, uh//rows)

    ac = hex2rgb(ACCENT)
    tc = hex2rgb(TEXT)

    palette = [(40,55,85),(35,60,70),(55,42,72),(60,48,36),(36,58,52),(52,52,42)]
    if not DARK:
        palette = [(220,230,250),(210,240,235),(235,220,245),(245,235,215),(215,235,228),(235,232,215)]

    for r_ in range(rows):
        for c_ in range(cols):
            x = mp + c_*(cw+ghp); y = mp + r_*(ch+gvp)
            cc = palette[(r_*cols+c_)%6]

            if src_img:
                s = src_img.copy().convert("RGBA")
                if rotation: s = s.rotate(-rotation, expand=True)
                s = s.resize((cw,ch), Image.LANCZOS)
                bg = Image.new("RGB",(cw,ch), cc)
                bg.paste(s.convert("RGB"),(0,0),s.split()[3])
                board.paste(bg,(x,y))
            else:
                draw.rectangle([x,y,x+cw-1,y+ch-1], fill=cc)

            draw.rectangle([x,y,x+cw-1,y+ch-1], outline=ac, width=2)
            n  = str(r_*cols+c_+1)
            fs = max(8, min(ch//3, 16))
            draw.text((x+cw//2,y+ch//2), n, fill=ac, font=font(fs), anchor="mm")

    # Marge
    if margin > 0:
        wc = hex2rgb(WARN)
        draw.rectangle([mp,mp,pw-mp,ph-mp], outline=wc+[0], width=0)
        draw.rectangle([mp,mp,pw-mp-1,ph-mp-1], outline=(*wc, 120), width=1)

    draw.rectangle([0,ph-22,pw,ph], fill=hex2rgb(SURFACE2))
    lbl = f"Planche {w_m:.3f}m × {h_m:.3f}m  |  {cols}×{rows} = {cols*rows} éléments  |  CMJN"
    draw.text((pw//2,ph-11), lbl, fill=hex2rgb(ACCENT), font=font_mono(9), anchor="mm")
    return board

def preview_dtf(src_img, w_mm, h_mm, mirror, pw_max=340):
    r = h_mm/w_mm if w_mm>0 else 1
    ph = min(int(pw_max*r), 460); pw = min(pw_max, int(ph/r))
    ph = max(ph,180)
    board = Image.new("RGB",(pw,ph), hex2rgb(PREV_BG))
    draw  = ImageDraw.Draw(board)

    pad=10
    draw.rectangle([pad,pad,pw-pad,ph-pad], fill=hex2rgb(SURFACE2), outline=hex2rgb(BORDER), width=1)

    if src_img:
        s = src_img.copy().convert("RGBA")
        if mirror: s = s.transpose(Image.FLIP_LEFT_RIGHT)
        iw,ih = pw-pad*4, ph-pad*4
        rr = s.width/s.height
        tt = iw/ih
        nw = iw if rr>tt else int(ih*rr)
        nh = int(iw/rr) if rr>tt else ih
        s  = s.resize((nw,nh),Image.LANCZOS)
        ox = pad*2+(iw-nw)//2; oy = pad*2+(ih-nh)//2
        bg = Image.new("RGB",(nw,nh), hex2rgb(SURFACE2))
        bg.paste(s.convert("RGB"),(0,0),s.split()[3])
        board.paste(bg,(ox,oy))
    else:
        draw.text((pw//2,ph//2), "📄 Chargez\nun fichier", fill=hex2rgb(MUTED), font=font(11), anchor="mm")

    # Coins repère
    gc = hex2rgb(GREEN); mk=14
    for (cx,cy) in [(pad,pad),(pw-pad,pad),(pad,ph-pad),(pw-pad,ph-pad)]:
        dx = 1 if cx==pad else -1; dy = 1 if cy==pad else -1
        draw.line([(cx,cy),(cx+dx*mk,cy)],fill=gc,width=2)
        draw.line([(cx,cy),(cx,cy+dy*mk)],fill=gc,width=2)

    if mirror:
        draw.rectangle([pad,pad,pw-pad,pad+16],fill=hex2rgb(SURFACE))
        draw.text((pw//2,pad+8),"MIROIR",fill=hex2rgb(ACCENT),font=font(9),anchor="mm")

    draw.rectangle([0,ph-20,pw,ph], fill=hex2rgb(SURFACE))
    draw.text((pw//2,ph-10),f"{w_mm:.0f}×{h_mm:.0f} mm",fill=hex2rgb(GREEN),font=font_mono(9),anchor="mm")
    return board

def make_zip(files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()

# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="psp-header">
  <div>
    <div class="psp-logo">Print<em>Studio</em> Pro</div>
    <div class="psp-sub">Système RIP intégré · Grand Format · Vinyle · Bâche · DTF · Suppression de fond</div>
  </div>
  <div style="display:flex;gap:10px;align-items:center">
    <span class="psp-badge">CMJN</span>
    <span class="psp-badge" style="background:{GREEN}">TIF</span>
    <span class="psp-badge" style="background:{BLUE}">PMN</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# TABS PRINCIPALES
# ═══════════════════════════════════════════════════════════
tab_gf, tab_dtf, tab_bg = st.tabs([
    "🖨️  Grand Format — Vinyle / Bâche",
    "👕  DTF — Textile",
    "✂️  Suppression de fond",
])

# ╔═══════════════════════════════════════════════════════════
# ║  TAB 1 — GRAND FORMAT
# ╚═══════════════════════════════════════════════════════════
with tab_gf:

    # ── COL GAUCHE (paramètres) + DROITE (aperçu) ───────────
    left, right = st.columns([1.1, 1], gap="large")

    with left:
        # ── 1. FICHIER ──────────────────────────────────────
        sec("1", "Fichier source")
        up = st.file_uploader(
            "Glissez votre logo, étiquette ou maquette",
            type=["pdf","png","jpg","jpeg","tif","tiff","bmp","ai","eps","cdr","svg"],
            key="gf_upload", label_visibility="collapsed",
        )
        src_img = None
        if up:
            try: src_img = load_image(up)
            except Exception as e: st.warning(f"Aperçu non disponible : {e}")
            result_box(f"📂 <strong>{up.name}</strong> &nbsp;|&nbsp; {up.size/1024:.0f} KB"
                + (f" &nbsp;|&nbsp; {src_img.width}×{src_img.height} px" if src_img else ""))

        # ── 2. MODE D'IMPRESSION ────────────────────────────
        sec("2", "Mode d'impression")
        mode = st.radio(
            "Mode",
            ["🖼️ Image simple", "📏 Multiplication — par planche", "🏷️ Multiplication — par étiquette"],
            key="gf_mode", label_visibility="collapsed",
        )

        # ── 3. DIMENSIONS ───────────────────────────────────
        sec("3", "Dimensions")

        if mode == "🖼️ Image simple":
            info_box("L'image sera redimensionnée aux dimensions indiquées. Aucune multiplication.")
            unit = st.radio("Unité", ["mm","cm","m"], horizontal=True, key="si_unit")
            k = {"mm":1.,"cm":10.,"m":1000.}[unit]
            dv_w = {"mm":1500.,"cm":150.,"m":1.5}[unit]
            dv_h = {"mm":1000.,"cm":100.,"m":1.0}[unit]
            c1,c2 = st.columns(2)
            with c1: iw_in = st.number_input(f"Largeur ({unit})", min_value=0.1, value=dv_w, step={"mm":.5,"cm":.05,"m":.001}[unit], key="si_w")
            with c2: ih_in = st.number_input(f"Hauteur ({unit})", min_value=0.1, value=dv_h, step={"mm":.5,"cm":.05,"m":.001}[unit], key="si_h")
            keep_ratio = st.checkbox("🔗 Conserver les proportions", value=True, key="si_kr")
            bleed = st.number_input("Fond perdu (mm)", min_value=0., max_value=20., value=0., key="si_bl")
            lbl_w_mm = iw_in * k; lbl_h_mm = ih_in * k
            print_w = lbl_w_mm/1000; print_h = lbl_h_mm/1000
            cols_v=1; rows_v=1; gap_h=0.; gap_v=0.; margin=0.
            result_box(f"📐 Dimensions : <strong>{lbl_w_mm:.1f} × {lbl_h_mm:.1f} mm</strong>"
                       f" &nbsp;({lbl_w_mm/10:.1f} × {lbl_h_mm/10:.1f} cm"
                       f" / {print_w:.3f} × {print_h:.3f} m)")

        elif mode == "📏 Multiplication — par planche":
            info_box("Entrez la taille totale du support. La taille de chaque élément est calculée automatiquement.")
            unit = st.radio("Unité du support", ["m","cm","mm"], horizontal=True, key="pl_unit")
            k = {"mm":0.001,"cm":0.01,"m":1.}[unit]
            dv_w = {"m":1.5,"cm":150.,"mm":1500.}[unit]
            dv_h = {"m":1.0,"cm":100.,"mm":1000.}[unit]
            c1,c2 = st.columns(2)
            with c1: pw_in = st.number_input(f"Largeur support ({unit})", min_value=0.01, value=dv_w, step={"m":.01,"cm":.5,"mm":1.}[unit], key="pl_w")
            with c2: ph_in = st.number_input(f"Hauteur support ({unit})", min_value=0.01, value=dv_h, step={"m":.01,"cm":.5,"mm":1.}[unit], key="pl_h")
            print_w = pw_in*k; print_h = ph_in*k

            st.markdown("**Grille de multiplication**")
            g1,g2,g3,g4 = st.columns(4)
            with g1: cols_v = st.number_input("Colonnes", min_value=1, max_value=100, value=3, key="pl_c")
            with g2: rows_v = st.number_input("Lignes",   min_value=1, max_value=100, value=4, key="pl_r")
            with g3: gap_h  = st.number_input("Esp. H (mm)", min_value=0., value=3., step=.5, key="pl_gh")
            with g4: gap_v  = st.number_input("Esp. V (mm)", min_value=0., value=3., step=.5, key="pl_gv")
            m1,m2 = st.columns(2)
            with m1: margin = st.number_input("Marge bord (mm)", min_value=0., value=5., key="pl_mg")
            with m2: bleed  = st.number_input("Fond perdu (mm)", min_value=0., max_value=20., value=3., key="pl_bl")
            keep_ratio = st.checkbox("🔗 Conserver proportions", value=False, key="pl_kr")

            uw = print_w*1000 - 2*margin - gap_h*(cols_v-1)
            uh = print_h*1000 - 2*margin - gap_v*(rows_v-1)
            lbl_w_mm = max(1., uw/cols_v); lbl_h_mm = max(1., uh/rows_v)
            result_box(f"🏷️ Taille de chaque élément : <strong>{lbl_w_mm:.1f} × {lbl_h_mm:.1f} mm</strong>"
                       f" &nbsp;({lbl_w_mm/10:.2f} × {lbl_h_mm/10:.2f} cm)"
                       f" &nbsp;— <strong>{int(cols_v*rows_v)}</strong> éléments au total")

        else:  # par étiquette
            info_box("Entrez la taille d'un élément. La taille du support est calculée automatiquement.")
            unit = st.radio("Unité de l'élément", ["mm","cm","m"], horizontal=True, key="et_unit")
            k = {"mm":1.,"cm":10.,"m":1000.}[unit]
            dv_w = {"mm":100.,"cm":10.,"m":0.1}[unit]
            dv_h = {"mm":50., "cm":5., "m":0.05}[unit]
            c1,c2 = st.columns(2)
            with c1: ew_in = st.number_input(f"Largeur élément ({unit})", min_value=0.1, value=dv_w, step={"mm":.5,"cm":.05,"m":.001}[unit], key="et_w")
            with c2: eh_in = st.number_input(f"Hauteur élément ({unit})", min_value=0.1, value=dv_h, step={"mm":.5,"cm":.05,"m":.001}[unit], key="et_h")
            lbl_w_mm = ew_in*k; lbl_h_mm = eh_in*k

            st.markdown("**Grille de multiplication**")
            g1,g2,g3,g4 = st.columns(4)
            with g1: cols_v = st.number_input("Colonnes", min_value=1, max_value=100, value=3, key="et_c")
            with g2: rows_v = st.number_input("Lignes",   min_value=1, max_value=100, value=4, key="et_r")
            with g3: gap_h  = st.number_input("Esp. H (mm)", min_value=0., value=3., step=.5, key="et_gh")
            with g4: gap_v  = st.number_input("Esp. V (mm)", min_value=0., value=3., step=.5, key="et_gv")
            m1,m2 = st.columns(2)
            with m1: margin = st.number_input("Marge bord (mm)", min_value=0., value=5., key="et_mg")
            with m2: bleed  = st.number_input("Fond perdu (mm)", min_value=0., max_value=20., value=3., key="et_bl")
            keep_ratio = st.checkbox("🔗 Conserver proportions", value=False, key="et_kr")

            # Calcul taille support — avec option de forcer un support standard
            st.markdown("**Support d'impression (optionnel)**")
            force_support = st.checkbox("📐 Forcer une taille de support spécifique", value=False, key="et_force")
            if force_support:
                unit_s = st.radio("Unité support", ["m","cm","mm"], horizontal=True, key="et_su")
                ks = {"mm":0.001,"cm":0.01,"m":1.}[unit_s]
                fs1,fs2 = st.columns(2)
                with fs1: fs_w = st.number_input(f"Largeur ({unit_s})", min_value=0.01, value=1.5, step=.01, key="et_fw")
                with fs2: fs_h = st.number_input(f"Hauteur ({unit_s})", min_value=0.01, value=1.0, step=.01, key="et_fh")
                print_w = fs_w*ks; print_h = fs_h*ks
                info_box(f"Support forcé : {print_w:.3f} m × {print_h:.3f} m. Les éléments seront placés selon la grille, le reste sera blanc.")
            else:
                print_w = (lbl_w_mm*cols_v + gap_h*(cols_v-1) + 2*margin) / 1000
                print_h = (lbl_h_mm*rows_v + gap_v*(rows_v-1) + 2*margin) / 1000

            result_box(f"📏 Support calculé : <strong>{print_w:.3f} m × {print_h:.3f} m</strong>"
                       f" &nbsp;({print_w*100:.1f} × {print_h*100:.1f} cm)"
                       f" &nbsp;— <strong>{int(cols_v*rows_v)}</strong> éléments")

        # ── 4. PARAMÈTRES RIP ───────────────────────────────
        sec("4", "Paramètres RIP")
        r1,r2,r3,r4 = st.columns(4)
        with r1: dpi    = st.selectbox("DPI", [72,150,300,600], index=2, key="gf_dpi")
        with r2: rot    = st.selectbox("Rotation", [0,90,180,270], index=0, format_func=lambda x:f"{x}°", key="gf_rot")
        with r3: icc    = st.selectbox("Profil ICC", ["ISOcoated_v2","CoatedFOGRA39","UncoatedFOGRA29","SWOP"], key="gf_icc")
        with r4: comp   = st.selectbox("Compression TIF", {"tiff_lzw":"LZW (recommandé)","tiff_deflate":"Deflate","raw":"Aucune"}.keys(),
                                        format_func={"tiff_lzw":"LZW (recommandé)","tiff_deflate":"Deflate","raw":"Aucune"}.get, key="gf_comp")

        # ── 5. FORMAT SORTIE ────────────────────────────────
        sec("5", "Format de sortie")
        out = st.radio("Sortie", ["tif","pmn","zip","zip_full"],
            format_func={"tif":"🖼️ TIF CMJN","pmn":"🖨️ PMN (MainTap)","zip":"📦 TIF + PMN","zip_full":"📦 ZIP complet + aperçu"}.get,
            horizontal=True, key="gf_out")

    # ── COLONNE DROITE : stats + aperçu ─────────────────────
    with right:
        sec("", "Récapitulatif & Aperçu")

        # Stats
        wpx = px_from_m(print_w, dpi); hpx = px_from_m(print_h, dpi)
        total = int(cols_v)*int(rows_v)
        s1,s2,s3 = st.columns(3)
        s1.markdown(f'<div class="stat-card"><div class="lbl">Éléments</div><div class="val accent">{total}</div></div>', unsafe_allow_html=True)
        s2.markdown(f'<div class="stat-card"><div class="lbl">{"Dim. image" if mode=="🖼️ Image simple" else "Taille élément"}</div><div class="val">{lbl_w_mm:.0f}×{lbl_h_mm:.0f} mm</div></div>', unsafe_allow_html=True)
        s3.markdown(f'<div class="stat-card"><div class="lbl">Support</div><div class="val">{print_w:.2f}×{print_h:.2f} m</div></div>', unsafe_allow_html=True)
        st.markdown("")
        s4,s5 = st.columns(2)
        s4.markdown(f'<div class="stat-card"><div class="lbl">Pixels</div><div class="val blue">{wpx:,}×{hpx:,}</div></div>', unsafe_allow_html=True)
        s5.markdown(f'<div class="stat-card"><div class="lbl">TIF estimé</div><div class="val green">{estimate_tif(wpx,hpx)}</div></div>', unsafe_allow_html=True)

        st.markdown("")

        # Aperçu
        if mode == "🖼️ Image simple":
            prev = preview_image_simple(src_img, lbl_w_mm, lbl_h_mm, rot, keep_ratio)
            cap  = f"Image : {lbl_w_mm:.1f}×{lbl_h_mm:.1f} mm"
        else:
            prev = preview_grid(src_img, int(cols_v), int(rows_v), print_w, print_h, gap_h, gap_v, margin, rot)
            cap  = f"Grille {int(cols_v)}×{int(rows_v)} — {total} éléments — Support {print_w:.2f}×{print_h:.2f} m"

        st.image(prev, use_container_width=True, caption=cap)

        # ── BOUTON RIP ───────────────────────────────────────
        st.markdown("")
        if not up:
            warn_box("Chargez un fichier source pour lancer le RIP.")
        else:
            if st.button("🚀  Lancer le RIP — Générer fichiers prêts à imprimer",
                         type="primary", use_container_width=True, key="gf_rip"):
                try:
                    prog = st.progress(0); stat = st.empty()
                    def cb(v,m): prog.progress(int(v)); stat.markdown(f"**⚙️ {m}**")

                    src_rip = src_img or load_image(up)

                    # Ajuster hauteur si proportions conservées en mode simple
                    print_h_rip = print_h
                    if mode == "🖼️ Image simple" and keep_ratio and src_rip:
                        sr = src_rip.width / src_rip.height
                        print_h_rip = print_w / sr

                    tif_b, info = rip_grand_format(
                        src_rip, print_w, print_h_rip,
                        int(cols_v), int(rows_v), gap_h, gap_v, margin, bleed,
                        dpi, rot, icc, comp, keep_ratio, cb,
                    )

                    ts = datetime.now().strftime("%Y%m%d_%H%M")
                    bn = Path(up.name).stem
                    if mode == "🖼️ Image simple":
                        fn_tif = f"{bn}_{lbl_w_mm:.0f}x{lbl_h_mm:.0f}mm_{dpi}dpi_CMJN_{ts}.tif"
                    else:
                        fn_tif = f"{bn}_elem{lbl_w_mm:.0f}x{lbl_h_mm:.0f}mm_support{print_w:.2f}x{print_h:.2f}m_{int(cols_v)}x{int(rows_v)}_{dpi}dpi_CMJN_{ts}.tif"
                    fn_pmn = fn_tif.replace(".tif",".pmn")

                    job = {"name":bn,"w_mm":print_w*1000,"h_mm":print_h_rip*1000,
                           "orient":"landscape" if print_w>print_h_rip else "portrait",
                           "copies":1,"dpi":dpi,"icc":icc,"mirror":False,"white_base":False,
                           "bleed":bleed,"cols":int(cols_v),"rows":int(rows_v),
                           "gap_h":gap_h,"gap_v":gap_v,"margin":margin,
                           "file":up.name,"mode":mode,"quality":"High"}
                    pmn_b = build_pmn(job).encode()

                    tif_mb = len(tif_b)/1_048_576
                    stat.markdown("**✅ RIP terminé !**")
                    result_box(f"✅ <strong>RIP terminé !</strong> &nbsp;|&nbsp; "
                               f"{info['wpx']:,}×{info['hpx']:,} px &nbsp;|&nbsp; "
                               f"TIF CMJN : {tif_mb:.1f} MB")

                    if out == "tif":
                        st.download_button("⬇️  Télécharger TIF CMJN", tif_b, fn_tif, "image/tiff", use_container_width=True)
                    elif out == "pmn":
                        st.download_button("⬇️  Télécharger PMN", pmn_b, fn_pmn, "text/plain", use_container_width=True)
                    elif out in ("zip","zip_full"):
                        files = {fn_tif: tif_b, fn_pmn: pmn_b}
                        if out == "zip_full":
                            buf = io.BytesIO(); prev.save(buf, "PNG")
                            files[f"{bn}_apercu.png"] = buf.getvalue()
                        zb = make_zip(files)
                        fn_zip = fn_tif.replace(".tif","_COMPLET.zip")
                        st.download_button("⬇️  Télécharger ZIP complet", zb, fn_zip, "application/zip", use_container_width=True)
                        d1,d2 = st.columns(2)
                        d1.download_button("⬇️ TIF seul", tif_b, fn_tif, "image/tiff")
                        d2.download_button("⬇️ PMN seul", pmn_b, fn_pmn, "text/plain")

                except Exception as e:
                    st.error(f"❌ Erreur RIP : {e}"); st.exception(e)


# ╔═══════════════════════════════════════════════════════════
# ║  TAB 2 — DTF
# ╚═══════════════════════════════════════════════════════════
with tab_dtf:

    d_left, d_right = st.columns([1.1, 1], gap="large")

    with d_left:
        sec("1","Fichier source DTF")
        up_d = st.file_uploader("Chargez votre fichier",
            type=["pdf","png","jpg","jpeg","tif","tiff","ai","eps","bmp","svg"],
            key="dtf_up", label_visibility="collapsed")
        src_d = None
        if up_d:
            try: src_d = load_image(up_d)
            except Exception as e: st.warning(f"Aperçu non disponible : {e}")
            result_box(f"📂 <strong>{up_d.name}</strong> &nbsp;|&nbsp; {up_d.size/1024:.0f} KB")

        sec("2","Format & Dimensions")
        fmt_choice = st.radio("Format",["A4","A3","A2","A1","Personnalisé"], horizontal=True, key="dtf_fmt")
        DIMS = {"A4":(210,297),"A3":(297,420),"A2":(420,594),"A1":(594,841)}

        if fmt_choice == "Personnalisé":
            dc1,dc2 = st.columns(2)
            with dc1: cw = st.number_input("Largeur (mm)", min_value=10., value=300., key="dtf_cw")
            with dc2: ch = st.number_input("Hauteur (mm)", min_value=10., value=400., key="dtf_ch")
            dtf_w, dtf_h = float(cw), float(ch)
        else:
            bw, bh = DIMS[fmt_choice]
            orient = st.radio("Orientation",["Portrait","Paysage"], horizontal=True, key="dtf_or")
            dtf_w, dtf_h = (float(bw),float(bh)) if orient=="Portrait" else (float(bh),float(bw))

        sec("3","Paramètres d'impression")
        dp1,dp2 = st.columns(2)
        with dp1:
            dtf_dpi   = st.selectbox("Résolution DPI",[150,300,600,1200],index=1,key="dtf_dpi")
            dtf_color = st.selectbox("Mode couleur",{"cmyk":"CMJN (standard)","rgb":"RVB"}.keys(),
                            format_func={"cmyk":"CMJN (standard)","rgb":"RVB"}.get, key="dtf_col")
            dtf_comp  = st.selectbox("Compression TIF",{"tiff_lzw":"LZW","tiff_deflate":"Deflate","raw":"Aucune"}.keys(),
                            format_func={"tiff_lzw":"LZW","tiff_deflate":"Deflate","raw":"Aucune"}.get, key="dtf_comp")
        with dp2:
            dtf_mirror = st.toggle("🪞 Miroir",    value=False, key="dtf_mir")
            dtf_white  = st.toggle("⬜ White underbase", value=True, key="dtf_wb")
            dtf_copies = st.number_input("Copies", min_value=1, max_value=999, value=1, key="dtf_cop")
            dtf_qual   = st.selectbox("Qualité RIP",["Draft","Normal","High","Ultra"],index=2, key="dtf_q")

        sec("4","Format de sortie")
        dtf_out = st.radio("Sortie DTF",["tif","pmn","zip"],
            format_func={"tif":"🖼️ TIF CMJN","pmn":"🖨️ PMN","zip":"📦 ZIP complet"}.get,
            horizontal=True, key="dtf_out", index=2)

    with d_right:
        sec("","Récapitulatif & Aperçu")

        wpx_d = px_from_mm(dtf_w, dtf_dpi); hpx_d = px_from_mm(dtf_h, dtf_dpi)
        ds1,ds2,ds3,ds4 = st.columns(4)
        ds1.markdown(f'<div class="stat-card"><div class="lbl">Format</div><div class="val accent">{fmt_choice}</div></div>', unsafe_allow_html=True)
        ds2.markdown(f'<div class="stat-card"><div class="lbl">Dimensions</div><div class="val">{dtf_w:.0f}×{dtf_h:.0f} mm</div></div>', unsafe_allow_html=True)
        ds3.markdown(f'<div class="stat-card"><div class="lbl">DPI</div><div class="val blue">{dtf_dpi}</div></div>', unsafe_allow_html=True)
        ds4.markdown(f'<div class="stat-card"><div class="lbl">TIF estimé</div><div class="val green">{estimate_tif(wpx_d,hpx_d)}</div></div>', unsafe_allow_html=True)

        st.markdown("")

        # Info tableau
        st.markdown(f"""
| Paramètre | Valeur |
|---|---|
| Format | `{fmt_choice}` |
| Dimensions | `{dtf_w:.0f} × {dtf_h:.0f} mm` |
| DPI | `{dtf_dpi}` → `{wpx_d:,} × {hpx_d:,} px` |
| Mode couleur | `{"CMJN" if dtf_color=="cmyk" else "RVB"}` |
| Miroir | `{"Oui" if dtf_mirror else "Non"}` |
| White underbase | `{"Oui" if dtf_white else "Non"}` |
| Copies | `{dtf_copies}` |
| Qualité | `{dtf_qual}` |
""")

        prev_d = preview_dtf(src_d, dtf_w, dtf_h, dtf_mirror)
        st.image(prev_d, caption=f"DTF {fmt_choice} — {dtf_w:.0f}×{dtf_h:.0f} mm")

        st.markdown("")
        if not up_d:
            warn_box("Chargez un fichier pour lancer le RIP DTF.")
        else:
            info_box("Workflow DTF : TIF CMJN (vérification visuelle) + PMN (envoi direct MainTap) générés en une seule passe.")
            if st.button("🚀  Lancer RIP DTF — Générer & Imprimer",
                         type="primary", use_container_width=True, key="dtf_rip"):
                try:
                    prog_d = st.progress(0); stat_d = st.empty()
                    def cb_d(v,m): prog_d.progress(int(v)); stat_d.markdown(f"**⚙️ {m}**")

                    src_d2 = src_d or load_image(up_d)
                    tif_d, info_d = rip_dtf(src_d2, dtf_w, dtf_h, dtf_dpi, dtf_mirror, dtf_white, comp if 'comp' in dir() else 'tiff_lzw', cb_d)

                    ts  = datetime.now().strftime("%Y%m%d_%H%M")
                    bn  = Path(up_d.name).stem
                    fn_tif_d = f"{bn}_DTF_{fmt_choice}_{dtf_dpi}dpi_CMJN_{ts}.tif"
                    fn_pmn_d = fn_tif_d.replace(".tif",".pmn")

                    job_d = {"name":bn,"w_mm":dtf_w,"h_mm":dtf_h,
                             "orient":"portrait" if dtf_h>=dtf_w else "landscape",
                             "copies":dtf_copies,"dpi":dtf_dpi,"icc":"DTF_CMYK",
                             "mirror":dtf_mirror,"white_base":dtf_white,
                             "bleed":0,"cols":1,"rows":1,"gap_h":0,"gap_v":0,"margin":0,
                             "file":up_d.name,"mode":"DTF","quality":dtf_qual}
                    pmn_d = build_pmn(job_d).encode()

                    stat_d.markdown("**✅ RIP DTF terminé !**")
                    result_box(f"✅ <strong>RIP DTF terminé !</strong> &nbsp;|&nbsp; {info_d['wpx']:,}×{info_d['hpx']:,} px &nbsp;|&nbsp; {len(tif_d)/1_048_576:.1f} MB")

                    if dtf_out == "tif":
                        st.download_button("⬇️ TIF CMJN DTF", tif_d, fn_tif_d, "image/tiff", use_container_width=True)
                    elif dtf_out == "pmn":
                        st.download_button("⬇️ PMN MainTap", pmn_d, fn_pmn_d, "text/plain", use_container_width=True)
                    else:
                        readme = f"""INSTRUCTIONS IMPRESSION DTF
===========================
Fichier  : {up_d.name}
Format   : {fmt_choice} — {dtf_w:.0f}×{dtf_h:.0f} mm
DPI      : {dtf_dpi}
Couleur  : CMJN
Miroir   : {"Oui" if dtf_mirror else "Non"}
White    : {"Oui" if dtf_white else "Non"}
Copies   : {dtf_copies}

1. {fn_tif_d} → Vérification couleur
2. {fn_pmn_d} → Charger dans MainTap → Imprimer
""".encode()
                        zb_d = make_zip({fn_tif_d:tif_d, fn_pmn_d:pmn_d, "README.txt":readme})
                        st.download_button("⬇️ ZIP complet (TIF + PMN + README)", zb_d,
                            fn_tif_d.replace(".tif","_COMPLET.zip"), "application/zip", use_container_width=True)
                        dd1,dd2 = st.columns(2)
                        dd1.download_button("⬇️ TIF seul", tif_d, fn_tif_d, "image/tiff")
                        dd2.download_button("⬇️ PMN seul", pmn_d, fn_pmn_d, "text/plain")

                except Exception as e:
                    st.error(f"❌ Erreur : {e}"); st.exception(e)


# ╔═══════════════════════════════════════════════════════════
# ║  TAB 3 — SUPPRESSION DE FOND
# ╚═══════════════════════════════════════════════════════════
with tab_bg:

    bg_left, bg_right = st.columns([1, 1], gap="large")

    with bg_left:
        sec("1","Image source")
        up_bg = st.file_uploader("Chargez votre image",
            type=["png","jpg","jpeg","tif","tiff","bmp","webp"],
            key="bg_up", label_visibility="collapsed")
        src_bg = None
        if up_bg:
            try: src_bg = load_image(up_bg)
            except Exception as e: st.warning(str(e))
            if src_bg:
                result_box(f"📂 <strong>{up_bg.name}</strong> &nbsp;|&nbsp; {src_bg.width}×{src_bg.height} px")

        sec("2","Méthode de suppression")
        bg_method = st.radio("Méthode", [
            "Blanc (fond blanc)",
            "Noir (fond noir)",
            "Couleur personnalisée",
        ], key="bg_method")

        if bg_method == "Couleur personnalisée":
            info_box("Entrez la couleur du fond à supprimer en valeurs RVB (0-255).")
            bx1,bx2,bx3 = st.columns(3)
            with bx1: cr = st.number_input("Rouge (R)", 0, 255, 255, key="bg_r")
            with bx2: cg = st.number_input("Vert (G)",  0, 255, 255, key="bg_g")
            with bx3: cb_col = st.number_input("Bleu (B)", 0, 255, 255, key="bg_b")
            color_pick = (int(cr), int(cg), int(cb_col))
        else:
            color_pick = (255,255,255)

        tol = st.slider("Tolérance (sensibilité de détection)", 0, 150, 30, 5, key="bg_tol",
                        help="Augmentez si des pixels du fond restent. Diminuez si l'image est trop effacée.")

        sec("3","Options de sortie")
        bg_bg_color = st.radio("Fond de remplacement", [
            "Transparent (PNG)",
            "Blanc",
            "Noir",
            "Couleur personnalisée",
        ], key="bg_repl")

        if bg_bg_color == "Couleur personnalisée":
            br1,br2,br3 = st.columns(3)
            with br1: rr = st.number_input("Rouge", 0, 255, 255, key="bg_rr")
            with br2: rg = st.number_input("Vert",  0, 255, 255, key="bg_rg")
            with br3: rb = st.number_input("Bleu",  0, 255, 255, key="bg_rb")
            repl_color = (int(rr),int(rg),int(rb))
        else:
            repl_color = None

        bg_fmt_out = st.radio("Format de sortie", ["PNG (transparent)","TIF CMJN","Les deux (ZIP)"],
                               horizontal=True, key="bg_fmt")

    with bg_right:
        sec("","Aperçu")

        if src_bg:
            # Aperçu avant/après côte à côte
            st.markdown("**Avant**")
            # Afficher un aperçu miniature de l'original
            prev_orig = src_bg.copy()
            prev_orig.thumbnail((360, 360))
            st.image(prev_orig, use_container_width=False, width=300)

        if not up_bg:
            warn_box("Chargez une image pour utiliser la suppression de fond.")
        else:
            if st.button("✂️  Supprimer le fond", type="primary", use_container_width=True, key="bg_run"):
                if not src_bg:
                    st.error("Impossible de charger l'image.")
                else:
                    with st.spinner("Suppression du fond en cours…"):
                        result = remove_background(src_bg, bg_method, int(tol), color_pick)

                        # Appliquer fond de remplacement
                        if bg_bg_color == "Transparent (PNG)":
                            final_img = result
                        else:
                            if bg_bg_color == "Blanc":       bg_fill = (255,255,255)
                            elif bg_bg_color == "Noir":      bg_fill = (0,0,0)
                            else:                            bg_fill = repl_color
                            bg_img = Image.new("RGBA", result.size, bg_fill+(255,))
                            bg_img.paste(result, (0,0), result.split()[3])
                            final_img = bg_img

                    result_box(f"✅ Fond supprimé — {final_img.width}×{final_img.height} px")

                    # Afficher résultat
                    prev_res = final_img.copy()
                    prev_res.thumbnail((360,360))
                    st.markdown("**Après**")
                    # Fond en damier pour montrer la transparence
                    checker = Image.new("RGBA", prev_res.size, (255,255,255,255))
                    for y in range(0, prev_res.height, 12):
                        for x in range(0, prev_res.width, 12):
                            if (x//12 + y//12) % 2:
                                for dy in range(min(12,prev_res.height-y)):
                                    for dx in range(min(12,prev_res.width-x)):
                                        checker.putpixel((x+dx,y+dy),(200,200,200,255))
                    checker.paste(prev_res, (0,0), prev_res.split()[3] if prev_res.mode=="RGBA" else None)
                    st.image(checker, width=300)

                    bn = Path(up_bg.name).stem
                    ts = datetime.now().strftime("%Y%m%d_%H%M")

                    # Export PNG
                    buf_png = io.BytesIO()
                    final_img.save(buf_png, "PNG")
                    fn_png = f"{bn}_sans_fond_{ts}.png"

                    # Export TIF CMJN
                    buf_tif = io.BytesIO()
                    tif_img = final_img.convert("RGB").convert("CMYK")
                    tif_img.save(buf_tif, "TIFF", dpi=(300,300), compression="tiff_lzw")
                    fn_tif2 = f"{bn}_sans_fond_{ts}.tif"

                    if bg_fmt_out == "PNG (transparent)":
                        st.download_button("⬇️ Télécharger PNG", buf_png.getvalue(), fn_png, "image/png", use_container_width=True)
                    elif bg_fmt_out == "TIF CMJN":
                        st.download_button("⬇️ Télécharger TIF CMJN", buf_tif.getvalue(), fn_tif2, "image/tiff", use_container_width=True)
                    else:
                        zb_bg = make_zip({fn_png:buf_png.getvalue(), fn_tif2:buf_tif.getvalue()})
                        st.download_button("⬇️ Télécharger ZIP (PNG + TIF)", zb_bg,
                            f"{bn}_sans_fond_{ts}.zip", "application/zip", use_container_width=True)
                        bg1,bg2 = st.columns(2)
                        bg1.download_button("⬇️ PNG seul", buf_png.getvalue(), fn_png, "image/png")
                        bg2.download_button("⬇️ TIF seul", buf_tif.getvalue(), fn_tif2, "image/tiff")
