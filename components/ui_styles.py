import streamlit as st
import base64

def apply_neo_tokyo_corporate():
    """
    Tema Neo-Tokyo Corporate: Vision Pro x Bloomberg Terminal.
    Fokus pada readability, data-density, dan estetika enterprise futuristik.
    Telah dilengkapi dengan Anti-Light Mode (Mencegah OS bleeding).
    """
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* =========================================================
           CORE ARCHITECTURE: NEO-TOKYO CORPORATE PALETTE
           ========================================================= */
        :root {
            /* Backgrounds */
            --nt-bg-main: #0D0E12;         /* Charcoal Black */
            --nt-bg-sec: rgba(21, 23, 28, 0.65); /* Dark Graphite (Translucent for Glassmorphism) */
            --nt-bg-solid: #15171C;        /* Dark Graphite (Solid) */
            
            /* Accents */
            --nt-cyan: #00E5FF;            /* Electric Cyan */
            --nt-cyan-glow: rgba(0, 229, 255, 0.2);
            --nt-violet: #9D4EDD;          /* Neon Violet */
            
            /* Semantic Status */
            --nt-success: #00E676;         /* Emerald Green */
            --nt-warning: #FFC400;         /* Amber */
            --nt-error: #FF1744;           /* Crimson Red */
            
            /* Typography & Borders */
            --nt-text-primary: #F8F9FA;    /* Crisp White */
            --nt-text-muted: #8B949E;      /* Steel Gray */
            --nt-border: rgba(255, 255, 255, 0.08); /* Subtle Glass Border */
        }

        /* ---------------------------------------------------------
           GLOBAL TYPOGRAPHY & RESET
           --------------------------------------------------------- */
        .stApp { 
            background-color: var(--nt-bg-main) !important; 
            color: var(--nt-text-primary) !important; 
            font-family: 'Inter', sans-serif !important; 
        }
        
        p, span, h1, h2, h3, h4, h5, h6, li, label {
            color: var(--nt-text-primary) !important;
        }
        
        hr { 
            border: none !important; 
            border-top: 1px solid var(--nt-border) !important; 
            margin: 1.5rem 0 !important; 
        }

        /* ---------------------------------------------------------
           PREMIUM GLASSMORPHISM CONTAINERS
           --------------------------------------------------------- */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--nt-bg-sec) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid var(--nt-border) !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
            padding: 12px !important;
            transition: all 0.3s ease !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: var(--nt-cyan-glow) !important;
            box-shadow: 0 0 15px var(--nt-cyan-glow) !important;
        }

        /* ---------------------------------------------------------
           DATA-FIRST METRICS (KPI CARDS)
           --------------------------------------------------------- */
        div[data-testid="stMetricValue"] {
            font-size: 2.4rem !important;
            font-weight: 800 !important;
            color: var(--nt-text-primary) !important;
            letter-spacing: -1px !important;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5) !important;
        }
        
        div[data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            color: var(--nt-text-muted) !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
        }

        /* ---------------------------------------------------------
           FUTURISTIC BUTTONS
           --------------------------------------------------------- */
        div.stButton > button {
            background-color: var(--nt-bg-solid) !important; 
            color: var(--nt-text-primary) !important; 
            border: 1px solid var(--nt-border) !important; 
            border-radius: 6px !important; 
            font-weight: 600 !important; 
            font-size: 13px !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.2s ease !important;
        }
        
        div.stButton > button:hover {
            border-color: var(--nt-cyan) !important;
            color: var(--nt-cyan) !important;
            box-shadow: 0 0 10px var(--nt-cyan-glow) !important;
            transform: translateY(-1px);
        }

        div.stButton > button[kind="primary"] {
            background-color: transparent !important;
            color: var(--nt-cyan) !important;
            border: 1px solid var(--nt-cyan) !important;
            box-shadow: inset 0 0 10px var(--nt-cyan-glow) !important;
        }
        
        div.stButton > button[kind="primary"]:hover {
            background-color: var(--nt-cyan) !important;
            color: var(--nt-bg-main) !important;
            box-shadow: 0 0 15px var(--nt-cyan-glow) !important;
        }

        /* ---------------------------------------------------------
           MODAL DIALOG FIX
           --------------------------------------------------------- */
        div[data-testid="stDialog"] > div[role="dialog"] {
            background: var(--nt-bg-solid) !important;
            border: 1px solid var(--nt-border) !important;
            border-top: 3px solid var(--nt-cyan) !important;
            box-shadow: 0 10px 40px rgba(0,0,0,0.8) !important;
            border-radius: 8px !important;
        }

        /* ---------------------------------------------------------
           UTILITY TYPOGRAPHY CLASSES
           --------------------------------------------------------- */
        .nt-nopol {
            font-size: 20px;
            font-weight: 800;
            letter-spacing: 1.5px;
            color: var(--nt-text-primary);
        }
        
        .nt-meta {
            font-size: 12px;
            color: var(--nt-text-muted);
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .nt-badge-success { color: var(--nt-success); font-weight: 700; }
        .nt-badge-warning { color: var(--nt-warning); font-weight: 700; }
        .nt-badge-error { color: var(--nt-error); font-weight: 800; text-shadow: 0 0 8px rgba(255, 23, 68, 0.4); }

        /* =========================================================
           ANTI-LIGHT MODE OVERRIDES (CRITICAL FIX)
           ========================================================= */
        
        /* 1. PAKSA SIDEBAR MENJADI GELAP */
        [data-testid="stSidebar"] {
            background-color: var(--nt-bg-main, #0D0E12) !important;
            border-right: 1px solid var(--nt-border, rgba(255,255,255,0.08)) !important;
        }
        
        /* 2. PAKSA BACKGROUND INPUT, DROPDOWN, NUMBER INPUT MENJADI GELAP */
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="number"] > div {
            background-color: var(--nt-bg-solid, #15171C) !important;
            border: 1px solid var(--nt-border, rgba(255,255,255,0.08)) !important;
        }

        /* 3. PAKSA TEKS DALAM INPUT MENJADI PUTIH */
        div[data-baseweb="input"] input,
        div[data-baseweb="select"] div[aria-selected="true"],
        div[data-baseweb="select"] span {
            color: var(--nt-text-primary, #F8F9FA) !important;
            -webkit-text-fill-color: var(--nt-text-primary, #F8F9FA) !important;
        }

        /* 4. PAKSA LIST DROPDOWN (POPOVER/OPTIONS) MENJADI GELAP */
        div[data-baseweb="popover"] > div,
        ul[role="listbox"],
        ul[role="listbox"] li {
            background-color: var(--nt-bg-solid, #15171C) !important;
            color: var(--nt-text-primary, #F8F9FA) !important;
        }
        
        ul[role="listbox"] li:hover {
            background-color: rgba(0, 229, 255, 0.1) !important; /* Efek hover cyan */
            color: var(--nt-cyan, #00E5FF) !important;
        }
        
        /* 5. FIX CHECKBOX & TEXT AREA (OPSIONAL) */
        textarea {
            background-color: var(--nt-bg-solid, #15171C) !important;
            color: var(--nt-text-primary, #F8F9FA) !important;
            border: 1px solid var(--nt-border, rgba(255,255,255,0.08)) !important;
        }
        div[data-testid="stCheckbox"] label span {
            color: var(--nt-text-primary) !important;
        }

        /* ---------------------------------------------------------
           DYNAMIC STATE CLASSES (OVERDUE ALERTS)
           --------------------------------------------------------- */
        [data-testid="stVerticalBlockBorderWrapper"]:has(.overdue-flag) {
            background: rgba(255, 23, 68, 0.05) !important;
            border-color: rgba(255, 23, 68, 0.4) !important;
            box-shadow: 0 0 15px rgba(255, 23, 68, 0.2) !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_neo_tokyo_header(title, subtitle, accent="var(--nt-cyan)", align="left"):
    align_style = "text-align: center;" if align == "center" else "text-align: left;"
    st.markdown(f"""
        <div style='{align_style} width: 100%; margin-bottom: 24px; border-bottom: 1px solid var(--nt-border); padding-bottom: 16px;'> 
            <h1 style='color: var(--nt-text-primary) !important; font-size: 26px; font-weight: 800; margin: 0; text-transform: uppercase; letter-spacing: 1px;'>
                <span style='color: {accent};'>|</span> {title}
            </h1>
            <p style='color: var(--nt-text-muted) !important; font-size: 12px; margin-top: 6px; margin-left: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px;'>
                {subtitle}
            </p>
        </div>
    """, unsafe_allow_html=True)

@st.cache_data
def get_base64_image(image_path: str) -> str:
    """Membaca file gambar dari disk dan menyimpannya di cache RAM server."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

def render_logo(align="center", max_width="140px", margin_bottom="15px", padding_top="10px"):
    """
    Render logo perusahaan secara dinamis.
    Mendukung pengaturan posisi (center/left) dan ukuran per halaman.
    """
    img_b64 = get_base64_image("assets/logo.png")
    if img_b64:
        justify = "center" if align == "center" else "flex-start"
        st.markdown(f"""
            <div style='display: flex; justify-content: {justify}; align-items: center; margin-bottom: {margin_bottom}; width: 100%; padding-top: {padding_top};'>
                <img src='data:image/png;base64,{img_b64}' style='max-width: {max_width}; height: auto; object-fit: contain; filter: drop-shadow(0 0 10px rgba(255,255,255,0.1));'>
            </div>
        """, unsafe_allow_html=True)
