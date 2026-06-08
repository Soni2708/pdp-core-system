from services.engine_kalkulasi import hitung_wt, get_sla_limit
import logging

log = logging.getLogger("PIPELINE")

def proses_kanban_pdp(semua_data: list, waktu_sekarang) -> dict:
    """
    Engine pemroses state Kanban (Pure Data Layer).
    Terintegrasi dengan SLA dinamis dari Supabase & Auto-Triage Sorting.
    """
    hasil = {
        "portal_kiri": [],
        "km72_tengah": [],
        "monitor_antrean": [],
        "grup_tujuan": {"MIM / BUAHBATU": [], "KOPO": [], "JATINANGOR": []},
        "total_pax": {"MIM / BUAHBATU": 0, "KOPO": 0, "JATINANGOR": 0},
        "auto_selesai_updates": [],
        "jumlah_armada_jalan": 0
    }

    if not semua_data:
        return hasil

    for row in semua_data:
        status = str(row.get('status', '')).strip().upper()
        if status != "IN TRANSIT":
            continue
            
        hasil["jumlah_armada_jalan"] += 1

        rute = str(row.get('rute', ''))
        nopol = str(row.get('nopol', ''))
        driver = str(row.get('driver', ''))
        jadwal = str(row.get('jadwal', ''))
        jam_72 = str(row.get('jam_72', ''))
        jam_tiba_pdp = str(row.get('jam_tiba_pdp', ''))
        trip_id = str(row.get('trip_id', ''))
        
        pax_mim = int(row.get('pax_mim', 0))
        pax_kopo = int(row.get('pax_kopo', 0))
        pax_jtn = int(row.get('pax_jtn', 0))
        
        jam_out_mim = str(row.get('jam_out_mim', ''))
        jam_out_kopo = str(row.get('jam_out_kopo', ''))
        jam_out_jtn = str(row.get('jam_out_jtn', ''))

        label_armada = f"[{rute}] {nopol} (Jam: {jadwal})"
        pax_details = [] 
        semua_berangkat = False 
        ada_pax = False 

        if not jam_72 and not jam_tiba_pdp:
            hasil["portal_kiri"].append({
                "nopol": nopol, "driver": driver, "rute": rute, "jadwal": jadwal,
                "pax_mim": pax_mim, "pax_kopo": pax_kopo, "pax_jtn": pax_jtn,
                "trip_id": trip_id
            })
            
        elif jam_72 and not jam_tiba_pdp:
            hasil["km72_tengah"].append({
                "nopol": nopol, "driver": driver, "rute": rute, "jadwal": jadwal,
                "pax_mim": pax_mim, "pax_kopo": pax_kopo, "pax_jtn": pax_jtn,
                "trip_id": trip_id,
                "jam_72": jam_72  
            })
            
        elif jam_tiba_pdp:
            semua_berangkat = True 
            
            rute_map = [
                ("MIM / BUAHBATU", pax_mim, jam_out_mim),
                ("KOPO", pax_kopo, jam_out_kopo),
                ("JATINANGOR", pax_jtn, jam_out_jtn)
            ]
            
            batas_sla = get_sla_limit(rute)
            
            for tj, pax_count, jam_out in rute_map:
                if pax_count > 0:
                    ada_pax = True
                    if not jam_out:
                        semua_berangkat = False 
                        wt = hitung_wt(jam_tiba_pdp, waktu_sekarang)
                        
                        pax_details.append({
                            "tujuan": tj,
                            "jumlah": pax_count,
                            "waktu_tunggu": wt,
                            "is_overdue": wt >= batas_sla 
                        })
                        
                        hasil["grup_tujuan"][tj].append({
                            "label": label_armada, 
                            "trip_id": trip_id, 
                            "jam_tiba": jam_tiba_pdp,
                            "pax_count": pax_count # Injeksi data untuk Kalkulator Modal
                        })
                        hasil["total_pax"][tj] += pax_count
            
            if ada_pax and pax_details:
                hasil["monitor_antrean"].append({
                    "label": label_armada,
                    "rute": rute,          
                    "nopol": nopol,        
                    "driver": driver,
                    "tiba": jam_tiba_pdp,
                    "pax_details": pax_details
                })
            
            if semua_berangkat or not ada_pax:
                hasil["auto_selesai_updates"].append({
                    "trip_id": trip_id,         
                    "updates": {"status": "SELESAI"}
                })

    # 🚀 SLA AUTO-TRIAGE: Urutkan monitor_antrean agar armada yang Overdue dipaksa naik ke atas
    for unit in hasil["monitor_antrean"]:
        unit['max_wt'] = max([p['waktu_tunggu'] for p in unit['pax_details']]) if unit['pax_details'] else 0
    
    hasil["monitor_antrean"].sort(key=lambda x: x['max_wt'], reverse=True)

    return hasil
