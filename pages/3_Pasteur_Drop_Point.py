import streamlit as st
import base64
import time

from components.ui_styles import apply_global_cyberpunk_theme
from components.navbar import render_navbar
from core.auth import require_auth
from db_utils import get_waktu_wib, fetch_mapped_data, safe_update_by_uuid, execute_batch_update_by_uuid
from services.data_pipeline import proses_kanban_pdp
from services.engine_kalkulasi import hitung_wt
from core.logger import setup_logger

log = setup_logger("SYSTEM_PDP")

st.set_page_config(page_title="PASTEUR DROP POINT", page_icon="🚐", layout="wide")
apply_global_cyberpunk_theme()
require_auth(module_name="pdp", secret_dict_name="users_pdp")

# ============================================================
# 🎨 SURGICAL CSS INJECTION: CARD COLOR CODING (FIXED)
# ============================================================
swimlane_css = """
<style>
/* KOLOM 1: KIRI (PORTAL) - Kotak warna Abu-abu Terang */
[data-testid="column"]:nth-child(1) [data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #f8fafc !important; 
    border: 1px solid #cbd5e1 !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
}

/* KOLOM 2: TENGAH (KM72) - Kotak warna Kuning/Amber Terang */
/* Pembeda warna yang sangat tegas untuk mengurangi pusing visual */
[data-testid="column"]:nth-child(2) [data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #fffbeb !important; 
    border: 2px solid #fde68a !important; 
    box-shadow: 0 4px 6px rgba(245, 158, 11, 0.1) !important;
}

/* KOLOM 3: KANAN (PDP) - Kotak warna Biru/Cyan Terang */
[data-testid="column"]:nth-child(3) [data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ecfeff !important; 
    border: 2px solid #a5f3fc !important;
    box-shadow: 0 4px 6px rgba(6, 182, 212, 0.1) !important;
}

/* DARK MODE ADAPTATION (Berjaga-jaga jika ada yang pakai mode gelap) */
@media (prefers-color-scheme: dark) {
    [data-testid="column"]:nth-child(1) [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161b22 !important; 
        border: 1px solid #30363d !important;
    }
    [data-testid="column"]:nth-child(2) [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #272114 !important; 
        border: 1px solid #926c05 !important;
    }
    [data-testid="column"]:nth-child(3) [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0b1a21 !important; 
        border: 1px solid #04414d !important;
    }
}
</style>
"""
st.markdown(swimlane_css, unsafe_allow_html=True)

# ========== SIDEBAR NAVIGASI ==========
render_navbar("pdp")

if 'reset_form_feeder' not in st.session_state: 
    st.session_state.reset_form_feeder = 0

# ==========================================
# 🛑 MODAL DIALOG DISPATCH FEEDER
# ==========================================
# 🛑 MODAL DIALOG DISPATCH FEEDER (REFACTORED: LEBIH COMPACT)
# width="medium" memberikan keseimbangan antara ruang input dan konteks dashboard
@st.dialog("🚦 DISPATCH FEEDER", width="medium")
def render_modal_dispatch(tujuan_target, armada_ready):
    # CSS Injeksi untuk mengontrol lebar dialog agar tidak 'bulky'
    st.markdown("""
        <style>
        [data-testid="stDialog"] {
            max-width: 600px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"Pemberangkatan Feeder rute: <b style='color:var(--accent-cyan);'>{tujuan_target}</b>", unsafe_allow_html=True)
    
    # ... (sisanya isi fungsi tetap sama)
    
    list_armada = [item['label'] for item in armada_ready]
    
    if not list_armada:
        st.warning(f"Belum ada antrian penumpang untuk rute {tujuan_target}.")
        if st.button("Tutup Panel"):
            st.rerun()
        return

    pilihan_massal = st.multiselect(
        f"Pilih Penumpang dari Unit Reguler tujuan ke ({tujuan_target}):", 
        options=list_armada,
        key=f"sel_{tujuan_target}_{st.session_state.reset_form_feeder}"
    )
    
    c1, c2 = st.columns(2)
    with c1: 
        drv_f = st.text_input("Nama Driver Feeder", key=f"drv_{tujuan_target}_{st.session_state.reset_form_feeder}").upper()
    with c2: 
        nopol_f = st.text_input("Nopol Feeder", placeholder="Contoh: D 4321 XYZ", key=f"npl_{tujuan_target}_{st.session_state.reset_form_feeder}").upper()
    
    with st.expander("📝 CATATAN KETERLAMBATAN (OPSIONAL)"):
        catatan_f = st.text_input(
            "Catatan", placeholder="Wajib diisi jika Waktu Tunggu lebih dari 30 Menit", 
            label_visibility="collapsed", key=f"cat_{tujuan_target}_{st.session_state.reset_form_feeder}"
        )
        
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    if st.button(f"BERANGKATKAN FEEDER {tujuan_target}", use_container_width=True, type="primary"):
        waktu_sekarang = get_waktu_wib()
        ada_pelanggaran = any(hitung_wt(next(i['jam_tiba'] for i in armada_ready if i['label'] == p), waktu_sekarang) >= 30 for p in pilihan_massal)
        
        if not pilihan_massal or not drv_f.strip() or not nopol_f.strip():
            st.error("⚠️ Validasi Gagal: Lengkapi Nama Pengemudi, Nomor Polisi, dan minimal satu unit pilihan!")
        elif ada_pelanggaran and not catatan_f.strip():
            st.error("🚨 PERINGATAN: Waktu Tunggu melebihi batas SLA (WT ≥ 30 Menit). Kolom Catatan Keterlambatan Wajib Diisi!")
        else:
            with st.spinner("Sinkronisasi enkripsi manifes Feeder ke PostgreSQL Supabase..."):
                jam_out = waktu_sekarang.strftime("%H:%M")
                
                map_kolom = {
                    "MIM / BUAHBATU": ["driver_mim_buahbatu", "nopol_mim_buahbatu", "mim_bbt_out", "wt_mim_bbt"],
                    "KOPO": ["driver_kopo", "nopol_kopo", "kopo_out", "wt_kopo"],
                    "JATINANGOR": ["driver_jtn", "nopol_jtn", "jtn_out", "wt_jtn"]
                }[tujuan_target]
                
                c_drv, c_nopol, c_jam, c_wt = map_kolom
                uuid_updates = []
                
                for p in pilihan_massal:
                    target_data = next(item for item in armada_ready if item['label'] == p)
                    wt_val = hitung_wt(target_data['jam_tiba'], waktu_sekarang)
                    
                    dict_update = {
                        c_drv: drv_f.strip(), 
                        c_nopol: nopol_f.strip(), 
                        c_jam: jam_out, 
                        c_wt: wt_val
                    }
                    if catatan_f.strip(): 
                        dict_update["keterangan"] = catatan_f.strip() 
                        
                    uuid_updates.append({"trip_id": target_data['trip_id'], "updates": dict_update})
                        
                if uuid_updates:
                    sukses, pesan = execute_batch_update_by_uuid(uuid_updates)
                    if sukses:
                        petugas = st.session_state.get('petugas_pdp', 'Unknown')
                        log.info(f"DISPATCH: Petugas {petugas} memberangkatkan Feeder {nopol_f} ({drv_f}) rute {tujuan_target}.")
                        st.session_state.reset_form_feeder += 1 
                        fetch_mapped_data.clear()
                        st.rerun()            
                    else:
                        st.error(f"Kegagalan Transmisi Pipa Data: {pesan}")

# ==========================================
# 🎨 UI HEADER STATIC 
# ==========================================
try:
    with open("assets/logo.png", "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    st.markdown(f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 15px; width: 100%; padding-top: 10px;'>
            <img src='data:image/png;base64,{img_b64}' style='max-width: 160px; height: auto; object-fit: contain; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.1));'>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

col_judul, col_spacer, col_sync, _ = st.columns([5, 2.5, 1.2, 1.3], vertical_alignment="bottom")
with col_judul:
    st.markdown("<h2 style='color: var(--text-primary); font-family: \"Rajdhani\", sans-serif; font-size: 32px; font-weight: 700; margin-top: -10px; margin-bottom: 5px; letter-spacing: 3px; border-bottom: 3px solid var(--accent-cyan); display: inline-block; padding-bottom: 6px;'>PASTEUR DROP POINT</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: left; margin-top:-5px; font-size:13px; font-family:\"Inter\", sans-serif;'><span style='color:var(--text-muted);'>Sistem Transit & Feeder</span> | <span style='color:var(--accent-cyan); font-weight:bold;'>USER: {st.session_state.get('petugas_pdp', '')}</span></p>", unsafe_allow_html=True)

with col_sync:
    if st.button("🔄 Refresh", use_container_width=True): 
        fetch_mapped_data.clear()
        st.rerun()            

st.divider()

# ==========================================
# ⚡ STREAMLIT FRAGMENT (Live Data Engine)
# ==========================================
@st.fragment(run_every=30)
def live_dashboard_board():
    waktu_sekarang = get_waktu_wib()
    semua_data = fetch_mapped_data()
    
    if semua_data is None:
        st.error("🚨 KONEKSI DATABASE TERPUTUS. SILAKAN CEK JARINGAN.")
        return

    data_kanban = proses_kanban_pdp(semua_data, waktu_sekarang)
    
    if data_kanban["auto_selesai_updates"]:
        sukses, _ = execute_batch_update_by_uuid(data_kanban["auto_selesai_updates"])
        if sukses: 
            fetch_mapped_data.clear()
            st.rerun() 

    armada_portal_kiri = data_kanban["portal_kiri"]
    armada_km72_tengah = data_kanban["km72_tengah"]
    monitor_antrean = data_kanban["monitor_antrean"]
    grup_tujuan = data_kanban["grup_tujuan"]
    total_pax_antre = data_kanban["total_pax"]

    # METRICS PANEL
    m1, m2, m3 = st.columns(3)
    with m1: st.metric(label="Menuju KM72", value=len(armada_portal_kiri))
    with m2: st.metric(label="Menuju PDP (Keluar KM72)", value=len(armada_km72_tengah))
    
    wt_list = [hitung_wt(item['jam_tiba'], waktu_sekarang) for tj in grup_tujuan for item in grup_tujuan[tj]]
    wt_tertinggi = max(wt_list) if wt_list else 0
    with m3: st.metric(label="Max Waktu Tunggu", value=f"{wt_tertinggi} Menit", delta="Overdue!" if wt_tertinggi >= 30 else "Aman", delta_color="inverse")

    st.markdown("<hr style='margin: 15px 0 20px 0; border-color: var(--border-color);'>", unsafe_allow_html=True)

    col_kiri, col_tengah, col_kanan = st.columns([1, 1, 1.4])

    # ==========================================
    # KIRI: KEBERANGKATAN
    # ==========================================
    with col_kiri:
        st.markdown("<h4 style='color:var(--text-primary); font-size:15px; margin:0 0 15px 0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:2px; text-transform:uppercase;'>KEBERANGKATAN</h4>", unsafe_allow_html=True)
        
        if not armada_portal_kiri:
            st.info("Belum ada unit berangkat.")
        else:
            with st.container(height=580, border=False):
                for unit in armada_portal_kiri:
                    # Kotak di sini akan menjadi warna abu-abu kebiruan pucat
                    with st.container(border=True):
                        st.markdown(f"""
                        <div style="line-height: 1.4; text-align: left; padding-bottom: 5px; background: transparent;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                                <span style="font-family:'Rajdhani', sans-serif; font-size: 20px; font-weight: bold; color: var(--text-primary);">{unit['nopol']}</span> 
                                <span style="font-size: 15px; font-weight: bold; color: var(--accent-cyan);">[ {unit['driver']} ]</span>
                            </div>
                            <div style="font-size: 14px; color: var(--text-primary); margin-bottom: 8px;">
                                {unit['rute']} <span style="color:var(--text-muted);">|</span> JAM: <span style="color:var(--accent-yellow); font-weight:bold;">{unit['jadwal']}</span>
                            </div>
                            <div style="font-size: 13px; color: var(--text-primary); padding:6px 10px; border-radius:4px; border:1px solid var(--border-color); text-align:center; font-weight:600;">
                                MIM/BB: <b style="color:var(--accent-yellow);">{unit['pax_mim']}</b> &nbsp;|&nbsp; KOPO: <b style="color:var(--accent-yellow);">{unit['pax_kopo']}</b> &nbsp;|&nbsp; JTN: <b style="color:var(--accent-yellow);">{unit['pax_jtn']}</b>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    # ==========================================
    # TENGAH: CHECKOUT KM72
    # ==========================================
    with col_tengah:
        st.markdown("<h4 style='color:var(--accent-yellow); font-size:15px; margin:0 0 15px 0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:2px; text-transform:uppercase;'>CHECKOUT KM72</h4>", unsafe_allow_html=True)
        
        if not armada_km72_tengah:
            st.info("Tidak ada unit yang keluar KM72.")
        else:
            with st.container(height=580, border=False):
                for unit in armada_km72_tengah:
                    # Kotak di sini akan menjadi warna kuning/amber pucat dengan border tebal
                    with st.container(border=True): 
                        st.markdown(f"""
                        <div style="line-height: 1.4; text-align: left; padding-bottom: 8px; background: transparent;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                                <span style="font-family:'Rajdhani', sans-serif; font-size: 20px; font-weight: bold; color: var(--text-primary);">{unit['nopol']}</span> 
                                <span style="font-size: 15px; font-weight: bold; color: var(--accent-cyan);">[ {unit['driver']} ]</span>
                            </div>
                            <div style="font-size: 14px; color: var(--text-primary); margin-bottom: 8px;">
                                {unit['rute']} <span style="color:var(--text-muted);">|</span> JAM: <span style="color:var(--accent-yellow); font-weight:bold;">{unit['jadwal']}</span> 
                                <br>
                                <span style="font-size:13px; color:var(--text-muted); font-weight:600;">OUT KM72:</span> <span style="color:var(--accent-yellow); font-weight:bold; font-size:13px;">{unit['jam_72']}</span>
                            </div>
                            <div style="font-size: 13px; color: var(--text-primary); padding:6px 10px; border-radius:4px; border:1px solid #fde68a; text-align:center; font-weight:600;">
                                MIM/BB: <b style="color:var(--accent-yellow);">{unit['pax_mim']}</b> &nbsp;|&nbsp; KOPO: <b style="color:var(--accent-yellow);">{unit['pax_kopo']}</b> &nbsp;|&nbsp; JTN: <b style="color:var(--accent-yellow);">{unit['pax_jtn']}</b>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("TIBA DI PDP", key=f"tiba_{unit['trip_id']}", use_container_width=True):
                            with st.spinner("Proses..."):
                                waktu_tiba = get_waktu_wib().strftime("%H:%M")
                                sukses, pesan = safe_update_by_uuid(unit['trip_id'], {"jam_tiba_pdp": waktu_tiba})
                                if sukses:
                                    fetch_mapped_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Gagal Tiba")

    # ==========================================
    # KANAN: WAKTU TUNGGU PDP
    # ==========================================
    with col_kanan:
        st.markdown("<h4 style='color:var(--accent-cyan); font-size:15px; margin:0 0 15px 0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:2px; text-transform:uppercase;'>WAKTU TUNGGU PDP</h4>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; background-color: var(--expander-bg); padding: 15px; border-radius:8px; border: 1px solid var(--border-color); margin-bottom: 20px; box-shadow: var(--shadow-subtle);">
            <div style="text-align: center; width: 33%; border-right: 1px solid var(--border-color);">
                <span style="color: var(--text-primary); font-size: 11px; font-weight: 700; letter-spacing:1px; text-transform:uppercase;">MIM / BUAHBATU</span><br>
                <span style="color: var(--accent-cyan); font-size: 28px; font-weight: bold; font-family:'Rajdhani', sans-serif;">{total_pax_antre['MIM / BUAHBATU']}</span> <span style="color: var(--text-muted); font-size: 12px;">PAX</span>
            </div>
            <div style="text-align: center; width: 33%; border-right: 1px solid var(--border-color);">
                <span style="color: var(--text-primary); font-size: 11px; font-weight: 700; letter-spacing:1px; text-transform:uppercase;">KOPO</span><br>
                <span style="color: var(--accent-cyan); font-size: 28px; font-weight: bold; font-family:'Rajdhani', sans-serif;">{total_pax_antre['KOPO']}</span> <span style="color: var(--text-muted); font-size: 12px;">PAX</span>
            </div>
            <div style="text-align: center; width: 33%;">
                <span style="color: var(--text-primary); font-size: 11px; font-weight: 700; letter-spacing:1px; text-transform:uppercase;">JATINANGOR</span><br>
                <span style="color: var(--accent-cyan); font-size: 28px; font-weight: bold; font-family:'Rajdhani', sans-serif;">{total_pax_antre['JATINANGOR']}</span> <span style="color: var(--text-muted); font-size: 12px;">PAX</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='background:var(--bg-surface); border: 1px dashed var(--accent-cyan); padding: 12px; border-radius: 8px; margin-bottom: 20px; box-shadow: var(--shadow-subtle);'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:var(--accent-cyan); font-size:12px; margin: 0 0 10px 0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:1px; text-transform:uppercase;'> KEBERANGKATAN FEEDER</h4>", unsafe_allow_html=True)
        
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button(f"MIM/BB ({len(grup_tujuan['MIM / BUAHBATU'])})", key="btn_dispatch_mim", use_container_width=True, disabled=(not grup_tujuan["MIM / BUAHBATU"])):
                render_modal_dispatch("MIM / BUAHBATU", grup_tujuan["MIM / BUAHBATU"])
        with col_b2:
            if st.button(f"KOPO ({len(grup_tujuan['KOPO'])})", key="btn_dispatch_kopo", use_container_width=True, disabled=(not grup_tujuan["KOPO"])):
                render_modal_dispatch("KOPO", grup_tujuan["KOPO"])
        with col_b3:
            if st.button(f"JATINANGOR ({len(grup_tujuan['JATINANGOR'])})", key="btn_dispatch_jtn", use_container_width=True, disabled=(not grup_tujuan["JATINANGOR"])):
                render_modal_dispatch("JATINANGOR", grup_tujuan["JATINANGOR"])
        st.markdown("</div>", unsafe_allow_html=True)

        if not monitor_antrean:
            st.info("Belum ada unit yang tiba di PDP.")
        else:
            with st.container(height=380, border=False):
                for unit in monitor_antrean:
                    # Kotak di sini akan menjadi warna cyan/biru pucat dengan border tebal
                    with st.container(border=True):
                        pax_info_html = ""
                        for pax in unit.get('pax_details', []):
                            tj = pax['tujuan']
                            pax_count = pax['jumlah']
                            wt = pax['waktu_tunggu']
                            badge = f"<span style='color:#ff4757; font-weight:bold;'>🚨 {wt} menit</span>" if pax['is_overdue'] else f"<span style='color:#f59e0b; font-weight:700;'>⏳ {wt} menit</span>"
                            pax_info_html += f"<div style='margin-bottom: 4px; border-left: 2px solid var(--border-color); padding-left: 8px;'><span style='color:var(--text-muted);'>{tj}:</span> <b style='color:var(--accent-yellow);'>{pax_count} PAX</b> &nbsp; {badge}</div>"

                        st.markdown(f"""
                        <div style="line-height: 1.4; text-align: left; background: transparent;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px dashed #a5f3fc; padding-bottom:8px; margin-bottom:8px;">
                                <div>
                                    <div style="font-size: 15px; color: var(--text-primary); font-weight: 600; letter-spacing: 1px; margin-bottom: 2px;">{unit['rute']}</div>
                                    <span style="font-family:'Rajdhani', sans-serif; font-size: 22px; font-weight: bold; color: var(--text-primary);">{unit['nopol']}</span>
                                    <span style="font-size: 14px; font-weight: bold; color: var(--accent-cyan);"> [ {unit['driver']} ]</span>
                                </div>
                                <div style="text-align: right;">
                                    <span style="font-size: 15px; color: var(--text-muted); display:block; margin-bottom:2px; font-weight:700; letter-spacing:1px; text-transform:uppercase;">TIBA PDP</span>
                                    <span style="font-size: 14px; color: var(--accent-yellow); font-weight:700;">🕒 {unit['tiba']}</span>
                                </div>
                            </div>
                            <div style="margin: 0; font-size: 13px;">
                                {pax_info_html}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

live_dashboard_board()
