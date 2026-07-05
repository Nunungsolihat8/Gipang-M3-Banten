import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import json
import urllib.parse
import requests
import base64

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
    .saas-card { background: white; border-radius: 20px; padding: 24px; border: 1px solid #e2e8f0; box-shadow: 0 10px 30px rgba(11, 31, 82, 0.02); transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); height: 100%; }
    .saas-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(11, 31, 82, 0.06); border-color: #60a5fa; }
    .icon-box { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-bottom: 12px; }
    .custom-table-container { background: white; border-radius: 20px; padding: 20px; border: 1px solid #e2e8f0; }
    .stButton button { border-radius: 10px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONEKSI SISTEM & MESIN API
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

# MESIN UPLOAD GAMBAR KE IMGBB
def upload_to_imgbb(image_file):
    try:
        api_key = st.secrets["imgbb"]["api_key"]
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": api_key,
            "image": base64.b64encode(image_file.getvalue()).decode("utf-8")
        }
        res = requests.post(url, data=payload)
        if res.status_code == 200:
            return res.json()['data']['url']
        return ""
    except Exception as e:
        return ""

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

# ==========================================
# 3. DYNAMIC WEB STICKY NAVBAR COMPONENT
# ==========================================
st.markdown("<div id='beranda'></div>", unsafe_allow_html=True)

st.markdown("""
    <div class='premium-navbar'>
        <div class='nav-brand'>🏛️ GIPANG <span>M3</span> BANTEN</div>
        <div style='display: flex; gap: 30px; font-weight: 500; font-size: 14px;'>
            <a href='#beranda' style='color:#1D4ED8; text-decoration:none;'>Beranda</a>
            <a href='#fitur' style='color:#475569; text-decoration:none;'>Fitur</a>
            <a href='#portofolio' style='color:#475569; text-decoration:none;'>Portofolio Kegiatan</a>
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

# --- POPUP LOGIN & REGISTRASI ---
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
            reg_pass = c4.text_input("🔑 Password (Wajib 1 Kapital & 1 Angka)", type="password")
            if st.form_submit_button("Daftar", type="primary"):
                if reg_nama and reg_sekolah and reg_email and reg_pass:
                    if any(char.isupper() for char in reg_pass) and any(char.isdigit() for char in reg_pass) and len(reg_pass) >= 6:
                        if client:
                            client.open(NAMA_SPREADSHEET).worksheet("User").append_row([reg_nama, reg_sekolah, reg_email, reg_role, reg_pass, "Pending"])
                            st.success("✅ Terdaftar! Menunggu persetujuan Admin.")
                    else:
                        st.error("❌ Password WAJIB minimal 6 karakter, 1 Huruf Kapital & 1 Angka!")

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
        sub_menu = st.sidebar.radio("Menu Pengawas", ["Dashboard Admin", "Cek Artefak Sekolah", "Sistem Reminder Email", "Validasi Akun Baru", "Manajemen Tagihan Tugas", "Upload Materi Pusat", "Respon Konsultasi", "Upload Galeri Kegiatan", "Log Out"])
    elif st.session_state.user_role == "Kepala Sekolah":
        sub_menu = st.sidebar.radio("Menu Kepala Sekolah", ["Dashboard Kepala Sekolah", "Pakta Integritas & Pengesahan", "Layanan Konsultasi", "Upload Galeri Kegiatan", "Log Out"])
    elif st.session_state.user_role == "Operator":
        sub_menu = st.sidebar.radio("Menu Operator", ["Dashboard Operator", "Upload Artefak", "Riwayat & Perbaikan", "Upload Galeri Kegiatan", "Log Out"])
    
    if sub_menu == "Log Out":
        st.session_state.logged_in = False
        st.session_state.user_role = "Public"
        st.session_state.user_name = "Guest"
        st.rerun()
else:
    sub_menu = "Beranda Publik"

# ==========================================
# 5. HALAMAN UTAMA (LANDING PAGE & NAVIGASI)
# ==========================================
if sub_menu == "Beranda Publik" and not st.session_state.logged_in:
    st.markdown("<hr style='opacity:0.2;'>", unsafe_allow_html=True)
    
    col_hero1, col_hero2 = st.columns([1.3, 1])
    with col_hero1:
        st.markdown("<div class='tagline-badge'>💻 Platform Pengawas Sekolah Modern</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-h1'>GIPANG <span>M3</span> BANTEN</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-sub'>Gerakan Inovatif Pendampingan Memantau, Mengevaluasi, Menilai Bantuan Teknologi</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-desc'>Platform digital untuk memudahkan pengawas sekolah dalam mengumpulkan, memantau, mengevaluasi, dan menilai portofolio artefak dari sekolah binaan secara transparan, dan terstruktur.</div>", unsafe_allow_html=True)
    with col_hero2:
        st.markdown("""<div class='mockup-container'><div style='background: white; border: 12px solid #1e293b; border-bottom-width: 24px; border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(11,31,82,0.25); overflow: hidden;'><div style='background: #f8fafc; padding: 12px; text-align: left; font-size: 11px; border-bottom: 1px solid #e2e8f0; font-weight: 600;'>📊 Dashboard Workspace - Pengawas Sekolah Banten</div><div style='padding: 20px; background: white; height: 210px; text-align: left;'><div style='display: flex; gap: 10px; margin-bottom: 15px;'><div style='flex:1; background:#eff6ff; padding: 10px; border-radius: 8px; border-left: 4px solid #1D4ED8;'><small style='color:#64748b;'>Sekolah Binaan</small><br><b style='font-size: 16px; color:#0B1F52;'>24</b></div><div style='flex:1; background:#f0fdf4; padding: 10px; border-radius: 8px; border-left: 4px solid #10b981;'><small style='color:#64748b;'>Diterima</small><br><b style='font-size: 16px; color:#065f46;'>156</b></div></div></div></div></div>""", unsafe_allow_html=True)

    st.markdown("<div id='fitur'></div><br>", unsafe_allow_html=True)
    row_f1, row_f2, row_f3 = st.columns(3)
    row_f1.markdown("<div class='saas-card'><div class='icon-box' style='background:#eff6ff; color:#1D4ED8;'>📤</div><h5>Pengumpulan Artefak</h5><p style='font-size:13px; color:#64748b;'>Upload berkas portofolio aman maksimal 3MB.</p></div>", unsafe_allow_html=True)
    row_f2.markdown("<div class='saas-card'><div class='icon-box' style='background:#f0fdf4; color:#10b981;'>🛡️</div><h5>Validasi & Evaluasi</h5><p style='font-size:13px; color:#64748b;'>Tinjauan kualitas real-time anti ganda.</p></div>", unsafe_allow_html=True)
    row_f3.markdown("<div class='saas-card'><div class='icon-box' style='background:#f5f3ff; color:#7c3aed;'>📥</div><h5>Download Materi</h5><p style='font-size:13px; color:#64748b;'>Unduh materi pembinaan pusat.</p></div>", unsafe_allow_html=True)

    st.markdown("<div id='portofolio'></div><br><hr style='opacity:0.5;'><br><h4>📸 Galeri Portofolio Kegiatan</h4>", unsafe_allow_html=True)
    df_galeri = load_data("Galeri_Portofolio")
    if not df_galeri.empty:
        gal_cols = st.columns(3)
        for index, row in df_galeri.iterrows():
            with gal_cols[index % 3]:
                img_sub_html = ""
                for col_name in ['Link_Foto1', 'Link_Foto2', 'Link_Foto3']:
                    img_url = row.get(col_name, "")
                    if img_url:
                        img_sub_html += f"<img src='{img_url}' style='width:31%; height:60px; object-fit:cover; border-radius:6px; border:1px solid #e2e8f0;' onerror=\"this.style.display='none'\">"
                
                foto_utama = row.get('Link_Foto1', 'https://via.placeholder.com/300x150.png?text=GIPANG+M3')
                
                st.markdown(f"""
                    <div class='saas-card' style='padding: 15px; margin-bottom: 15px;'>
                        <div style='background-color: #f1f5f9; height: 160px; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; overflow: hidden;'>
                            <img src='{foto_utama}' style='width: 100%; height: 100%; object-fit: cover;' onerror=\"this.src='https://via.placeholder.com/300x150.png?text=Tidak+Ada+Gambar'\">
                        </div>
                        <div style='display:flex; gap:6px; margin-bottom:12px; justify-content:flex-start;'>
                            {img_sub_html}
                        </div>
                        <h6 style='margin: 0 0 5px 0; color: #0B1F52; font-weight:700;'>🏫 {row.get('Asal_Sekolah', '')}</h6>
                        <p style='font-size: 11px; color: #64748b; margin: 0;'>{row.get('Deskripsi_Kegiatan', '')}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Belum ada dokumentasi kegiatan yang diunggah.")

    st.markdown("<div id='materi'></div><br><hr style='opacity:0.5;'><br><h4>📥 Pusat Download Materi Publik</h4>", unsafe_allow_html=True)
    df_materi = load_data("Materi_Publik")
    if not df_materi.empty:
        materi_cols = st.columns(3)
        for index, row in df_materi.iterrows():
            with materi_cols[index % 3]:
                st.markdown(f"""<div class='saas-card' style='padding: 20px; margin-bottom: 15px;'><div style='font-size: 35px; margin-bottom: 10px;'>{row.get('Icon', '📄')}</div><h5 style='margin: 0 0 5px 0; color: #0B1F52;'>{row.get('Judul', 'Tanpa Judul')}</h5><p style='font-size: 12px; color: #64748b; margin: 0;'>🏷️ {row.get('Kategori', '')} &nbsp;|&nbsp; 📅 {row.get('Tanggal', '')}</p></div>""", unsafe_allow_html=True)

# ==========================================
# 6. KONTEN PRIVATE (RUANG WORKSPACE)
# ==========================================

# --- FITUR UPLOAD GAMBAR LANGSUNG ---
elif sub_menu == "Upload Galeri Kegiatan":
    st.title("📸 Publikasikan Foto Kegiatan")
    st.write("Unggah langsung file JPG/PNG dari perangkat Anda. Sistem akan otomatis memproses dan menampilkannya di Galeri Beranda.")
    
    with st.container(border=True):
        st.info("💡 Anda dapat memilih hingga 3 Foto sekaligus. Batas ukuran maksimal per foto adalah 2 MB.")
        desc_keg = st.text_input("Judul / Deskripsi Singkat Kegiatan")
        
        uploaded_photos = st.file_uploader("Pilih File (JPG/PNG)", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
        
        if st.button("🚀 Upload ke Portofolio", type="primary"):
            if desc_keg and uploaded_photos:
                if len(uploaded_photos) > 3:
                    st.error("❌ Anda memilih lebih dari 3 foto. Silakan kurangi.")
                else:
                    ukuran_aman = True
                    for foto in uploaded_photos:
                        if foto.size > 2 * 1024 * 1024:
                            st.error(f"❌ Ukuran foto '{foto.name}' melebihi 2 MB!")
                            ukuran_aman = False
                            break
                            
                    if ukuran_aman and client:
                        with st.spinner("Sedang memproses dan mengunggah foto ke server..."):
                            ts = datetime.datetime.now().strftime("%Y-%m-%d")
                            urls = []
                            for foto in uploaded_photos:
                                link = upload_to_imgbb(foto)
                                urls.append(link)
                                
                            while len(urls) < 3:
                                urls.append("")
                                
                            client.open(NAMA_SPREADSHEET).worksheet("Galeri_Portofolio").append_row([ts, st.session_state.asal_sekolah if st.session_state.asal_sekolah else "Pengawas Pusat", desc_keg, urls[0], urls[1], urls[2]])
                            st.success("🎉 Foto kegiatan berhasil tayang di Beranda Publik!")
                            st.balloons()
            else:
                st.error("⚠️ Mohon isi deskripsi dan pilih minimal 1 foto.")

# --- SISA MENU PRIVATE (SAMA SEPERTI SEBELUMNYA) ---
elif sub_menu == "Dashboard Admin":
    st.title("📊 Panel Kontrol Utama Pengawas")
    st.write(f"Selamat bertugas kembali, **{st.session_state.user_name}**.")

elif sub_menu == "Cek Artefak Sekolah":
    st.title("🛡️ Pemeriksaan Portofolio")
    df_art = load_data("Artefak_Portofolio")
    if not df_art.empty:
        df_pending = df_art[df_art['Status'].isin(['Menunggu Validasi', 'Perlu Revisi ♻️'])]
        if not df_pending.empty:
            st.dataframe(df_pending[['Timestamp', 'Nama_Sekolah', 'Nama_Tugas', 'Status']], use_container_width=True)
            with st.form("form_nilai"):
                baris_terpilih = st.selectbox("Pilih Dokumen", df_pending.apply(lambda x: f"{x['Timestamp']} | {x['Nama_Sekolah']} | {x['Nama_Tugas']}", axis=1))
                status_baru = st.radio("Keputusan Akhir", ["Disetujui ✅", "Perlu Revisi ♻️"])
                catatan = st.text_area("Catatan Pengawas")
                if st.form_submit_button("Simpan Keputusan", type="primary"):
                    ts_pilih, sekolah_pilih = baris_terpilih.split(" | ")[0], baris_terpilih.split(" | ")[1]
                    sheet_art = client.open(NAMA_SPREADSHEET).worksheet("Artefak_Portofolio")
                    records = sheet_art.get_all_records()
                    for idx, row in enumerate(records):
                        if str(row.get('Timestamp')) == str(ts_pilih) and str(row.get('Nama_Sekolah')) == str(sekolah_pilih):
                            sheet_art.update_cell(idx + 2, 5, status_baru)
                            sheet_art.update_cell(idx + 2, 6, catatan)
                            st.success("Tersimpan!")
                            st.rerun()

elif sub_menu == "Dashboard Kepala Sekolah":
    st.title(f"🏛️ Dasbor Manajerial - {st.session_state.asal_sekolah}")
    df_saya = load_data("Artefak_Portofolio")
    if not df_saya.empty:
        df_saya = df_saya[df_saya['Nama_Sekolah'] == st.session_state.asal_sekolah]
        st.dataframe(df_saya[['Nama_Tugas', 'Status', 'Catatan_Pengawas']], use_container_width=True)

elif sub_menu == "Pakta Integritas & Pengesahan":
    st.title("📜 Pengesahan Digital Pimpinan")
    df_sah = load_data("Pengesahan")
    if not df_sah.empty and st.session_state.asal_sekolah in df_sah['Asal_Sekolah'].values:
        st.markdown("""<div style='background-color: #d1fae5; padding: 25px; border-radius: 12px; border-left: 8px solid #10b981;'><h3 style='color: #065f46; margin-top:0;'>✅ Pengesahan Selesai</h3></div>""", unsafe_allow_html=True)
    else:
        setuju = st.checkbox("Saya menyetujui pakta integritas ini.")
        if st.button("🔒 Klik Sekali untuk Sahkan Permanen", type="primary", disabled=not setuju):
            client.open(NAMA_SPREADSHEET).worksheet("Pengesahan").append_row([datetime.datetime.now().strftime("%Y-%m-%d"), st.session_state.asal_sekolah, st.session_state.user_name])
            st.rerun()

elif sub_menu == "Dashboard Operator":
    st.title(f"🔧 Dasbor Teknis - {st.session_state.asal_sekolah}")
    st.warning("⚠️ Dokumen wajib di-kompres di bawah batas maksimal 3 MB per file!")

elif sub_menu == "Upload Artefak":
    st.title("📤 Unggah Berkas Tagihan")
    df_tag = load_data("Tagihan_Tugas")
    daftar = df_tag["Nama_Tugas"].tolist() if not df_tag.empty else ["Kosong"]
    with st.form("f_up"):
        tugas = st.selectbox("Pilih Tagihan", daftar)
        file_art = st.file_uploader("Upload Dokumen (MAKS 3 MB)")
        if st.form_submit_button("Kirim Dokumen"):
            if file_art and file_art.size <= 3 * 1024 * 1024 and client:
                sheet_art = client.open(NAMA_SPREADSHEET).worksheet("Artefak_Portofolio")
                records = sheet_art.get_all_records()
                df_cek = pd.DataFrame(records)
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if not df_cek.empty and len(df_cek[(df_cek['Nama_Sekolah'] == st.session_state.asal_sekolah) & (df_cek['Nama_Tugas'] == tugas)]) > 0:
                    for idx, row in enumerate(records):
                        if str(row.get('Nama_Sekolah')) == str(st.session_state.asal_sekolah) and str(row.get('Nama_Tugas')) == str(tugas):
                            sheet_art.update_cell(idx + 2, 4, "File_Revisi_Terkumpul")
                            sheet_art.update_cell(idx + 2, 5, "Menunggu Validasi")
                            st.success("✅ File lama berhasil ditimpa dengan revisi!")
                            break
                else:
                    sheet_art.append_row([ts, st.session_state.asal_sekolah, tugas, "File_Baru_Masuk", "Menunggu Validasi", ""])
                    st.success("✅ Terkirim!")

else:
    st.title(sub_menu)
