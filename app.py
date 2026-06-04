"""
PrintStudio Pro v4.0
Système RIP professionnel — Grand Format · DTF · Suppression de fond IA
"""
import streamlit as st
import io, zipfile, math
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import cv2

try:
    import fitz
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# ─────────────────────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────────────────────
st.set_page_config(page_title="PrintStudio Pro", page_icon="🖨️",
                   layout="wide", initial_sidebar_state="expanded")

# ─────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Paramètres")
    DARK = st.radio("Thème", ["🌙 Sombre", "☀️ Clair"], index=0) == "🌙 Sombre"
    st.markdown("---")
    st.markdown("**PrintStudio Pro** `v4.0`")
    st.caption("Système RIP intégré\nCMJN · TIF · PRN\nGrand Format · DTF")
    st.markdown("---")
    st.caption("Formats supportés :\nPDF · PNG · JPG · TIF\nAI · EPS · CDR · SVG · BMP")

# ─────────────────────────────────────────────────────────
# THÈME
# ─────────────────────────────────────────────────────────
if DARK:
    BG="#0d0f14";SRF="#161921";SRF2="#1e2330";BOR="#2a3045"
    TXT="#e8ecf5";MUT="#7a869a";ACC="#ff5c1a";GRN="#00c8a0";BLU="#4da6ff";WRN="#ffb020"
    PBG="#111520";PGR="#1d2235";SHD="rgba(0,0,0,.25)"
    IBG="rgba(77,166,255,.07)";IBD="rgba(77,166,255,.3)"
    OBG="rgba(0,200,160,.07)";OBD="rgba(0,200,160,.35)"
    WBG="rgba(255,176,32,.07)";WBD="rgba(255,176,32,.3)"
else:
    BG="#f4f6fb";SRF="#ffffff";SRF2="#eef0f8";BOR="#d5d9ec"
    TXT="#1a1e2e";MUT="#6b7280";ACC="#e64a00";GRN="#00a882";BLU="#2563eb";WRN="#d97706"
    PBG="#e8eaf2";PGR="#d2d6e8";SHD="rgba(0,0,0,.07)"
    IBG="rgba(37,99,235,.06)";IBD="rgba(37,99,235,.25)"
    OBG="rgba(0,168,130,.07)";OBD="rgba(0,168,130,.3)"
    WBG="rgba(217,119,6,.06)";WBD="rgba(217,119,6,.25)"

# ─────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html,body,[class*="css"],.stApp{{font-family:'Inter',sans-serif!important;background:{BG}!important;color:{TXT}!important}}
.block-container{{padding-top:1rem!important;padding-bottom:3rem!important;max-width:1340px!important}}
/* HEADER */
.hdr{{background:{SRF};border:1px solid {BOR};border-radius:16px;padding:22px 32px;margin-bottom:22px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 16px {SHD}}}
.hdr-logo{{font-size:26px;font-weight:800;color:{TXT};letter-spacing:-.5px}}
.hdr-logo em{{color:{ACC};font-style:normal}}
.hdr-sub{{font-size:12px;color:{MUT};margin-top:3px}}
.badge{{background:{ACC};color:white;font-size:10px;font-weight:700;padding:3px 10px;border-radius:20px;letter-spacing:1px;text-transform:uppercase}}
/* SEC */
.sec{{display:flex;align-items:center;gap:9px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:{MUT};padding:16px 0 9px;border-bottom:1px solid {BOR};margin-bottom:13px}}
.sn{{width:21px;height:21px;background:{ACC};color:white;border-radius:50%;font-size:11px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}}
/* STAT CARDS */
.sc{{background:{SRF};border:1px solid {BOR};border-radius:11px;padding:13px 10px;text-align:center;box-shadow:0 1px 4px {SHD}}}
.sc .l{{font-size:10px;font-weight:600;color:{MUT};text-transform:uppercase;letter-spacing:.7px;margin-bottom:5px}}
.sc .v{{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:700;color:{TXT};line-height:1.3}}
.sc .v.a{{color:{ACC}}}.sc .v.g{{color:{GRN}}}.sc .v.b{{color:{BLU}}}
/* BOXES */
.rb{{background:{OBG};border:1.5px solid {OBD};border-radius:10px;padding:12px 15px;font-size:13px;color:{GRN};margin:11px 0;line-height:1.6}}
.ib{{background:{IBG};border:1.5px solid {IBD};border-radius:10px;padding:11px 14px;font-size:13px;color:{BLU};margin:9px 0 13px}}
.wb{{background:{WBG};border:1.5px solid {WBD};border-radius:10px;padding:11px 14px;font-size:13px;color:{WRN};margin:9px 0}}
/* UPLOAD CARD */
.up-card{{background:{SRF2};border:2px dashed {BOR};border-radius:12px;padding:16px;margin-bottom:8px;transition:border-color .2s}}
/* TABS */
.stTabs [data-baseweb="tab-list"]{{background:{SRF};border-radius:12px;padding:5px;gap:3px;border:1px solid {BOR};box-shadow:0 1px 6px {SHD}}}
.stTabs [data-baseweb="tab"]{{border-radius:9px!important;font-weight:600!important;font-size:13px!important;padding:9px 18px!important;color:{MUT}!important;background:transparent!important;transition:all .2s!important}}
.stTabs [aria-selected="true"]{{background:{ACC}!important;color:white!important}}
/* INPUTS */
.stNumberInput input,.stSelectbox select,.stTextInput input{{background:{SRF2}!important;border:1px solid {BOR}!important;border-radius:8px!important;color:{TXT}!important;font-size:14px!important}}
/* SIDEBAR */
[data-testid="stSidebar"]{{background:{SRF}!important;border-right:1px solid {BOR}!important}}
/* FILE UPLOADER */
[data-testid="stFileUploader"]{{background:{SRF2}!important;border:2px dashed {BOR}!important;border-radius:12px!important}}
/* BUTTONS */
.stButton>button{{background:{ACC}!important;color:white!important;border:none!important;border-radius:10px!important;font-weight:600!important;font-size:14px!important;padding:11px 24px!important;transition:all .2s!important;box-shadow:0 2px 8px rgba(255,92,26,.28)!important}}
.stButton>button:hover{{transform:translateY(-1px)!important;box-shadow:0 4px 14px rgba(255,92,26,.38)!important}}
.stDownloadButton>button{{background:{GRN}!important;color:{'#051210' if DARK else 'white'}!important;border:none!important;border-radius:10px!important;font-weight:700!important;padding:11px 24px!important;box-shadow:0 2px 8px rgba(0,200,160,.25)!important}}
.stRadio label{{font-size:13px!important;font-weight:500!important;color:{TXT}!important}}
hr{{border-color:{BOR}!important;margin:16px 0!important}}
#MainMenu,footer,header{{visibility:hidden}}
/* SLOT CARD (multi-image) */
.slot-hdr{{background:{SRF};border:1px solid {BOR};border-radius:9px;padding:10px 14px;display:flex;align-items:center;gap:10px;margin-bottom:6px}}
.slot-num{{width:28px;height:28px;background:{ACC};color:white;border-radius:6px;font-weight:700;font-size:13px;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# CONSTANTES & UTILITAIRES
# ─────────────────────────────────────────────────────────
INCH=39.3701; MMPI=25.4

def sec(n,t): st.markdown(f'<div class="sec">{"<span class=sn>"+str(n)+"</span>" if n else ""}{t}</div>',unsafe_allow_html=True)
def rb(h): st.markdown(f'<div class="rb">{h}</div>',unsafe_allow_html=True)
def ib(h): st.markdown(f'<div class="ib">ℹ️ {h}</div>',unsafe_allow_html=True)
def wb(h): st.markdown(f'<div class="wb">⚠️ {h}</div>',unsafe_allow_html=True)
def sc(l,v,c=""): return f'<div class="sc"><div class="l">{l}</div><div class="v {c}">{v}</div></div>'

def px_m(m,d):   return max(1,int(m*INCH*d))
def px_mm(mm,d): return max(1,int((mm/MMPI)*d))
def est(w,h): b=int(w*h*4*.38); return f"{b/1e6:.1f} MB" if b>=1e6 else f"{b/1024:.0f} KB"

def h2r(h):
    h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))

def fnt(s=9):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        try: return ImageFont.truetype(p,s)
        except: pass
    return ImageFont.load_default()

def fnt_m(s=9):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"]:
        try: return ImageFont.truetype(p,s)
        except: pass
    return ImageFont.load_default()

# ─────────────────────────────────────────────────────────
# CHARGEMENT IMAGE
# ─────────────────────────────────────────────────────────
def load_img(up) -> Image.Image:
    data=up.read(); up.seek(0)
    if up.name.lower().endswith(".pdf") and HAS_PDF:
        doc=fitz.open(stream=data,filetype="pdf")
        pix=doc[0].get_pixmap(matrix=fitz.Matrix(4,4),alpha=True)
        img=Image.frombytes("RGBA",[pix.width,pix.height],pix.samples)
        doc.close(); return img
    img=Image.open(io.BytesIO(data))
    return img.convert("RGBA") if img.mode!="RGBA" else img

# ─────────────────────────────────────────────────────────
# ENCODAGE TIF
# ─────────────────────────────────────────────────────────
def to_tif(img:Image.Image, dpi:int, comp:str) -> bytes:
    if img.mode=="RGBA":
        bg=Image.new("RGB",img.size,(255,255,255))
        bg.paste(img.convert("RGB"),mask=img.split()[3])
        img=bg.convert("CMYK")
    elif img.mode=="RGB":
        img=img.convert("CMYK")
    buf=io.BytesIO(); img.save(buf,format="TIFF",dpi=(dpi,dpi),compression=comp)
    return buf.getvalue()

# ─────────────────────────────────────────────────────────
# PRN
# ─────────────────────────────────────────────────────────
def make_prn(j:dict)->str:
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return "\n".join([
        "; PrintStudio Pro v4.0 — Fichier Job PRN",f"; Généré : {now}","",
        "[JobInfo]",f"JobName={j.get('name','Job')}",f"Created={now}","",
        "[Media]",f"Width={j.get('w',0):.2f}",f"Height={j.get('h',0):.2f}","Unit=mm",
        f"Orientation={j.get('or','portrait')}","",
        "[Print]",f"Copies={j.get('cop',1)}",f"DPI={j.get('dpi',300)}",
        "ColorMode=CMYK",f"ColorProfile={j.get('icc','ISOcoated_v2')}",
        f"Mirror={1 if j.get('mir') else 0}",f"WhiteBase={1 if j.get('wb') else 0}",
        f"Bleed={j.get('bl',0):.1f}","",
        "[RIP]","Software=MainTap",f"Quality={j.get('q','High')}","RenderIntent=Perceptual","",
        "[Source]",f"File={j.get('file','')}",f"Mode={j.get('mode','Standard')}","",
        "[Grid]",f"Cols={j.get('cols',1)}",f"Rows={j.get('rows',1)}",
        f"GapH={j.get('gh',0):.1f}",f"GapV={j.get('gv',0):.1f}",f"Margin={j.get('mg',0):.1f}",
    ])

def make_zip(files:dict)->bytes:
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED) as z:
        for n,d in files.items(): z.writestr(n,d if isinstance(d,bytes) else d.encode())
    return buf.getvalue()

def make_pdf(img_cmyk: Image.Image, w_mm: float, h_mm: float, dpi: int) -> bytes:
    """Encode la planche CMJN en PDF haute résolution prêt à imprimer."""
    # Convertir en RGB pour l'encodage PDF (Pillow encode PDF via RGB/L)
    img_rgb = img_cmyk.convert("RGB")
    buf = io.BytesIO()
    # resolution en DPI, taille en points (1pt = 25.4/72 mm)
    w_pt = w_mm / 25.4 * 72
    h_pt = h_mm / 25.4 * 72
    img_rgb.save(buf, format="PDF", resolution=dpi,
                 save_all=False)
    return buf.getvalue()

# ─────────────────────────────────────────────────────────
# SUPPRESSION DE FOND — AVANCÉE (OpenCV)
# ─────────────────────────────────────────────────────────
def remove_bg_advanced(img:Image.Image, method:str, tol:int, cpick:tuple,
                        refine:bool, feather:int) -> Image.Image:
    rgba = img.convert("RGBA")
    arr  = np.array(rgba, dtype=np.uint8)
    rgb  = arr[:,:,:3]

    if method in ("Blanc","Noir","Couleur"):
        if method=="Blanc":
            r0,g0,b0=255,255,255
        elif method=="Noir":
            r0,g0,b0=0,0,0
        else:
            r0,g0,b0=cpick
        dr=rgb[:,:,0].astype(np.float32)-r0
        dg=rgb[:,:,1].astype(np.float32)-g0
        db=rgb[:,:,2].astype(np.float32)-b0
        dist=np.sqrt(dr**2+dg**2+db**2)
        alpha_f=np.clip((dist-tol/3)/(tol-tol/3+1e-6),0,1)
        alpha_u8=(alpha_f*255).astype(np.uint8)

    elif method=="FloodFill (bords)":
        # Supprime le fond connecté aux bords
        gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
        mask_ff=np.zeros((gray.shape[0]+2,gray.shape[1]+2),np.uint8)
        img_ff=rgb.copy()
        seed_points=[]
        h,w=gray.shape
        for x in range(0,w,max(1,w//20)): seed_points+=[(x,0),(x,h-1)]
        for y in range(0,h,max(1,h//20)): seed_points+=[(0,y),(w-1,y)]
        for sp in seed_points:
            try: cv2.floodFill(img_ff,mask_ff,sp,(0,255,0),
                               (tol,tol,tol),(tol,tol,tol),cv2.FLOODFILL_MASK_ONLY|cv2.FLOODFILL_FIXED_RANGE)
            except: pass
        fg_mask=1-(mask_ff[1:-1,1:-1])
        alpha_u8=(fg_mask*255).astype(np.uint8)

    elif method=="GrabCut (auto)":
        # GrabCut : sépare sujet/fond automatiquement
        mask_gc=np.zeros(rgb.shape[:2],np.uint8)
        bgd=np.zeros((1,65),np.float64); fgd=np.zeros((1,65),np.float64)
        marg=max(5,min(rgb.shape[0],rgb.shape[1])//15)
        rect=(marg,marg,rgb.shape[1]-2*marg,rgb.shape[0]-2*marg)
        try:
            cv2.grabCut(rgb,mask_gc,rect,bgd,fgd,8,cv2.GC_INIT_WITH_RECT)
            fg=(mask_gc==cv2.GC_FGD)|(mask_gc==cv2.GC_PR_FGD)
            alpha_u8=(fg.astype(np.uint8)*255)
        except:
            alpha_u8=np.ones(rgb.shape[:2],np.uint8)*255

    else:
        alpha_u8=np.ones(rgb.shape[:2],np.uint8)*255

    # Affinement bords (érosion légère puis dilat)
    if refine:
        kernel=np.ones((3,3),np.uint8)
        alpha_u8=cv2.morphologyEx(alpha_u8,cv2.MORPH_OPEN,kernel,iterations=1)
        alpha_u8=cv2.morphologyEx(alpha_u8,cv2.MORPH_CLOSE,kernel,iterations=2)

    # Lissage bords (anti-aliasing)
    if feather>0:
        alpha_u8=cv2.GaussianBlur(alpha_u8,(feather*2+1,feather*2+1),feather*0.5)

    out=arr.copy(); out[:,:,3]=alpha_u8
    return Image.fromarray(out,"RGBA")

# ─────────────────────────────────────────────────────────
# MOTEUR RIP GRAND FORMAT
# ─────────────────────────────────────────────────────────
def rip_gf(slots, w_m, h_m, cols, rows, gh, gv, mg, bl,
           dpi, rot_global, icc, comp, prog=None):
    """
    slots : liste de dict {img, rot, kr, x_off, y_off, scale}
    Mode uniforme (1 image) ou multi-images (N images sur grille).
    """
    def p(v,m):
        if prog: prog(v,m)

    p(5,"Calcul dimensions pixel…")
    wpx=px_m(w_m,dpi); hpx=px_m(h_m,dpi)
    mp=px_mm(mg,dpi); ghp=px_mm(gh,dpi); gvp=px_mm(gv,dpi)
    cw=max(1,(wpx-2*mp-ghp*(cols-1))//cols)
    ch=max(1,(hpx-2*mp-gvp*(rows-1))//rows)

    p(20,"Création de la planche…")
    board=Image.new("RGB",(wpx,hpx),(255,255,255))

    total=cols*rows
    p(35,f"Placement {total} éléments…")

    for idx in range(total):
        r_=idx//cols; c_=idx%cols
        x=mp+c_*(cw+ghp); y=mp+r_*(ch+gvp)

        # Récupérer l'image du slot (cyclique si moins d'images que de cases)
        slot=slots[idx%len(slots)]
        src=slot["img"].convert("RGBA")

        # Rotation individuelle ou globale
        rot=slot.get("rot",0) or rot_global
        if rot: src=src.rotate(-rot,expand=True)

        # Dimensions cible : taille personnalisée par slot ou taille de cellule par défaut
        if slot.get("use_custom_size") and slot.get("custom_w_mm") and slot.get("custom_h_mm"):
            tw=px_mm(slot["custom_w_mm"],dpi); th=px_mm(slot["custom_h_mm"],dpi)
        else:
            tw,th=cw,ch
        kr=slot.get("kr",False)
        if kr:
            r=src.width/src.height
            tw2,th2=(int(th*r),th) if tw/th>r else (tw,int(tw/r))
        else:
            tw2,th2=tw,th
        src=src.resize((tw2,th2),Image.LANCZOS)
        ox=x+(cw-tw2)//2; oy=y+(ch-th2)//2
        cell=Image.new("RGB",(tw2,th2),(255,255,255))
        alpha=src.split()[3]
        cell.paste(src.convert("RGB"),(0,0),alpha)
        board.paste(cell,(ox,oy))

        pct=35+int(55*(idx+1)/total)
        p(pct,f"Élément {idx+1}/{total} placé…")

    p(92,f"Conversion CMJN — {icc}…"); board=board.convert("CMYK")
    p(97,f"Encodage TIF ({comp})…"); tif=to_tif(board,dpi,comp)
    p(100,"✅ RIP terminé !")
    return tif,{"wpx":wpx,"hpx":hpx,
                "cw_mm":(cw/dpi)*MMPI,"ch_mm":(ch/dpi)*MMPI,"total":total}

# ─────────────────────────────────────────────────────────
# MOTEUR RIP DTF
# ─────────────────────────────────────────────────────────
def rip_dtf_eng(src,w_mm,h_mm,dpi,mirror,comp,prog=None):
    def p(v,m):
        if prog: prog(v,m)
    p(5,"Calcul zone DTF…"); wpx=px_mm(w_mm,dpi); hpx=px_mm(h_mm,dpi)
    p(20,"Mise en forme…"); s=src.convert("RGBA")
    if mirror: s=s.transpose(Image.FLIP_LEFT_RIGHT)
    r=s.width/s.height; t=wpx/hpx
    nw=wpx if r>t else int(hpx*r); nh=int(wpx/r) if r>t else hpx
    s=s.resize((nw,nh),Image.LANCZOS)
    p(50,"Composition sur fond…"); base=Image.new("RGB",(wpx,hpx),(255,255,255))
    ox=(wpx-nw)//2; oy=(hpx-nh)//2; al=s.split()[3]
    base.paste(s.convert("RGB"),(ox,oy),al)
    p(75,"Conversion CMJN…"); cmyk=base.convert("CMYK")
    p(92,"Encodage TIF…"); tif=to_tif(cmyk,dpi,comp)
    p(100,"✅ RIP DTF terminé !"); return tif,{"wpx":wpx,"hpx":hpx}

# ─────────────────────────────────────────────────────────
# APERÇU PLANCHE
# ─────────────────────────────────────────────────────────
def draw_preview(slots, cols, rows, w_m, h_m, gh, gv, mg, rot_g, pw=680):
    ph=min(int(pw*h_m/w_m) if w_m>0 else pw,500); ph=max(ph,180)
    board=Image.new("RGB",(pw,ph),h2r(PBG)); draw=ImageDraw.Draw(board)
    gc=h2r(PGR)
    for x in range(0,pw,28): draw.line([(x,0),(x,ph)],fill=gc,width=1)
    for y in range(0,ph,28): draw.line([(0,y),(pw,y)],fill=gc,width=1)
    sc_=pw/(w_m*1000); mp=int(mg*sc_); ghp=int(gh*sc_); gvp=int(gv*sc_)
    uw=pw-2*mp-ghp*(cols-1); uh=ph-2*mp-gvp*(rows-1)
    cw=max(2,uw//cols); ch=max(2,uh//rows)
    pal=[(40,55,85),(35,62,72),(55,40,72),(60,48,36),(36,58,52),(52,52,42)] if DARK else \
        [(215,228,252),(210,242,235),(235,218,248),(248,235,215),(215,237,228),(235,232,215)]
    ac=h2r(ACC); total=cols*rows
    for idx in range(total):
        r_=idx//cols; c_=idx%cols
        x=mp+c_*(cw+ghp); y=mp+r_*(ch+gvp)
        cc=pal[idx%6]
        slot=slots[idx%len(slots)] if slots else None
        if slot and slot.get("img"):
            s=slot["img"].copy().convert("RGBA")
            rot=(slot.get("rot",0) or rot_g)
            if rot: s=s.rotate(-rot,expand=True)
            s=s.resize((cw,ch),Image.LANCZOS)
            bg=Image.new("RGB",(cw,ch),cc)
            bg.paste(s.convert("RGB"),(0,0),s.split()[3])
            board.paste(bg,(x,y))
        else:
            draw.rectangle([x,y,x+cw-1,y+ch-1],fill=cc)
        draw.rectangle([x,y,x+cw-1,y+ch-1],outline=ac,width=2)
        fs=max(7,min(ch//3,14)); lbl=str(idx+1)
        if slot and slot.get("label") and len(slots)>1: lbl=slot["label"][:6]
        draw.text((x+cw//2,y+ch//2),lbl,fill=ac,font=fnt(fs),anchor="mm")
    if mg>0:
        wc=h2r(WRN); draw.rectangle([mp,mp,pw-mp-1,ph-mp-1],outline=(*wc,140),width=1)
    draw.rectangle([0,ph-22,pw,ph],fill=h2r(SRF2))
    draw.text((pw//2,ph-11),
        f"Support {w_m:.3f}m × {h_m:.3f}m  ·  {cols}×{rows}={total} éléments  ·  CMJN TIF",
        fill=h2r(ACC),font=fnt_m(9),anchor="mm")
    return board

def draw_preview_simple(src,w_mm,h_mm,rot,kr,pw=680):
    ph=min(int(pw*h_mm/w_mm) if w_mm>0 else pw,500); ph=max(ph,160)
    board=Image.new("RGB",(pw,ph),h2r(PBG)); draw=ImageDraw.Draw(board)
    gc=h2r(PGR)
    for x in range(0,pw,28): draw.line([(x,0),(x,ph)],fill=gc,width=1)
    for y in range(0,ph,28): draw.line([(0,y),(pw,y)],fill=gc,width=1)
    pad=24; iw,ih=pw-pad*2,ph-pad*2
    if src:
        s=src.copy().convert("RGBA")
        if rot: s=s.rotate(-rot,expand=True)
        if kr:
            r=s.width/s.height
            iw2,ih2=(int(ih*r),ih) if iw/ih>r else (iw,int(iw/r))
        else: iw2,ih2=iw,ih
        s=s.resize((iw2,ih2),Image.LANCZOS)
        ox=pad+(iw-iw2)//2; oy=pad+(ih-ih2)//2
        bg=Image.new("RGB",(iw2,ih2),h2r(PBG))
        bg.paste(s.convert("RGB"),(0,0),s.split()[3])
        board.paste(bg,(ox,oy))
        ac=h2r(ACC)
        draw.rectangle([ox-2,oy-2,ox+iw2+1,oy+ih2+1],outline=ac,width=2)
        draw.line([(ox,oy-13),(ox+iw2,oy-13)],fill=ac,width=1)
        draw.line([(ox,oy-17),(ox,oy-9)],fill=ac,width=1)
        draw.line([(ox+iw2,oy-17),(ox+iw2,oy-9)],fill=ac,width=1)
        draw.text(((ox+ox+iw2)//2,oy-13),f"{w_mm:.1f} mm",fill=ac,font=fnt(9),anchor="mm")
    else:
        draw.rectangle([pad,pad,pw-pad,ph-pad],outline=h2r(BOR),width=2)
        draw.text((pw//2,ph//2),"Chargez une image",fill=h2r(MUT),font=fnt(14),anchor="mm")
    draw.rectangle([0,ph-22,pw,ph],fill=h2r(SRF2))
    draw.text((pw//2,ph-11),
        f"{w_mm:.1f} × {h_mm:.1f} mm  ·  {w_mm/10:.1f} × {h_mm/10:.1f} cm  ·  {w_mm/1000:.3f} × {h_mm/1000:.3f} m",
        fill=h2r(ACC),font=fnt_m(9),anchor="mm")
    return board

def draw_preview_dtf(src,w_mm,h_mm,mirror,pw=300):
    r=h_mm/w_mm if w_mm>0 else 1; ph=min(int(pw*r),460); ph=max(ph,180)
    board=Image.new("RGB",(pw,ph),h2r(PBG)); draw=ImageDraw.Draw(board)
    pad=10
    draw.rectangle([pad,pad,pw-pad,ph-pad],fill=h2r(SRF2),outline=h2r(BOR),width=1)
    if src:
        s=src.copy().convert("RGBA")
        if mirror: s=s.transpose(Image.FLIP_LEFT_RIGHT)
        iw,ih=pw-pad*4,ph-pad*4; rr=s.width/s.height; tt=iw/ih
        nw=iw if rr>tt else int(ih*rr); nh=int(iw/rr) if rr>tt else ih
        s=s.resize((nw,nh),Image.LANCZOS)
        ox=pad*2+(iw-nw)//2; oy=pad*2+(ih-nh)//2
        bg=Image.new("RGB",(nw,nh),h2r(SRF2))
        bg.paste(s.convert("RGB"),(0,0),s.split()[3])
        board.paste(bg,(ox,oy))
    else: draw.text((pw//2,ph//2),"Chargez un fichier",fill=h2r(MUT),font=fnt(11),anchor="mm")
    gc=h2r(GRN); mk=14
    for (cx,cy) in [(pad,pad),(pw-pad,pad),(pad,ph-pad),(pw-pad,ph-pad)]:
        dx=1 if cx==pad else -1; dy=1 if cy==pad else -1
        draw.line([(cx,cy),(cx+dx*mk,cy)],fill=gc,width=2)
        draw.line([(cx,cy),(cx,cy+dy*mk)],fill=gc,width=2)
    if mirror:
        draw.rectangle([pad,pad,pw-pad,pad+16],fill=h2r(SRF))
        draw.text((pw//2,pad+8),"🪞 MIROIR",fill=h2r(ACC),font=fnt(9),anchor="mm")
    draw.rectangle([0,ph-20,pw,ph],fill=h2r(SRF))
    draw.text((pw//2,ph-10),f"{w_mm:.0f}×{h_mm:.0f} mm",fill=h2r(GRN),font=fnt_m(9),anchor="mm")
    return board

# ─────────────────────────────────────────────────────────
# HELPER DIMENSIONS
# ─────────────────────────────────────────────────────────
def unit_cfg(unit,mode="wh"):
    k={"mm":1.,"cm":10.,"m":1000.}
    s={"mm":.5,"cm":.05,"m":.001}
    dw={"mm":1500.,"cm":150.,"m":1.5}
    dh={"mm":1000.,"cm":100.,"m":1.0}
    return k[unit],s[unit],dw[unit],dh[unit]

def unit_cfg_sup(unit):
    k={"m":1.,"cm":.01,"mm":.001}
    s={"m":.01,"cm":.5,"mm":1.}
    dw={"m":1.5,"cm":150.,"mm":1500.}
    dh={"m":1.0,"cm":100.,"mm":1000.}
    return k[unit],s[unit],dw[unit],dh[unit]

# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="hdr">
  <div>
    <div class="hdr-logo">Print<em>Studio</em> Pro</div>
    <div class="hdr-sub">Système RIP professionnel · Grand Format · Vinyle · Bâche · DTF · Suppression de fond</div>
  </div>
  <div style="display:flex;gap:7px;align-items:center">
    <span class="badge">CMJN</span>
    <span class="badge" style="background:{GRN}">TIF</span>
    <span class="badge" style="background:{BLU}">PRN</span>
    <span class="badge" style="background:{MUT}">v4.0</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# ONGLETS
# ═══════════════════════════════════════════════════════════
TAB_GF, TAB_DTF, TAB_BG = st.tabs([
    "🖨️  Grand Format — Vinyle / Bâche",
    "👕  DTF — Textile",
    "✂️  Suppression de fond",
])

# ╔═══════════════════════════════════════════════════════════
# ║  ONGLET 1 — GRAND FORMAT
# ╚═══════════════════════════════════════════════════════════
with TAB_GF:

    L, R = st.columns([1.05, 1], gap="large")

    with L:
        # ── 1. MODE ──────────────────────────────────────────
        sec("1","Type de travail")
        mode=st.radio("Mode",
            ["🖼️ Image simple",
             "📋 Plusieurs images différentes sur un support",
             "📏 Répétition — par taille de support",
             "🏷️ Répétition — par taille d'élément"],
            key="gf_mode", label_visibility="collapsed")

        # ── 2. FICHIER(S) ─────────────────────────────────────
        sec("2","Fichier(s) source")

        if mode == "📋 Plusieurs images différentes sur un support":
            ib("Chargez autant d'images que vous voulez placer sur le support. "
               "Chaque image occupera une case de la grille dans l'ordre de chargement.")
            ups=st.file_uploader("Chargez vos images (plusieurs à la fois)",
                type=["pdf","png","jpg","jpeg","tif","tiff","bmp","ai","eps","svg"],
                key="gf_multi", accept_multiple_files=True, label_visibility="collapsed")
            slots=[]
            if ups:
                rb(f"📂 <strong>{len(ups)} fichier(s) chargé(s)</strong>")
                for i,u in enumerate(ups):
                    try:
                        img=load_img(u)
                        slots.append({"img":img,"label":Path(u.name).stem[:8],
                                      "rot":0,"kr":True,"file":u.name})
                    except: st.warning(f"❌ {u.name} — format non supporté")
                if slots:
                    st.markdown("**Paramètres par image :**")
                    u_slot=st.radio("Unité dimensions images",["mm","cm","m"],
                        horizontal=True,key="slot_unit")
                    ku_s={"mm":1.,"cm":10.,"m":1000.}[u_slot]
                    su_s={"mm":.5,"cm":.05,"m":.001}[u_slot]
                    for i,slot in enumerate(slots):
                        with st.expander(f"Image {i+1} — {slot['label']}", expanded=(i==0)):
                            st.image(slot["img"],width=120,
                                caption=f"Original : {slot['img'].width}×{slot['img'].height} px")
                            st.markdown("**Dimensions sur le support**")
                            slot["use_custom_size"]=st.checkbox(
                                "📐 Taille personnalisée pour cette image",
                                value=False,key=f"slot_cs_{i}")
                            if slot["use_custom_size"]:
                                sd1,sd2=st.columns(2)
                                def_w=round(100./ku_s,2); def_h=round(100./ku_s,2)
                                with sd1:
                                    slot["custom_w_mm"]=st.number_input(
                                        f"Largeur ({u_slot})",min_value=.1,
                                        value=def_w,step=su_s,key=f"slot_w_{i}") * ku_s
                                with sd2:
                                    slot["custom_h_mm"]=st.number_input(
                                        f"Hauteur ({u_slot})",min_value=.1,
                                        value=def_h,step=su_s,key=f"slot_h_{i}") * ku_s
                                st.caption(f"→ {slot['custom_w_mm']:.1f} × {slot['custom_h_mm']:.1f} mm")
                            else:
                                slot["custom_w_mm"]=None; slot["custom_h_mm"]=None
                                st.caption("Taille calculée automatiquement depuis la grille")
                            ec1,ec2=st.columns(2)
                            with ec1:
                                slot["rot"]=st.selectbox("Rotation",
                                    [0,90,180,270],index=0,
                                    format_func=lambda x:f"{x}°",key=f"slot_rot_{i}")
                            with ec2:
                                slot["kr"]=st.checkbox("Conserver proportions",
                                    value=True,key=f"slot_kr_{i}")
            up=None; src_img=None
        else:
            ups=[]
            up=st.file_uploader("Logo, étiquette ou maquette",
                type=["pdf","png","jpg","jpeg","tif","tiff","bmp","ai","eps","cdr","svg"],
                key="gf_up", label_visibility="collapsed")
            src_img=None
            if up:
                try: src_img=load_img(up)
                except Exception as e: st.warning(f"Aperçu non disponible : {e}")
                rb(f"📂 <strong>{up.name}</strong> · {up.size/1024:.0f} KB"
                   +(f" · {src_img.width}×{src_img.height} px" if src_img else ""))
            slots=[{"img":src_img,"rot":0,"kr":False,"label":"1","file":up.name if up else ""}] if src_img else []

        # ── 3. DIMENSIONS ─────────────────────────────────────
        sec("3","Dimensions & Support")

        # IMAGE SIMPLE
        if mode=="🖼️ Image simple":
            ib("L'image est redimensionnée exactement aux dimensions indiquées — aucune multiplication.")
            u=st.radio("Unité",["mm","cm","m"],horizontal=True,key="si_u")
            ku,su,dw,dh=unit_cfg(u)
            a,b_=st.columns(2)
            with a: iw_i=st.number_input(f"Largeur ({u})",min_value=.1,value=dw,step=su,key="si_w")
            with b_: ih_i=st.number_input(f"Hauteur ({u})",min_value=.1,value=dh,step=su,key="si_h")
            lbl_w=iw_i*ku; lbl_h=ih_i*ku
            c1,c2=st.columns(2)
            with c1: kr_si=st.checkbox("🔗 Conserver les proportions",value=True,key="si_kr")
            with c2: bleed=st.number_input("Fond perdu (mm)",min_value=0.,max_value=20.,value=0.,key="si_bl")
            print_w=lbl_w/1000; print_h=lbl_h/1000
            cols_v=1; rows_v=1; gh=0.; gv=0.; mg=0.
            rot_g=st.selectbox("Rotation",[0,90,180,270],index=0,format_func=lambda x:f"{x}°",key="si_rot")
            rb(f"📐 <strong>{lbl_w:.1f} × {lbl_h:.1f} mm</strong>"
               f" · {lbl_w/10:.1f}×{lbl_h/10:.1f} cm · {print_w:.3f}×{print_h:.3f} m")
            if slots: slots[0]["rot"]=rot_g; slots[0]["kr"]=kr_si

        # PLUSIEURS IMAGES DIFFÉRENTES
        elif mode=="📋 Plusieurs images différentes sur un support":
            ib("Définissez le support et la grille. Chaque case reçoit une image différente dans l'ordre.")
            # Support
            st.markdown("**Support d'impression**")
            u_p=st.radio("Unité support",["m","cm","mm"],horizontal=True,key="mi_us")
            kp,sp,dwp,dhp=unit_cfg_sup(u_p)
            a,b_=st.columns(2)
            with a: pw_i=st.number_input(f"Largeur ({u_p})",min_value=.01,value=dwp,step=sp,key="mi_pw")
            with b_: ph_i=st.number_input(f"Hauteur ({u_p})",min_value=.01,value=dhp,step=sp,key="mi_ph")
            print_w=pw_i*kp; print_h=ph_i*kp
            # Grille
            st.markdown("**Grille**")
            g1,g2,g3,g4=st.columns(4)
            with g1: cols_v=st.number_input("Colonnes",min_value=1,max_value=50,value=2,key="mi_c")
            with g2: rows_v=st.number_input("Lignes",min_value=1,max_value=50,value=2,key="mi_r")
            with g3: gh=st.number_input("Esp. H (mm)",min_value=0.,value=5.,step=.5,key="mi_gh")
            with g4: gv=st.number_input("Esp. V (mm)",min_value=0.,value=5.,step=.5,key="mi_gv")
            m1,m2=st.columns(2)
            with m1: mg=st.number_input("Marge bord (mm)",min_value=0.,value=5.,key="mi_mg")
            with m2: bleed=st.number_input("Fond perdu (mm)",min_value=0.,max_value=20.,value=0.,key="mi_bl")
            rot_g=st.selectbox("Rotation globale",[0,90,180,270],index=0,format_func=lambda x:f"{x}°",key="mi_rot")
            total_slots=int(cols_v)*int(rows_v)
            uw=print_w*1000-2*mg-gh*(cols_v-1); uh=print_h*1000-2*mg-gv*(rows_v-1)
            lbl_w=max(1.,uw/cols_v); lbl_h=max(1.,uh/rows_v)
            if slots:
                if len(slots)<total_slots:
                    ib(f"{len(slots)} image(s) chargée(s) pour {total_slots} cases — "
                       f"les images seront répétées en boucle pour remplir la grille.")
                elif len(slots)>total_slots:
                    ib(f"{len(slots)} images chargées, grille de {total_slots} cases — "
                       f"seules les {total_slots} premières seront utilisées. Ajustez la grille si besoin.")
                rb(f"🏷️ Case : <strong>{lbl_w:.1f}×{lbl_h:.1f} mm</strong> · "
                   f"Support : <strong>{print_w:.3f}×{print_h:.3f} m</strong> · "
                   f"{total_slots} cases")
            else:
                wb("Chargez des images dans la section fichier ci-dessus.")
                lbl_w=100.; lbl_h=100.

        # RÉPÉTITION PAR PLANCHE
        elif mode=="📏 Répétition — par taille de support":
            ib("Entrez la taille totale du support. La taille de chaque élément est calculée automatiquement.")
            st.markdown("**Support d'impression**")
            u_p=st.radio("Unité support",["m","cm","mm"],horizontal=True,key="pl_u")
            kp,sp,dwp,dhp=unit_cfg_sup(u_p)
            a,b_=st.columns(2)
            with a: pw_i=st.number_input(f"Largeur ({u_p})",min_value=.01,value=dwp,step=sp,key="pl_pw")
            with b_: ph_i=st.number_input(f"Hauteur ({u_p})",min_value=.01,value=dhp,step=sp,key="pl_ph")
            print_w=pw_i*kp; print_h=ph_i*kp
            st.markdown("**Grille de répétition**")
            g1,g2,g3,g4=st.columns(4)
            with g1: cols_v=st.number_input("Colonnes",min_value=1,max_value=100,value=3,key="pl_c")
            with g2: rows_v=st.number_input("Lignes",min_value=1,max_value=100,value=4,key="pl_r")
            with g3: gh=st.number_input("Esp. H (mm)",min_value=0.,value=3.,step=.5,key="pl_gh")
            with g4: gv=st.number_input("Esp. V (mm)",min_value=0.,value=3.,step=.5,key="pl_gv")
            m1,m2=st.columns(2)
            with m1: mg=st.number_input("Marge bord (mm)",min_value=0.,value=5.,key="pl_mg")
            with m2: bleed=st.number_input("Fond perdu (mm)",min_value=0.,max_value=20.,value=3.,key="pl_bl")
            c1,c2=st.columns(2)
            with c1: kr_pl=st.checkbox("🔗 Conserver proportions",value=False,key="pl_kr")
            with c2: rot_g=st.selectbox("Rotation",[0,90,180,270],index=0,format_func=lambda x:f"{x}°",key="pl_rot")
            uw=print_w*1000-2*mg-gh*(cols_v-1); uh=print_h*1000-2*mg-gv*(rows_v-1)
            lbl_w=max(1.,uw/cols_v); lbl_h=max(1.,uh/rows_v)
            if slots: slots[0]["kr"]=kr_pl; slots[0]["rot"]=rot_g
            rb(f"🏷️ Taille / élément : <strong>{lbl_w:.1f}×{lbl_h:.1f} mm</strong>"
               f" ({lbl_w/10:.2f}×{lbl_h/10:.2f} cm) · <strong>{int(cols_v*rows_v)}</strong> éléments")

        # RÉPÉTITION PAR ÉTIQUETTE
        else:
            ib("Entrez la taille d'un élément. La planche est calculée automatiquement. "
               "Vous pouvez aussi imposer un support fixe.")
            st.markdown("**Taille de l'élément**")
            u_e=st.radio("Unité élément",["mm","cm","m"],horizontal=True,key="et_u")
            ke,se,dwe,dhe=unit_cfg(u_e)
            a,b_=st.columns(2)
            with a: ew_i=st.number_input(f"Largeur ({u_e})",min_value=.1,value=dwe/15,step=se,key="et_w")
            with b_: eh_i=st.number_input(f"Hauteur ({u_e})",min_value=.1,value=dhe/20,step=se,key="et_h")
            lbl_w=ew_i*ke; lbl_h=eh_i*ke
            st.markdown("**Grille de répétition**")
            g1,g2,g3,g4=st.columns(4)
            with g1: cols_v=st.number_input("Colonnes",min_value=1,max_value=100,value=3,key="et_c")
            with g2: rows_v=st.number_input("Lignes",min_value=1,max_value=100,value=4,key="et_r")
            with g3: gh=st.number_input("Esp. H (mm)",min_value=0.,value=3.,step=.5,key="et_gh")
            with g4: gv=st.number_input("Esp. V (mm)",min_value=0.,value=3.,step=.5,key="et_gv")
            m1,m2=st.columns(2)
            with m1: mg=st.number_input("Marge bord (mm)",min_value=0.,value=5.,key="et_mg")
            with m2: bleed=st.number_input("Fond perdu (mm)",min_value=0.,max_value=20.,value=3.,key="et_bl")
            c1,c2=st.columns(2)
            with c1: kr_et=st.checkbox("🔗 Conserver proportions",value=False,key="et_kr")
            with c2: rot_g=st.selectbox("Rotation",[0,90,180,270],index=0,format_func=lambda x:f"{x}°",key="et_rot")
            # Support optionnel
            st.markdown("**Support d'impression**")
            force=st.checkbox("📐 Imposer un support de taille fixe",value=False,key="et_fs")
            if force:
                u_s=st.radio("Unité support",["m","cm","mm"],horizontal=True,key="et_su")
                ks,ss,dws,dhs=unit_cfg_sup(u_s)
                fs1,fs2=st.columns(2)
                with fs1: fsw=st.number_input(f"Largeur ({u_s})",min_value=.01,value=dws,step=ss,key="et_fw")
                with fs2: fsh=st.number_input(f"Hauteur ({u_s})",min_value=.01,value=dhs,step=ss,key="et_fh")
                print_w=fsw*ks; print_h=fsh*ks
                ib(f"Support imposé : <strong>{print_w:.3f}×{print_h:.3f} m</strong>. "
                   "L'espace non couvert restera blanc.")
            else:
                print_w=(lbl_w*cols_v+gh*(cols_v-1)+2*mg)/1000
                print_h=(lbl_h*rows_v+gv*(rows_v-1)+2*mg)/1000
            if slots: slots[0]["kr"]=kr_et; slots[0]["rot"]=rot_g
            rb(f"📏 Support : <strong>{print_w:.3f}×{print_h:.3f} m</strong>"
               f" ({print_w*100:.1f}×{print_h*100:.1f} cm)"
               f" · <strong>{int(cols_v*rows_v)}</strong> éléments de {lbl_w:.1f}×{lbl_h:.1f} mm")

        # ── 4. PARAMÈTRES RIP ─────────────────────────────────
        sec("4","Paramètres RIP")
        r1,r2,r3,r4=st.columns(4)
        with r1: dpi=st.selectbox("DPI",[72,150,300,600],index=2,key="gf_dpi")
        with r2: icc=st.selectbox("Profil ICC",["ISOcoated_v2","CoatedFOGRA39","UncoatedFOGRA29","SWOP"],key="gf_icc")
        with r3: comp=st.selectbox("Compression",{"tiff_lzw":"LZW ✓","tiff_deflate":"Deflate","raw":"Aucune"}.keys(),
                    format_func={"tiff_lzw":"LZW ✓","tiff_deflate":"Deflate","raw":"Aucune"}.get,key="gf_comp")
        with r4: copies=st.number_input("Copies",min_value=1,max_value=99,value=1,key="gf_cop")

        # ── 5. SORTIE ─────────────────────────────────────────
        sec("5","Format de sortie")
        out=st.radio("Sortie",["tif","pdf","prn","zip","zip_full"],
            format_func={"tif":"🖼️ TIF CMJN","pdf":"📄 PDF","prn":"🖨️ PRN","zip":"📦 TIF+PRN","zip_full":"📦 ZIP+aperçu"}.get,
            horizontal=True,key="gf_out")

    # ── COLONNE DROITE ─────────────────────────────────────
    with R:
        sec("","Récapitulatif & Aperçu")
        wpx=px_m(print_w,dpi); hpx=px_m(print_h,dpi)
        total=int(cols_v)*int(rows_v)
        a_,b_,c_=st.columns(3)
        a_.markdown(sc("Éléments",str(total),"a"),unsafe_allow_html=True)
        b_.markdown(sc("Taille élément",f"{lbl_w:.0f}×{lbl_h:.0f} mm"),unsafe_allow_html=True)
        c_.markdown(sc("Support",f"{print_w:.2f}×{print_h:.2f} m"),unsafe_allow_html=True)
        st.markdown("")
        d_,e_=st.columns(2)
        d_.markdown(sc("Pixels",f"{wpx:,}×{hpx:,}","b"),unsafe_allow_html=True)
        e_.markdown(sc("TIF estimé",est(wpx,hpx),"g"),unsafe_allow_html=True)
        st.markdown("")

        # Aperçu
        has_any = (mode=="📋 Plusieurs images différentes sur un support" and slots) or \
                  (mode!="📋 Plusieurs images différentes sur un support" and src_img)

        if mode=="🖼️ Image simple":
            rot_g_si = rot_g if 'rot_g' in dir() else 0
            kr_si_v  = kr_si if 'kr_si' in dir() else True
            pv=draw_preview_simple(src_img,lbl_w,lbl_h,rot_g_si,kr_si_v)
            st.image(pv,use_container_width=True,caption=f"Image : {lbl_w:.1f}×{lbl_h:.1f} mm")
        else:
            pv=draw_preview(slots,int(cols_v),int(rows_v),
                            print_w,print_h,gh,gv,mg,
                            rot_g if 'rot_g' in dir() else 0)
            cap=f"{int(cols_v)}×{int(rows_v)} éléments · Support {print_w:.3f}×{print_h:.3f} m"
            st.image(pv,use_container_width=True,caption=cap)

        st.markdown("")
        has_files = (mode=="📋 Plusieurs images différentes sur un support" and slots) or \
                    (mode!="📋 Plusieurs images différentes sur un support" and up and src_img)
        if not has_files:
            wb("Chargez un fichier source pour lancer le RIP.")
        else:
            if st.button("🚀  Lancer RIP — Générer fichier prêt à imprimer",
                         type="primary",use_container_width=True,key="gf_rip"):
                try:
                    pg=st.progress(0); st_msg=st.empty()
                    def cb(v,m): pg.progress(int(v)); st_msg.markdown(f"**⚙️ {m}**")

                    # Recalc hauteur si image simple + proportions
                    ph_rip=print_h
                    if mode=="🖼️ Image simple" and kr_si and src_img:
                        ph_rip=print_w/(src_img.width/src_img.height)

                    rot_used=rot_g if 'rot_g' in dir() else 0
                    tif_b,info=rip_gf(slots,print_w,ph_rip,
                        int(cols_v),int(rows_v),gh,gv,mg,bleed,
                        dpi,rot_used,icc,comp,cb)

                    ts=datetime.now().strftime("%Y%m%d_%H%M")
                    if mode in ("📋 Plusieurs images différentes sur un support",):
                        bn=f"multi_{len(slots)}images"
                    else:
                        bn=Path(up.name).stem
                    if mode=="🖼️ Image simple":
                        fn_tif=f"{bn}_{lbl_w:.0f}x{lbl_h:.0f}mm_{dpi}dpi_CMJN_{ts}.tif"
                    else:
                        fn_tif=f"{bn}_elem{lbl_w:.0f}x{lbl_h:.0f}mm_sup{print_w:.2f}x{print_h:.2f}m_{int(cols_v)}x{int(rows_v)}_{dpi}dpi_CMJN_{ts}.tif"
                    fn_prn=fn_tif.replace(".tif",".prn")

                    job={"name":bn,"w":print_w*1000,"h":ph_rip*1000,
                         "or":"landscape" if print_w>ph_rip else "portrait",
                         "cop":copies,"dpi":dpi,"icc":icc,"mir":False,"wb":False,
                         "bl":bleed,"cols":int(cols_v),"rows":int(rows_v),
                         "gh":gh,"gv":gv,"mg":mg,
                         "file":up.name if up else "multi","mode":mode,"q":"High"}
                    prn_b=make_prn(job).encode()

                    st_msg.markdown("**✅ RIP terminé !**")
                    rb(f"✅ <strong>RIP terminé !</strong> · "
                       f"{info['wpx']:,}×{info['hpx']:,} px · "
                       f"TIF CMJN : {len(tif_b)/1e6:.1f} MB")

                    fn_pdf=fn_tif.replace(".tif",".pdf")

                    if out=="tif":
                        st.download_button("⬇️ Télécharger TIF CMJN",tif_b,fn_tif,"image/tiff",use_container_width=True)
                    elif out=="pdf":
                        st_msg.markdown("**⚙️ Génération PDF…**")
                        # Reconstruire l'image RGB depuis le TIF pour le PDF
                        img_for_pdf=Image.open(io.BytesIO(tif_b)).convert("RGB")
                        pdf_b=make_pdf(img_for_pdf, print_w*1000, ph_rip*1000, dpi)
                        st.download_button("⬇️ Télécharger PDF",pdf_b,fn_pdf,"application/pdf",use_container_width=True)
                        st_msg.markdown("**✅ PDF prêt !**")
                    elif out=="prn":
                        st.download_button("⬇️ Télécharger PRN",prn_b,fn_prn,"text/plain",use_container_width=True)
                    else:
                        # ZIP — toujours inclure TIF + PRN, PDF en bonus dans zip_full
                        files={fn_tif:tif_b,fn_prn:prn_b}
                        if out=="zip_full":
                            buf_pv=io.BytesIO(); pv.save(buf_pv,"PNG")
                            files[f"{bn}_apercu.png"]=buf_pv.getvalue()
                            img_for_pdf2=Image.open(io.BytesIO(tif_b)).convert("RGB")
                            files[fn_pdf]=make_pdf(img_for_pdf2, print_w*1000, ph_rip*1000, dpi)
                        zb=make_zip(files)
                        fn_zip=fn_tif.replace(".tif","_COMPLET.zip")
                        st.download_button("⬇️ Télécharger ZIP",zb,fn_zip,"application/zip",use_container_width=True)
                        da,db,dc=st.columns(3)
                        da.download_button("⬇️ TIF",tif_b,fn_tif,"image/tiff")
                        db.download_button("⬇️ PRN",prn_b,fn_prn,"text/plain")
                        if out=="zip_full":
                            img_for_pdf3=Image.open(io.BytesIO(tif_b)).convert("RGB")
                            pdf_b3=make_pdf(img_for_pdf3, print_w*1000, ph_rip*1000, dpi)
                            dc.download_button("⬇️ PDF",pdf_b3,fn_pdf,"application/pdf")
                except Exception as e: st.error(f"❌ Erreur RIP : {e}"); st.exception(e)


# ╔═══════════════════════════════════════════════════════════
# ║  ONGLET 2 — DTF
# ╚═══════════════════════════════════════════════════════════
with TAB_DTF:
    DL,DR=st.columns([1.05,1],gap="large")
    with DL:
        sec("1","Fichier source")
        up_d=st.file_uploader("Chargez votre fichier DTF",
            type=["pdf","png","jpg","jpeg","tif","tiff","ai","eps","bmp","svg"],
            key="dtf_up",label_visibility="collapsed")
        src_d=None
        if up_d:
            try: src_d=load_img(up_d)
            except Exception as e: st.warning(f"Aperçu non disponible : {e}")
            rb(f"📂 <strong>{up_d.name}</strong> · {up_d.size/1024:.0f} KB")

        sec("2","Format & Dimensions")
        fmt=st.radio("Format",["A4","A3","A2","A1","Personnalisé"],horizontal=True,key="dtf_fmt")
        DIMS={"A4":(210,297),"A3":(297,420),"A2":(420,594),"A1":(594,841)}
        if fmt=="Personnalisé":
            dc1,dc2=st.columns(2)
            with dc1: cw_d=st.number_input("Largeur (mm)",min_value=10.,value=300.,key="dtf_cw")
            with dc2: ch_d=st.number_input("Hauteur (mm)",min_value=10.,value=400.,key="dtf_ch")
            dtf_w,dtf_h=float(cw_d),float(ch_d)
        else:
            bw,bh=DIMS[fmt]
            ori=st.radio("Orientation",["Portrait","Paysage"],horizontal=True,key="dtf_or")
            dtf_w,dtf_h=(float(bw),float(bh)) if ori=="Portrait" else (float(bh),float(bw))

        sec("3","Paramètres d'impression")
        dp1,dp2=st.columns(2)
        with dp1:
            dtf_dpi=st.selectbox("DPI",[150,300,600,1200],index=1,key="dtf_dpi")
            dtf_comp=st.selectbox("Compression",{"tiff_lzw":"LZW ✓","tiff_deflate":"Deflate","raw":"Aucune"}.keys(),
                        format_func={"tiff_lzw":"LZW ✓","tiff_deflate":"Deflate","raw":"Aucune"}.get,key="dtf_comp")
            dtf_q=st.selectbox("Qualité RIP",["Draft","Normal","High","Ultra"],index=2,key="dtf_q")
        with dp2:
            dtf_mir=st.toggle("🪞 Miroir (face intérieure)",value=False,key="dtf_mir")
            dtf_wb=st.toggle("⬜ White underbase",value=True,key="dtf_wb")
            dtf_cop=st.number_input("Copies",min_value=1,max_value=999,value=1,key="dtf_cop")

        sec("4","Format de sortie")
        dtf_out=st.radio("Sortie",["tif","pdf","prn","zip"],
            format_func={"tif":"🖼️ TIF CMJN","pdf":"📄 PDF","prn":"🖨️ PRN","zip":"📦 ZIP complet"}.get,
            horizontal=True,key="dtf_out",index=3)

    with DR:
        sec("","Récapitulatif & Aperçu")
        wpx_d=px_mm(dtf_w,dtf_dpi); hpx_d=px_mm(dtf_h,dtf_dpi)
        e1,e2=st.columns(2); e3,e4=st.columns(2)
        e1.markdown(sc("Format",fmt,"a"),unsafe_allow_html=True)
        e2.markdown(sc("Dimensions",f"{dtf_w:.0f}×{dtf_h:.0f} mm"),unsafe_allow_html=True)
        e3.markdown(sc("DPI",str(dtf_dpi),"b"),unsafe_allow_html=True)
        e4.markdown(sc("TIF estimé",est(wpx_d,hpx_d),"g"),unsafe_allow_html=True)
        st.markdown("")
        st.markdown(f"""
| Paramètre | Valeur |
|---|---|
| Format | `{fmt}` |
| Dimensions | `{dtf_w:.0f} × {dtf_h:.0f} mm` |
| DPI | `{dtf_dpi}` → `{wpx_d:,} × {hpx_d:,} px` |
| Miroir | `{"Oui ✅" if dtf_mir else "Non"}` |
| White underbase | `{"Oui ✅" if dtf_wb else "Non"}` |
| Copies | `{dtf_cop}` · Qualité `{dtf_q}` |
""")
        pv_d=draw_preview_dtf(src_d,dtf_w,dtf_h,dtf_mir)
        st.image(pv_d,caption=f"DTF {fmt} — {dtf_w:.0f}×{dtf_h:.0f} mm")
        st.markdown("")
        if not up_d:
            wb("Chargez un fichier pour lancer le RIP DTF.")
        else:
            ib("TIF CMJN + PRN générés en une passe — prêts pour impression.")
            if st.button("🚀 Lancer RIP DTF",type="primary",use_container_width=True,key="dtf_rip"):
                try:
                    pg=st.progress(0); sm=st.empty()
                    def cbd(v,m): pg.progress(int(v)); sm.markdown(f"**⚙️ {m}**")
                    s2=src_d or load_img(up_d)
                    tif_d,inf_d=rip_dtf_eng(s2,dtf_w,dtf_h,dtf_dpi,dtf_mir,dtf_comp,cbd)
                    ts=datetime.now().strftime("%Y%m%d_%H%M"); bn=Path(up_d.name).stem
                    fn_td=f"{bn}_DTF_{fmt}_{dtf_dpi}dpi_CMJN_{ts}.tif"
                    fn_prd=fn_td.replace(".tif",".prn")
                    job_d={"name":bn,"w":dtf_w,"h":dtf_h,
                           "or":"portrait" if dtf_h>=dtf_w else "landscape",
                           "cop":dtf_cop,"dpi":dtf_dpi,"icc":"DTF_CMYK",
                           "mir":dtf_mir,"wb":dtf_wb,"bl":0,
                           "cols":1,"rows":1,"gh":0,"gv":0,"mg":0,
                           "file":up_d.name,"mode":"DTF","q":dtf_q}
                    prn_d=make_prn(job_d).encode()
                    fn_pdf_d=fn_td.replace(".tif",".pdf")
                    sm.markdown("**✅ RIP DTF terminé !**")
                    rb(f"✅ <strong>RIP DTF !</strong> · {inf_d['wpx']:,}×{inf_d['hpx']:,} px · {len(tif_d)/1e6:.1f} MB")
                    if dtf_out=="tif":
                        st.download_button("⬇️ TIF CMJN DTF",tif_d,fn_td,"image/tiff",use_container_width=True)
                    elif dtf_out=="pdf":
                        pdf_d=make_pdf(Image.open(io.BytesIO(tif_d)).convert("RGB"),dtf_w,dtf_h,dtf_dpi)
                        st.download_button("⬇️ PDF DTF",pdf_d,fn_pdf_d,"application/pdf",use_container_width=True)
                    elif dtf_out=="prn":
                        st.download_button("⬇️ PRN MainTap",prn_d,fn_prd,"text/plain",use_container_width=True)
                    else:
                        pdf_zip=make_pdf(Image.open(io.BytesIO(tif_d)).convert("RGB"),dtf_w,dtf_h,dtf_dpi)
                        readme=(f"IMPRESSION DTF\nFormat:{fmt} {dtf_w:.0f}x{dtf_h:.0f}mm DPI:{dtf_dpi} Copies:{dtf_cop}\n"
                                f"Miroir:{'Oui' if dtf_mir else 'Non'} WhiteBase:{'Oui' if dtf_wb else 'Non'}\n\n"
                                f"1. {fn_td}   → vérification TIF\n"
                                f"2. {fn_pdf_d} → vérification PDF\n"
                                f"3. {fn_prd}   → charger dans MainTap\n").encode()
                        pv_buf=io.BytesIO(); pv_d.save(pv_buf,"PNG")
                        zb=make_zip({fn_td:tif_d,fn_pdf_d:pdf_zip,fn_prd:prn_d,
                                     f"{bn}_apercu.png":pv_buf.getvalue(),"README.txt":readme})
                        st.download_button("⬇️ ZIP complet",zb,fn_td.replace(".tif","_DTF.zip"),"application/zip",use_container_width=True)
                        da,db,dc=st.columns(3)
                        da.download_button("⬇️ TIF",tif_d,fn_td,"image/tiff")
                        db.download_button("⬇️ PDF",pdf_zip,fn_pdf_d,"application/pdf")
                        dc.download_button("⬇️ PRN",prn_d,fn_prd,"text/plain")
                except Exception as e: st.error(f"❌ Erreur DTF : {e}"); st.exception(e)


# ╔═══════════════════════════════════════════════════════════
# ║  ONGLET 3 — SUPPRESSION DE FOND (pro)
# ╚═══════════════════════════════════════════════════════════
with TAB_BG:

    BGL,BGR=st.columns([1.05,1],gap="large")

    with BGL:
        sec("1","Image source")
        up_b=st.file_uploader("Image avec fond à supprimer",
            type=["png","jpg","jpeg","tif","tiff","bmp","webp"],
            key="bg_up",label_visibility="collapsed")
        src_b=None
        if up_b:
            try: src_b=load_img(up_b)
            except Exception as e: st.warning(f"❌ {e}")
            if src_b:
                rb(f"📂 <strong>{up_b.name}</strong> · {up_b.size/1024:.0f} KB · {src_b.width}×{src_b.height} px")

        sec("2","Méthode de suppression")
        method=st.radio("Algorithme",
            ["Blanc","Noir","Couleur","FloodFill (bords)","GrabCut (auto)"],
            horizontal=False,key="bg_meth",
            captions=[
                "Supprime les zones proches du blanc",
                "Supprime les zones proches du noir",
                "Supprime une couleur précise",
                "Supprime le fond connecté aux bords de l'image (idéal fond uni)",
                "Séparation automatique sujet/fond par IA (idéal objets centrés)",
            ])

        tol=st.slider("Tolérance / Sensibilité",min_value=5,max_value=150,value=40,key="bg_tol",
                      help="Augmentez si le fond n'est pas entièrement supprimé. "
                           "Réduisez si des parties du sujet disparaissent.")

        if method=="Couleur":
            ib("Entrez les valeurs RVB de la couleur à supprimer (0–255).")
            bc1,bc2,bc3=st.columns(3)
            with bc1: cr=st.number_input("Rouge",min_value=0,max_value=255,value=0,key="bg_r")
            with bc2: cg=st.number_input("Vert",min_value=0,max_value=255,value=255,key="bg_g")
            with bc3: cb_=st.number_input("Bleu",min_value=0,max_value=255,value=0,key="bg_b")
            cpick=(int(cr),int(cg),int(cb_))
        else:
            cpick=(255,255,255)

        sec("3","Affinement des bords")
        c1,c2=st.columns(2)
        with c1: refine=st.toggle("🔬 Nettoyer les pixels parasites",value=True,key="bg_ref")
        with c2: feather=st.slider("Lissage bords (px)",0,8,2,key="bg_fth")

        sec("4","Format de sortie")
        bg_fmt=st.radio("Format",
            ["PNG transparent","PNG fond coloré","TIF CMJN (fond blanc)"],
            horizontal=False,key="bg_fmt")
        bg_dpi=st.selectbox("Résolution DPI",[72,150,300,600],index=2,key="bg_dpi")

        if "fond coloré" in bg_fmt:
            fc1,fc2,fc3=st.columns(3)
            with fc1: nbr=st.number_input("R fond",0,255,255,key="nr")
            with fc2: nbg=st.number_input("G fond",0,255,255,key="ng")
            with fc3: nbb=st.number_input("B fond",0,255,255,key="nb")
            new_bg_color=(int(nbr),int(nbg),int(nbb))
        else:
            new_bg_color=(255,255,255)

    with BGR:
        sec("","Aperçu")

        if not src_b:
            wb("Chargez une image pour commencer.")
        else:
            # Calcul aperçu en temps réel
            with st.spinner("Calcul de l'aperçu…"):
                try:
                    prev_result=remove_bg_advanced(src_b,method,int(tol),cpick,refine,feather)
                    result_ready=True
                except Exception as e:
                    st.error(f"Erreur aperçu : {e}"); result_ready=False; prev_result=None

            if result_ready and prev_result:
                col_av,col_ap=st.columns(2)
                with col_av:
                    st.markdown("**Avant**")
                    st.image(src_b,use_container_width=True)
                with col_ap:
                    st.markdown("**Après**")
                    # Damier pour montrer la transparence
                    W,H=prev_result.size; cs=max(8,min(W,H)//30)
                    chk=Image.new("RGB",(W,H))
                    dk=ImageDraw.Draw(chk)
                    c1v=(200,200,200) if DARK else (180,180,180)
                    c2v=(255,255,255)
                    for y in range(0,H,cs):
                        for x in range(0,W,cs):
                            dk.rectangle([x,y,x+cs,y+cs],fill=c1v if (x//cs+y//cs)%2==0 else c2v)
                    chk.paste(prev_result.convert("RGB"),(0,0),prev_result.split()[3])
                    st.image(chk,use_container_width=True)

                # Info pixels supprimés
                alpha_arr=np.array(prev_result.split()[3])
                pct_removed=int(100*(alpha_arr<128).sum()/(alpha_arr.size))
                rb(f"✅ Aperçu prêt · <strong>{pct_removed}%</strong> du fond supprimé · "
                   f"{prev_result.width}×{prev_result.height} px")

                st.markdown("")
                if st.button("✂️  Supprimer le fond — Télécharger",
                             type="primary",use_container_width=True,key="bg_run"):
                    try:
                        with st.spinner("Génération du fichier final…"):
                            final=remove_bg_advanced(src_b,method,int(tol),cpick,refine,feather)
                        bn=Path(up_b.name).stem; ts=datetime.now().strftime("%Y%m%d_%H%M")
                        if "PNG transparent" in bg_fmt:
                            buf=io.BytesIO(); final.save(buf,"PNG",optimize=True); buf.seek(0)
                            st.download_button("⬇️ PNG transparent",buf.read(),
                                f"{bn}_sans_fond_{ts}.png","image/png",use_container_width=True)
                        elif "fond coloré" in bg_fmt:
                            nbg_img=Image.new("RGB",final.size,new_bg_color)
                            nbg_img.paste(final.convert("RGB"),(0,0),final.split()[3])
                            buf=io.BytesIO(); nbg_img.save(buf,"PNG"); buf.seek(0)
                            st.download_button("⬇️ PNG fond coloré",buf.read(),
                                f"{bn}_fond_colore_{ts}.png","image/png",use_container_width=True)
                        else:
                            bg_w=Image.new("RGB",final.size,(255,255,255))
                            bg_w.paste(final.convert("RGB"),(0,0),final.split()[3])
                            tif_bg=to_tif(bg_w.convert("CMYK"),bg_dpi,"tiff_lzw")
                            st.download_button("⬇️ TIF CMJN",tif_bg,
                                f"{bn}_sans_fond_{ts}.tif","image/tiff",use_container_width=True)
                        rb(f"✅ <strong>Fichier prêt !</strong> · Format : {bg_fmt} · "
                           f"{final.width}×{final.height} px · {bg_dpi} DPI")
                    except Exception as e: st.error(f"❌ Erreur : {e}"); st.exception(e)
