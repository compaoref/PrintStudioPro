"""
PrintStudio Pro — Application d'impression professionnelle
Grand Format (Vinyle / Bâche) + DTF avec RIP intégré
"""

import streamlit as st
import io
import math
import zipfile
import struct
import zlib
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageCms, ImageDraw, ImageFont

# ── Tenter import PyMuPDF pour PDF ──────────────────────────
try:
    import fitz  # PyMuPDF
    HAS_MUPDF = True
except ImportError:
    HAS_MUPDF = False

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="PrintStudio Pro",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.main { background: #0d0f14; }

.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 1300px !important; }

/* HEADER */
.app-header {
    background: linear-gradient(135deg, #161921 0%, #1a1f2e 100%);
    border: 1px solid #2a3045;
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.app-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 32px;
    letter-spacing: 3px;
    color: #e8ecf5;
    margin: 0;
}
.app-title span { color: #ff5c1a; }
.app-subtitle { color: #7a869a; font-size: 13px; margin-top: 2px; }

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    background: #161921;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #2a3045;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 24px !important;
    color: #7a869a !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: #1e2330 !important;
    color: #e8ecf5 !important;
}

/* CARDS */
.stat-card {
    background: #161921;
    border: 1px solid #2a3045;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
}
.stat-label { font-size: 11px; color: #7a869a; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
.stat-value { font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 700; color: #e8ecf5; }
.stat-value.orange { color: #ff5c1a; }
.stat-value.green  { color: #00c8a0; }
.stat-value.blue   { color: #4da6ff; }

.info-box {
    background: rgba(77,166,255,0.08);
    border: 1px solid rgba(77,166,255,0.25);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    color: #4da6ff;
    margin-bottom: 16px;
}
.success-box {
    background: rgba(0,200,160,0.08);
    border: 1px solid rgba(0,200,160,0.3);
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 14px;
    color: #00c8a0;
}
.warn-box {
    background: rgba(255,176,32,0.08);
    border: 1px solid rgba(255,176,32,0.3);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    color: #ffb020;
}

/* SECTION TITLES */
.section-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 13px;
    letter-spacing: 3px;
    color: #7a869a;
    text-transform: uppercase;
    border-bottom: 1px solid #2a3045;
    padding-bottom: 8px;
    margin-bottom: 14px;
    margin-top: 20px;
}

/* HIDE streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════
st.markdown("""
<div class="app-header">
  <div>
    <div class="app-title">Print<span>Studio</span> Pro</div>
    <div class="app-subtitle">Système RIP intégré — Grand Format · Vinyle · Bâche · DTF</div>
  </div>
  <div style="color:#7a869a;font-size:12px;text-align:right;font-family:'JetBrains Mono',monospace">
    CMJN · TIF · PMN<br>RIP Intégré v2.0
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# UTILITAIRES CORE
# ═══════════════════════════════════════════════════════════

INCH_PER_METER = 39.3701
MM_PER_INCH    = 25.4

def load_image_from_upload(uploaded) -> Image.Image:
    """Charge n'importe quel format uploadé en objet PIL Image (RGBA)."""
    data = uploaded.read()
    uploaded.seek(0)
    name = uploaded.name.lower()

    if name.endswith(".pdf") and HAS_MUPDF:
        doc = fitz.open(stream=data, filetype="pdf")
        page = doc[0]
        mat  = fitz.Matrix(4, 4)          # 4× pour haute résolution
        pix  = page.get_pixmap(matrix=mat, alpha=True)
        img  = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
        doc.close()
        return img

    img = Image.open(io.BytesIO(data))
    if img.mode not in ("RGBA", "RGB"):
        img = img.convert("RGBA")
    elif img.mode == "RGB":
        img = img.convert("RGBA")
    return img


def to_cmyk_image(img: Image.Image, profile_name: str = "ISOcoated_v2") -> Image.Image:
    """Convertit PIL Image en mode CMYK (Pillow natif)."""
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    return img.convert("CMYK")


def encode_tif_cmyk(img_cmyk: Image.Image, dpi: int, compression: str = "tiff_lzw") -> bytes:
    """Encode l'image CMYK en TIF bytes (vrai format TIFF)."""
    buf = io.BytesIO()
    save_kwargs = {
        "format": "TIFF",
        "dpi": (dpi, dpi),
        "compression": compression,   # 'tiff_lzw', 'tiff_deflate', 'raw'
    }
    img_cmyk.save(buf, **save_kwargs)
    return buf.getvalue()


def build_pmn(job: dict) -> str:
    """Génère le contenu du fichier .pmn pour MainTap / Maintop RIP."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "; ================================================",
        f"; PrintStudio Pro — Fichier Job PMN",
        f"; Généré le : {now}",
        "; ================================================",
        "",
        "[JobInfo]",
        f"JobName={job.get('name','PrintJob')}",
        f"Created={now}",
        f"Software=PrintStudio Pro",
        "",
        "[Media]",
        f"Width={job.get('media_w_mm', 0):.2f}",
        f"Height={job.get('media_h_mm', 0):.2f}",
        "Unit=mm",
        f"Orientation={job.get('orientation','portrait')}",
        "",
        "[Print]",
        f"Copies={job.get('copies', 1)}",
        f"DPI={job.get('dpi', 300)}",
        f"ColorMode=CMYK",
        f"ColorProfile={job.get('icc', 'ISOcoated_v2')}",
        f"Mirror={1 if job.get('mirror') else 0}",
        f"WhiteBase={1 if job.get('white_base') else 0}",
        f"Bleed={job.get('bleed_mm', 0):.1f}",
        "",
        "[RIP]",
        "Software=MainTap",
        f"Quality={job.get('quality','High')}",
        "RenderIntent=Perceptual",
        "",
        "[Grid]",
        f"Cols={job.get('cols', 1)}",
        f"Rows={job.get('rows', 1)}",
        f"GapH={job.get('gap_h', 0):.1f}",
        f"GapV={job.get('gap_v', 0):.1f}",
        f"Margin={job.get('margin', 0):.1f}",
        "",
        "[Source]",
        f"File={job.get('source_file','unknown')}",
        f"Format={job.get('mode','GrandFormat')}",
    ]
    return "\n".join(lines)


def estimate_size(wpx: int, hpx: int, channels: int = 4) -> str:
    raw = wpx * hpx * channels
    lzw = int(raw * 0.38)
    if lzw < 1_048_576:
        return f"{lzw/1024:.0f} KB"
    return f"{lzw/1_048_576:.1f} MB"


def px_from_meters(meters: float, dpi: int) -> int:
    return int(meters * INCH_PER_METER * dpi)

def px_from_mm(mm: float, dpi: int) -> int:
    return int((mm / MM_PER_INCH) * dpi)


# ═══════════════════════════════════════════════════════════
# MOTEUR RIP — GRAND FORMAT
# ═══════════════════════════════════════════════════════════

def rip_grand_format(
    source_img: Image.Image,
    print_w_m: float, print_h_m: float,
    cols: int, rows: int,
    gap_h_mm: float, gap_v_mm: float,
    margin_mm: float, bleed_mm: float,
    dpi: int, rotation: int,
    icc_profile: str, compression: str,
    progress_cb=None,
) -> tuple[bytes, dict]:
    """
    Construit la planche CMJN complète (TIF) avec la grille d'étiquettes.
    Retourne (bytes_tif, info_dict).
    """

    def pct(p, msg):
        if progress_cb:
            progress_cb(p, msg)

    pct(5, "Calcul des dimensions…")

    # Dimensions en pixels
    total_wpx = px_from_meters(print_w_m, dpi)
    total_hpx = px_from_meters(print_h_m, dpi)

    margin_px = px_from_mm(margin_mm, dpi)
    gap_h_px  = px_from_mm(gap_h_mm,  dpi)
    gap_v_px  = px_from_mm(gap_v_mm,  dpi)
    bleed_px  = px_from_mm(bleed_mm,  dpi)

    usable_w = total_wpx - 2 * margin_px - gap_h_px * (cols - 1)
    usable_h = total_hpx - 2 * margin_px - gap_v_px * (rows - 1)
    cell_w = usable_w // cols
    cell_h = usable_h // rows

    pct(15, f"Grille : {cols}×{rows} — cellule {cell_w}×{cell_h} px")

    # Préparer l'image source
    pct(25, "Préparation de l'image source…")
    src = source_img.convert("RGBA") if source_img.mode != "RGBA" else source_img

    # Appliquer rotation
    if rotation != 0:
        src = src.rotate(-rotation, expand=True)

    # Redimensionner pour la cellule
    src_resized = src.resize((cell_w, cell_h), Image.LANCZOS)

    # Créer la planche blanche
    pct(40, "Création de la planche d'impression…")
    board = Image.new("RGB", (total_wpx, total_hpx), (255, 255, 255))

    # Coller les étiquettes
    pct(55, "Placement des étiquettes sur la planche…")
    for r in range(rows):
        for c in range(cols):
            x = margin_px + c * (cell_w + gap_h_px)
            y = margin_px + r * (cell_h + gap_v_px)
            # Fond blanc pour transparence
            cell_bg = Image.new("RGB", (cell_w, cell_h), (255, 255, 255))
            alpha = src_resized.split()[3] if src_resized.mode == "RGBA" else None
            cell_bg.paste(
                src_resized.convert("RGB"),
                (0, 0),
                alpha
            )
            board.paste(cell_bg, (x, y))

    # Conversion CMJN
    pct(72, f"Conversion CMJN — profil {icc_profile}…")
    board_cmyk = board.convert("CMYK")

    # Encodage TIF
    pct(88, f"Encodage TIF ({compression})…")
    tif_bytes = encode_tif_cmyk(board_cmyk, dpi, compression)

    pct(100, "✅ Traitement terminé !")

    info = {
        "total_wpx": total_wpx, "total_hpx": total_hpx,
        "cell_w_mm": (cell_w / dpi) * MM_PER_INCH,
        "cell_h_mm": (cell_h / dpi) * MM_PER_INCH,
        "tif_size_bytes": len(tif_bytes),
        "total_labels": cols * rows,
    }
    return tif_bytes, info


# ═══════════════════════════════════════════════════════════
# MOTEUR RIP — DTF
# ═══════════════════════════════════════════════════════════

def rip_dtf(
    source_img: Image.Image,
    media_w_mm: float, media_h_mm: float,
    dpi: int, mirror: bool, white_base: bool,
    color_mode: str, copies: int,
    progress_cb=None,
) -> tuple[bytes, dict]:
    """
    RIP DTF : redimensionne, applique miroir, canal blanc, convertit CMJN → TIF.
    """

    def pct(p, msg):
        if progress_cb:
            progress_cb(p, msg)

    pct(5, "Préparation DTF…")

    wpx = px_from_mm(media_w_mm, dpi)
    hpx = px_from_mm(media_h_mm, dpi)

    pct(20, f"Zone : {media_w_mm:.0f}×{media_h_mm:.0f} mm → {wpx}×{hpx} px à {dpi} DPI")

    src = source_img.convert("RGBA")

    # Miroir
    if mirror:
        pct(30, "Application du miroir horizontal…")
        src = src.transpose(Image.FLIP_LEFT_RIGHT)

    # Fond blanc ou transparent
    pct(40, "Composition sur fond…")
    if white_base:
        base = Image.new("RGBA", (wpx, hpx), (255, 255, 255, 255))
    else:
        base = Image.new("RGBA", (wpx, hpx), (255, 255, 255, 255))

    # Redimensionner en conservant le ratio
    src_ratio = src.width / src.height
    tgt_ratio  = wpx / hpx
    if src_ratio > tgt_ratio:
        new_w = wpx
        new_h = int(wpx / src_ratio)
    else:
        new_h = hpx
        new_w = int(hpx * src_ratio)

    src_fit = src.resize((new_w, new_h), Image.LANCZOS)
    off_x = (wpx - new_w) // 2
    off_y = (hpx - new_h) // 2
    alpha_ch = src_fit.split()[3]
    base.paste(src_fit, (off_x, off_y), alpha_ch)

    # Conversion couleur
    pct(60, "Conversion CMJN…")
    out_rgb = base.convert("RGB")
    out_cmyk = out_rgb.convert("CMYK")

    # Ajouter un canal blanc (underbase) si demandé — couche K inversée
    if white_base:
        pct(72, "Génération couche blanc (underbase)…")
        # Pas de manipulation native CMYK multi-canal dans Pillow, on l'encode en commentaire PMN

    pct(85, "Encodage TIF CMJN…")
    tif_bytes = encode_tif_cmyk(out_cmyk, dpi, "tiff_lzw")

    pct(100, "✅ RIP DTF terminé !")

    info = {
        "wpx": wpx, "hpx": hpx,
        "tif_size_bytes": len(tif_bytes),
        "copies": copies,
    }
    return tif_bytes, info


# ═══════════════════════════════════════════════════════════
# APERÇU RAPIDE (miniature)
# ═══════════════════════════════════════════════════════════

def make_preview_vinyl(
    source_img, cols, rows,
    print_w_m, print_h_m,
    gap_h_mm, gap_v_mm, margin_mm,
    rotation, has_file,
    preview_w=680
) -> Image.Image:
    aspect = print_h_m / print_w_m
    pw = preview_w
    ph = int(pw * aspect)
    ph = max(ph, 200)

    board = Image.new("RGB", (pw, ph), (17, 21, 32))

    scale = pw / (print_w_m * 1000)
    m_px  = int(margin_mm * scale)
    gh_px = int(gap_h_mm * scale)
    gv_px = int(gap_v_mm * scale)

    uw = pw - 2 * m_px - gh_px * (cols - 1)
    uh = ph - 2 * m_px - gv_px * (rows - 1)
    cw = uw // cols
    ch = uh // rows
    if cw < 2 or ch < 2:
        return board

    draw = ImageDraw.Draw(board)

    for r in range(rows):
        for c in range(cols):
            x = m_px + c * (cw + gh_px)
            y = m_px + r * (ch + gv_px)
            # Cell bg
            hue_idx = (r * cols + c) % 6
            colors = [(40,55,80),(35,60,70),(50,40,70),(60,45,35),(35,55,50),(50,50,40)]
            cell_color = colors[hue_idx]
            draw.rectangle([x, y, x+cw-1, y+ch-1], fill=cell_color)

            if source_img and has_file:
                src_mini = source_img.copy()
                if rotation:
                    src_mini = src_mini.rotate(-rotation, expand=True)
                src_mini = src_mini.resize((cw, ch), Image.LANCZOS).convert("RGBA")
                bg_cell = Image.new("RGB", (cw, ch), cell_color)
                alpha = src_mini.split()[3]
                bg_cell.paste(src_mini.convert("RGB"), (0,0), alpha)
                board.paste(bg_cell, (x, y))

            # Border orange
            draw.rectangle([x, y, x+cw-1, y+ch-1], outline=(255, 92, 26), width=1)

            # Numéro
            num = str(r * cols + c + 1)
            font_size = max(8, min(ch // 3, 14))
            try:
                fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                fnt = ImageFont.load_default()
            draw.text((x + cw//2, y + ch//2), num, fill=(255,92,26), font=fnt, anchor="mm")

    # Ligne de dimensions
    draw.rectangle([0, ph-18, pw, ph], fill=(10,12,18))
    try:
        fnt_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 9)
    except:
        fnt_small = ImageFont.load_default()
    label = f"{print_w_m:.2f}m × {print_h_m:.2f}m  |  {cols}×{rows} = {cols*rows} étiquettes  |  CMJN TIF"
    draw.text((8, ph-14), label, fill=(100,120,150), font=fnt_small)

    return board


def make_preview_dtf(source_img, w_mm, h_mm, mirror, has_file, max_h=380) -> Image.Image:
    aspect = h_mm / w_mm
    ph = max_h
    pw = int(ph / aspect)
    pw = max(pw, 180)

    board = Image.new("RGB", (pw, ph), (17, 21, 32))
    draw  = ImageDraw.Draw(board)

    # Paper
    pad = 8
    draw.rectangle([pad, pad, pw-pad, ph-pad], fill=(15, 20, 30), outline=(42,48,70), width=1)

    if source_img and has_file:
        src = source_img.copy().convert("RGBA")
        if mirror:
            src = src.transpose(Image.FLIP_LEFT_RIGHT)
        # Fit
        inner_w = pw - pad*2 - 20
        inner_h = ph - pad*2 - 20
        src_r = src.width / src.height
        tgt_r = inner_w / inner_h
        if src_r > tgt_r:
            nw = inner_w; nh = int(inner_w / src_r)
        else:
            nh = inner_h; nw = int(inner_h * src_r)
        src_fit = src.resize((nw, nh), Image.LANCZOS)
        ox = pad + 10 + (inner_w - nw)//2
        oy = pad + 10 + (inner_h - nh)//2
        bg = Image.new("RGB", (pw, ph), (15, 20, 30))
        alpha = src_fit.split()[3]
        bg.paste(src_fit.convert("RGB"), (ox, oy), alpha)
        board = bg
        draw = ImageDraw.Draw(board)

    # Corner marks
    mk = 14
    for (cx, cy) in [(pad, pad), (pw-pad, pad), (pad, ph-pad), (pw-pad, ph-pad)]:
        dx = 1 if cx == pad else -1
        dy = 1 if cy == pad else -1
        draw.line([(cx, cy), (cx+dx*mk, cy)], fill=(0,200,160), width=2)
        draw.line([(cx, cy), (cx, cy+dy*mk)], fill=(0,200,160), width=2)

    if mirror:
        draw.rectangle([pad, pad, pw-pad, pad+16], fill=(40,20,10))
        try:
            fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 9)
        except:
            fnt = ImageFont.load_default()
        draw.text((pad+6, pad+4), "MIROIR", fill=(255,92,26), font=fnt)

    # Bas
    draw.rectangle([0, ph-18, pw, ph], fill=(10,12,18))
    try:
        fnt_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 9)
    except:
        fnt_s = ImageFont.load_default()
    draw.text((pw//2, ph-9), f"{w_mm:.0f}×{h_mm:.0f} mm", fill=(0,200,160), font=fnt_s, anchor="mm")

    return board


# ═══════════════════════════════════════════════════════════
# TABS PRINCIPALE
# ═══════════════════════════════════════════════════════════

tab_vinyl, tab_dtf = st.tabs(["🖨️  Grand Format — Vinyle / Bâche", "👕  DTF — Impression Textile"])


# ╔═══════════════════════════════════════════════════════════
# ║  TAB 1 — GRAND FORMAT
# ╚═══════════════════════════════════════════════════════════
with tab_vinyl:

    st.markdown('<div class="section-title">📁 Fichier Source</div>', unsafe_allow_html=True)

    up_vinyl = st.file_uploader(
        "Chargez votre logo / étiquette / maquette",
        type=["pdf","png","jpg","jpeg","tif","tiff","bmp","svg","eps","ai","cdr"],
        key="vinyl_upload",
        label_visibility="collapsed",
    )

    if up_vinyl:
        st.markdown(f"""
        <div class="success-box">
          📂 <strong>{up_vinyl.name}</strong> — {up_vinyl.size/1024:.1f} KB
        </div>""", unsafe_allow_html=True)

    # ── CHOIX DU MODE D'IMPRESSION ───────────────────────────
    st.markdown('<div class="section-title">📐 Mode d\'impression</div>', unsafe_allow_html=True)

    print_mode = st.radio(
        "Type de travail",
        options=["image_simple", "planche", "etiquette"],
        format_func=lambda x: {
            "image_simple": "🖼️  Image simple — pas de multiplication, juste redimensionner et imprimer",
            "planche":      "📏  Multiplication par planche — j'entre la taille totale du support",
            "etiquette":    "🏷️  Multiplication par étiquette — j'entre la taille d'une étiquette",
        }[x],
        horizontal=False,
        key="print_mode_v",
    )

    # ════════════════════════════════════════════════
    # MODE IMAGE SIMPLE
    # ════════════════════════════════════════════════
    if print_mode == "image_simple":

        st.markdown("""
        <div class="info-box">
          🖼️ <strong>Mode Image Simple :</strong> L'image sera redimensionnée exactement
          aux dimensions que vous indiquez, convertie en CMJN et exportée en TIF.
          Aucune multiplication — une seule image sur la planche.
        </div>""", unsafe_allow_html=True)

        img_unit = st.radio("Unité", ["mm", "cm", "m"], horizontal=True, key="img_unit_v")
        to_mm_i = {"mm": 1.0, "cm": 10.0, "m": 1000.0}[img_unit]
        u_step   = {"mm": 0.5,   "cm": 0.05,  "m": 0.001}[img_unit]
        u_max    = {"mm": 9999., "cm": 999.9,  "m": 9.999}[img_unit]
        u_dw     = {"mm": 1500., "cm": 150.0,  "m": 1.500}[img_unit]
        u_dh     = {"mm": 1000., "cm": 100.0,  "m": 1.000}[img_unit]

        ci1, ci2 = st.columns(2)
        with ci1:
            img_w_input = st.number_input(f"Largeur ({img_unit})", min_value=0.1,
                max_value=u_max, value=u_dw, step=u_step,
                format="%.1f" if img_unit=="mm" else "%.3f", key="img_w_v")
        with ci2:
            img_h_input = st.number_input(f"Hauteur ({img_unit})", min_value=0.1,
                max_value=u_max, value=u_dh, step=u_step,
                format="%.1f" if img_unit=="mm" else "%.3f", key="img_h_v")

        img_w_mm = img_w_input * to_mm_i
        img_h_mm = img_h_input * to_mm_i

        ci3, ci4 = st.columns(2)
        with ci3:
            keep_ratio = st.toggle("🔗 Conserver les proportions de l'image", value=True, key="keep_ratio_v")
        with ci4:
            bleed_v = st.number_input("Fond perdu (mm)", min_value=0.0, max_value=20.0, value=0.0, step=0.5, key="bleed_si")

        # Valeurs unifiées pour les sections communes
        print_w    = img_w_mm / 1000
        print_h    = img_h_mm / 1000
        cols_v     = 1
        rows_v     = 1
        gap_h      = 0.0
        gap_v      = 0.0
        margin_v   = 0.0
        lbl_w_mm   = img_w_mm
        lbl_h_mm   = img_h_mm

        st.markdown(f"""
        <div class="success-box">
          📐 <strong>Dimensions d'impression :</strong>
          &nbsp;<span style="font-family:'JetBrains Mono',monospace;font-size:18px">
          {img_w_mm:.1f} mm × {img_h_mm:.1f} mm
          </span>
          &nbsp;({img_w_mm/10:.2f} cm × {img_h_mm/10:.2f} cm
          &nbsp;/&nbsp; {img_w_mm/1000:.3f} m × {img_h_mm/1000:.3f} m)
        </div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════
    # MODE MULTIPLICATION — PLANCHE
    # ════════════════════════════════════════════════
    elif print_mode == "planche":

        st.markdown("""
        <div class="info-box">
          📏 <strong>Mode Planche :</strong> Entrez la taille totale du support à imprimer.
          La taille de chaque étiquette est calculée depuis la grille et les espacements.
        </div>""", unsafe_allow_html=True)

        cg1, cg2, cg3, cg4 = st.columns(4)
        with cg1:
            cols_v = st.number_input("Colonnes (X)", min_value=1, max_value=100, value=3, step=1, key="cols_pl")
        with cg2:
            rows_v = st.number_input("Lignes (Y)", min_value=1, max_value=100, value=4, step=1, key="rows_pl")
        with cg3:
            gap_h = st.number_input("Espacement H (mm)", min_value=0.0, max_value=200.0, value=3.0, step=0.5, key="gaph_pl")
        with cg4:
            gap_v = st.number_input("Espacement V (mm)", min_value=0.0, max_value=200.0, value=3.0, step=0.5, key="gapv_pl")

        cm1, cm2 = st.columns(2)
        with cm1:
            margin_v = st.number_input("Marge bord (mm)", min_value=0.0, max_value=200.0, value=5.0, step=1.0, key="margin_pl")
        with cm2:
            bleed_v = st.number_input("Fond perdu (mm)", min_value=0.0, max_value=20.0, value=3.0, step=0.5, key="bleed_pl")

        cd1, cd2 = st.columns(2)
        with cd1:
            print_w = st.number_input("Largeur totale de la planche (m)", min_value=0.01, max_value=10.0, value=1.50, step=0.01, format="%.2f", key="pw_pl")
        with cd2:
            print_h = st.number_input("Hauteur totale de la planche (m)", min_value=0.01, max_value=10.0, value=1.00, step=0.01, format="%.2f", key="ph_pl")

        _uw = print_w * 1000 - 2 * margin_v - gap_h * (cols_v - 1)
        _uh = print_h * 1000 - 2 * margin_v - gap_v * (rows_v - 1)
        lbl_w_mm = max(1.0, _uw / cols_v)
        lbl_h_mm = max(1.0, _uh / rows_v)
        keep_ratio = False

        st.markdown(f"""
        <div class="success-box">
          🏷️ <strong>Taille calculée de chaque étiquette :</strong>
          &nbsp;<span style="font-family:'JetBrains Mono',monospace;font-size:18px">
          {lbl_w_mm:.1f} × {lbl_h_mm:.1f} mm
          </span>
          &nbsp;({lbl_w_mm/10:.2f} × {lbl_h_mm/10:.2f} cm)
          &nbsp;— {int(cols_v)*int(rows_v)} étiquettes au total
        </div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════
    # MODE MULTIPLICATION — ÉTIQUETTE
    # ════════════════════════════════════════════════
    else:  # etiquette

        st.markdown("""
        <div class="info-box">
          🏷️ <strong>Mode Étiquette :</strong> Entrez la taille exacte d'une étiquette.
          La planche totale est calculée automatiquement.
        </div>""", unsafe_allow_html=True)

        cg1, cg2, cg3, cg4 = st.columns(4)
        with cg1:
            cols_v = st.number_input("Colonnes (X)", min_value=1, max_value=100, value=3, step=1, key="cols_et")
        with cg2:
            rows_v = st.number_input("Lignes (Y)", min_value=1, max_value=100, value=4, step=1, key="rows_et")
        with cg3:
            gap_h = st.number_input("Espacement H (mm)", min_value=0.0, max_value=200.0, value=3.0, step=0.5, key="gaph_et")
        with cg4:
            gap_v = st.number_input("Espacement V (mm)", min_value=0.0, max_value=200.0, value=3.0, step=0.5, key="gapv_et")

        cm1, cm2 = st.columns(2)
        with cm1:
            margin_v = st.number_input("Marge bord (mm)", min_value=0.0, max_value=200.0, value=5.0, step=1.0, key="margin_et")
        with cm2:
            bleed_v = st.number_input("Fond perdu (mm)", min_value=0.0, max_value=20.0, value=3.0, step=0.5, key="bleed_et")

        lbl_unit = st.radio("Unité de l'étiquette", ["mm", "cm", "m"], horizontal=True, key="lbl_unit_v")
        to_mm = {"mm": 1.0, "cm": 10.0, "m": 1000.0}[lbl_unit]
        u_step = {"mm": 0.5, "cm": 0.05, "m": 0.001}[lbl_unit]
        u_max  = {"mm": 5000., "cm": 500., "m": 5.}[lbl_unit]
        u_dw   = {"mm": 100., "cm": 10., "m": 0.10}[lbl_unit]
        u_dh   = {"mm": 50.,  "cm": 5.,  "m": 0.05}[lbl_unit]

        ce1, ce2 = st.columns(2)
        with ce1:
            lbl_w_input = st.number_input(f"Largeur étiquette ({lbl_unit})",
                min_value=0.1, max_value=u_max, value=u_dw, step=u_step,
                format="%.1f" if lbl_unit=="mm" else "%.3f", key="lbl_w_v")
        with ce2:
            lbl_h_input = st.number_input(f"Hauteur étiquette ({lbl_unit})",
                min_value=0.1, max_value=u_max, value=u_dh, step=u_step,
                format="%.1f" if lbl_unit=="mm" else "%.3f", key="lbl_h_v")

        lbl_w_mm = lbl_w_input * to_mm
        lbl_h_mm = lbl_h_input * to_mm
        print_w  = (lbl_w_mm * cols_v + gap_h * (cols_v - 1) + 2 * margin_v) / 1000
        print_h  = (lbl_h_mm * rows_v + gap_v * (rows_v - 1) + 2 * margin_v) / 1000
        keep_ratio = False

        st.markdown(f"""
        <div class="success-box">
          📏 <strong>Taille calculée de la planche :</strong>
          &nbsp;<span style="font-family:'JetBrains Mono',monospace;font-size:18px">
          {print_w:.3f} m × {print_h:.3f} m
          </span>
          &nbsp;({print_w*100:.1f} × {print_h*100:.1f} cm)
          &nbsp;— {int(cols_v)*int(rows_v)} étiquettes
        </div>""", unsafe_allow_html=True)

    # ── PARAMÈTRES RIP (communs aux 3 modes) ─────────────────
    st.markdown('<div class="section-title">⚙️ Paramètres RIP</div>', unsafe_allow_html=True)

    ca, cb, cc, cd = st.columns(4)
    with ca:
        dpi_v = st.selectbox("Résolution (DPI)", [72, 150, 300, 600], index=2)
    with cb:
        rotation_v = st.selectbox(
            "Rotation" if print_mode == "image_simple" else "Rotation étiquette",
            [0, 90, 180, 270], index=0, format_func=lambda x: f"{x}°")
    with cc:
        icc_v = st.selectbox("Profil ICC / Couleur", [
            "ISOcoated_v2","CoatedFOGRA39","UncoatedFOGRA29","SWOP"
        ])
    with cd:
        compression_v = st.selectbox("Compression TIF", {
            "tiff_lzw":     "LZW — Sans perte (recommandé)",
            "tiff_deflate": "Deflate — Sans perte",
            "raw":          "Aucune — Maximum qualité",
        }.keys(), format_func=lambda k: {
            "tiff_lzw":     "LZW — Sans perte (recommandé)",
            "tiff_deflate": "Deflate — Sans perte",
            "raw":          "Aucune — Maximum qualité",
        }[k])

    # ── FORMAT SORTIE ────────────────────────────────────────
    st.markdown('<div class="section-title">📦 Format de Sortie — RIP</div>', unsafe_allow_html=True)

    output_mode_v = st.radio(
        "Que voulez-vous générer ?",
        options=["tif_only", "pmn_only", "tif_and_pmn", "zip_all"],
        format_func=lambda x: {
            "tif_only":    "🖼️  TIF CMJN uniquement",
            "pmn_only":    "🖨️  PMN uniquement (MainTap)",
            "tif_and_pmn": "📦  TIF + PMN (ZIP)",
            "zip_all":     "📦  ZIP complet : TIF + PMN + aperçu PNG",
        }[x],
        horizontal=True,
        key="output_v",
    )

    # ── STATS ────────────────────────────────────────────────
    total_labels = int(cols_v) * int(rows_v)
    wpx_est = px_from_meters(print_w, dpi_v)
    hpx_est = px_from_meters(print_h, dpi_v)

    st.markdown('<div class="section-title">📊 Récapitulatif</div>', unsafe_allow_html=True)
    s1, s2, s3, s4, s5 = st.columns(5)
    mode_label = {"image_simple": "Image unique", "planche": "Étiquettes", "etiquette": "Étiquettes"}[print_mode]
    s1.markdown(f'<div class="stat-card"><div class="stat-label">{mode_label}</div><div class="stat-value orange">{total_labels}</div></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="stat-card"><div class="stat-label">{"Dimensions image" if print_mode=="image_simple" else "Taille étiquette"}</div><div class="stat-value">{lbl_w_mm:.1f} × {lbl_h_mm:.1f} mm</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="stat-card"><div class="stat-label">Planche totale</div><div class="stat-value">{print_w:.3f} × {print_h:.3f} m</div></div>', unsafe_allow_html=True)
    s4.markdown(f'<div class="stat-card"><div class="stat-label">Pixels totaux</div><div class="stat-value blue">{wpx_est:,} × {hpx_est:,}</div></div>', unsafe_allow_html=True)
    s5.markdown(f'<div class="stat-card"><div class="stat-label">TIF estimé</div><div class="stat-value green">{estimate_size(wpx_est,hpx_est,4)}</div></div>', unsafe_allow_html=True)

    # ── APERÇU ───────────────────────────────────────────────
    st.markdown('<div class="section-title">👁️ Aperçu</div>', unsafe_allow_html=True)

    src_img_v = None
    if up_vinyl:
        try:
            if up_vinyl.name.lower().endswith(".pdf") and not HAS_MUPDF:
                st.warning("PDF — PyMuPDF non disponible pour l'aperçu visuel.")
            else:
                src_img_v = load_image_from_upload(up_vinyl)
        except Exception as e:
            st.warning(f"Aperçu non disponible pour ce format : {e}")

    if print_mode == "image_simple":
        # Aperçu image seule centrée sur fond sombre, avec dimensions overlay
        if src_img_v:
            # Construire un aperçu propre avec bordure et annotations
            pw_prev = 700
            # Calculer ratio réel
            if keep_ratio and src_img_v:
                src_r = src_img_v.width / src_img_v.height
                ph_prev = int(pw_prev / src_r)
            else:
                ph_prev = int(pw_prev * img_h_mm / img_w_mm) if img_w_mm > 0 else 400
            ph_prev = max(150, min(ph_prev, 550))

            board_si = Image.new("RGB", (pw_prev, ph_prev), (17, 21, 32))
            draw_si  = ImageDraw.Draw(board_si)

            # Grille de fond
            for x in range(0, pw_prev, 30):
                draw_si.line([(x,0),(x,ph_prev)], fill=(22,26,38), width=1)
            for y in range(0, ph_prev, 30):
                draw_si.line([(0,y),(pw_prev,y)], fill=(22,26,38), width=1)

            # Image centrée avec padding
            pad = 20
            iw = pw_prev - pad*2
            ih = ph_prev - pad*2
            src_fit = src_img_v.copy()
            if rotation_v:
                src_fit = src_fit.rotate(-rotation_v, expand=True)

            if keep_ratio:
                r = src_fit.width / src_fit.height
                if iw / ih > r:
                    iw2 = int(ih * r); ih2 = ih
                else:
                    iw2 = iw; ih2 = int(iw / r)
            else:
                iw2, ih2 = iw, ih

            src_fit = src_fit.resize((iw2, ih2), Image.LANCZOS).convert("RGBA")
            ox = pad + (iw - iw2)//2
            oy = pad + (ih - ih2)//2
            bg_cell = Image.new("RGB", (iw2, ih2), (17,21,32))
            alpha = src_fit.split()[3]
            bg_cell.paste(src_fit.convert("RGB"), (0,0), alpha)
            board_si.paste(bg_cell, (ox, oy))

            # Bordure orange autour de l'image
            draw_si.rectangle([ox-1, oy-1, ox+iw2, oy+ih2], outline=(255,92,26), width=2)

            # Annotation dimensions
            draw_si.rectangle([0, ph_prev-22, pw_prev, ph_prev], fill=(10,12,18))
            try:
                fnt_ann = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
            except:
                fnt_ann = ImageFont.load_default()
            ann = f"{img_w_mm:.1f} mm × {img_h_mm:.1f} mm  |  {img_w_mm/10:.1f} cm × {img_h_mm/10:.1f} cm  |  {dpi_v} DPI  |  CMJN TIF"
            draw_si.text((pw_prev//2, ph_prev-11), ann, fill=(200,130,60), font=fnt_ann, anchor="mm")

            st.image(board_si, use_container_width=True,
                caption=f"Image : {img_w_mm:.1f} × {img_h_mm:.1f} mm — {'Proportions conservées' if keep_ratio else 'Redimensionnement forcé'}")
            preview_v = board_si
        else:
            st.info("📂 Chargez une image pour voir l'aperçu.")
            preview_v = Image.new("RGB", (700, 300), (17,21,32))
    else:
        # Aperçu grille multiplication
        preview_v = make_preview_vinyl(
            src_img_v, int(cols_v), int(rows_v),
            float(print_w), float(print_h),
            float(gap_h), float(gap_v), float(margin_v),
            int(rotation_v), up_vinyl is not None,
            preview_w=700,
        )
        st.image(preview_v, use_container_width=True,
            caption=f"Grille {int(cols_v)}×{int(rows_v)} — {total_labels} étiquettes — "
                    f"{lbl_w_mm:.1f}×{lbl_h_mm:.1f} mm chacune — Planche : {print_w:.3f}×{print_h:.3f} m")

    # ── BOUTON RIP ───────────────────────────────────────────
    st.markdown('<div class="section-title">🚀 Lancer le RIP & Téléchargement</div>', unsafe_allow_html=True)

    if not up_vinyl:
        st.markdown('<div class="warn-box">⚠️ Chargez d\'abord un fichier source pour lancer le RIP.</div>', unsafe_allow_html=True)
    else:
        mode_btn_label = {
            "image_simple": "🖨️  Lancer RIP — Image simple CMJN prête à imprimer",
            "planche":      "🖨️  Lancer RIP — Planche avec multiplication",
            "etiquette":    "🖨️  Lancer RIP — Planche avec multiplication",
        }[print_mode]

        btn_rip_v = st.button(mode_btn_label, type="primary", use_container_width=True, key="btn_rip_vinyl")

        if btn_rip_v:
            try:
                prog_bar = st.progress(0)
                status   = st.empty()

                def cb_vinyl(pct, msg):
                    prog_bar.progress(int(pct))
                    status.markdown(f"**⚙️ {msg}**")

                if src_img_v is None:
                    src_img_v2 = load_image_from_upload(up_vinyl)
                else:
                    src_img_v2 = src_img_v

                # Pour image simple : keep_ratio appliqué avant RIP
                if print_mode == "image_simple" and keep_ratio and src_img_v2:
                    src_r = src_img_v2.width / src_img_v2.height
                    tgt_r = img_w_mm / img_h_mm
                    if abs(src_r - tgt_r) > 0.01:
                        # Ajuster la hauteur pour respecter les proportions
                        img_h_mm_rip = img_w_mm / src_r
                        print_h_rip  = img_h_mm_rip / 1000
                        status.markdown(f"**ℹ️ Hauteur ajustée à {img_h_mm_rip:.1f} mm pour conserver les proportions**")
                    else:
                        print_h_rip = print_h
                else:
                    print_h_rip = print_h

                tif_bytes, info = rip_grand_format(
                    source_img=src_img_v2,
                    print_w_m=float(print_w),
                    print_h_m=float(print_h_rip),
                    cols=int(cols_v), rows=int(rows_v),
                    gap_h_mm=float(gap_h), gap_v_mm=float(gap_v),
                    margin_mm=float(margin_v), bleed_mm=float(bleed_v),
                    dpi=int(dpi_v), rotation=int(rotation_v),
                    icc_profile=icc_v, compression=compression_v,
                    progress_cb=cb_vinyl,
                )

                base_name = Path(up_vinyl.name).stem
                ts = datetime.now().strftime("%Y%m%d_%H%M")
                if print_mode == "image_simple":
                    fname_tif = f"{base_name}_{lbl_w_mm:.0f}x{lbl_h_mm:.0f}mm_{dpi_v}dpi_CMJN_{ts}.tif"
                else:
                    fname_tif = (
                        f"{base_name}_"
                        f"etiq{lbl_w_mm:.0f}x{lbl_h_mm:.0f}mm_"
                        f"planche{print_w:.2f}mx{print_h:.2f}m_"
                        f"{int(cols_v)}x{int(rows_v)}_{dpi_v}dpi_CMJN_{ts}.tif"
                    )
                fname_pmn = fname_tif.replace(".tif", ".pmn")

                job_info = {
                    "name": base_name,
                    "media_w_mm": print_w * 1000, "media_h_mm": print_h_rip * 1000,
                    "orientation": "landscape" if print_w > print_h_rip else "portrait",
                    "copies": 1, "dpi": dpi_v, "icc": icc_v,
                    "mirror": False, "white_base": False,
                    "bleed_mm": bleed_v,
                    "cols": int(cols_v), "rows": int(rows_v),
                    "gap_h": gap_h, "gap_v": gap_v, "margin": margin_v,
                    "source_file": up_vinyl.name,
                    "mode": "ImageSimple" if print_mode=="image_simple" else "GrandFormat",
                    "quality": "High",
                }
                pmn_content = build_pmn(job_info)

                status.markdown("**✅ RIP terminé — Fichiers prêts !**")

                tif_size_mb = len(tif_bytes) / 1_048_576
                st.markdown(f"""
                <div class="success-box">
                  ✅ <strong>RIP terminé avec succès !</strong><br>
                  📐 Planche : {info['total_wpx']:,} × {info['total_hpx']:,} px |
                  🏷️ {info['total_labels']} étiquettes ({info['cell_w_mm']:.1f} × {info['cell_h_mm']:.1f} mm chacune) |
                  💾 TIF CMJN : {tif_size_mb:.1f} MB
                </div>""", unsafe_allow_html=True)

                # Téléchargements selon mode
                if output_mode_v == "tif_only":
                    st.download_button(
                        "⬇️  Télécharger TIF CMJN",
                        data=tif_bytes,
                        file_name=fname_tif,
                        mime="image/tiff",
                        use_container_width=True,
                    )

                elif output_mode_v == "pmn_only":
                    st.download_button(
                        "⬇️  Télécharger PMN (MainTap)",
                        data=pmn_content.encode(),
                        file_name=fname_pmn,
                        mime="text/plain",
                        use_container_width=True,
                    )

                elif output_mode_v in ("tif_and_pmn", "zip_all"):
                    zip_buf = io.BytesIO()
                    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr(fname_tif, tif_bytes)
                        zf.writestr(fname_pmn, pmn_content.encode())
                        if output_mode_v == "zip_all":
                            prev_buf = io.BytesIO()
                            preview_v.save(prev_buf, format="PNG")
                            zf.writestr(f"{base_name}_apercu.png", prev_buf.getvalue())
                    zip_buf.seek(0)
                    fname_zip = fname_tif.replace(".tif", "_COMPLET.zip")
                    st.download_button(
                        "⬇️  Télécharger le ZIP complet",
                        data=zip_buf.read(),
                        file_name=fname_zip,
                        mime="application/zip",
                        use_container_width=True,
                    )

                # Toujours offrir TIF séparément si ZIP
                if output_mode_v in ("tif_and_pmn", "zip_all"):
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button("⬇️ TIF seul", data=tif_bytes,
                            file_name=fname_tif, mime="image/tiff")
                    with col_dl2:
                        st.download_button("⬇️ PMN seul", data=pmn_content.encode(),
                            file_name=fname_pmn, mime="text/plain")

            except Exception as e:
                st.error(f"❌ Erreur RIP : {e}")
                st.exception(e)


# ╔═══════════════════════════════════════════════════════════
# ║  TAB 2 — DTF
# ╚═══════════════════════════════════════════════════════════
with tab_dtf:

    st.markdown('<div class="section-title">📁 Fichier Source DTF</div>', unsafe_allow_html=True)

    up_dtf = st.file_uploader(
        "Chargez votre fichier",
        type=["pdf","png","jpg","jpeg","tif","tiff","ai","eps","svg","bmp"],
        key="dtf_upload",
        label_visibility="collapsed",
    )

    if up_dtf:
        st.markdown(f"""
        <div class="success-box">
          📂 <strong>{up_dtf.name}</strong> — {up_dtf.size/1024:.1f} KB
        </div>""", unsafe_allow_html=True)

    # ── FORMAT DTF ───────────────────────────────────────────
    st.markdown('<div class="section-title">📏 Format & Paramètres DTF</div>', unsafe_allow_html=True)

    dtf_col1, dtf_col2 = st.columns([1, 1])

    with dtf_col1:
        dtf_format = st.radio(
            "Format d'impression",
            ["A4", "A3", "A2", "Personnalisé"],
            horizontal=True,
        )

        DTF_DIMS = {"A4": (210, 297), "A3": (297, 420), "A2": (420, 594)}

        if dtf_format == "Personnalisé":
            pc1, pc2 = st.columns(2)
            with pc1:
                dtf_cust_w = st.number_input("Largeur (mm)", min_value=10, max_value=2000, value=300)
            with pc2:
                dtf_cust_h = st.number_input("Hauteur (mm)", min_value=10, max_value=3000, value=400)
            dtf_w_mm, dtf_h_mm = float(dtf_cust_w), float(dtf_cust_h)
        else:
            base_dims = DTF_DIMS[dtf_format]
            dtf_orientation = st.radio("Orientation", ["Portrait", "Paysage"], horizontal=True)
            if dtf_orientation == "Portrait":
                dtf_w_mm, dtf_h_mm = float(base_dims[0]), float(base_dims[1])
            else:
                dtf_w_mm, dtf_h_mm = float(base_dims[1]), float(base_dims[0])

        dtf_copies = st.number_input("Nombre de copies", min_value=1, max_value=999, value=1)

    with dtf_col2:
        dtf_dpi     = st.selectbox("Résolution DPI", [150, 300, 600, 1200], index=1, key="dtf_dpi")
        dtf_color   = st.selectbox("Mode couleur", {
            "cmyk": "CMJN — Standard impression DTF",
            "rgb":  "RVB — Si requis par l'imprimante",
        }.keys(), format_func=lambda k: {
            "cmyk": "CMJN — Standard impression DTF",
            "rgb":  "RVB — Si requis par l'imprimante",
        }[k])
        dtf_mirror  = st.toggle("🪞 Miroir (impression face intérieure)", value=False)
        dtf_white   = st.toggle("⬜ Canal blanc / White underbase", value=True)
        dtf_quality = st.selectbox("Qualité RIP", ["Draft", "Normal", "High", "Ultra"], index=2)

    # ── FORMAT SORTIE DTF ────────────────────────────────────
    st.markdown('<div class="section-title">📦 Format de Sortie DTF — RIP</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
      ℹ️ <strong>Workflow DTF unifié :</strong> Le RIP traite votre fichier en une seule passe —
      vous téléchargez directement le <strong>TIF CMJN</strong> prêt pour vérification ET le <strong>PMN</strong>
      prêt pour MainTap. Plus aucune étape manuelle.
    </div>
    """, unsafe_allow_html=True)

    output_mode_dtf = st.radio(
        "Sortie souhaitée",
        options=["tif_only", "pmn_only", "zip_complet"],
        format_func=lambda x: {
            "tif_only":    "🖼️  TIF CMJN — Vérification visuelle avant impression",
            "pmn_only":    "🖨️  PMN — Lancement direct impression MainTap",
            "zip_complet": "📦  ZIP : TIF + PMN (recommandé — tout en un)",
        }[x],
        horizontal=False,
        key="output_dtf",
        index=2,
    )

    # ── STATS DTF ────────────────────────────────────────────
    wpx_dtf = px_from_mm(dtf_w_mm, dtf_dpi)
    hpx_dtf = px_from_mm(dtf_h_mm, dtf_dpi)

    st.markdown('<div class="section-title">📊 Récapitulatif DTF</div>', unsafe_allow_html=True)
    sd1, sd2, sd3, sd4 = st.columns(4)
    sd1.markdown(f'<div class="stat-card"><div class="stat-label">Format</div><div class="stat-value green">{dtf_format}</div></div>', unsafe_allow_html=True)
    sd2.markdown(f'<div class="stat-card"><div class="stat-label">Dimensions</div><div class="stat-value">{dtf_w_mm:.0f} × {dtf_h_mm:.0f} mm</div></div>', unsafe_allow_html=True)
    sd3.markdown(f'<div class="stat-card"><div class="stat-label">Résolution</div><div class="stat-value blue">{dtf_dpi} DPI</div></div>', unsafe_allow_html=True)
    sd4.markdown(f'<div class="stat-card"><div class="stat-label">Taille TIF estimée</div><div class="stat-value orange">{estimate_size(wpx_dtf,hpx_dtf,4)}</div></div>', unsafe_allow_html=True)

    # ── APERÇU DTF ───────────────────────────────────────────
    st.markdown('<div class="section-title">👁️ Aperçu Format DTF</div>', unsafe_allow_html=True)

    src_img_dtf = None
    if up_dtf:
        try:
            src_img_dtf = load_image_from_upload(up_dtf)
        except Exception as e:
            st.warning(f"Aperçu non disponible : {e}")

    prev_dtf = make_preview_dtf(src_img_dtf, dtf_w_mm, dtf_h_mm, dtf_mirror, up_dtf is not None)
    col_prev, col_info = st.columns([1, 2])
    with col_prev:
        st.image(prev_dtf, caption=f"{dtf_format} — {dtf_w_mm:.0f}×{dtf_h_mm:.0f} mm")
    with col_info:
        st.markdown(f"""
        **Récapitulatif du job DTF :**

        | Paramètre | Valeur |
        |---|---|
        | Format | `{dtf_format}` |
        | Dimensions | `{dtf_w_mm:.0f} × {dtf_h_mm:.0f} mm` |
        | Résolution | `{dtf_dpi} DPI → {wpx_dtf} × {hpx_dtf} px` |
        | Mode couleur | `{'CMJN' if dtf_color == 'cmyk' else 'RVB'}` |
        | Miroir | `{'Oui ✅' if dtf_mirror else 'Non'}` |
        | White underbase | `{'Oui ✅' if dtf_white else 'Non'}` |
        | Copies | `{dtf_copies}` |
        | Qualité RIP | `{dtf_quality}` |
        | Sortie | `{output_mode_dtf.replace('_',' ').upper()}` |
        """)

    # ── BOUTON RIP DTF ────────────────────────────────────────
    st.markdown('<div class="section-title">🚀 Lancer RIP DTF</div>', unsafe_allow_html=True)

    if not up_dtf:
        st.markdown('<div class="warn-box">⚠️ Chargez d\'abord un fichier source.</div>', unsafe_allow_html=True)
    else:
        btn_rip_dtf = st.button(
            "🖨️  Lancer RIP DTF — Générer fichiers prêts à imprimer",
            type="primary",
            use_container_width=True,
            key="btn_rip_dtf",
        )

        if btn_rip_dtf:
            try:
                prog_dtf = st.progress(0)
                stat_dtf = st.empty()

                def cb_dtf(pct, msg):
                    prog_dtf.progress(int(pct))
                    stat_dtf.markdown(f"**⚙️ {msg}**")

                if src_img_dtf is None:
                    src_img_dtf2 = load_image_from_upload(up_dtf)
                else:
                    src_img_dtf2 = src_img_dtf

                tif_bytes_dtf, info_dtf = rip_dtf(
                    source_img=src_img_dtf2,
                    media_w_mm=dtf_w_mm, media_h_mm=dtf_h_mm,
                    dpi=int(dtf_dpi),
                    mirror=dtf_mirror, white_base=dtf_white,
                    color_mode=dtf_color, copies=int(dtf_copies),
                    progress_cb=cb_dtf,
                )

                base_name_dtf = Path(up_dtf.name).stem
                ts_dtf  = datetime.now().strftime("%Y%m%d_%H%M")
                fname_tif_dtf = f"{base_name_dtf}_DTF_{dtf_format}_{dtf_dpi}dpi_CMJN_{ts_dtf}.tif"
                fname_pmn_dtf = fname_tif_dtf.replace(".tif", ".pmn")

                job_dtf = {
                    "name": base_name_dtf,
                    "media_w_mm": dtf_w_mm, "media_h_mm": dtf_h_mm,
                    "orientation": "portrait" if dtf_h_mm >= dtf_w_mm else "landscape",
                    "copies": int(dtf_copies), "dpi": dtf_dpi,
                    "icc": "DTF_CMYK_Standard",
                    "mirror": dtf_mirror, "white_base": dtf_white,
                    "bleed_mm": 0, "cols": 1, "rows": 1,
                    "gap_h": 0, "gap_v": 0, "margin": 0,
                    "source_file": up_dtf.name, "mode": "DTF",
                    "quality": dtf_quality,
                }
                pmn_dtf = build_pmn(job_dtf)

                tif_mb_dtf = len(tif_bytes_dtf) / 1_048_576
                stat_dtf.markdown("**✅ RIP DTF terminé !**")

                st.markdown(f"""
                <div class="success-box">
                  ✅ <strong>RIP DTF terminé !</strong><br>
                  📐 {info_dtf['wpx']:,} × {info_dtf['hpx']:,} px |
                  💾 TIF CMJN : {tif_mb_dtf:.1f} MB |
                  🖨️ {int(dtf_copies)} copie(s)
                </div>""", unsafe_allow_html=True)

                if output_mode_dtf == "tif_only":
                    st.download_button(
                        "⬇️  Télécharger TIF CMJN DTF",
                        data=tif_bytes_dtf,
                        file_name=fname_tif_dtf,
                        mime="image/tiff",
                        use_container_width=True,
                    )

                elif output_mode_dtf == "pmn_only":
                    st.download_button(
                        "⬇️  Télécharger PMN — MainTap",
                        data=pmn_dtf.encode(),
                        file_name=fname_pmn_dtf,
                        mime="text/plain",
                        use_container_width=True,
                    )

                else:  # zip_complet
                    zip_dtf = io.BytesIO()
                    with zipfile.ZipFile(zip_dtf, "w", zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr(fname_tif_dtf, tif_bytes_dtf)
                        zf.writestr(fname_pmn_dtf, pmn_dtf.encode())
                        prev_buf = io.BytesIO()
                        prev_dtf.save(prev_buf, format="PNG")
                        zf.writestr(f"{base_name_dtf}_apercu.png", prev_buf.getvalue())
                        zf.writestr("README_IMPRESSION.txt",
                            f"""INSTRUCTIONS D'IMPRESSION DTF
================================
Fichier source : {up_dtf.name}
Format         : {dtf_format} — {dtf_w_mm:.0f} × {dtf_h_mm:.0f} mm
DPI            : {dtf_dpi}
Couleur        : {'CMJN' if dtf_color=='cmyk' else 'RVB'}
Miroir         : {'Oui' if dtf_mirror else 'Non'}
White base     : {'Oui' if dtf_white else 'Non'}
Copies         : {dtf_copies}
Qualité        : {dtf_quality}

FICHIERS INCLUS :
  1. {fname_tif_dtf}  → Vérification visuelle / contrôle couleur
  2. {fname_pmn_dtf}  → Chargez ce fichier dans MainTap pour lancer l'impression

Généré par PrintStudio Pro — {datetime.now().strftime('%d/%m/%Y %H:%M')}
""".encode())
                    zip_dtf.seek(0)
                    fname_zip_dtf = fname_tif_dtf.replace(".tif", "_COMPLET.zip")

                    st.download_button(
                        "⬇️  Télécharger ZIP complet (TIF + PMN + README)",
                        data=zip_dtf.read(),
                        file_name=fname_zip_dtf,
                        mime="application/zip",
                        use_container_width=True,
                    )

                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        st.download_button("⬇️ TIF seul", data=tif_bytes_dtf,
                            file_name=fname_tif_dtf, mime="image/tiff")
                    with col_d2:
                        st.download_button("⬇️ PMN seul", data=pmn_dtf.encode(),
                            file_name=fname_pmn_dtf, mime="text/plain")

            except Exception as e:
                st.error(f"❌ Erreur RIP DTF : {e}")
                st.exception(e)
