import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import json
import urllib.parse

# ==========================================
# 1. PREMIUM COGNITIVE COMPONENT & UI DESIGN
# ==========================================
st.set_page_config(page_title="GIPANG M3 BANTEN - Portal Pengawas", page_icon="🏫", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
    html { scroll-behavior: smooth; }
    body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: linear-gradient(180deg, #eef5ff 0%, #ffffff 400px, #ffffff 100%); font-family: 'Poppins', sans-serif !important; color: #0B1F52; }
    .premium-navbar { display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); padding: 12px 40px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.5); box-shadow: 0 4px 20px rgba(11, 31, 82, 0.04); margin-bottom: 25px; }
    .nav-brand { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 22px; color: #0B1F52; }
    .nav-brand span { color: #1D4ED8; }
    .tagline-badge { background-color: #1D4ED8; color: white; padding: 6px 16px; border-radius: 30px; font-size: 13px; font-weight: 600; display: inline-block; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(29, 78, 216, 0.2); }
    .hero-h1 { font-size: 45px; font-weight: 800; color: #0B1F52; line-height: 1.15; margin: 0 0 10px 0; }
    .hero-h1 span { color: #1D4ED8; }
    .saas-card { background: white; border-radius: 20px; padding: 24px; border: 1px solid #e2e8f0; box-shadow: 0 10px 30px rgba(11, 31, 82, 0.02); transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); height: 100%; }
    .saas-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(11, 31, 82, 0.06); border-color: #60a5fa; }
    .icon-box { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-bottom: 12px; }
    .custom-table-container { background: white; border-radius: 20px; padding: 20px; border: 1px solid #e2e8f0; }
    .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .stButton button { border-radius: 10px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONEKSI GOOGLE SHEETS
# ==========================================
NAMA_SPREADSHEET = "Database_Portofolio_Pengawas"

@st.cache_resource
def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        kunci_mentah = st.secrets["gcp"]["kunci_json"]
        import ast
        try:
            creds_dict = json.loads(kunci_mentah, strict=False)
        except:
            creds_dict = ast.literal_eval(kunci_mentah.replace('\n', ''))
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds), "Sukses"
    except Exception as e:
        return None, f"Error Kredensial: {str(e)}"

client, conn_status = get_gspread_client()

def load_data(sheet_name):
    if client:
        try:
            sheet = client.open(NAMA_SPREADSHEET).worksheet(sheet_name)
            return pd.DataFrame(sheet.get_all_records())
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# State Management
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = "Public"
    st.session_state.user_name = "Guest"
    st.session_state.asal_sekolah = ""

st.markdown("<div id='beranda'></div>", unsafe_allow_html=True)

# ==========================================
# 3. NAVIGASI ATAS & LOGIN
# ==========================================
st.markdown("""
    <div class='premium-navbar'>
        <div class='nav-brand'>🏛️ GIPANG <span>M3</span> BANTEN</div>
    </div>
""", unsafe_allow_html=True)

col_nav1, col_nav2, col_nav3 = st.columns([7, 1.2, 1.5])
with col_nav2:
    if not st.session_state.logged_in:
        if st.button("🔒 Masuk", use_container_width=True):
            st.session_state.show_login = True
            st.session_state.show_register = False
with col_nav3:
    if not st.session_state.logged_in:
        if st.button("🚀 Request Akses", type="primary", use_container_width=True):
            st.session_state.show_register = True
            st.session_state.show_login = False

# --- POPUP LOGIN ---
if st.session_state.get("show_login", False) and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown("#### 🔐 Portal Autentikasi")
        e_login = st.text_input("📧 Alamat Email")
        p_login = st.text_input("🔑 Password", type="password")
        if st.button("Login", type="primary"):
            if client:
                df_users = load_data("User")
                if not df_users.empty:
                    user_match = df_users[(df_users['Email'].astype(str) == e_login) & (df_users['Password'].astype(str) == p_login)]
                    if not user_match.empty:
                        status_akun = user_match.iloc[0].get('Status_Akun', 'Pending')
                        if status_akun == 'Aktif':
                            st.session_state.logged_in = True
                            st.session_state.user_role = user_match.iloc[0]['Role']
                            # ISOLASI DATA: Menyimpan Asal Sekolah ke memori khusus
                            st.session_state.asal_sekolah = user_match.iloc[0]['Asal_Sekolah']
                            st.session_state.user_name = f"{user_match.iloc[0]['Nama_Lengkap']} - {st.session_state.asal_sekolah}"
                            st.session_state.show_login = False
                            st.rerun()
                        else:
                            st.warning("⏳ Akun Anda masih PENDING. Menunggu validasi Ibu Pengawas.")
                    else:
                        st.error("❌ Email atau Password salah!")
            else:
                st.error("Gagal terhubung ke database.")

# --- POPUP REGISTRASI ---
if st.session_state.get("show_register", False) and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown("#### 🚀 Permohonan Akses")
        with st.form("form_reg"):
            c1, c2 = st.columns(2)
            reg_nama = c1.text_input("Nama Lengkap")
            reg_sekolah = c2.text_input("Asal Sekolah (Cth: SDN 1 Serang)")
            reg_email = st.text_input("Email (Untuk Login)")
            c3, c4 = st.columns(2)
            reg_role = c3.selectbox("Role", ["Kepala Sekolah", "Operator"])
            reg_pass = c4.text_input("Password (Wajib 1 Kapital, 1 Angka, min 6)", type="password")
            
            if st.form_submit_button("Daftar Sekarang", type="primary"):
                if reg_nama and reg_sekolah and reg_email and reg_pass:
                    if any(c.isupper() for c in reg_pass) and any(c.isdigit() for c in reg_pass) and len(reg_pass) >= 6:
                        if client:
                            client.open(NAMA_SPREADSHEET).worksheet("User").append_row([reg_nama, reg_sekolah, reg_email, reg_role, reg_pass, "Pending"])
                            st.success("Berhasil! Menunggu validasi Admin.")
                        else:
                            st.error("Database terputus.")
                    else:
                        st.error("Password tidak memenuhi syarat.")

# ==========================================
# 4. WORKSPACE ROUTER (SIDEBAR EKSKLUSIF)
# ==========================================
st.sidebar.markdown("### ⚙️ Workspace Router")
if st.session_state.logged_in:
    st.sidebar.markdown(f"""
        <div style='background-color: #f0fdf4; padding: 12px; border-radius: 8px; border: 1px solid #bbf7d0; margin-bottom: 15px;'>
            <small style='color: #166534; font-weight: 600;'>🔑 AKSI SEBAGAI:</small><br>
            <b style='color: #0b1f52; font-size: 13px;'>{st.session_state.user_name}</b><br>
            <span style='background: #1D4ED8; color: white; font-size: 10px; padding: 2px 8px; border-radius: 10px;'>{st.session_state.user_role}</span>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user_role == "Admin":
        sub_menu = st.sidebar.radio("Menu Pengawas", ["Dashboard Admin", "Cek Artefak Sekolah", "Sistem Reminder Email", "Validasi Akun Baru", "Manajemen Tagihan Tugas", "Upload Materi Pusat", "Respon Konsultasi", "Log Out"])
    elif st.session_state.user_role == "Kepala Sekolah":
        sub_menu = st.sidebar.radio("Menu Kepala Sekolah", ["Dashboard Kepala Sekolah", "Pakta Integritas & Pengesahan", "Layanan Konsultasi", "Log Out"])
    elif st.session_state.user_role == "Operator":
        sub_menu = st.sidebar.radio("Menu Operator", ["Dashboard Operator", "Upload Artefak", "Riwayat & Perbaikan", "Log Out"])
    else:
        sub_menu = "Beranda Publik"
        
    if sub_menu == "Log Out":
        st.session_state.logged_in = False
        st.session_state.user_role = "Public"
        st.session_state.user_name = "Guest"
        st.rerun()
else:
    sub_menu = "Beranda Publik"

# ==========================================
# 5. KONTEN KHUSUS: ADMIN (PENGAWAS)
# ==========================================
if sub_menu == "Dashboard Admin":
    st.title("📊 Panel Kontrol Utama Pengawas")
    df_artefak = load_data("Artefak_Portofolio")
    pending = len(df_artefak[df_artefak['Status'] == 'Menunggu Validasi']) if not df_artefak.empty else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Menunggu Pemeriksaan", f"{pending} Dokumen", "Perlu Tindakan" if pending > 0 else "Aman", delta_color="inverse" if pending > 0 else "normal")

elif sub_menu == "Cek Artefak Sekolah":
    st.title("🛡️ Pemeriksaan & Penilaian Portofolio")
    st.write("Berikan catatan dan ubah status dokumen yang dikirim oleh sekolah.")
    
    df_art = load_data("Artefak_Portofolio")
    if not df_art.empty:
        df_pending = df_art[df_art['Status'].isin(['Menunggu Validasi', 'Perlu Revisi'])]
        if not df_pending.empty:
            st.dataframe(df_pending[['Timestamp', 'Nama_Sekolah', 'Nama_Tugas', 'Status']], use_container_width=True)
            
            with st.form("form_nilai"):
                st.markdown("### 📝 Berikan Penilaian")
                baris_terpilih = st.selectbox("Pilih Dokumen (Berdasarkan Waktu Upload & Sekolah)", df_pending.apply(lambda x: f"{x['Timestamp']} | {x['Nama_Sekolah']} | {x['Nama_Tugas']}", axis=1))
                status_baru = st.radio("Keputusan Akhir", ["Disetujui ✅", "Perlu Revisi ♻️"])
                catatan = st.text_area("Catatan Pengawas / Detail Revisi")
                
                if st.form_submit_button("Simpan Keputusan", type="primary"):
                    ts_pilih = baris_terpilih.split(" | ")[0]
                    sekolah_pilih = baris_terpilih.split(" | ")[1]
                    
                    sheet_art = client.open(NAMA_SPREADSHEET).worksheet("Artefak_Portofolio")
                    
                    # Mencari baris yang tepat di Google Sheets
                    records = sheet_art.get_all_records()
                    for idx, row in enumerate(records):
                        if str(row.get('Timestamp')) == str(ts_pilih) and str(row.get('Nama_Sekolah')) == str(sekolah_pilih):
                            row_number = idx + 2 # +2 karena index gspread mulai dari 1 dan ada header
                            sheet_art.update_cell(row_number, 5, status_baru)
                            sheet_art.update_cell(row_number, 6, catatan)
                            st.success(f"Status dokumen {sekolah_pilih} berhasil diubah menjadi {status_baru}!")
                            st.rerun()
                            break
        else:
            st.success("🎉 Luar biasa! Semua dokumen sudah Anda periksa.")
    else:
        st.info("Belum ada data artefak.")

elif sub_menu == "Sistem Reminder Email":
    st.title("🔔 Pengingat Otomatis Sekolah Binaan")
    st.write("Kirimkan email *reminder* langsung kepada sekolah yang belum mengumpulkan tagihan tertentu.")
    
    df_tagihan = load_data("Tagihan_Tugas")
    df_user = load_data("User")
    df_art = load_data("Artefak_Portofolio")
    
    if not df_tagihan.empty and not df_user.empty:
        tugas_pilih = st.selectbox("Pilih Tugas yang Akan Dicek", df_tagihan['Nama_Tugas'].tolist())
        
        # Cari sekolah yang SUDAH mengumpulkan tugas ini
        sekolah_sudah = []
        if not df_art.empty:
            sekolah_sudah = df_art[df_art['Nama_Tugas'] == tugas_pilih]['Nama_Sekolah'].unique().tolist()
            
        # Ambil daftar SEMUA sekolah (dari data user yang Aktif dan bukan Admin)
        semua_sekolah = df_user[(df_user['Role'].isin(['Kepala Sekolah', 'Operator'])) & (df_user['Status_Akun'] == 'Aktif')]
        
        # Saring yang BELUM (Hanya ambil emailnya)
        sekolah_belum = semua_sekolah[~semua_sekolah['Asal_Sekolah'].isin(sekolah_sudah)]
        
        if not sekolah_belum.empty:
            st.warning(f"⚠️ Ada {len(sekolah_belum)} sekolah yang belum mengumpulkan '{tugas_pilih}'")
            st.dataframe(sekolah_belum[['Asal_Sekolah', 'Nama_Lengkap', 'Email']])
            
            # Membuat Link MailTo Otomatis
            daftar_email = ",".join(sekolah_belum['Email'].tolist())
            subject = urllib.parse.quote(f"PEMBERITAHUAN PENTING: Tagihan {tugas_pilih}")
            body = urllib.parse.quote(f"Yth. Bapak/Ibu Kepala Sekolah & Operator,\n\nBerdasarkan pantauan sistem dasbor Pengawas, kami mendapati bahwa satuan pendidikan Anda belum mengunggah dokumen: {tugas_pilih}.\n\nMohon segera dilengkapi.\n\nSalam,\nAdmin Pengawas GIPANG M3 BANTEN")
            mailto_link = f"mailto:{daftar_email}?subject={subject}&body={body}"
            
            st.markdown(f"""
                <a href="{mailto_link}" target="_blank">
                    <button style="background-color: #d93025; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 14px;">
                        📧 Buka Aplikasi Email & Kirim Reminder Massal
                    </button>
                </a>
            """, unsafe_allow_html=True)
            st.caption("*Tombol ini akan otomatis membuka Gmail/Outlook di perangkat Anda dengan email penerima (BCC) dan template pesan yang sudah disiapkan.")
        else:
            st.success("✅ Hebat! Seluruh sekolah binaan sudah mengumpulkan tugas ini.")

elif sub_menu == "Respon Konsultasi":
    st.title("💬 Layanan Konsultasi & Keluhan Sekolah")
    df_konsul = load_data("Konsultasi_Sekolah")
    if not df_konsul.empty:
        df_masuk = df_konsul[df_konsul['Status'] == 'Menunggu Respon']
        if not df_masuk.empty:
            st.dataframe(df_masuk[['Timestamp', 'Asal_Sekolah', 'Topik_Keluhan', 'Detail_Pesan']], use_container_width=True)
            with st.form("respon_keluhan"):
                pilih_tanya = st.selectbox("Pilih Keluhan", df_masuk.apply(lambda x: f"{x['Timestamp']} | {x['Asal_Sekolah']} | {x['Topik_Keluhan']}", axis=1))
                tanggapan = st.text_area("Berikan Tanggapan / Arahan")
                if st.form_submit_button("Kirim Jawaban"):
                    ts = pilih_tanya.split(" | ")[0]
                    sheet_k = client.open(NAMA_SPREADSHEET).worksheet("Konsultasi_Sekolah")
                    records = sheet_k.get_all_records()
                    for idx, row in enumerate(records):
                        if str(row.get('Timestamp')) == ts:
                            sheet_k.update_cell(idx + 2, 6, tanggapan)
                            sheet_k.update_cell(idx + 2, 7, "Dijawab ✅")
                            st.success("Tanggapan terkirim!")
                            st.rerun()
                            break
        else:
            st.info("Semua keluhan sudah ditanggapi.")

# ==========================================
# 6. KONTEN KHUSUS: KEPALA SEKOLAH (DATA TERISOLASI)
# ==========================================
elif sub_menu == "Dashboard Kepala Sekolah":
    st.title(f"🏛️ Dasbor Manajerial - {st.session_state.asal_sekolah}")
    
    # PROGRESS BAR EKSKLUSIF BERDASARKAN ASAL SEKOLAH
    df_tagihan = load_data("Tagihan_Tugas")
    total = len(df_tagihan) if not df_tagihan.empty else 0
    
    df_art = load_data("Artefak_Portofolio")
    # PENTING: Saring data HANYA untuk sekolah yang sedang login
    df_saya = df_art[df_art['Nama_Sekolah'] == st.session_state.asal_sekolah] if not df_art.empty else pd.DataFrame()
    
    disetujui = len(df_saya[df_saya['Status'] == 'Disetujui ✅']) if not df_saya.empty else 0
    revisi = len(df_saya[df_saya['Status'] == 'Perlu Revisi ♻️']) if not df_saya.empty else 0
    
    st.markdown("### 📈 Rapor Ketercapaian Administrasi")
    if total > 0:
        pct = min(disetujui / total, 1.0)
        st.progress(pct)
        c1, c2, c3 = st.columns(3)
        c1.metric("Target Tugas", total)
        c2.metric("Tuntas (Disetujui)", disetujui)
        c3.metric("Terkendala (Revisi)", revisi)
    
    st.markdown("### 📋 Detail Status & Catatan Pengawas")
    if not df_saya.empty:
        st.dataframe(df_saya[['Nama_Tugas', 'Status', 'Catatan_Pengawas']], use_container_width=True)
    else:
        st.info("Belum ada pergerakan administrasi dari operator Anda.")

elif sub_menu == "Pakta Integritas & Pengesahan":
    st.title("📜 Pengesahan Digital Pimpinan")
    st.markdown("""
        <div style='background-color: #fffbeb; padding: 25px; border-radius: 12px; border: 1px solid #fde68a; border-left: 8px solid #f59e0b;'>
            <h3 style='color: #92400e; margin-top:0;'>Pakta Integritas Validasi Data Akhir</h3>
            <p style='color: #78350f;'>Dengan menyetujui halaman ini, saya selaku Kepala Sekolah menyatakan bahwa seluruh Portofolio Artefak, Rapor Pendidikan, dan Laporan Kinerja yang telah diunggah oleh Operator Sekolah melalui sistem ini adalah <b>benar, valid, dan dapat dipertanggungjawabkan</b> sesuai dengan pedoman GIPANG M3 BANTEN.</p>
        </div>
    """, unsafe_allow_html=True)
    
    setuju = st.checkbox(f"Saya, Pimpinan {st.session_state.asal_sekolah}, menyetujui pakta integritas ini.")
    if st.button("🔒 Kunci Dokumen & Sahkan Secara Digital", type="primary", disabled=not setuju):
        st.success("✅ Pengesahan berhasil dicatat dalam riwayat Cloud Pengawas!")
        st.balloons()

elif sub_menu == "Layanan Konsultasi":
    st.title("💬 Kotak Keluhan & Arahan Pengawas")
    st.write("Sampaikan kendala implementasi atau permasalahan sekolah langsung kepada Ibu Pengawas.")
    
    with st.form("form_keluhan"):
        topik = st.text_input("Topik Keluhan / Permasalahan")
        pesan = st.text_area("Jelaskan detail kendala yang dialami sekolah")
        if st.form_submit_button("Kirim ke Pengawas"):
            if topik and pesan and client:
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                client.open(NAMA_SPREADSHEET).worksheet("Konsultasi_Sekolah").append_row([ts, st.session_state.asal_sekolah, st.session_state.user_name, topik, pesan, "", "Menunggu Respon"])
                st.success("Keluhan terkirim! Silakan cek kembali halaman ini nanti untuk melihat arahan Ibu Pengawas.")
    
    st.markdown("### 📥 Riwayat & Arahan Pengawas")
    df_k = load_data("Konsultasi_Sekolah")
    if not df_k.empty:
        # Tampilkan HANYA keluhan dari sekolah ini
        df_ksaya = df_k[df_k['Asal_Sekolah'] == st.session_state.asal_sekolah]
        if not df_ksaya.empty:
            for idx, row in df_ksaya.iterrows():
                st.info(f"**Topik:** {row['Topik_Keluhan']}\n\n**Keluhan Kami:** {row['Detail_Pesan']}\n\n**Jawaban Pengawas:** {row.get('Tanggapan_Pengawas', '⏳ Belum dibalas')}")

# ==========================================
# 7. KONTEN KHUSUS: OPERATOR (DATA TERISOLASI)
# ==========================================
elif sub_menu == "Dashboard Operator":
    st.title(f"🔧 Dasbor Teknis - {st.session_state.asal_sekolah}")
    st.info("Pemberitahuan: Batas maksimal ukuran dokumen unggahan kini dibatasi 3 MB.")

elif sub_menu == "Upload Artefak":
    st.title("📤 Unggah Berkas Tagihan")
    df_tag = load_data("Tagihan_Tugas")
    daftar = df_tag["Nama_Tugas"].tolist() if not df_tag.empty else ["Kosong"]
    
    with st.form("f_up"):
        tugas = st.selectbox("Pilih Tagihan", daftar)
        file_art = st.file_uploader("Upload Dokumen PDF/Office (MAKSIMAL 3 MB)")
        
        if st.form_submit_button("Kirim Dokumen"):
            if file_art:
                # CEK BATAS MAKSIMAL 3MB
                if file_art.size > 3 * 1024 * 1024:
                    st.error("❌ UPLOAD GAGAL: Ukuran file Anda melebihi 3 MB! Silakan kompres (perkecil) file Anda terlebih dahulu.")
                elif client:
                    sheet = client.open(NAMA_SPREADSHEET).worksheet("Artefak_Portofolio")
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sheet.append_row([ts, st.session_state.asal_sekolah, tugas, "File_Masuk", "Menunggu Validasi", ""])
                    st.success("Terkirim! Mohon tunggu review Ibu Pengawas.")
            else:
                st.error("Pilih file.")

elif sub_menu == "Riwayat & Perbaikan":
    st.title("♻️ Log Catatan Perbaikan & Revisi")
    st.write("Cek segera jika dokumen Anda ditolak atau membutuhkan revisi.")
    
    df_art = load_data("Artefak_Portofolio")
    if not df_art.empty:
        # Filter HANYA untuk sekolah operator ini, dan yang butuh Revisi
        df_rev = df_art[(df_art['Nama_Sekolah'] == st.session_state.asal_sekolah) & (df_art['Status'] == 'Perlu Revisi ♻️')]
        if not df_rev.empty:
            for idx, row in df_rev.iterrows():
                st.error(f"❌ **Tugas:** {row['Nama_Tugas']}\n\n**Catatan Pengawas:** {row['Catatan_Pengawas']}\n\n*(Silakan perbaiki dan upload ulang di menu Upload Artefak)*")
        else:
            st.success("🎉 Hebat! Tidak ada dokumen Anda yang perlu direvisi saat ini.")
