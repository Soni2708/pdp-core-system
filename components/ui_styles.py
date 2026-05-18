import streamlit as st

def apply_global_cyberpunk_theme():
    """Tema Cinematic Enterprise + Adaptive Light/Dark Mode + Safe Compact Mode"""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Rajdhani:wght@600;700&display=swap');
        
        /* =========================================================
           🚀 NEXUS PRIME ARCHITECTURE: CSS Variables (Adaptive Theme)
           ========================================================= */
        :root {
            /* LIGHT MODE (Default - untuk siang hari / layar terang) */
            --bg-base: #f8fafc;
            --bg-surface: #ffffff;
            --border-color: #cbd5e1;
            --text-primary: #0f172a;
            --text-muted: #64748b;
            --accent-cyan: #0284c7;
            --accent-red: #e11d48;
            --accent-yellow: #d97706;
            --shadow-subtle: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            --shadow-glow-cyan: 0 0 10px rgba(2, 132, 199, 0.15);
            --btn-hover-bg: rgba(2, 132, 199, 0.05);
            --expander-bg: #f1f5f9;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                /* DARK MODE (Cyberpunk Enterprise - untuk malam / ruang kontrol) */
                --bg-base: #0d1117;
                --bg-surface: #161b22;
                --border-color: #30363d;
                --text-primary: #c9d1d9;
                --text-muted: #8b949e;
                --accent-cyan: #00d2d3;
                --accent-red: #ff4d6d;
                --accent-yellow: #feca57;
                --shadow-subtle: 0 4px 12px rgba(0, 210, 211, 0.05);
                --shadow-glow-cyan: 0 0 10px rgba(0, 210, 211, 0.15);
                --btn-hover-bg: rgba(0, 210, 211, 0.05);
                --expander-bg: #0d1117;
            }
        }

        /* ---------------------------------------------------------
           GLOBAL INJECTION
           --------------------------------------------------------- */
        .stApp { 
            background-color: var(--bg-base) !important; 
            color: var(--text-primary) !important; 
            font-family: 'Inter', sans-serif; 
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        
        hr { 
            border: none !important; 
            border-top: 1px dashed var(--border-color) !important; 
            margin: 1rem 0 !important; 
        }
        
        div[data-testid="metric-container"] { padding-bottom: 0.5rem !important; }

        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }

        /* ---------------------------------------------------------
           FORM & INPUTS (Crisp Minimalist + Glass-like UI)
           --------------------------------------------------------- */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, div[data-baseweb="number"] > div { 
            background-color: var(--bg-surface) !important; 
            border: 1px solid var(--border-color) !important; 
            border-radius: 6px !important; 
            color: var(--text-primary) !important; 
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
        }
        div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within { 
            border-color: var(--accent-cyan) !important; 
            box-shadow: 0 0 0 1px var(--accent-cyan) !important; 
        }
        
        label { 
            color: var(--text-muted) !important; 
            font-weight: 600 !important; 
            margin-bottom: 4px !important; 
            font-size: 13px !important;
            letter-spacing: 0.5px;
        }

        /* ---------------------------------------------------------
           MAIN BUTTONS (Elegant Ghost Button)
           --------------------------------------------------------- */
        div.stButton > button:first-child, div[data-testid="stFormSubmitButton"] > button {
            background-color: transparent !important; 
            color: var(--text-primary) !important; 
            border: 1px solid var(--border-color) !important; 
            border-radius: 6px !important; 
            font-family: 'Rajdhani', sans-serif !important;
            font-size: 16px !important;
            font-weight: 700 !important; 
            letter-spacing: 1px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
        }
        div.stButton > button:first-child:hover, div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: var(--accent-cyan) !important; 
            color: var(--accent-cyan) !important;
            background-color: var(--btn-hover-bg) !important;
            transform: translateY(-2px);
            box-shadow: var(--shadow-glow-cyan);
        }

        /* ---------------------------------------------------------
           SPECIFIC BUTTONS (Logout & Sync) - Reliable Selection
           --------------------------------------------------------- */
        .btn-logout div[data-testid="stButton"] button, .btn-sync div[data-testid="stButton"] button { 
            border-color: var(--border-color) !important; 
            color: var(--text-muted) !important; 
            font-size: 13px !important; 
            padding: 4px 12px !important; 
            background: var(--bg-surface) !important;
            transition: all 0.2s ease-in-out !important;
        }
        .btn-logout div[data-testid="stButton"] button:hover { 
            border-color: var(--accent-red) !important; 
            color: var(--accent-red) !important; 
            background-color: rgba(225, 29, 72, 0.05) !important; 
            transform: scale(0.98); /* Tactile press effect */
            box-shadow: 0 0 10px rgba(225, 29, 72, 0.15) !important; 
        }
        .btn-sync div[data-testid="stButton"] button:hover { 
            border-color: var(--accent-yellow) !important; 
            color: var(--accent-yellow) !important; 
            background-color: rgba(217, 119, 6, 0.05) !important; 
            transform: scale(0.98);
            box-shadow: 0 0 10px rgba(217, 119, 6, 0.15) !important; 
        }

        /* ---------------------------------------------------------
           BADGES & ALARMS
           --------------------------------------------------------- */
        .badge-overdue { 
            background-color: rgba(225, 29, 72, 0.1); 
            color: var(--accent-red); 
            border: 1px solid rgba(225, 29, 72, 0.5); 
            padding: 4px 8px; 
            border-radius: 4px; 
            font-size: 11px; 
            font-weight: 700; 
            display: inline-block; 
            margin-top: 5px; 
        }
        .badge-normal { 
            background-color: var(--bg-surface); 
            color: var(--text-muted); 
            border: 1px solid var(--border-color); 
            padding: 4px 8px; 
            border-radius: 4px; 
            font-size: 11px; 
            font-weight: 600; 
            display: inline-block; 
            margin-top: 5px; 
        }

        /* ---------------------------------------------------------
           EXPANDER UI (Premium Box)
           --------------------------------------------------------- */
        div[data-testid="stExpander"] { 
            background-color: var(--expander-bg); 
            border: 1px solid var(--border-color); 
            border-radius: 6px; 
            transition: all 0.3s ease;
        }
        div[data-testid="stExpander"] summary { 
            color: var(--text-muted) !important; 
            font-family: 'Inter', sans-serif !important; 
            font-size: 13px !important; 
            font-weight: 600 !important;
            letter-spacing: 0.5px !important; 
            transition: color 0.2s ease !important;
        }
        div[data-testid="stExpander"] summary:hover {
            color: var(--text-primary) !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_cyberpunk_header(title, subtitle, color_hex="#00d2d3", align="center"):
    """Render Judul dengan Cinematic Depth adaptif untuk Light/Dark Mode"""
    
    # Mapping pintar untuk mengamankan warna neon jika sedang di light mode agar tetap terlihat berkelas
    color_map = {
        "#0284c7": "var(--accent-cyan)", 
        "#dc2626": "var(--accent-red)", 
        "#d97706": "var(--accent-yellow)", 
        "#00e5ff": "var(--accent-cyan)", 
        "#ff2a2a": "var(--accent-red)", 
        "#ffc107": "var(--accent-yellow)", 
        "#ff0055": "var(--accent-red)"
    }
    
    # Gunakan mapping jika ada, atau fallback ke color_hex input
    adaptive_color = color_map.get(color_hex.lower(), color_hex)
    align_style = "text-align: center;" if align == "center" else "text-align: left;"
    
    st.markdown(f"""
        <div style='{align_style} width: 100%; margin-bottom: 20px;'> 
            <h1 style='
                color: var(--text-primary); 
                font-family: "Rajdhani", sans-serif; 
                font-size: 34px; 
                font-weight: 700; 
                margin-top: 0px; 
                margin-bottom: 0px; 
                letter-spacing: 2px;
                text-transform: uppercase;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1); 
                border-bottom: 3px solid {adaptive_color};
                display: inline-block;
                padding-bottom: 6px;
            '>{title}</h1>
            <p style='
                color: var(--text-muted); 
                font-family: "Inter", sans-serif; 
                font-size: 14px; 
                margin-top: 8px; 
                letter-spacing: 1px; 
                font-weight: 500;
            '>{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)
