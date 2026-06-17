import streamlit as st
import time
import copy

from components.ui_styles import apply_neo_tokyo_corporate, render_neo_tokyo_header, render_logo
from components.navbar import render_navbar
from core.auth import require_auth
from db_utils import get_waktu_wib, fetch_mapped_data, safe_update_by_uuid, execute_batch_update_by_uuid
from services.data_pipeline import proses_kanban_pdp
from services.engine_kalkulasi import hitung_wt
from services.pdp_helpers import render_muatan_html, add_activity_log, render_activity_log_panel, calculate_warning_level
from core.logger import setup_logger

log = setup_logger("SYSTEM_PDP")

# Konfigurasi halaman
st.set_page_config(page_title="PASTEUR DROP POINT", layout="wide", initial_sidebar_state="collapsed")
apply_neo_tokyo_corporate()
require_auth(module_name="pdp", secret_dict_name="users_pdp")
render_navbar("pdp")

# ==========================================
# 🌐 LOGO LINTAS
# ==========================================
render_logo(align="left", margin_bottom="5px")

# ========== INIT STATE ==========
if 'reset_form_feeder' not in st.session_state: 
    st.session_state.reset_form_feeder = 0

if 'modal_sedang_terbuka' not in st.session_state:
    st.session_state.modal_sedang_terbuka = False

# INIT STATE: ACTIVITY LOG (gunakan helper)
if 'activity_log' not in st.session_state:
    st.session_state.activity_log = []

# OPTIMISTIC UPDATE STATE (Memory Ilusi Lokal)
if 'local_pdp_mutations' not in st.session_state:
    st.session_state.local_pdp_mutations = {}


# ==========================================
# 🛑 MODAL DIALOG: KONFIRMASI TIBA DI PDP
# ==========================================
@st.dialog("KONFIRMASI KEDATANGAN PDP", width="small")
def confirm_tiba_dialog(unit):
    st.markdown(f"<div class='nt-nopol' style='text-align: center; font-size: 28px;'>{unit['nopol']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='nt-meta' style='text-align: center; margin-bottom: 20px;'>DRIVER: {unit['driver']}</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.caption("RUTE")
        st.write(f"**{unit['rute']}**")
    with c2:
        st.caption("JAM OUT KM72")
        st.write(f"**{unit['jam_72']}**")
        
    st.warning("Tandai armada ini TELAH TIBA di Pasteur Drop Point?")
    
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    col_yes, col_no = st.columns(2)
    with col_yes:
        if 'sedang_tiba_pdp' not in st.session_state:
            st.session_state.sedang_tiba_pdp = False
            
        if st.button("KONFIRMASI", type="primary", use_container_width=True, disabled=st.session_state.sedang_tiba_pdp):
            st.session_state.sedang_tiba_pdp = True
            with st.spinner("Proses..."):
                waktu_tiba = get_waktu_wib().strftime("%H:%M")
                sukses, pesan = safe_update_by_uuid(unit['trip_id'], {"jam_tiba_pdp": waktu_tiba})
                if sukses:
                    # OPTIMISTIC UPDATE: Suntik status kedatangan lokal
                    if unit['trip_id'] not in st.session_state.local_pdp_mutations:
                        st.session_state.local_pdp_mutations[unit['trip_id']] = {}
                    st.session_state.local_pdp_mutations[unit['trip_id']]["jam_tiba_pdp"] = waktu_tiba

                    st.session_state.activity_log = add_activity_log(
                        f"<span style='color: #00E5FF; font-weight: bold;'>[TIBA]</span> Unit <b>{unit['nopol']}</b> ({unit['rute']}) telah tiba di PDP.",
                        st.session_state.activity_log
                    )
                    st.session_state.sedang_tiba_pdp = False
                    st.rerun()
                else:
                    st.session_state.sedang_tiba_pdp = False
                    st.error(f"GAGAL: {pesan}")
    with col_no:
        if st.button("BATAL", use_container_width=True):
            st.rerun()


# ==========================================
# 🛑 MODAL DIALOG: GLOBAL DISPATCH FEEDER
# ==========================================
@st.dialog("KEBERANGKATAN FEEDER", width="medium")
def render_global_dispatch_modal():
    waktu_sekarang = get_waktu_wib()
    
    # Ambil data raw dan aplikasikan filter memori lokal (supaya modal selalu up-to-date)
    raw_data = fetch_mapped_data()
    if raw_data is None:
        st.error("GAGAL MENARIK DATA DARI SERVER.")
        return
        
    semua_data = copy.deepcopy(raw_data)
    local_mutations = st.session_state.get('local_pdp_mutations', {})
    if local_mutations and semua_data:
        for row in semua_data:
            tid = row.get("trip_id")
            if tid in local_mutations:
                row.update(local_mutations[tid])

    data_kanban = proses_kanban_pdp(semua_data, waktu_sekarang)
    grup_tujuan = data_kanban["grup_tujuan"]
    
    tujuan_target = st.selectbox("RUTE FEEDER", ["MIM / BUAHBATU", "KOPO", "JATINANGOR"])
    st.divider()
    
    armada_ready = grup_tujuan[tujuan_target]
    list_armada = [item['label'] for item in armada_ready]
    
    if not list_armada:
        st.warning(f"TIDAK ADA ANTRIAN UNTUK RUTE {tujuan_target}.")
        return

    pilihan_massal = st.multiselect(
        f"PILIH PENUMPANG (TUJUAN {tujuan_target})", 
        options=list_armada,
        key=f"sel_global_{st.session_state.reset_form_feeder}"
    )
    
    # Kalkulasi kapasitas
    if pilihan_massal:
        total_pax_terpilih = sum(next(item['pax_count'] for item in armada_ready if item['label'] == p) for p in pilihan_massal)
        if total_pax_terpilih <= 14:
            st.markdown(f"<div style='background: rgba(0, 230, 118, 0.1); border: 1px solid #00E676; padding: 8px 12px; border-radius: 4px; color: #00E676; font-weight: 700; font-size: 13px; margin-bottom: 15px;'>📊 TOTAL MUATAN TERPILIH: {total_pax_terpilih} PAX (KAPASITAS AMAN)</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background: rgba(255, 23, 68, 0.1); border: 1px solid #FF1744; padding: 8px 12px; border-radius: 4px; color: #FF1744; font-weight: 700; font-size: 13px; margin-bottom: 15px;'>🚨 TOTAL MUATAN TERPILIH: {total_pax_terpilih} PAX (MELEBIHI KAPASITAS HIACE 14 PAX!)</div>", unsafe_allow_html=True)
    
    kunci_drv = f"drv_g_{st.session_state.reset_form_feeder}"
    kunci_npl = f"npl_g_{st.session_state.reset_form_feeder}"
    kunci_cat = f"cat_g_{st.session_state.reset_form_feeder}"
    
    if kunci_drv not in st.session_state: st.session_state[kunci_drv] = ""
    if kunci_npl not in st.session_state: st.session_state[kunci_npl] = ""
    if kunci_cat not in st.session_state: st.session_state[kunci_cat] = ""

    c1, c2 = st.columns(2)
    with c1: 
        st.text_input("NAMA DRIVER FEEDER", key=kunci_drv)
        drv_f = st.session_state[kunci_drv].upper()
    with c2: 
        st.text_input("NOPOL FEEDER", placeholder="CONTOH: D 4321 XYZ", key=kunci_npl)
        nopol_f = st.session_state[kunci_npl].upper()
    
    with st.expander("CATATAN KETERLAMBATAN (OPSIONAL)"):
        st.text_input(
            "ALASAN KETERLAMBATAN", placeholder="WAJIB DIISI JIKA MELEWATI SLA", 
            label_visibility="collapsed", key=kunci_cat
        )
        catatan_f = st.session_state[kunci_cat]
        
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    if 'sedang_dispatch' not in st.session_state:
        st.session_state.sedang_dispatch = False

    if st.button(f"BERANGKATKAN FEEDER", use_container_width=True, type="primary", disabled=st.session_state.sedang_dispatch):
        # Validasi SLA
        ada_pelanggaran = any(hitung_wt(next(i['jam_tiba'] for i in armada_ready if i['label'] == p), waktu_sekarang) >= 30 for p in pilihan_massal)
        
        if not pilihan_massal or not drv_f.strip() or not nopol_f.strip():
            st.error("VALIDASI GAGAL: LENGKAPI NAMA DRIVER, NOPOL, DAN MINIMAL 1 UNIT PILIHAN.")
        elif ada_pelanggaran and not catatan_f.strip():
            st.error("PERINGATAN KRITIS: WAKTU TUNGGU MELEBIHI SLA. CATATAN WAJIB DIISI.")
        else:
            st.session_state.sedang_dispatch = True
            with st.spinner("Sinkronisasi enkripsi manifes..."):
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
                        st.toast(f"FEEDER {tujuan_target} BERHASIL DIBERANGKATKAN")
                        
                        # OPTIMISTIC UPDATE: Suntik memori kelenyapan armada ke RAM Lokal
                        for item in uuid_updates:
                            tid = item["trip_id"]
                            if tid not in st.session_state.local_pdp_mutations:
                                st.session_state.local_pdp_mutations[tid] = {}
                            st.session_state.local_pdp_mutations[tid].update(item["updates"])

                        # Tambahkan ke activity log
                        st.session_state.activity_log = add_activity_log(
                            f"<span style='color: #00E676; font-weight: bold;'>[DISPATCH]</span> Feeder <b>{nopol_f}</b> ({tujuan_target}) diberangkatkan dengan {total_pax_terpilih} PAX.",
                            st.session_state.activity_log
                        )
                        
                        st.session_state.reset_form_feeder += 1 
                        st.session_state.sedang_dispatch = False
                        st.session_state["modal_sedang_terbuka"] = False
                        st.rerun()            
                    else:
                        st.session_state.sedang_dispatch = False
                        st.error(f"TRANSMISI GAGAL: {pesan}")


# ==========================================
# 🎨 UI HEADER STATIC & STATUS CENTER (REDUX)
# ==========================================
col_judul, col_status = st.columns([2.8, 1.7])
with col_judul:
    render_neo_tokyo_header(
        title="PASTEUR DROP POINT", 
        subtitle="Sistem Transit & Monitoring Feeder", 
        accent="var(--nt-violet)",
        align="left"
    )

with col_status:
    petugas_aktif = st.session_state.get('petugas_pdp', 'UNKNOWN')
    waktu_sekarang_dt = get_waktu_wib()
    tanggal_str = waktu_sekarang_dt.strftime("%d %B %Y")
    waktu_str = waktu_sekarang_dt.strftime("%H:%M:%S")

    st.markdown(f"""
    <div style="text-align: right; margin-top: 5px;">
        <div style='display: inline-block; background: rgba(157, 78, 221, 0.05); border: 1px solid rgba(157, 78, 221, 0.2); padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: 700; color: var(--nt-text-muted); margin-bottom: 10px;'>
            <span style='color: #00E676;'>●</span> USER ACTIVE: <span style='color: var(--nt-violet); letter-spacing: 0.5px;'>{petugas_aktif}</span>
        </div>
        <div style="margin-top: 2px; margin-bottom: 8px;">
            <span style="background: rgba(0, 230, 118, 0.15); color: #00E676; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 800; letter-spacing: 0.5px; border: 1px solid rgba(0, 230, 118, 0.3);">SISTEM AKTIF</span>
        </div>
        <div style="font-size: 11px; color: #8B949E; margin-bottom: 12px; font-weight: 500;">
            {tanggal_str} | <span style="color: #F8F9FA;">{waktu_str} WIB</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Penataan tombol aksi utama secara ringkas dan sejajar
    btn_col1, btn_col2 = st.columns([1.3, 1])
    with btn_col1:
        if st.button("DISPATCH FEEDER", type="primary", use_container_width=True):
            st.session_state["modal_sedang_terbuka"] = True
            render_global_dispatch_modal()
    with btn_col2:
        if st.button("🔄 REFRESH", use_container_width=True, type="primary"): 
            st.session_state["modal_sedang_terbuka"] = False
            # Jika admin menekan refresh secara manual, hapus semua cache agar sinkron paksa dengan database
            st.cache_data.clear() 
            st.rerun()            

st.divider()

# 🚀 TACTICAL SYSTEM NOTIFICATION BOX
st.markdown("<div style='color: #8B949E; font-size: 11px; margin-bottom: 10px; text-align: right;'><i>STATUS JARINGAN: AUTO-REFRESH (2 MENIT)</i></div>", unsafe_allow_html=True)

# 🚀 RENDER TERMINAL ACTIVITY LOG (menggunakan helper)
with st.expander("HISTORY ACTIVITY (50 Aktivitas Terakhir)", expanded=False):
    log_html = render_activity_log_panel(st.session_state.activity_log)
    st.markdown(log_html, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)


# ==========================================
# ⚡ STREAMLIT FRAGMENT (Auto Data Engine)
# ==========================================
@st.fragment(run_every=120)
def live_dashboard_board():
    waktu_sekarang = get_waktu_wib()
    raw_data = fetch_mapped_data()
    
    if raw_data is None:
        st.error("KONEKSI DATABASE TERPUTUS. SILAKAN CEK JARINGAN.")
        return

    # GABUNGKAN DATA DATABASE DENGAN ILUSI MEMORI LOKAL
    semua_data = copy.deepcopy(raw_data)
    local_mutations = st.session_state.get('local_pdp_mutations', {})
    
    if local_mutations and semua_data:
        for row in semua_data:
            tid = row.get("trip_id")
            if tid in local_mutations:
                row.update(local_mutations[tid])

    # Teruskan data yang sudah dipoles ke engine pemroses kanban
    data_kanban = proses_kanban_pdp(semua_data, waktu_sekarang)
    
    # Auto-complete trips yang sudah selesai
    if data_kanban["auto_selesai_updates"]:
        sukses, _ = execute_batch_update_by_uuid(data_kanban["auto_selesai_updates"])
        if sukses: 
            st.cache_data.clear() 
            if not st.session_state.get("modal_sedang_terbuka", False):
                st.rerun() 

    armada_portal_kiri = data_kanban["portal_kiri"]
    armada_km72_tengah = data_kanban["km72_tengah"]
    monitor_antrean = data_kanban["monitor_antrean"]
    
    grup_tujuan = data_kanban["grup_tujuan"]
    total_pax_antre = data_kanban["total_pax"]

    # Menghitung max WT untuk display alarm
    wt_list = [hitung_wt(item['jam_tiba'], waktu_sekarang) for tj in grup_tujuan for item in grup_tujuan[tj]]
    wt_tertinggi = max(wt_list) if wt_list else 0
    warning_level = calculate_warning_level(wt_tertinggi)

    # ==========================================
    # 🎨 COMPACT TOP HUD PANEL
    # ==========================================
    st.markdown("<div class='nt-meta' style='color: #8B949E; margin-bottom: 8px; letter-spacing: 1px;'>⚡ SUMMARY & ACTION CENTER</div>", unsafe_allow_html=True)
    
    hud_metric, hud_alarm = st.columns([2.5, 1.2], gap="large")
    
    with hud_metric:
        st.markdown(f"""
        <div style='background: rgba(21, 23, 28, 0.65); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center;'>
            <div style='color: var(--nt-text-primary); font-size: 11px; font-weight: 700; letter-spacing: 1px;'>TOTAL PAX ANTRIAN PDP</div>
            <div style='display: flex; gap: 35px;'>
                <div style='text-align: center;'>
                    <div style='font-size: 10px; color: #ffffff; margin-bottom: 2px;'>MIM/BBT</div>
                    <div style='font-size: 18px; font-weight: 800; color: #00E5FF; line-height: 1;'>{total_pax_antre['MIM / BUAHBATU']}</div>
                </div>
                <div style='text-align: center;'>
                    <div style='font-size: 10px; color: #ffffff; margin-bottom: 2px;'>KOPO</div>
                    <div style='font-size: 18px; font-weight: 800; color: #00E5FF; line-height: 1;'>{total_pax_antre['KOPO']}</div>
                </div>
                <div style='text-align: center;'>
                    <div style='font-size: 10px; color: #ffffff; margin-bottom: 2px;'>JATINANGOR</div>
                    <div style='font-size: 18px; font-weight: 800; color: #00E5FF; line-height: 1;'>{total_pax_antre['JATINANGOR']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
            
    with hud_alarm:
        total_semua = sum(total_pax_antre.values())
        if warning_level["level"] == "critical":
            st.markdown(f"""
            <div style='background: rgba(255, 23, 68, 0.15); border: 1px solid {warning_level['color']}; padding: 12px 20px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; height: 100%; box-shadow: 0 0 15px rgba(255, 23, 68, 0.3);'>
                <div style='color: {warning_level['color']}; font-size: 12px; font-weight: 800; letter-spacing: 1px;'>{warning_level['message']}</div>
                <div style='text-align: right;'>
                    <div style='color: #F8F9FA; font-size: 18px; font-weight: 800; line-height: 1;'>{wt_tertinggi} MENIT</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif warning_level["level"] == "warning":
            st.markdown(f"""
            <div style='background: rgba(255, 196, 0, 0.1); border: 1px solid {warning_level['color']}; padding: 12px 20px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; height: 100%;'>
                <div style='color: {warning_level['color']}; font-size: 12px; font-weight: 800; letter-spacing: 1px;'>{warning_level['message']}</div>
                <div style='text-align: right;'>
                    <div style='color: #F8F9FA; font-size: 16px; font-weight: 800; line-height: 1;'>{wt_tertinggi} MENIT</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif total_semua > 0:
            st.markdown(f"""
            <div style='background: rgba(0, 229, 255, 0.05); border: 1px solid rgba(0, 229, 255, 0.3); padding: 12px 20px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; height: 100%;'>
                <div style='color: #00E5FF; font-size: 12px; font-weight: 700; letter-spacing: 1px;'>⏳ MENUNGGU FEEDER</div>
                <div style='color: #8B949E; font-size: 11px;'>{total_semua} PAX</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background: rgba(0, 230, 118, 0.05); border: 1px solid rgba(0, 230, 118, 0.3); padding: 12px 20px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; height: 100%;'>
                <div style='color: #00E676; font-size: 12px; font-weight: 700; letter-spacing: 1px;'>✔️ AREA CLEAR</div>
                <div style='color: #8B949E; font-size: 11px;'>0 Antrian</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 📡 FULL WIDTH 3-COLUMN KANBAN
    # ==========================================
    st.markdown("<div class='nt-meta' style='color: #8B949E; margin-bottom: 12px; letter-spacing: 1px;'>📡 PDP MONITORING (LIVE)</div>", unsafe_allow_html=True)
    
    col_portal, col_km72, col_pdp = st.columns([1, 1, 1.2], gap="medium")
    
    # --- KOLOM 1: BARU BERANGKAT ---
    with col_portal:
        st.markdown(f"<div class='nt-meta' style='text-align: center; margin-bottom: 16px; color: #00E5FF; border-bottom: 2px solid rgba(0, 229, 255, 0.3); padding-bottom: 8px;'>[ 1 ] BARU BERANGKAT ({len(armada_portal_kiri)})</div>", unsafe_allow_html=True)
        
        if not armada_portal_kiri:
            st.info("BELUM ADA UNIT BERANGKAT DARI JABODETABEK & SEKITARNYA")
        else:
            with st.container(height=580, border=False):
                for unit in armada_portal_kiri:
                    with st.container(border=True):
                        muatan_html = render_muatan_html(unit['trip_id'], semua_data)
                        st.markdown(f"""
                        <div class='nt-nopol' style='color: #F8F9FA;'>{unit['nopol']}</div>
                        <div class='nt-meta' style='color: #8B949E; margin-top: 4px;'>
                            {unit['rute']} <b style='color: #334155; font-weight: normal; margin: 0 6px;'>|</b> JAM: <b style='color: #00E5FF; font-weight: 800; font-size: 13px;'>{unit['jadwal']} WIB</b>
                        </div>
                        <div class='nt-meta' style='color: #8B949E; margin-top: 4px;'>DRIVER: {unit['driver']}</div>
                        {muatan_html}
                        """, unsafe_allow_html=True)

    # --- KOLOM 2: OUT KM72 ---
    with col_km72:
        st.markdown(f"<div class='nt-meta' style='text-align: center; margin-bottom: 16px; color: #FFC400; border-bottom: 2px solid rgba(255, 196, 0, 0.3); padding-bottom: 8px;'>[ 2 ] OUT KM72 ({len(armada_km72_tengah)})</div>", unsafe_allow_html=True)
        
        if not armada_km72_tengah:
            st.info("BELUM ADA UNIT MENUJU PDP (DARI KM72)")
        else:
            with st.container(height=580, border=False):
                for unit in armada_km72_tengah:
                    with st.container(border=True): 
                        muatan_html = render_muatan_html(unit['trip_id'], semua_data)
                        
                        col_nopol, col_btn = st.columns([2.2, 1.2], vertical_alignment="center")
                        
                        with col_nopol:
                            st.markdown(f"<div class='nt-nopol' style='color: #F8F9FA; font-size: 18px;'>{unit['nopol']}</div>", unsafe_allow_html=True)
                        
                        with col_btn:
                            if st.button("TIBA DI PDP", key=f"btn_tiba_{unit['trip_id']}", use_container_width=True, type="primary"):
                                confirm_tiba_dialog(unit)
                                        
                        st.markdown(f"""
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-top: 8px;'>
                            <div class='nt-meta' style='color: #8B949E;'>
                                {unit['rute']} <b style='color: #334155; font-weight: normal; margin: 0 6px;'>|</b> JAM: <b style='color: #00E5FF; font-weight: 800; font-size: 13px;'>{unit['jadwal']} WIB</b>
                            </div>
                            <div class='nt-meta' style='color: #F8F9FA; text-align: right;'>
                                CHECKOUT KM72: <b style='color: #FFC400; font-weight: 800; font-size: 13px;'>{unit['jam_72']}</b>
                            </div>
                        </div>
                        <div class='nt-meta' style='color: #8B949E; margin-top: 4px;'>DRIVER: {unit['driver']}</div>
                        {muatan_html}
                        """, unsafe_allow_html=True)

    # --- KOLOM 3: STANDBY DI PDP ---
    with col_pdp:
        st.markdown(f"<div class='nt-meta' style='text-align: center; margin-bottom: 16px; color: #ffffff; border-bottom: 2px solid rgba(157, 78, 221, 0.3); padding-bottom: 8px;'>[ 3 ] STANDBY DI PDP ({len(monitor_antrean)})</div>", unsafe_allow_html=True)
        
        if not monitor_antrean:
            st.info("BELUM ADA PAX MENUNGGU DI PDP")
        else:
            with st.container(height=580, border=False): 
                for unit in monitor_antrean:
                    is_overdue_card = any(p['is_overdue'] for p in unit.get('pax_details', []))
                    
                    with st.container(border=True):
                        # REFACTOR CTO: Mencegah Memory Leak CSS di Looping Browser
                        if is_overdue_card: 
                            st.markdown("<div class='overdue-flag'></div>", unsafe_allow_html=True)

                        pax_info_html = ""
                        for pax in unit.get('pax_details', []):
                            tj = pax['tujuan']
                            pax_count = pax['jumlah']
                            wt = pax['waktu_tunggu']
                            
                            if pax['is_overdue']:
                                badge = f"<b style='color:#FF1744; font-size: 11px; font-weight:800; text-shadow: 0 0 8px rgba(255, 23, 68, 0.4); float:right;'>[{wt} MENIT - OVERDUE]</b>"
                            else:
                                badge = f"<b style='color:#FFC400; font-size: 11px; font-weight:700; float:right;'>[{wt} MENIT]</b>"
                                
                            pax_info_html += f"<div style='margin-bottom: 4px; border-left: 2px solid rgba(255,255,255,0.08); padding-left: 6px;'><span style='font-size: 10px; color: #8B949E; font-weight: 600;'>{tj}:</span> <b style='color:#00E5FF; font-size: 12px;'>{pax_count} PAX</b> {badge}</div>"

                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px dashed rgba(255,255,255,0.08); padding-bottom: 6px; margin-bottom: 6px;">
                            <div>
                                <div style="color: #ffffff; font-size: 10px; font-weight: 700; margin-bottom: 2px;">{unit['rute']}</div>
                                <div style="font-size: 15px; font-weight: 800; color: #F8F9FA; letter-spacing: 1px;">{unit['nopol']}</div>
                                <div style="color: #8B949E; font-size: 10px; font-weight: 600; margin-top: 2px;">DRIVER: {unit['driver']}</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="color: #ffffff; font-size: 10px; font-weight: 600;">TIBA PDP</div>
                                <div style="font-size: 12px; color: #FFC400; font-weight: 800;">{unit['tiba']}</div>
                            </div>
                        </div>
                        <div>
                            {pax_info_html}
                        </div>
                        """, unsafe_allow_html=True)

# Jalankan dashboard
live_dashboard_board()
