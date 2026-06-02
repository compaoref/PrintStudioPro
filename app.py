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
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="PrintStudio Pro",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════
# SIDEBAR — THÈME & INFOS
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Paramètres")
    theme = st.radio("Thème", ["🌙 Sombre", "☀️ Clair"], index=0, key="theme")
    DARK = theme == "🌙 Sombre"
    st.markdown("---")
    st.markdown("**PrintStudio Pro** `v3.0`")
    st.caption("Système RIP intégré\nCMJN · TIF · PMN\nGrand Format · DTF")
    st.markdown("---")
    st.markdown("**Formats supportés**")
    st.caption("PDF · PNG · JPG · TIF\nAI · EPS · CDR · SVG · BMP")

# ═══════════════════════════════════════════════════════════
# PALETTE THÈME
# ═══════════════════════════════════════════════════════════
if DARK:
    BG="#0d0f14"; SURFACE="#161921"; SURFACE2="#1e2330"; BORDER="#2a3045"
    TEXT="#e8ecf5"; MUTED="#7a869a"; ACCENT="#ff5c1a"; GREEN="#00c8a0"
    BLUE="#4da6ff"; WARN="#ffb020"; PREV_BG="#111520"; PREV_GRID="#1d2235"
    SHADOW="rgba(0,0,0,.22)"; INFO_BG="rgba(77,166,255,.07)"; INFO_BD="rgba(77,166,255,.3)"
    OK_BG="rgba(0,200,160,.07)"; OK_BD="rgba(0,200,160,.35)"; WARN_BG="rgba(255,176,32,.07)"; WARN_BD="rgba(255,176,32,.3)"
else:
    BG="#f4f6fb"; SURFACE="#ffffff"; SURFACE2="#eef0f8"; BORDER="#d5d9ec"
    TEXT="#1a1e2e"; MUTED="#6b7280"; ACCENT="#e64a00"; GREEN="#00a882"
    BLUE="#2563eb"; WARN="#d97706"; PREV_BG="#e8eaf2"; PREV_GRID="#d2d6e8"
    SHADOW="rgba(0,0,0,.07)"; INFO_BG="rgba(37,99,235,.06)"; INFO_BD="rgba(37,99,235,.25)"
    OK_BG="rgba(0,168,130,.07)"; OK_BD="rgba(0,168,130,.3)"; WARN_BG="rgba(217,119,6,.06)"; WARN_BD="rgba(217,119,6,.25)"

# ═══════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html,body,[class*="css"],.stApp{{font-family:'Inter',sans-serif!important;background:{BG}!important;color:{TEXT}!important}}
.block-container{{padding-top:1.2rem!important;padding-bottom:3rem!important;max-width:1300px!important}}

/* HEADER */
.psp-header{{background:{SURFACE};border:1px solid {BORDER};border-radius:16px;padding:24px 32px;margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 16px {SHADOW}}}
.psp-logo{{font-size:26px;font-weight:800;letter-spacing:-.5px;color:{TEXT}}}
.psp-logo em{{color:{ACCENT};font-style:normal}}
.psp-sub{{font-size:12px;color:{MUTED};margin-top:4px}}
.psp-badge{{background:{ACCENT};color:white;font-size:10px;font-weight:700;padding:3px 10px;border-radius:20px;letter-spacing:1px;text-transform:uppercase}}

/* SECTION HEADERS */
.sec-hdr{{display:flex;align-items:center;gap:10px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:{MUTED};padding:18px 0 10px;border-bottom:1px solid {BORDER};margin-bottom:14px}}
.sec-num{{width:22px;height:22px;background:{ACCENT};color:white;border-radius:50%;font-size:11px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}}

/* CARDS */
.stat-card{{background:{SURFACE};border:1px solid {BORDER};border-radius:12px;padding:14px 10px;text-align:center;box-shadow:0 1px 4px {SHADOW}}}
.stat-card .lbl{{font-size:10px;font-weight:600;color:{MUTED};text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px}}
.stat-card .val{{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:700;color:{TEXT};line-height:1.3}}
.stat-card .val.accent{{color:{ACCENT}}}
.stat-card .val.green{{color:{GREEN}}}
.stat-card .val.blue{{color:{BLUE}}}

/* ALERT BOXES */
.result-box{{background:{OK_BG};border:1.5px solid {OK_BD};border-radius:10px;padding:13px 16px;font-size:13px;color:{GREEN};margin:12px 0;line-height:1.6}}
.info-box{{background:{INFO_BG};border:1.5px solid {INFO_BD};border-radius:10px;padding:12px 15px;font-size:13px;color:{BLUE};margin:10px 0 14px}}
.warn-box{{background:{WARN_BG};border:1.5px solid {WARN_BD};border-radius:10px;padding:12px 15px;font-size:13px;color:{WARN};margin:10px 0}}

/* CARD CONTAINER */
.param-card{{background:{SURFACE};border:1px solid {BORDER};border-radius:14px;padding:20px;margin-bottom:16px;box-shadow:0 1px 6px {SHADOW}}}

/* TABS */
.stTabs [data-baseweb="tab-list"]{{background:{SURFACE};border-radius:12px;padding:5px;gap:4px;border:1px solid {BORDER};box-shadow:0 1px 6px {SHADOW}}}
.stTabs [data-baseweb="tab"]{{border-radius:9px!important;font-weight:600!important;font-size:14px!important;padding:10px 22px!important;color:{MUTED}!important;background:transparent!important;transition:all .2s!important}}
.stTabs [aria-selected="true"]{{background:{ACCENT}!important;color:white!important}}

/* INPUTS */
.stNumberInput input,.stSelectbox select,.stTextInput input{{background:{SURFACE2}!important;border:1px solid {BORDER}!important;border-radius:8px!important;color:{TEXT}!important;font-size:14px!important}}

/* SIDEBAR */
[data-testid="stSidebar"]{{background:{SURFACE}!important;border-right:1px solid {BORDER}!important}}

/* FILE UPLOADER */
[data-testid="stFileUploader"]{{background:{SURFACE2}!important;border:2px dashed {BORDER}!important;border-radius:12px!important}}
[data-testid="stFileUploader"]:hover{{border-color:{ACCENT}!important}}

/* BUTTONS */
.stButton>button{{background:{ACCENT}!important;color:white!important;border:none!important;border-radius:10px!important;font-weight:600!important;font-size:14px!important;padding:12px 28px!important;transition:all .2s!important;box-shadow:0 2px 8px rgba(255,92,26,.28)!important}}
.stButton>button:hover{{transform:translateY(-1px)!important;box-shadow:0 4px 14px rgba(255,92,26,.38)!important}}
.stDownloadButton>button{{background:{GREEN}!important;color:{'#061410' if DARK else 'white'}!important;border:none!important;border-radius:10px!important;font-weight:700!important;font-size:14px!important;padding:12px 28px!important;box-shadow:0 2px 8px rgba(0,200,160,.25)!important}}

/* RADIO */
.stRadio label{{font-size:13px!important;font-weight:500!important;color:{TEXT}!important}}
hr{{border-color:{BORDER}!important;margin:18px 0!important}}
#MainMenu,footer,header{{visibility:hidden}}

/* COLUMN DIVIDER */
.col-divider{{width:1px;background:{BORDER};min-height:400px;margin:0 8px}}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# CONSTANTES & FONCTIONS
# ═══════════════════════════════════════════════════════════
INCH=39.3701; MMPI=25.4

def sec(n,t): st.markdown(f'<div class="sec-hdr">{"<span class=sec-num>"+str(n)+"</span>" if n else ""}{t}</div>',unsafe_allow_html=True)
def rbox(h):  st.markdown(f'<div class="result-box">{h}</div>',unsafe_allow_html=True)
def ibox(h):  st.markdown(f'<div class="info-box">ℹ️ {h}</div>',unsafe_allow_html=True)
def wbox(h):  st.markdown(f'<div class="warn-box">⚠️ {h}</div>',unsafe_allow_html=True)
def scard(lbl,val,cls=""): return f'<div class="stat-card"><div class="lbl">{lbl}</div><div class="val {cls}">{val}</div></div>'

def px_m(m,d):   return max(1,int(m*INCH*d))
def px_mm(mm,d): return max(1,int((mm/MMPI)*d))
def est_tif(w,h): b=int(w*h*4*.38); return f"{b/1e6:.1f} MB" if b>=1e6 else f"{b/1024:.0f} KB"

def fnt(s=9):
    try: return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",s)
    except: return ImageFont.load_default()
def fnt_mono(s=9):
    try: return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",s)
    except: return ImageFont.load_default()
def h2rgb(h):
    h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))

def load_img(up) -> Image.Image:
    data=up.read(); up.seek(0)
    if up.name.lower().endswith(".pdf") and HAS_MUPDF:
        doc=fitz.open(stream=data,filetype="pdf")
        pix=doc[0].get_pixmap(matrix=fitz.Matrix(4,4),alpha=True)
        img=Image.frombytes("RGBA",[pix.width,pix.height],pix.samples)
        doc.close(); return img
    img=Image.open(io.BytesIO(data))
    return img.convert("RGBA") if img.mode!="RGBA" else img

def to_tif(img:Image.Image, dpi:int, comp:str) -> bytes:
    if img.mode in ("RGBA","RGB"):
        bg=Image.new("RGB",img.size,(255,255,255))
        if img.mode=="RGBA": bg.paste(img.convert("RGB"),mask=img.split()[3])
        else: bg=img
        img=bg.convert("CMYK")
    buf=io.BytesIO(); img.save(buf,format="TIFF",dpi=(dpi,dpi),compression=comp)
    return buf.getvalue()

def pmn(job:dict) -> str:
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return "\n".join([
        "; PrintStudio Pro — Job PMN",f"; {now}","","[JobInfo]",
        f"JobName={job.get('name','Job')}",f"Created={now}","","[Media]",
        f"Width={job.get('w_mm',0):.2f}",f"Height={job.get('h_mm',0):.2f}",
        "Unit=mm",f"Orientation={job.get('orient','portrait')}","","[Print]",
        f"Copies={job.get('copies',1)}",f"DPI={job.get('dpi',300)}",
        "ColorMode=CMYK",f"ColorProfile={job.get('icc','ISOcoated_v2')}",
        f"Mirror={1 if job.get('mirror') else 0}",
        f"WhiteBase={1 if job.get('wb') else 0}",
        f"Bleed={job.get('bleed',0):.1f}","","[RIP]","Software=MainTap",
        f"Quality={job.get('q','High')}","RenderIntent=Perceptual","","[Grid]",
        f"Cols={job.get('cols',1)}",f"Rows={job.get('rows',1)}",
        f"GapH={job.get('gh',0):.1f}",f"GapV={job.get('gv',0):.1f}",
        f"Margin={job.get('mg',0):.1f}","","[Source]",
        f"File={job.get('file','')}",f"Mode={job.get('mode','Standard')}",
    ])

def make_zip(files:dict) -> bytes:
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED) as z:
        for n,d in files.items(): z.writestr(n,d)
    return buf.getvalue()

# ── RIP GRAND FORMAT ────────────────────────────────────────
def rip_gf(src,w_m,h_m,cols,rows,gh,gv,mg,bl,dpi,rot,icc,comp,kr,prog=None):
    def p(v,m):
        if prog: prog(v,m)
    p(5,"Calcul dimensions pixel…")
    wpx=px_m(w_m,dpi); hpx=px_m(h_m,dpi)
    mp=px_mm(mg,dpi); ghp=px_mm(gh,dpi); gvp=px_mm(gv,dpi)
    cw=max(1,(wpx-2*mp-ghp*(cols-1))//cols)
    ch=max(1,(hpx-2*mp-gvp*(rows-1))//rows)
    p(18,f"Préparation source — {rot}°…")
    s=src.convert("RGBA")
    if rot: s=s.rotate(-rot,expand=True)
    if kr:
        r=s.width/s.height
        cw2,ch2=(int(ch*r),ch) if cw/ch>r else (cw,int(cw/r))
    else: cw2,ch2=cw,ch
    s=s.resize((cw2,ch2),Image.LANCZOS)
    p(35,"Création planche blanche…")
    board=Image.new("RGB",(wpx,hpx),(255,255,255))
    p(50,f"Placement {cols}×{rows}={cols*rows} éléments…")
    alpha=s.split()[3] if s.mode=="RGBA" else None
    sr=s.convert("RGB")
    for r_ in range(rows):
        for c_ in range(cols):
            x=mp+c_*(cw+ghp)+(cw-cw2)//2
            y=mp+r_*(ch+gvp)+(ch-ch2)//2
            cb=Image.new("RGB",(cw2,ch2),(255,255,255))
            cb.paste(sr,(0,0),alpha)
            board.paste(cb,(x,y))
    p(75,f"Conversion CMJN — {icc}…"); board=board.convert("CMYK")
    p(90,f"Encodage TIF ({comp})…"); tif=to_tif(board,dpi,comp)
    p(100,"✅ RIP terminé !")
    return tif,{"wpx":wpx,"hpx":hpx,"cw_mm":(cw/dpi)*MMPI,"ch_mm":(ch/dpi)*MMPI,"total":cols*rows}

# ── RIP DTF ─────────────────────────────────────────────────
def rip_dtf(src,w_mm,h_mm,dpi,mirror,wb,comp,prog=None):
    def p(v,m):
        if prog: prog(v,m)
    p(5,"Calcul zone DTF…")
    wpx=px_mm(w_mm,dpi); hpx=px_mm(h_mm,dpi)
    p(20,"Mise en forme…"); s=src.convert("RGBA")
    if mirror: s=s.transpose(Image.FLIP_LEFT_RIGHT)
    r=s.width/s.height; t=wpx/hpx
    nw=wpx if r>t else int(hpx*r); nh=int(wpx/r) if r>t else hpx
    s=s.resize((nw,nh),Image.LANCZOS)
    p(45,"Composition…"); base=Image.new("RGB",(wpx,hpx),(255,255,255))
    ox=(wpx-nw)//2; oy=(hpx-nh)//2; al=s.split()[3]
    base.paste(s.convert("RGB"),(ox,oy),al)
    p(70,"Conversion CMJN…"); cmyk=base.convert("CMYK")
    p(88,"Encodage TIF…"); tif=to_tif(cmyk,dpi,comp)
    p(100,"✅ RIP DTF terminé !")
    return tif,{"wpx":wpx,"hpx":hpx}

# ── SUPPRESSION FOND ────────────────────────────────────────
def remove_bg(img:Image.Image, method:str, tol:int, cpick:tuple) -> Image.Image:
    rgba=img.convert("RGBA"); arr=np.array(rgba,dtype=np.uint8)
    if method=="Blanc":
        mask=(arr[:,:,0].astype(int)+arr[:,:,1].astype(int)+arr[:,:,2].astype(int))>(765-tol*3)
    elif method=="Noir":
        mask=(arr[:,:,0].astype(int)+arr[:,:,1].astype(int)+arr[:,:,2].astype(int))<(tol*3)
    else:
        r0,g0,b0=cpick
        dist=np.sqrt((arr[:,:,0].astype(int)-r0)**2+(arr[:,:,1].astype(int)-g0)**2+(arr[:,:,2].astype(int)-b0)**2)
        mask=dist<tol
    arr[mask,3]=0
    return Image.fromarray(arr,"RGBA")

# ── APERÇUS ─────────────────────────────────────────────────
def prev_simple(src,w_mm,h_mm,rot,kr,pw=680):
    ph=min(int(pw*h_mm/w_mm) if w_mm>0 else pw,520); ph=max(ph,160)
    board=Image.new("RGB",(pw,ph),h2rgb(PREV_BG)); draw=ImageDraw.Draw(board)
    gc=h2rgb(PREV_GRID)
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
        bg=Image.new("RGB",(iw2,ih2),h2rgb(PREV_BG))
        bg.paste(s.convert("RGB"),(0,0),s.split()[3])
        board.paste(bg,(ox,oy))
        ac=h2rgb(ACCENT)
        draw.rectangle([ox-2,oy-2,ox+iw2+1,oy+ih2+1],outline=ac,width=2)
        draw.line([(ox,oy-14),(ox+iw2,oy-14)],fill=ac,width=1)
        draw.line([(ox,oy-18),(ox,oy-10)],fill=ac,width=1); draw.line([(ox+iw2,oy-18),(ox+iw2,oy-10)],fill=ac,width=1)
        draw.text(((ox+ox+iw2)//2,oy-14),f"{w_mm:.1f} mm",fill=ac,font=fnt(9),anchor="mm")
    else:
        draw.rectangle([pad,pad,pw-pad,ph-pad],outline=h2rgb(BORDER),width=2)
        draw.text((pw//2,ph//2),"Chargez une image",fill=h2rgb(MUTED),font=fnt(14),anchor="mm")
    draw.rectangle([0,ph-22,pw,ph],fill=h2rgb(SURFACE2))
    draw.text((pw//2,ph-11),f"{w_mm:.1f}×{h_mm:.1f} mm  |  {w_mm/10:.1f}×{h_mm/10:.1f} cm  |  {w_mm/1000:.3f}×{h_mm/1000:.3f} m",
              fill=h2rgb(ACCENT),font=fnt_mono(9),anchor="mm")
    return board

def prev_grid(src,cols,rows,w_m,h_m,gh,gv,mg,rot,pw=680):
    ph=min(int(pw*h_m/w_m) if w_m>0 else pw,520); ph=max(ph,180)
    board=Image.new("RGB",(pw,ph),h2rgb(PREV_BG)); draw=ImageDraw.Draw(board)
    gc=h2rgb(PREV_GRID)
    for x in range(0,pw,28): draw.line([(x,0),(x,ph)],fill=gc,width=1)
    for y in range(0,ph,28): draw.line([(0,y),(pw,y)],fill=gc,width=1)
    sc=pw/(w_m*1000); mp=int(mg*sc); ghp=int(gh*sc); gvp=int(gv*sc)
    uw=pw-2*mp-ghp*(cols-1); uh=ph-2*mp-gvp*(rows-1)
    cw=max(2,uw//cols); ch=max(2,uh//rows)
    ac=h2rgb(ACCENT)
    pal=[(40,55,85),(35,60,70),(55,42,72),(60,48,36),(36,58,52),(52,52,42)] if DARK else \
        [(218,230,252),(210,242,236),(236,222,248),(248,236,216),(215,237,228),(236,232,216)]
    for r_ in range(rows):
        for c_ in range(cols):
            x=mp+c_*(cw+ghp); y=mp+r_*(ch+gvp)
            cc=pal[(r_*cols+c_)%6]
            if src:
                s=src.copy().convert("RGBA")
                if rot: s=s.rotate(-rot,expand=True)
                s=s.resize((cw,ch),Image.LANCZOS)
                bg=Image.new("RGB",(cw,ch),cc)
                bg.paste(s.convert("RGB"),(0,0),s.split()[3])
                board.paste(bg,(x,y))
            else: draw.rectangle([x,y,x+cw-1,y+ch-1],fill=cc)
            draw.rectangle([x,y,x+cw-1,y+ch-1],outline=ac,width=2)
            fs=max(7,min(ch//3,15))
            draw.text((x+cw//2,y+ch//2),str(r_*cols+c_+1),fill=ac,font=fnt(fs),anchor="mm")
    if mg>0:
        wc=h2rgb(WARN)
        draw.rectangle([mp,mp,pw-mp-1,ph-mp-1],outline=(*wc,130),width=1)
    draw.rectangle([0,ph-22,pw,ph],fill=h2rgb(SURFACE2))
    draw.text((pw//2,ph-11),f"Support {w_m:.3f}×{h_m:.3f} m  |  {cols}×{rows}={cols*rows} éléments  |  CMJN TIF",
              fill=h2rgb(ACCENT),font=fnt_mono(9),anchor="mm")
    return board

def prev_dtf(src,w_mm,h_mm,mirror,pw_max=320):
    r=h_mm/w_mm if w_mm>0 else 1; ph=min(int(pw_max*r),460); pw=min(pw_max,int(ph/r)); ph=max(ph,180)
    board=Image.new("RGB",(pw,ph),h2rgb(PREV_BG)); draw=ImageDraw.Draw(board)
    pad=10
    draw.rectangle([pad,pad,pw-pad,ph-pad],fill=h2rgb(SURFACE2),outline=h2rgb(BORDER),width=1)
    if src:
        s=src.copy().convert("RGBA")
        if mirror: s=s.transpose(Image.FLIP_LEFT_RIGHT)
        iw,ih=pw-pad*4,ph-pad*4; rr=s.width/s.height; tt=iw/ih
        nw=iw if rr>tt else int(ih*rr); nh=int(iw/rr) if rr>tt else ih
        s=s.resize((nw,nh),Image.LANCZOS)
        ox=pad*2+(iw-nw)//2; oy=pad*2+(ih-nh)//2
        bg=Image.new("RGB",(nw,nh),h2rgb(SURFACE2))
        bg.paste(s.convert("RGB"),(0,0),s.split()[3])
        board.paste(bg,(ox,oy))
    else: draw.text((pw//2,ph//2),"Chargez un fichier",fill=h2rgb(MUTED),font=fnt(11),anchor="mm")
    gc=h2rgb(GREEN); mk=14
    for (cx,cy) in [(pad,pad),(pw-pad,pad),(pad,ph-pad),(pw-pad,ph-pad)]:
        dx=1 if cx==pad else -1; dy=1 if cy==pad else -1
        draw.line([(cx,cy),(cx+dx*mk,cy)],fill=gc,width=2)
        draw.line([(cx,cy),(cx,cy+dy*mk)],fill=gc,width=2)
    if mirror:
        draw.rectangle([pad,pad,pw-pad,pad+16],fill=h2rgb(SURFACE))
        draw.text((pw//2,pad+8),"MIROIR",fill=h2rgb(ACCENT),font=fnt(9),anchor="mm")
    draw.rectangle([0,ph-20,pw,ph],fill=h2rgb(SURFACE))
    draw.text((pw//2,ph-10),f"{w_mm:.0f}×{h_mm:.0f} mm",fill=h2rgb(GREEN),font=fnt_mono(9),anchor="mm")
    return board

# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="psp-header">
  <div>
    <div class="psp-logo">Print<em>Studio</em> Pro</div>
    <div class="psp-sub">Système RIP intégré · Grand Format · Vinyle · Bâche · DTF · Suppression de fond</div>
  </div>
  <div style="display:flex;gap:8px;align-items:center">
    <span class="psp-badge">CMJN</span>
    <span class="psp-badge" style="background:{GREEN}">TIF</span>
    <span class="psp-badge" style="background:{BLUE}">PMN</span>
    <span class="psp-badge" style="background:{MUTED}">RIP v3</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# ONGLETS
# ═══════════════════════════════════════════════════════════
tab_gf, tab_dtf, tab_bg = st.tabs([
    "🖨️  Grand Format — Vinyle / Bâche",
    "👕  DTF — Textile",
    "✂️  Suppression de fond",
])

# ╔═══════════════════════════════════════════════════════════
# ║  ONGLET 1 — GRAND FORMAT
# ╚═══════════════════════════════════════════════════════════
with tab_gf:

    col_params, col_preview = st.columns([1.05, 1], gap="large")

    # ── COLONNE PARAMÈTRES ────────────────────────────────────
    with col_params:

        # 1. FICHIER
        sec("1","Fichier source")
        up = st.file_uploader(
            "Logo, étiquette, maquette…",
            type=["pdf","png","jpg","jpeg","tif","tiff","bmp","ai","eps","cdr","svg"],
            key="gf_up", label_visibility="collapsed",
        )
        src_img = None
        if up:
            try: src_img = load_img(up)
            except Exception as e: st.warning(f"Aperçu non disponible : {e}")
            rbox(f"📂 <strong>{up.name}</strong> &nbsp;·&nbsp; {up.size/1024:.0f} KB"
                 +(f" &nbsp;·&nbsp; {src_img.width}×{src_img.height} px" if src_img else ""))

        # 2. MODE
        sec("2","Type de travail")
        mode = st.radio("Mode",
            ["🖼️  Image simple","📏  Multiplication par planche","🏷️  Multiplication par étiquette"],
            key="gf_mode", label_visibility="collapsed")

        # 3. DIMENSIONS selon le mode
        sec("3","Dimensions & Support")

        # ─── IMAGE SIMPLE ─────────────────────────────────────
        if mode == "🖼️  Image simple":
            ibox("L'image est redimensionnée aux dimensions exactes indiquées, sans multiplication.")
            unit = st.radio("Unité", ["mm","cm","m"], horizontal=True, key="si_u")
            ku={"mm":1.,"cm":10.,"m":1000.}[unit]
            dw={"mm":1500.,"cm":150.,"m":1.5}[unit]; dh={"mm":1000.,"cm":100.,"m":1.}[unit]
            st_={"mm":.5,"cm":.05,"m":.001}[unit]
            a,b_ = st.columns(2)
            with a: iw_i=st.number_input(f"Largeur ({unit})",min_value=.1,value=dw,step=st_,key="si_w")
            with b_: ih_i=st.number_input(f"Hauteur ({unit})",min_value=.1,value=dh,step=st_,key="si_h")
            lbl_w=iw_i*ku; lbl_h=ih_i*ku
            c1,c2=st.columns(2)
            with c1: kr=st.checkbox("🔗 Conserver les proportions",value=True,key="si_kr")
            with c2: bleed=st.number_input("Fond perdu (mm)",min_value=0.,max_value=20.,value=0.,key="si_bl")
            print_w=lbl_w/1000; print_h=lbl_h/1000
            cols_v=1; rows_v=1; gh=0.; gv=0.; mg=0.
            rbox(f"📐 Impression : <strong>{lbl_w:.1f} × {lbl_h:.1f} mm</strong>"
                 f" &nbsp;({lbl_w/10:.1f} × {lbl_h/10:.1f} cm / {print_w:.3f} × {print_h:.3f} m)")

        # ─── MULTIPLICATION PAR PLANCHE ───────────────────────
        elif mode == "📏  Multiplication par planche":
            ibox("Définissez la taille totale du support d'impression. La taille de chaque élément est calculée automatiquement.")

            # Support
            st.markdown("**Support d'impression**")
            unit_p=st.radio("Unité support",["m","cm","mm"],horizontal=True,key="pl_u")
            kp={"m":1.,"cm":.01,"mm":.001}[unit_p]
            dw_p={"m":1.5,"cm":150.,"mm":1500.}[unit_p]; dh_p={"m":1.,"cm":100.,"mm":1000.}[unit_p]
            st_p={"m":.01,"cm":.5,"mm":1.}[unit_p]
            a,b_=st.columns(2)
            with a: pw_i=st.number_input(f"Largeur support ({unit_p})",min_value=.01,value=dw_p,step=st_p,key="pl_w")
            with b_: ph_i=st.number_input(f"Hauteur support ({unit_p})",min_value=.01,value=dh_p,step=st_p,key="pl_h")
            print_w=pw_i*kp; print_h=ph_i*kp

            # Grille
            st.markdown("**Grille de multiplication**")
            g1,g2,g3,g4=st.columns(4)
            with g1: cols_v=st.number_input("Colonnes",min_value=1,max_value=100,value=3,key="pl_c")
            with g2: rows_v=st.number_input("Lignes",min_value=1,max_value=100,value=4,key="pl_r")
            with g3: gh=st.number_input("Esp. H (mm)",min_value=0.,value=3.,step=.5,key="pl_gh")
            with g4: gv=st.number_input("Esp. V (mm)",min_value=0.,value=3.,step=.5,key="pl_gv")
            m1,m2=st.columns(2)
            with m1: mg=st.number_input("Marge bord (mm)",min_value=0.,value=5.,key="pl_mg")
            with m2: bleed=st.number_input("Fond perdu (mm)",min_value=0.,max_value=20.,value=3.,key="pl_bl")
            kr=st.checkbox("🔗 Conserver proportions de l'élément",value=False,key="pl_kr")

            uw=print_w*1000-2*mg-gh*(cols_v-1); uh=print_h*1000-2*mg-gv*(rows_v-1)
            lbl_w=max(1.,uw/cols_v); lbl_h=max(1.,uh/rows_v)
            rbox(f"🏷️ Taille calculée / élément : <strong>{lbl_w:.1f} × {lbl_h:.1f} mm</strong>"
                 f" ({lbl_w/10:.2f} × {lbl_h/10:.2f} cm)"
                 f" &nbsp;·&nbsp; <strong>{int(cols_v*rows_v)}</strong> éléments")

        # ─── MULTIPLICATION PAR ÉTIQUETTE ─────────────────────
        else:
            ibox("Définissez la taille d'un élément. Vous pouvez aussi imposer une taille de support fixe.")

            # Taille de l'élément
            st.markdown("**Taille de l'élément**")
            unit_e=st.radio("Unité élément",["mm","cm","m"],horizontal=True,key="et_u")
            ke={"mm":1.,"cm":10.,"m":1000.}[unit_e]
            dw_e={"mm":100.,"cm":10.,"m":.1}[unit_e]; dh_e={"mm":50.,"cm":5.,"m":.05}[unit_e]
            st_e={"mm":.5,"cm":.05,"m":.001}[unit_e]
            a,b_=st.columns(2)
            with a: ew_i=st.number_input(f"Largeur élément ({unit_e})",min_value=.1,value=dw_e,step=st_e,key="et_w")
            with b_: eh_i=st.number_input(f"Hauteur élément ({unit_e})",min_value=.1,value=dh_e,step=st_e,key="et_h")
            lbl_w=ew_i*ke; lbl_h=eh_i*ke

            # Grille
            st.markdown("**Grille de multiplication**")
            g1,g2,g3,g4=st.columns(4)
            with g1: cols_v=st.number_input("Colonnes",min_value=1,max_value=100,value=3,key="et_c")
            with g2: rows_v=st.number_input("Lignes",min_value=1,max_value=100,value=4,key="et_r")
            with g3: gh=st.number_input("Esp. H (mm)",min_value=0.,value=3.,step=.5,key="et_gh")
            with g4: gv=st.number_input("Esp. V (mm)",min_value=0.,value=3.,step=.5,key="et_gv")
            m1,m2=st.columns(2)
            with m1: mg=st.number_input("Marge bord (mm)",min_value=0.,value=5.,key="et_mg")
            with m2: bleed=st.number_input("Fond perdu (mm)",min_value=0.,max_value=20.,value=3.,key="et_bl")
            kr=st.checkbox("🔗 Conserver proportions",value=False,key="et_kr")

            # Support d'impression
            st.markdown("**Support d'impression**")
            force_sup=st.checkbox("📐 Imposer une taille de support spécifique",value=False,key="et_fs")
            if force_sup:
                unit_s=st.radio("Unité support",["m","cm","mm"],horizontal=True,key="et_su")
                ks={"m":1.,"cm":.01,"mm":.001}[unit_s]
                dw_s={"m":1.5,"cm":150.,"mm":1500.}[unit_s]; dh_s={"m":1.,"cm":100.,"mm":1000.}[unit_s]
                st_s={"m":.01,"cm":.5,"mm":1.}[unit_s]
                fs1,fs2=st.columns(2)
                with fs1: fsw=st.number_input(f"Largeur support ({unit_s})",min_value=.01,value=dw_s,step=st_s,key="et_fw")
                with fs2: fsh=st.number_input(f"Hauteur support ({unit_s})",min_value=.01,value=dh_s,step=st_s,key="et_fh")
                print_w=fsw*ks; print_h=fsh*ks
                ibox(f"Support imposé : <strong>{print_w:.3f} m × {print_h:.3f} m</strong>. Les éléments sont placés selon la grille ; l'espace restant sera blanc.")
            else:
                print_w=(lbl_w*cols_v+gh*(cols_v-1)+2*mg)/1000
                print_h=(lbl_h*rows_v+gv*(rows_v-1)+2*mg)/1000

            rbox(f"📏 Support : <strong>{print_w:.3f} m × {print_h:.3f} m</strong>"
                 f" ({print_w*100:.1f} × {print_h*100:.1f} cm)"
                 f" &nbsp;·&nbsp; <strong>{int(cols_v*rows_v)}</strong> éléments"
                 f" de {lbl_w:.1f}×{lbl_h:.1f} mm")

        # 4. PARAMÈTRES RIP
        sec("4","Paramètres RIP")
        r1,r2,r3,r4=st.columns(4)
        with r1: dpi=st.selectbox("DPI",[72,150,300,600],index=2,key="gf_dpi")
        with r2: rot=st.selectbox("Rotation",[0,90,180,270],index=0,format_func=lambda x:f"{x}°",key="gf_rot")
        with r3: icc=st.selectbox("Profil ICC",["ISOcoated_v2","CoatedFOGRA39","UncoatedFOGRA29","SWOP"],key="gf_icc")
        with r4: comp=st.selectbox("Compression TIF",
                    {"tiff_lzw":"LZW (recommandé)","tiff_deflate":"Deflate","raw":"Aucune"}.keys(),
                    format_func={"tiff_lzw":"LZW (recommandé)","tiff_deflate":"Deflate","raw":"Aucune"}.get,
                    key="gf_comp")

        # 5. FORMAT DE SORTIE
        sec("5","Format de sortie")
        out=st.radio("Sortie",["tif","pmn","zip","zip_full"],
            format_func={"tif":"🖼️ TIF CMJN","pmn":"🖨️ PMN","zip":"📦 TIF + PMN","zip_full":"📦 ZIP + aperçu"}.get,
            horizontal=True, key="gf_out")

    # ── COLONNE DROITE — STATS & APERÇU ──────────────────────
    with col_preview:
        sec("","Récapitulatif & Aperçu")

        wpx=px_m(print_w,dpi); hpx=px_m(print_h,dpi); total=int(cols_v)*int(rows_v)
        a,b_,c_=st.columns(3)
        a.markdown(scard("Éléments",str(total),"accent"),unsafe_allow_html=True)
        b_.markdown(scard("Taille élément",f"{lbl_w:.0f}×{lbl_h:.0f} mm"),unsafe_allow_html=True)
        c_.markdown(scard("Support",f"{print_w:.2f}×{print_h:.2f} m"),unsafe_allow_html=True)
        st.markdown("")
        d,e=st.columns(2)
        d.markdown(scard("Pixels totaux",f"{wpx:,}×{hpx:,}","blue"),unsafe_allow_html=True)
        e.markdown(scard("TIF estimé",est_tif(wpx,hpx),"green"),unsafe_allow_html=True)

        st.markdown("")

        # Aperçu visuel
        if mode=="🖼️  Image simple":
            pv=prev_simple(src_img,lbl_w,lbl_h,rot,kr)
            st.image(pv,use_container_width=True,caption=f"Image : {lbl_w:.1f}×{lbl_h:.1f} mm")
        else:
            pv=prev_grid(src_img,int(cols_v),int(rows_v),print_w,print_h,gh,gv,mg,rot)
            st.image(pv,use_container_width=True,
                caption=f"{int(cols_v)}×{int(rows_v)} éléments — {lbl_w:.1f}×{lbl_h:.1f} mm — Support {print_w:.3f}×{print_h:.3f} m")

        st.markdown("")

        # Bouton RIP
        if not up:
            wbox("Chargez un fichier source pour lancer le RIP.")
        else:
            lbl_btn={"🖼️  Image simple":"🚀 Lancer RIP — Image simple CMJN",
                     "📏  Multiplication par planche":"🚀 Lancer RIP — Planche avec multiplication",
                     "🏷️  Multiplication par étiquette":"🚀 Lancer RIP — Planche avec multiplication"}[mode]
            if st.button(lbl_btn,type="primary",use_container_width=True,key="gf_rip"):
                try:
                    prog=st.progress(0); stat=st.empty()
                    def cb(v,m): prog.progress(int(v)); stat.markdown(f"**⚙️ {m}**")
                    src2=src_img or load_img(up)
                    ph_rip=print_h
                    if mode=="🖼️  Image simple" and kr and src2:
                        ph_rip=print_w/(src2.width/src2.height)
                    tif_b,info=rip_gf(src2,print_w,ph_rip,int(cols_v),int(rows_v),gh,gv,mg,bleed,dpi,rot,icc,comp,kr,cb)
                    ts=datetime.now().strftime("%Y%m%d_%H%M"); bn=Path(up.name).stem
                    if mode=="🖼️  Image simple":
                        fn_tif=f"{bn}_{lbl_w:.0f}x{lbl_h:.0f}mm_{dpi}dpi_CMJN_{ts}.tif"
                    else:
                        fn_tif=f"{bn}_elem{lbl_w:.0f}x{lbl_h:.0f}mm_sup{print_w:.2f}x{print_h:.2f}m_{int(cols_v)}x{int(rows_v)}_{dpi}dpi_CMJN_{ts}.tif"
                    fn_pmn=fn_tif.replace(".tif",".pmn")
                    job={"name":bn,"w_mm":print_w*1000,"h_mm":ph_rip*1000,
                         "orient":"landscape" if print_w>ph_rip else "portrait",
                         "copies":1,"dpi":dpi,"icc":icc,"mirror":False,"wb":False,
                         "bleed":bleed,"cols":int(cols_v),"rows":int(rows_v),
                         "gh":gh,"gv":gv,"mg":mg,"file":up.name,"mode":mode,"q":"High"}
                    pmn_b=pmn(job).encode()
                    stat.markdown("**✅ RIP terminé !**")
                    rbox(f"✅ <strong>RIP terminé !</strong> &nbsp;·&nbsp; {info['wpx']:,}×{info['hpx']:,} px &nbsp;·&nbsp; TIF {len(tif_b)/1e6:.1f} MB")
                    if out=="tif": st.download_button("⬇️ Télécharger TIF CMJN",tif_b,fn_tif,"image/tiff",use_container_width=True)
                    elif out=="pmn": st.download_button("⬇️ Télécharger PMN",pmn_b,fn_pmn,"text/plain",use_container_width=True)
                    else:
                        files={fn_tif:tif_b,fn_pmn:pmn_b}
                        if out=="zip_full":
                            buf=io.BytesIO(); pv.save(buf,"PNG"); files[f"{bn}_apercu.png"]=buf.getvalue()
                        zb=make_zip(files)
                        st.download_button("⬇️ Télécharger ZIP complet",zb,fn_tif.replace(".tif","_COMPLET.zip"),"application/zip",use_container_width=True)
                        da,db=st.columns(2)
                        da.download_button("⬇️ TIF seul",tif_b,fn_tif,"image/tiff")
                        db.download_button("⬇️ PMN seul",pmn_b,fn_pmn,"text/plain")
                except Exception as e: st.error(f"❌ Erreur : {e}"); st.exception(e)


# ╔═══════════════════════════════════════════════════════════
# ║  ONGLET 2 — DTF
# ╚═══════════════════════════════════════════════════════════
with tab_dtf:

    dl, dr = st.columns([1.05, 1], gap="large")

    with dl:
        sec("1","Fichier source")
        up_d=st.file_uploader("Chargez votre fichier DTF",
            type=["pdf","png","jpg","jpeg","tif","tiff","ai","eps","bmp","svg"],
            key="dtf_up", label_visibility="collapsed")
        src_d=None
        if up_d:
            try: src_d=load_img(up_d)
            except Exception as e: st.warning(f"Aperçu non disponible : {e}")
            rbox(f"📂 <strong>{up_d.name}</strong> &nbsp;·&nbsp; {up_d.size/1024:.0f} KB")

        sec("2","Format & Dimensions")
        fmt=st.radio("Format",["A4","A3","A2","A1","Personnalisé"],horizontal=True,key="dtf_fmt")
        DIMS={"A4":(210,297),"A3":(297,420),"A2":(420,594),"A1":(594,841)}
        if fmt=="Personnalisé":
            dc1,dc2=st.columns(2)
            with dc1: cw_=st.number_input("Largeur (mm)",min_value=10.,value=300.,key="dtf_cw")
            with dc2: ch_=st.number_input("Hauteur (mm)",min_value=10.,value=400.,key="dtf_ch")
            dtf_w,dtf_h=float(cw_),float(ch_)
        else:
            bw,bh=DIMS[fmt]
            ori=st.radio("Orientation",["Portrait","Paysage"],horizontal=True,key="dtf_or")
            dtf_w,dtf_h=(float(bw),float(bh)) if ori=="Portrait" else (float(bh),float(bw))

        sec("3","Paramètres d'impression")
        dp1,dp2=st.columns(2)
        with dp1:
            dtf_dpi=st.selectbox("Résolution DPI",[150,300,600,1200],index=1,key="dtf_dpi")
            dtf_col=st.selectbox("Mode couleur",{"cmyk":"CMJN (standard)","rgb":"RVB"}.keys(),
                        format_func={"cmyk":"CMJN (standard)","rgb":"RVB"}.get,key="dtf_col")
            dtf_comp=st.selectbox("Compression TIF",{"tiff_lzw":"LZW","tiff_deflate":"Deflate","raw":"Aucune"}.keys(),
                        format_func={"tiff_lzw":"LZW","tiff_deflate":"Deflate","raw":"Aucune"}.get,key="dtf_comp")
        with dp2:
            dtf_mir=st.toggle("🪞 Miroir (face intérieure)",value=False,key="dtf_mir")
            dtf_wb=st.toggle("⬜ White underbase",value=True,key="dtf_wb")
            dtf_cop=st.number_input("Copies",min_value=1,max_value=999,value=1,key="dtf_cop")
            dtf_q=st.selectbox("Qualité RIP",["Draft","Normal","High","Ultra"],index=2,key="dtf_q")

        sec("4","Format de sortie")
        dtf_out=st.radio("Sortie DTF",["tif","pmn","zip"],
            format_func={"tif":"🖼️ TIF CMJN","pmn":"🖨️ PMN","zip":"📦 ZIP complet"}.get,
            horizontal=True,key="dtf_out",index=2)

    with dr:
        sec("","Récapitulatif & Aperçu")
        wpx_d=px_mm(dtf_w,dtf_dpi); hpx_d=px_mm(dtf_h,dtf_dpi)
        e1,e2,e3,e4=st.columns(4)
        e1.markdown(scard("Format",fmt,"accent"),unsafe_allow_html=True)
        e2.markdown(scard("Dimensions",f"{dtf_w:.0f}×{dtf_h:.0f} mm"),unsafe_allow_html=True)
        e3.markdown(scard("DPI",str(dtf_dpi),"blue"),unsafe_allow_html=True)
        e4.markdown(scard("TIF estimé",est_tif(wpx_d,hpx_d),"green"),unsafe_allow_html=True)
        st.markdown("")
        st.markdown(f"""
| Paramètre | Valeur |
|---|---|
| Format | `{fmt}` |
| Dimensions | `{dtf_w:.0f} × {dtf_h:.0f} mm` |
| DPI | `{dtf_dpi}` → `{wpx_d:,} × {hpx_d:,} px` |
| Mode couleur | `{"CMJN" if dtf_col=="cmyk" else "RVB"}` |
| Miroir | `{"Oui ✅" if dtf_mir else "Non"}` |
| White underbase | `{"Oui ✅" if dtf_wb else "Non"}` |
| Copies | `{dtf_cop}` |
| Qualité | `{dtf_q}` |
""")
        pv_d=prev_dtf(src_d,dtf_w,dtf_h,dtf_mir)
        st.image(pv_d,caption=f"DTF {fmt} — {dtf_w:.0f}×{dtf_h:.0f} mm")
        st.markdown("")
        if not up_d:
            wbox("Chargez un fichier pour lancer le RIP DTF.")
        else:
            ibox("TIF CMJN + PMN générés en une seule passe — prêts pour MainTap.")
            if st.button("🚀 Lancer RIP DTF — Générer & Imprimer",type="primary",use_container_width=True,key="dtf_rip"):
                try:
                    pg=st.progress(0); st_=st.empty()
                    def cbd(v,m): pg.progress(int(v)); st_.markdown(f"**⚙️ {m}**")
                    s2=src_d or load_img(up_d)
                    tif_d,inf_d=rip_dtf(s2,dtf_w,dtf_h,dtf_dpi,dtf_mir,dtf_wb,dtf_comp,cbd)
                    ts=datetime.now().strftime("%Y%m%d_%H%M"); bn=Path(up_d.name).stem
                    fn_td=f"{bn}_DTF_{fmt}_{dtf_dpi}dpi_CMJN_{ts}.tif"; fn_pd=fn_td.replace(".tif",".pmn")
                    job_d={"name":bn,"w_mm":dtf_w,"h_mm":dtf_h,
                           "orient":"portrait" if dtf_h>=dtf_w else "landscape",
                           "copies":dtf_cop,"dpi":dtf_dpi,"icc":"DTF_CMYK",
                           "mirror":dtf_mir,"wb":dtf_wb,"bleed":0,
                           "cols":1,"rows":1,"gh":0,"gv":0,"mg":0,
                           "file":up_d.name,"mode":"DTF","q":dtf_q}
                    pmn_d=pmn(job_d).encode()
                    st_.markdown("**✅ RIP DTF terminé !**")
                    rbox(f"✅ <strong>RIP DTF terminé !</strong> &nbsp;·&nbsp; {inf_d['wpx']:,}×{inf_d['hpx']:,} px &nbsp;·&nbsp; {len(tif_d)/1e6:.1f} MB")
                    if dtf_out=="tif": st.download_button("⬇️ TIF CMJN DTF",tif_d,fn_td,"image/tiff",use_container_width=True)
                    elif dtf_out=="pmn": st.download_button("⬇️ PMN MainTap",pmn_d,fn_pd,"text/plain",use_container_width=True)
                    else:
                        readme=f"IMPRESSION DTF\nFormat:{fmt} {dtf_w:.0f}x{dtf_h:.0f}mm DPI:{dtf_dpi} Copies:{dtf_cop}\nMiroir:{'Oui' if dtf_mir else 'Non'} WhiteBase:{'Oui' if dtf_wb else 'Non'}\n\n1. {fn_td} → vérification visuelle\n2. {fn_pd} → charger dans MainTap\n".encode()
                        pv_buf=io.BytesIO(); pv_d.save(pv_buf,"PNG")
                        zb=make_zip({fn_td:tif_d,fn_pd:pmn_d,f"{bn}_apercu.png":pv_buf.getvalue(),"README.txt":readme})
                        st.download_button("⬇️ ZIP complet (TIF + PMN + README)",zb,fn_td.replace(".tif","_DTF.zip"),"application/zip",use_container_width=True)
                        da,db=st.columns(2)
                        da.download_button("⬇️ TIF seul",tif_d,fn_td,"image/tiff")
                        db.download_button("⬇️ PMN seul",pmn_d,fn_pd,"text/plain")
                except Exception as e: st.error(f"❌ Erreur DTF : {e}"); st.exception(e)


# ╔═══════════════════════════════════════════════════════════
# ║  ONGLET 3 — SUPPRESSION DE FOND
# ╚═══════════════════════════════════════════════════════════
with tab_bg:

    bl, br = st.columns([1.05, 1], gap="large")

    with bl:
        sec("1","Image source")
        up_b=st.file_uploader("Chargez une image avec fond à supprimer",
            type=["png","jpg","jpeg","tif","tiff","bmp","webp"],
            key="bg_up", label_visibility="collapsed")
        src_b=None
        if up_b:
            try: src_b=load_img(up_b)
            except Exception as e: st.warning(f"Aperçu non disponible : {e}")
            rbox(f"📂 <strong>{up_b.name}</strong> &nbsp;·&nbsp; {up_b.size/1024:.0f} KB"
                 +(f" &nbsp;·&nbsp; {src_b.width}×{src_b.height} px" if src_b else ""))

        sec("2","Méthode de suppression")
        method=st.radio("Type de fond",["Blanc","Noir","Couleur personnalisée"],horizontal=True,key="bg_meth")
        tol=st.slider("Tolérance (seuil de détection)",min_value=5,max_value=120,value=30,key="bg_tol",
                      help="Plus la valeur est haute, plus le fond est supprimé largement.")

        if method=="Couleur personnalisée":
            ibox("Entrez la couleur du fond à supprimer (valeurs R, G, B de 0 à 255).")
            bc1,bc2,bc3=st.columns(3)
            with bc1: cr=st.number_input("Rouge (R)",min_value=0,max_value=255,value=255,key="bg_r")
            with bc2: cg=st.number_input("Vert (G)",min_value=0,max_value=255,value=255,key="bg_g")
            with bc3: cb_=st.number_input("Bleu (B)",min_value=0,max_value=255,value=255,key="bg_b")
            cpick=(int(cr),int(cg),int(cb_))
        else:
            cpick=(255,255,255)

        sec("3","Options de sortie")
        bg_fmt=st.radio("Format de sortie",["PNG (transparent)","TIF CMJN (fond blanc)"],horizontal=True,key="bg_fmt")
        bg_dpi=st.selectbox("Résolution DPI",[72,150,300,600],index=2,key="bg_dpi")

    with br:
        sec("","Aperçu")

        if not src_b:
            st.markdown("")
            wbox("Chargez une image pour voir l'aperçu et lancer la suppression du fond.")
        else:
            col_av, col_ap = st.columns(2)
            with col_av:
                st.markdown("**Avant**")
                st.image(src_b, use_container_width=True)
            with col_ap:
                st.markdown("**Après (aperçu)**")
                try:
                    prev_bg=remove_bg(src_b,method,int(tol),cpick)
                    # Aperçu sur damier pour montrer la transparence
                    csize=14; W,H=prev_bg.width,prev_bg.height
                    checker=Image.new("RGB",(W,H))
                    draw_c=ImageDraw.Draw(checker)
                    for y in range(0,H,csize):
                        for x in range(0,W,csize):
                            c=(200,200,200) if (x//csize+y//csize)%2==0 else (255,255,255)
                            draw_c.rectangle([x,y,x+csize,y+csize],fill=c)
                    checker.paste(prev_bg.convert("RGB"),(0,0),prev_bg.split()[3])
                    st.image(checker,use_container_width=True)
                except Exception as e:
                    st.warning(f"Aperçu erreur : {e}"); prev_bg=None

            st.markdown("")
            if st.button("✂️  Supprimer le fond & Télécharger",type="primary",use_container_width=True,key="bg_run"):
                try:
                    with st.spinner("Traitement en cours…"):
                        result=remove_bg(src_b,method,int(tol),cpick)
                    bn=Path(up_b.name).stem; ts=datetime.now().strftime("%Y%m%d_%H%M")
                    if "PNG" in bg_fmt:
                        buf=io.BytesIO(); result.save(buf,"PNG"); buf.seek(0)
                        st.download_button("⬇️ Télécharger PNG transparent",buf.read(),f"{bn}_sans_fond_{ts}.png","image/png",use_container_width=True)
                    else:
                        # TIF CMJN avec fond blanc
                        bg_w=Image.new("RGB",result.size,(255,255,255))
                        bg_w.paste(result.convert("RGB"),(0,0),result.split()[3])
                        tif_bg=to_tif(bg_w.convert("CMYK"),bg_dpi,"tiff_lzw")
                        st.download_button("⬇️ Télécharger TIF CMJN",tif_bg,f"{bn}_sans_fond_{ts}.tif","image/tiff",use_container_width=True)
                    rbox(f"✅ <strong>Fond supprimé !</strong> &nbsp;·&nbsp; Format : {bg_fmt} &nbsp;·&nbsp; {result.width}×{result.height} px")
                except Exception as e: st.error(f"❌ Erreur : {e}"); st.exception(e)
