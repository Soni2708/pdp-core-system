from services.engine_kalkulasi import hitung_wt

def _parse_pax(val) -> int:
    """
    Helper internal murni untuk memastikan nilai PAX selalu Integer yang aman.
    Mencegah TypeError dan menghilangkan duplikasi kode kotor (DRY Principle).
    """
    v_str = str(val).strip()
    return int(v_str) if v_str.isdigit() else 0

def proses_kanban_pdp(semua_data, waktu_sekarang):
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
        rute = str(row.get('rute', ''))
        nopol = str(row.get('nopol', ''))
        driver = str(row.get('driver', ''))
        jadwal = str(row.get('jadwal', ''))
        jam_72 = str(row.get('jam_72', ''))
        jam_tiba_pdp = str(row.get('jam_tiba_pdp', ''))
        baris_db = row.get('baris_db')
        trip_id = str(row.get('trip_id', ''))
        
        # Konversi tipe terpusat, sejajar presisi, tidak ada spasi hantu.
        pax_mim = _parse_pax(row.get('pax_mim'))
        pax_kopo = _parse_pax(row.get('pax_kopo'))
        pax_jtn = _parse_pax(row.get('pax_jtn'))
        
        jam_out_mim = str(row.get('jam_out_mim', ''))
        jam_out_kopo = str(row.get('jam_out_kopo', ''))
        jam_out_jtn = str(row.get('jam_out_jtn', ''))

        # Logika Bisnis: Hanya proses armada yang sedang aktif
        if status != "IN TRANSIT":
            continue
        
        hasil["jumlah_armada_jalan"] += 1
        label_armada = f"[{rute}] {nopol}"

        pax_info = []
        semua_berangkat = False 
        ada_pax = False 

        # -----------------------------------------------------------------
        # DISTRIBUSI KANBAN (Logika Inti Dipertahankan - JANGAN DISENTUH)
        # -----------------------------------------------------------------
        
        if jam_72 == "" and jam_tiba_pdp == "":
            # 1. Armada baru berangkat dari Portal Lintas
            hasil["portal_kiri"].append({
                "nopol": nopol, "driver": driver, "rute": rute, "jadwal": jadwal,
                "pax_mim": pax_mim, "pax_kopo": pax_kopo, "pax_jtn": pax_jtn,
                "baris_db": baris_db,
                "trip_id": trip_id
            })
            
        elif jam_72 != "" and jam_tiba_pdp == "":
            # 2. Armada sudah keluar KM72, sedang meluncur ke PDP
            hasil["km72_tengah"].append({
                "nopol": nopol, "driver": driver, "rute": rute, "jadwal": jadwal,
                "pax_mim": pax_mim, "pax_kopo": pax_kopo, "pax_jtn": pax_jtn,
                "baris_db": baris_db,
                "trip_id": trip_id,
                "jam_72": jam_72
            })
            
        elif jam_tiba_pdp != "":
            # 3. Armada sudah tiba di Pasteur Drop Point (PDP)
            semua_berangkat = True 
            
            rutes = [
                ("MIM / BUAHBATU", pax_mim, jam_out_mim),
                ("KOPO", pax_kopo, jam_out_kopo),
                ("JATINANGOR", pax_jtn, jam_out_jtn)
            ]
            
            for tj, pax_count, jam_out in rutes:
                if pax_count > 0:
                    ada_pax = True
                    # Jika ada penumpang tujuan tersebut yang belum berangkat (jam_out kosong)
                    if jam_out == "":
                        semua_berangkat = False 
                        wt = hitung_wt(jam_tiba_pdp, waktu_sekarang)
                        
                        # 💉 NEXUS PRIME REFACTOR: Menggunakan Adaptive CSS Variables (var(--accent-red), var(--text-primary), dll)
                        badge = f"<span style='color:var(--accent-red); font-weight:bold;'>🚨 {wt} menit</span>" if wt >= 30 else f"<span style='color:var(--accent-yellow); font-weight:700;'>⏱️ {wt} menit</span>"
                        
                        pax_info.append(f"<div style='margin-bottom: 4px; border-left: 2px solid var(--border-color); padding-left: 8px;'><span style='color:var(--text-muted);'>{tj}:</span> <b style='color:var(--text-primary);'>{pax_count} PAX</b> &nbsp; {badge}</div>")
                        
                        hasil["grup_tujuan"][tj].append({"label": label_armada, "baris_db": baris_db, "trip_id": trip_id, "jam_tiba": jam_tiba_pdp})
                        hasil["total_pax"][tj] += pax_count
            
            # Jika masih ada yang mengantre, masukkan ke panel Monitor Antrean
            if ada_pax and pax_info:
                hasil["monitor_antrean"].append({
                    "label": label_armada, 
                    "rute": rute,          
                    "nopol": nopol,        
                    "driver": driver,
                    "tiba": jam_tiba_pdp,
                    "html": "".join(pax_info)
                })
            
            # Jika semua tujuan sudah diberangkatkan atau memang tidak membawa PAX sedari awal
            if semua_berangkat or not ada_pax:
                hasil["auto_selesai_updates"].append({
                    "trip_id": trip_id,         
                    "updates": {"I": "SELESAI"} 
                })

    return hasil
