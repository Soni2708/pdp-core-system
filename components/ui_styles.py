import streamlit as st

def apply_global_cyberpunk_theme():
    """Tema Soft Pastel Cyberpunk + COMPACT MODE (Hemat Space)"""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Rajdhani:wght@600;700&display=swap');
        
        /* Background Dark Slate */
        .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
        
        /* =========================================================
           🚀 COMPACT MODE TWEAKS (MEMANGKAS JARAK KOSONG) 
           ========================================================= */
        /* 1. Pangkas jarak gila bawaan garis Streamlit (hr) */
        hr { 
            border: none !important; 
            border-top: 1px dashed #30363d !important; 
            margin: 5px 0 10px 0 !important; /* Jarak atas cuma 5px, bawah 10px */
        }
        
        /* 2. Pangkas margin bawah pada angka metrik (st.metric) */
        div[data-testid="metric-container"] {
            margin-bottom: -15px !important; 
        }
        
        /* 3. Rapatkan container metrik custom kita */
        div[data-testid="stMarkdownContainer"] > div {
            margin-bottom: 0px !important;
        }

        /* 4. Tarik seluruh aplikasi agak ke atas agar tidak buang space di layar atas */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        /* ========================================================= */

        /* Kotak Input & Selectbox */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, div[data-baseweb="number"] > div { 
            background-color: #161b22 !important; 
            border: 1px solid #30363d !important; 
            border-radius: 6px !important; 
            color: #e2e8f0 !important; 
        }
        div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within { 
            border-color: #00d2d3 !important; 
            box-shadow: 0 0 8px rgba(0, 210, 211, 0.25) !important; 
        }
        
        label { color: #8b949e !important; font-weight: 500 !important; margin-bottom: 2px !important;}

        /* Tombol Eksekusi Utama */
        div.stButton > button:first-child, div[data-testid="stFormSubmitButton"] > button {
            background-color: transparent !important; 
            color: #00d2d3 !important; 
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
            box-shadow: 0 0 12px rgba(0, 210, 211, 0.2) !important;
            transform: translateY(-1px);
        }

        /* Tombol Spesifik (Logout & Sync) */
        .btn-logout div.stButton > button:first-child { border-color: #ff4d6d !important; color: #ff4d6d !important; font-size:12px !important; padding: 4px 8px !important; }
        .btn-logout div.stButton > button:first-child:hover { background-color: rgba(255, 77, 109, 0.1) !important; box-shadow: 0 0 8px rgba(255, 77, 109, 0.3) !important; }
        
        .btn-sync div.stButton > button:first-child { border-color: #feca57 !important; color: #feca57 !important; font-size:12px !important; padding: 4px 8px !important; }
        .btn-sync div.stButton > button:first-child:hover { background-color: rgba(254, 202, 87, 0.1) !important; box-shadow: 0 0 8px rgba(254, 202, 87, 0.3) !important; }

        /* Badge Alarm Soft Glow */
        .badge-overdue { background-color: rgba(255, 77, 109, 0.15); color: #ff4d6d; border: 1px solid #ff4d6d; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; display: inline-block; margin-top: 5px; box-shadow: 0 0 8px rgba(255, 77, 109, 0.25); }
        .badge-normal { background-color: #161b22; color: #8b949e; border: 1px solid #30363d; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; display: inline-block; margin-top: 5px; }

        /* Expander & Custom UI (Diperkecil sesuai instruksi) */
        div[data-testid="stExpander"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; }
        div[data-testid="stExpander"] summary { 
            color: #00d2d3 !important; 
            font-family: 'Inter', sans-serif !important; /* Font lebih kalem */
            font-size: 13px !important; /* Diperkecil */
            font-weight: 500 !important;
            letter-spacing: 0.5px !important; 
        }
        </style>
    """, unsafe_allow_html=True)

def render_cyberpunk_header(title, subtitle, color_hex="#00d2d3", align="center"):
    """Render Judul dengan Soft Neon Glow & Margin Compact"""
    color_map = {"#0284c7": "#00d2d3", "#dc2626": "#ff4d6d", "#d97706": "#feca57", "#00e5ff": "#00d2d3", "#ff2a2a": "#ff4d6d", "#ffc107": "#feca57", "#ff0055": "#ff4d6d"}
    soft_neon = color_map.get(color_hex.lower(), color_hex)

    align_style = "text-align: center;" if align == "center" else "text-align: left;"
    st.markdown(f"""
        <div style='{align_style} width: 100%; margin-bottom: 5px;'> <!-- Margin bottom dikecilkan -->
            <h1 style='
                color: #ffffff; 
                font-family: "Rajdhani", sans-serif; 
                font-size: 34px; 
                font-weight: 700; 
                margin-top: -15px; /* Ditarik naik */
                margin-bottom: 0px; 
                letter-spacing: 3px;
                text-transform: uppercase;
                text-shadow: 0 0 12px {soft_neon}50;
                border-bottom: 2px solid {soft_neon}80;
                display: inline-block;
                padding-bottom: 5px;
            '>{title}</h1>
            <p style='color:#8b949e; font-family:"Inter", sans-serif; font-size: 13px; margin-top: 5px; letter-spacing: 1px; font-weight:500;'>{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)