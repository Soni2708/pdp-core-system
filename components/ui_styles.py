import streamlit as st

def apply_global_cyberpunk_theme():
    """Tema Cinematic Enterprise + Safe Compact Mode"""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Rajdhani:wght@600;700&display=swap');
        
        /* Background Dark Slate (Premium SaaS vibe) */
        .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
        
        /* =========================================================
           🚀 SAFE COMPACT MODE (PRODUCTION-GRADE SPACING)
           ========================================================= */
        hr { 
            border: none !important; 
            border-top: 1px dashed #30363d !important; 
            margin: 1rem 0 !important; 
        }
        
        div[data-testid="metric-container"] {
            padding-bottom: 0.5rem !important; 
        }

        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            /* 💉 NEXUS PRIME PATCH: max-width dicabut agar tetap menghormati layout="centered" bawaan page */
        }
        /* ========================================================= */

        /* Kotak Input & Selectbox - Crisp Minimalist */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, div[data-baseweb="number"] > div { 
            background-color: #161b22 !important; 
            border: 1px solid #30363d !important; 
            border-radius: 6px !important; 
            color: #e2e8f0 !important; 
            transition: border-color 0.3s ease !important;
        }
        div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within { 
            border-color: #00d2d3 !important; 
            box-shadow: 0 0 0 1px #00d2d3 !important; /* Sharp glow, bukan blur glow */
        }
        
        label { color: #8b949e !important; font-weight: 500 !important; margin-bottom: 4px !important; font-size: 13px !important;}

        /* Tombol Eksekusi Utama - Elegant Ghost Button */
        div.stButton > button:first-child, div[data-testid="stFormSubmitButton"] > button {
            background-color: transparent !important; 
            color: #c9d1d9 !important; 
            border: 1px solid #30363d !important; 
            border-radius: 6px !important; 
            font-family: 'Rajdhani', sans-serif !important;
            font-size: 16px !important;
            font-weight: 700 !important; 
            letter-spacing: 1px;
            transition: all 0.3s ease !important;
            width: 100% !important;
        }
        div.stButton > button:first-child:hover, div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: #00d2d3 !important; 
            color: #00d2d3 !important;
            background-color: rgba(0, 210, 211, 0.05) !important;
            transform: translateY(-1px);
        }

        /* Tombol Spesifik (Logout & Sync) - Muted Resting State */
        .btn-logout div.stButton > button:first-child, .btn-sync div.stButton > button:first-child { 
            border-color: #30363d !important; 
            color: #8b949e !important; 
            font-size: 12px !important; 
            padding: 4px 8px !important; 
            background: transparent !important;
        }
        .btn-logout div.stButton > button:first-child:hover { 
            border-color: #ff4d6d !important; 
            color: #ff4d6d !important; 
            background-color: rgba(255, 77, 109, 0.05) !important; 
            box-shadow: 0 0 10px rgba(255, 77, 109, 0.15) !important; 
        }
        .btn-sync div.stButton > button:first-child:hover { 
            border-color: #feca57 !important; 
            color: #feca57 !important; 
            background-color: rgba(254, 202, 87, 0.05) !important; 
            box-shadow: 0 0 10px rgba(254, 202, 87, 0.15) !important; 
        }

        /* Badge Alarm - Dikalibrasi untuk keterbacaan tinggi */
        .badge-overdue { background-color: rgba(255, 77, 109, 0.1); color: #ff4d6d; border: 1px solid rgba(255, 77, 109, 0.5); padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; display: inline-block; margin-top: 5px; }
        .badge-normal { background-color: #161b22; color: #8b949e; border: 1px solid #30363d; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; display: inline-block; margin-top: 5px; }

        /* Expander UI - Premium Box */
        div[data-testid="stExpander"] { background-color: #0d1117; border: 1px solid #30363d; border-radius: 6px; }
        div[data-testid="stExpander"] summary { 
            color: #8b949e !important; 
            font-family: 'Inter', sans-serif !important; 
            font-size: 13px !important; 
            font-weight: 500 !important;
            letter-spacing: 0.5px !important; 
            transition: color 0.2s ease !important;
        }
        div[data-testid="stExpander"] summary:hover {
            color: #c9d1d9 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_cyberpunk_header(title, subtitle, color_hex="#00d2d3", align="center"):
    """Render Judul dengan Cinematic Depth (Tanpa Neon Menyilaukan)"""
    color_map = {"#0284c7": "#00d2d3", "#dc2626": "#ff4d6d", "#d97706": "#feca57", "#00e5ff": "#00d2d3", "#ff2a2a": "#ff4d6d", "#ffc107": "#feca57", "#ff0055": "#ff4d6d"}
    soft_neon = color_map.get(color_hex.lower(), color_hex)

    align_style = "text-align: center;" if align == "center" else "text-align: left;"
    st.markdown(f"""
        <div style='{align_style} width: 100%; margin-bottom: 15px;'> 
            <h1 style='
                color: #ffffff; 
                font-family: "Rajdhani", sans-serif; 
                font-size: 32px; 
                font-weight: 700; 
                margin-top: 0px; 
                margin-bottom: 0px; 
                letter-spacing: 2px;
                text-transform: uppercase;
                text-shadow: 0 2px 4px rgba(0,0,0,0.5); /* Depth shadow, bukan glow shadow */
                border-bottom: 2px solid {soft_neon}80;
                display: inline-block;
                padding-bottom: 6px;
            '>{title}</h1>
            <p style='color:#8b949e; font-family:"Inter", sans-serif; font-size: 13px; margin-top: 8px; letter-spacing: 1px; font-weight:500;'>{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)
