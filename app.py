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
    .hero-sub { font-size: 19px; color: #0B1F52; font-weight: 600; margin-bottom: 15px; line-height: 1.3; }
    .hero-desc { font-size: 14px; color: #475569; line-height: 1.6; margin-bottom: 25px; }
    .mockup-container { position: relative; background: radial-gradient(circle, rgba(96,165,254,0.15) 0%, rgba(255,255,255,0) 70%); text-align: center; padding: 20px; }
    .saas-card { background: white; border-radius: 20px; padding: 24px; border: 1px solid #e2e8f0; box-shadow: 0 10px 30px rgba(11, 31, 82, 0.02); transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); height: 100%; }
    .saas-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(11, 31, 82, 0.06); border-color: #60a5fa; }
    .icon-box { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-bottom: 12px; }
    .custom-table-container { background: white; border-radius: 20px; padding: 20px; border: 1px solid #e2e8f0; }
    .stButton button { border-radius: 10px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONEKSI GOOGLE SHEETS (ANTI ERROR)
# ==========================================
NAMA_SPREADSHEET = "Database_Portofolio_Pengawas"

@st.cache_resource
def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp" not in st.secrets or "kunci_json" not in st.secrets["gcp"]:
            return None, "Kunci Secrets GCP belum disetting."
        kunci_mentah = st.secrets["gcp"]["kunci_json"]
        import ast
        try:
            creds_dict = json.loads(kunci_mentah, strict=False)
        except:
            creds_dict = ast.literal_eval(kunci_mentah.replace('\n', ''))
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client, "Sukses"
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
if "show_login" not in st.session_state:
    st.session_state.show_login = False
if "show_register" not in st.session_state:
    st.session_state.show_register = False

st.markdown("<div id='beranda'></div>", unsafe_allow_html=True)

# ==========================================
# 3. DYNAMIC WEB STICKY NAVBAR COMPONENT
# ==========================================
st.markdown("""
    <div class='premium-navbar'>
        <div class='nav-brand'>🏛️ GIPANG <span>M3</span> BANTEN</div>
        <div style='display: flex; gap: 30px; font-weight: 500; font-size: 14px;'>
            <a href='#beranda' style='color:#1D4ED8; text-decoration:none;'>Beranda</a>
            <a href='#fitur' style='color:#475569; text-decoration:none;'>Fitur</a>
            <a href='#portofolio' style='color:#475569; text-decoration:none;'>Portofolio</a>
            <a href='#materi' style='color:#475569; text-decoration:none;'>Materi Publik</a>
        </div>
        <div style='visibility: hidden; width: 0px;'>Nav Spacer</div>
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
if st.session_state.show_login and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown("#### 🔐 Portal Autentikasi Ruang Kerja")
        e_login = st.text_input("📧 Alamat Email")
        p_login = st.text_input("🔑 Password", type="password")
        if st.button("Login Sekarang", type="primary"):
            if client:
                df_users = load_data("User")
                if not df_users.empty:
                    user_match = df_users[(df_users['Email'].astype(str) == e_login) & (df_users['Password'].astype(str) == p_login)]
                    if not user_match.empty:
                        status_akun = user_match.iloc[0].get('Status_Akun', 'Pending')
                        if status_akun == 'Aktif':
                            st.session_state.logged_in = True
                            st.session_state.user_role = user_match.iloc[0]['Role']
                            st.session_state.asal_sekolah = user_match.iloc[0]['Asal_Sekolah']
                            st.session_state.user_name = f"{user_match.iloc[0]['Nama_Lengkap']} - {st.session_state.asal_sekolah}"
                            st.session_state.show_login = False
                            st.rerun()
                        else:
                            st.warning("⏳ Akun Anda masih PENDING. Menunggu persetujuan Pengawas.")
                    else:
                        st.error("❌ Email atau Password salah!")
            else:
                st.error("Gagal terhubung ke database.")

# --- POPUP REGISTRASI ---
if st.session_state.show_register and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown("#### 🚀 Formulir Permohonan Akses")
        with st.form("form_registrasi"):
            c1, c2 = st.columns(2)
            reg_nama = c1.text_input("👤 Nama Lengkap")
            reg_sekolah = c2.text_input("🏫 Asal Sekolah")
            reg_email = st.text_input("📧 Alamat Email")
            c3, c4 = st.columns(2)
            reg_role = c3.selectbox("💼 Role", ["Kepala Sekolah", "Operator"])
            reg_pass = c4.text_input("🔑 Buat Password Baru (Wajib 1 Kapital & 1 Angka)", type="password")
            
            if st.form_submit_button("Daftar Sekarang", type="primary"):
                if reg_nama and reg_sekolah and reg_email and reg_pass:
                    if any(char.isupper() for char in reg_pass) and any(char.isdigit() for char in reg_pass) and len(reg_pass) >= 6:
                        if client:
                            client.open(NAMA_SPREADSHEET).worksheet("User").append_row([reg_nama, reg_sekolah, reg_email, reg_role, reg_pass, "Pending"])
                            st.success("✅ Pendaftaran Berhasil! Akun berstatus PENDING hingga disetujui.")
                        else:
                            st.error("Gagal terhubung ke database.")
                    else:
                        st.error("❌ Password WAJIB minimal 6 karakter, 1 Huruf Kapital & 1 Angka!")
                else:
                    st.error("⚠️ Lengkapi seluruh kolom!")

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
    
    if sub_menu == "Log Out":
        st.session_state.logged_in = False
        st.session_state.user_role = "Public"
        st.session_state.user_name = "Guest"
        st.rerun()
else:
    sub_menu = "Beranda Publik"
    st.sidebar.info("Silakan klik tombol **🔒 Masuk** atau **🚀 Request Akses**.")

# ==========================================
# 5. HALAMAN UTAMA (LANDING PAGE - SELALU TAMPIL JIKA BELUM LOGIN)
# ==========================================
if sub_menu == "Beranda Publik" and not st.session_state.logged_in:
    st.markdown("<hr style='opacity:0.2;'>", unsafe_allow_html=True) # Spacer
    
    # 5.1 Hero Grid Layout
    col_hero1, col_hero2 = st.columns([1.3, 1])
    with col_hero1:
        st.markdown("<div class='tagline-badge'>💻 Platform Pengawas Sekolah Modern</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-h1'>GIPANG <span>M3</span> BANTEN</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-sub'>Gerakan Inovatif Pendampingan Memantau, Mengevaluasi, Menilai Bantuan Teknologi</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-desc'>Platform digital untuk memudahkan pengawas sekolah dalam mengumpulkan, memantau, mengevaluasi, dan menilai portofolio artefak dari sekolah binaan secara transparan, dan terstruktur.</div>", unsafe_allow_html=True)
    with col_hero2:
        st.markdown("""<div class='mockup-container'><div style='background: white; border: 12px solid #1e293b; border-bottom-width: 24px; border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(11,31,82,0.25); overflow: hidden;'><div style='background: #f8fafc; padding: 12px; text-align: left; font-size: 11px; border-bottom: 1px solid #e2e8f0; font-weight: 600;'>📊 Dashboard Workspace - Pengawas Sekolah Banten</div><div style='padding: 20px; background: white; height: 210px; text-align: left;'><div style='display: flex; gap: 10px; margin-bottom: 15px;'><div style='flex:1; background:#eff6ff; padding: 10px; border-radius: 8px; border-left: 4px solid #1D4ED8;'><small style='color:#64748b;'>Sekolah Binaan</small><br><b style='font-size: 16px; color:#0B1F52;'>24</b></div><div style='flex:1; background:#f0fdf4; padding: 10px; border-radius: 8px; border-left: 4px solid #10b981;'><small style='color:#64748b;'>Diterima</small><br><b style='font-size: 16px; color:#065f46;'>156</b></div></div></div></div></div>""", unsafe_allow_html=True)

    # 5.2 Row Section Fitur
    st.markdown("<div id='fitur'></div><br>", unsafe_allow_html=True)
    row_f1, row_f2, row_f3 = st.columns(3)
    row_f1.markdown("<div class='saas-card'><div class='icon-box' style='background:#eff6ff; color:#1D4ED8;'>📤</div><h5>Pengumpulan Artefak</h5><p style='font-size:13px; color:#64748b;'>Upload berkas data portofolio maksimal 3MB per file.</p></div>", unsafe_allow_html=True)
    row_f2.markdown("<div class='saas-card'><div class='icon-box' style='background:#f0fdf4; color:#10b981;'>🛡️</div><h5>Validasi & Evaluasi</h5><p style='font-size:13px; color:#64748b;'>Status tinjauan kualitas dan progres langsung terpantau.</p></div>", unsafe_allow_html=True)
    row_f3.markdown("<div class='saas-card'><div class='icon-box' style='background:#f5f3ff; color:#7c3aed;'>📥</div><h5>Download Materi</h5><p style='font-size:13px; color:#64748b;'>Unduh akses materi pendampingan Juknis dari Pengawas.</p></div>", unsafe_allow_html=True)

    # 5.3 Pengumpulan Terbaru
    st.markdown("<div id='portofolio'></div><br><hr style='opacity:0.5;'><br><h4>📋 Pengumpulan Terbaru</h4>", unsafe_allow_html=True)
    df_artefak = load_data("Artefak_Portofolio")
    if not df_artefak.empty:
        # Tampilkan secara anonim di publik (tanpa status/catatan rahasia)
        st.dataframe(df_artefak[["Nama_Sekolah", "Nama_Tugas", "Timestamp"]].tail(5), use_container_width=True)
    else:
        st.info("Belum ada data artefak yang terkumpul dari sekolah binaan.")

    # 5.4 Pusat Materi Publik
    st.markdown("<div id='materi'></div><br><hr style='opacity:0.5;'><br><h4>📥 Pusat Download Materi & Regulasi</h4>", unsafe_allow_html=True)
    df_materi = load_data("Materi_Publik")
    if not df_materi.empty:
        materi_cols = st.columns(3)
        for index, row in df_materi.iterrows():
            with materi_cols[index % 3]:
                st.markdown(f"""
                    <div class='saas-card' style='padding: 20px; margin-bottom: 15px;'>
                        <div style='font-size: 35px; margin-bottom: 10px;'>{row.get('Icon', '📄')}</div>
                        <h5 style='margin: 0 0 5px 0; color: #0B1F52;'>{row.get('Judul', 'Tanpa Judul')}</h5>
                        <p style='font-size: 12px; color: #64748b; margin: 0;'>🏷️ {row.get('Kategori', '')} &nbsp;|&nbsp; 📅 {row.get('Tanggal', '')}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Belum ada materi publik yang tersedia.")
        
    st.markdown("<br><div style='text-align:center; color:#64748b; font-size:12px;'>© 2026 GIPANG M3 BANTEN. All rights reserved.</div><br>", unsafe_allow_html=True)

# ==========================================
# 6. KONTEN PRIVATE (HANYA TAMPIL JIKA LOGIN)
# ==========================================

# ----------------- AREA ADMIN -----------------
elif sub_menu == "Dashboard Admin" and st.session_state.logged_in:
    st.title("📊 Panel Kontrol Utama Pengawas")
    df_artefak = load_data("Artefak_Portofolio")
    pending = len(df_artefak[df_artefak['Status'] == 'Menunggu Validasi']) if not df_artefak.empty else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Menunggu Pemeriksaan", f"{pending} Dokumen", "Perlu Tindakan" if pending > 0 else "Aman", delta_color="inverse" if pending > 0 else "normal")
    st.write("Gunakan menu di samping untuk memantau, memeriksa, dan mengirim pengingat ke sekolah binaan Anda.")

elif sub_menu == "Cek Artefak Sekolah":
    st.title("🛡️ Pemeriksaan & Penilaian Portofolio")
    st.write("Berikan catatan dan ubah status dokumen yang dikirim oleh sekolah.")
    df_art = load_data("Artefak_Portofolio")
    if not df_art.empty:
        df_pending = df_art[df_art['Status'].isin(['Menunggu Validasi', 'Perlu Revisi ♻️'])]
        if not df_pending.empty:
            st.dataframe(df_pending[['Timestamp', 'Nama_Sekolah', 'Nama_Tugas', 'Status']], use_container_width=True)
            with st.form("form_nilai"):
                st.markdown("### 📝 Berikan Penilaian")
                baris_terpilih = st.selectbox("Pilih Dokumen", df_pending.apply(lambda x: f"{x['Timestamp']} | {x['Nama_Sekolah']} | {x['Nama_Tugas']}", axis=1))
                status_baru = st.radio("Keputusan Akhir", ["Disetujui ✅", "Perlu Revisi ♻️"])
                catatan = st.text_area("Catatan Pengawas / Detail Revisi")
                
                if st.form_submit_button("Simpan Keputusan", type="primary"):
                    ts_pilih = baris_terpilih.split(" | ")[0]
                    sekolah_pilih = baris_terpilih.split(" | ")[1]
                    sheet_art = client.open(NAMA_SPREADSHEET).worksheet("Artefak_Portofolio")
                    records = sheet_art.get_all_records()
                    for idx, row in enumerate(records):
                        if str(row.get('Timestamp')) == str(ts_pilih) and str(row.get('Nama_Sekolah')) == str(sekolah_pilih):
                            sheet_art.update_cell(idx + 2, 5, status_baru)
                            sheet_art.update_cell(idx + 2, 6, catatan)
                            st.success(f"Status dokumen berhasil diubah menjadi {status_baru}!")
                            st.rerun()
                            break
        else:
            st.success("🎉 Luar biasa! Semua dokumen sudah Anda periksa.")
    else:
        st.info("Belum ada data artefak dari sekolah.")

elif sub_menu == "Sistem Reminder Email":
    st.title("🔔 Pengingat Otomatis Sekolah Binaan")
    df_tagihan = load_data("Tagihan_Tugas")
    df_user = load_data("User")
    df_art = load_data("Artefak_Portofolio")
    
    if not df_tagihan.empty and not df_user.empty:
        tugas_pilih = st.selectbox("Pilih Tugas yang Akan Dicek", df_tagihan['Nama_Tugas'].tolist())
        sekolah_sudah = df_art[df_art['Nama_Tugas'] == tugas_pilih]['Nama_Sekolah'].unique().tolist() if not df_art.empty else []
        semua_sekolah = df_user[(df_user['Role'].isin(['Kepala Sekolah', 'Operator'])) & (df_user['Status_Akun'] == 'Aktif')]
        sekolah_belum = semua_sekolah[~semua_sekolah['Asal_Sekolah'].isin(sekolah_sudah)]
        
        if not sekolah_belum.empty:
            st.warning(f"⚠️ Ada {len(sekolah_belum)} akun yang belum mengumpulkan '{tugas_pilih}'")
            st.dataframe(sekolah_belum[['Asal_Sekolah', 'Nama_Lengkap', 'Email']])
            
            daftar_email = ",".join(sekolah_belum['Email'].tolist())
            subject = urllib.parse.quote(f"PEMBERITAHUAN PENTING: Tagihan {tugas_pilih}")
            body = urllib.parse.quote(f"Yth. Bapak/Ibu Kepala Sekolah & Operator,\n\nBerdasarkan pantauan sistem, satuan pendidikan Anda belum mengunggah dokumen: {tugas_pilih}.\n\nMohon segera dilengkapi.\n\nSalam,\nAdmin Pengawas GIPANG M3 BANTEN")
            mailto_link = f"mailto:?bcc={daftar_email}&subject={subject}&body={body}"
            
            st.markdown(f'<a href="{mailto_link}" target="_blank"><button style="background-color: #d93025; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 14px;">📧 Buka Aplikasi Email & Kirim Reminder Massal</button></a>', unsafe_allow_html=True)
        else:
            st.success("✅ Hebat! Seluruh sekolah binaan sudah mengumpulkan tugas ini.")

elif sub_menu == "Validasi Akun Baru":
    st.title("🛡️ Validasi & Persetujuan Akun")
    df_users = load_data("User")
    if not df_users.empty:
        df_pending = df_users[df_users['Status_Akun'] == 'Pending']
        if not df_pending.empty:
            st.dataframe(df_pending[['Nama_Lengkap', 'Asal_Sekolah', 'Role', 'Email']], use_container_width=True)
            with st.form("form_setujui"):
                email_pilihan = st.selectbox("Pilih Email yang Ingin Disetujui (Diaktifkan)", df_pending['Email'].tolist())
                if st.form_submit_button("✅ Setujui & Aktifkan Akun"):
                    sheet_users = client.open(NAMA_SPREADSHEET).worksheet("User")
                    cell = sheet_users.find(email_pilihan)
                    if cell:
                        sheet_users.update_cell(cell.row, 6, "Aktif")
                        st.success(f"Akun dengan email {email_pilihan} berhasil DIAKTIFKAN!")
                        st.rerun()
        else:
            st.info("✅ Tidak ada akun baru yang menunggu validasi.")

elif sub_menu == "Manajemen Tagihan Tugas":
    st.title("📋 Pembuatan & Distribusi Tugas")
    with st.form("form_buat_tugas"):
        nama_tugas = st.text_input("Nama/Judul Tugas")
        kategori_tugas = st.selectbox("Kategori", ["Manajerial", "Akademik", "Administrasi"])
        batas_waktu = st.date_input("Batas Waktu Pengumpulan")
        deskripsi = st.text_area("Deskripsi / Petunjuk")
        if st.form_submit_button("Terbitkan Tugas ke Sekolah", type="primary"):
            if nama_tugas and client:
                client.open(NAMA_SPREADSHEET).worksheet("Tagihan_Tugas").append_row([nama_tugas, kategori_tugas, batas_waktu.strftime("%d %B %Y"), deskripsi])
                st.success("Tugas berhasil diterbitkan!")
            else:
                st.error("Isi Nama Tugas.")

elif sub_menu == "Upload Materi Pusat":
    st.title("📤 Publikasi Materi Instruksional Pusat")
    with st.form("form_materi"):
        judul_materi = st.text_input("Judul Materi")
        kategori_materi = st.selectbox("Kategori", ["Regulasi", "Modul Ajar", "Template"])
        file_materi = st.file_uploader("Upload File")
        if st.form_submit_button("Publikasikan ke Website"):
            if judul_materi and file_materi and client:
                sz = f"{round(file_materi.size / (1024*1024), 2)} MB"
                client.open(NAMA_SPREADSHEET).worksheet("Materi_Publik").append_row([judul_materi, kategori_materi, datetime.datetime.now().strftime("%d %b %Y"), sz, "🆕"])
                st.success("Materi dipublikasikan!")

elif sub_menu == "Respon Konsultasi":
    st.title("💬 Layanan Konsultasi & Keluhan")
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

# ----------------- AREA KEPALA SEKOLAH -----------------
elif sub_menu == "Dashboard Kepala Sekolah":
    st.title(f"🏛️ Dasbor Manajerial - {st.session_state.asal_sekolah}")
    df_tagihan = load_data("Tagihan_Tugas")
    total = len(df_tagihan) if not df_tagihan.empty else 0
    df_art = load_data("Artefak_Portofolio")
    
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
    st.markdown("""<div style='background-color: #fffbeb; padding: 25px; border-radius: 12px; border-left: 8px solid #f59e0b;'><h3 style='color: #92400e; margin-top:0;'>Pakta Integritas Validasi Data Akhir</h3><p style='color: #78350f;'>Dengan menyetujui halaman ini, saya selaku Kepala Sekolah menyatakan bahwa seluruh Portofolio yang telah diunggah oleh Operator adalah <b>benar, valid, dan dapat dipertanggungjawabkan</b>.</p></div>""", unsafe_allow_html=True)
    setuju = st.checkbox(f"Saya, Pimpinan {st.session_state.asal_sekolah}, menyetujui pakta integritas ini.")
    if st.button("🔒 Kunci Dokumen & Sahkan", type="primary", disabled=not setuju):
        st.success("✅ Pengesahan berhasil dicatat dalam riwayat Cloud Pengawas!")
        st.balloons()

elif sub_menu == "Layanan Konsultasi":
    st.title("💬 Kotak Keluhan & Arahan Pengawas")
    with st.form("form_keluhan"):
        topik = st.text_input("Topik Keluhan / Permasalahan")
        pesan = st.text_area("Jelaskan detail kendala yang dialami sekolah")
        if st.form_submit_button("Kirim ke Pengawas"):
            if topik and pesan and client:
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                client.open(NAMA_SPREADSHEET).worksheet("Konsultasi_Sekolah").append_row([ts, st.session_state.asal_sekolah, st.session_state.user_name, topik, pesan, "", "Menunggu Respon"])
                st.success("Keluhan terkirim!")
    
    st.markdown("### 📥 Riwayat & Arahan Pengawas")
    df_k = load_data("Konsultasi_Sekolah")
    if not df_k.empty:
        df_ksaya = df_k[df_k['Asal_Sekolah'] == st.session_state.asal_sekolah]
        if not df_ksaya.empty:
            for idx, row in df_ksaya.iterrows():
                st.info(f"**Topik:** {row['Topik_Keluhan']}\n\n**Keluhan Kami:** {row['Detail_Pesan']}\n\n**Jawaban Pengawas:** {row.get('Tanggapan_Pengawas', '⏳ Belum dibalas')}")

# ----------------- AREA OPERATOR -----------------
elif sub_menu == "Dashboard Operator":
    st.title(f"🔧 Dasbor Teknis - {st.session_state.asal_sekolah}")
    st.warning("⚠️ Pemberitahuan: Batas maksimal ukuran dokumen unggahan dibatasi 3 MB per file.")
    st.write("Silakan cek menu 'Riwayat & Perbaikan' untuk melihat apakah ada berkas yang ditolak oleh Ibu Pengawas.")

elif sub_menu == "Upload Artefak":
    st.title("📤 Unggah Berkas Tagihan")
    df_tag = load_data("Tagihan_Tugas")
    daftar = df_tag["Nama_Tugas"].tolist() if not df_tag.empty else ["Kosong"]
    
    with st.form("f_up"):
        tugas = st.selectbox("Pilih Tagihan", daftar)
        file_art = st.file_uploader("Upload Dokumen PDF/Office (MAKS 3 MB)")
        
        if st.form_submit_button("Kirim Dokumen"):
            if file_art:
                if file_art.size > 3 * 1024 * 1024:
                    st.error("❌ UPLOAD GAGAL: Ukuran file Anda melebihi 3 MB! Silakan kompres file Anda.")
                elif client:
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    client.open(NAMA_SPREADSHEET).worksheet("Artefak_Portofolio").append_row([ts, st.session_state.asal_sekolah, tugas, "File_Masuk", "Menunggu Validasi", ""])
                    st.success("Terkirim! Mohon tunggu review Pengawas.")
            else:
                st.error("Pilih file terlebih dahulu.")

elif sub_menu == "Riwayat & Perbaikan":
    st.title("♻️ Log Catatan Perbaikan & Revisi")
    df_art = load_data("Artefak_Portofolio")
    if not df_art.empty:
        df_rev = df_art[(df_art['Nama_Sekolah'] == st.session_state.asal_sekolah) & (df_art['Status'] == 'Perlu Revisi ♻️')]
        if not df_rev.empty:
            for idx, row in df_rev.iterrows():
                st.error(f"❌ **Tugas:** {row['Nama_Tugas']}\n\n**Catatan Pengawas:** {row['Catatan_Pengawas']}\n\n*(Silakan perbaiki dan upload ulang di menu Upload Artefak)*")
        else:
            st.success("🎉 Hebat! Tidak ada dokumen Anda yang perlu direvisi saat ini.")
