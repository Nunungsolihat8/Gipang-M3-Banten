import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import json

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
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    .stButton button { border-radius: 10px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONEKSI GOOGLE SHEETS (ANTI-KESELEK)
# ==========================================
NAMA_SPREADSHEET = "Database_Portofolio_Pengawas"

@st.cache_resource
def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp" not in st.secrets or "kunci_json" not in st.secrets["gcp"]:
            return None, "Kunci Secrets GCP belum disetting di Streamlit."
            
        # Perbaikan Khusus: Tambahkan strict=False agar aman dari JSONDecodeError (Karakter Tersembunyi)
        kunci_mentah = st.secrets["gcp"]["kunci_json"]
        
        # Bersihkan string yang mungkin membawa newline tidak sah akibat copy-paste
        import ast
        try:
            creds_dict = json.loads(kunci_mentah, strict=False)
        except:
            # Plan B: Jika json.loads gagal, gunakan pemrosesan literal yang lebih kuat
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

# --- POPUP FORM: LOGIN ---
if st.session_state.show_login and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown("#### 🔐 Portal Autentikasi Ruang Kerja")
        
        if client is None:
            st.error(f"Koneksi Database Terputus! {conn_status}")
            
        st.info("Silakan login menggunakan Email dan Password yang telah terdaftar.")
        e_login = st.text_input("📧 Alamat Email")
        p_login = st.text_input("🔑 Password", type="password")
        
        if st.button("Login Sekarang", type="primary"):
            if client:
                df_users = load_data("User")
                if not df_users.empty:
                    user_match = df_users[(df_users['Email'].astype(str) == e_login) & (df_users['Password'].astype(str) == p_login)]
                    if not user_match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_role = user_match.iloc[0]['Role']
                        st.session_state.user_name = f"{user_match.iloc[0]['Nama_Lengkap']} - {user_match.iloc[0]['Asal_Sekolah']}"
                        st.session_state.show_login = False
                        st.rerun()
                    else:
                        st.error("❌ Email atau Password salah!")
                else:
                    st.error("⚠️ Database User kosong atau gagal dimuat dari Google Sheets.")
            else:
                st.error("Gagal terhubung ke database. Harap cek pengaturan Secrets.")

# --- POPUP FORM: REGISTRASI (REQUEST AKSES) ---
if st.session_state.show_register and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown("#### 🚀 Formulir Permohonan Akses (Pendaftaran)")
        st.write("Silakan isi data diri dan sekolah Anda dengan lengkap.")
        
        if client is None:
            st.error(f"Koneksi Database Terputus! {conn_status}")
            
        with st.form("form_registrasi"):
            col_reg1, col_reg2 = st.columns(2)
            reg_nama = col_reg1.text_input("👤 Nama Lengkap")
            reg_sekolah = col_reg2.text_input("🏫 Asal Sekolah")
            
            reg_email = st.text_input("📧 Alamat Email (Akan digunakan untuk Login)")
            
            col_reg3, col_reg4 = st.columns(2)
            reg_role = col_reg3.selectbox("💼 Pilih Role Anda", ["Kepala Sekolah", "Operator"])
            reg_pass = col_reg4.text_input("🔑 Buat Password Baru (Wajib 1 Huruf Kapital & 1 Angka)", type="password")
            
            if st.form_submit_button("Daftar Sekarang", type="primary"):
                if not all([reg_nama, reg_sekolah, reg_email, reg_pass]):
                    st.error("⚠️ Mohon lengkapi seluruh kolom pendaftaran di atas.")
                else:
                    has_upper = any(char.isupper() for char in reg_pass)
                    has_digit = any(char.isdigit() for char in reg_pass)
                    
                    if not (has_upper and has_digit and len(reg_pass) >= 6):
                        st.error("❌ PENDAFTARAN GAGAL: Password WAJIB terdiri dari minimal 6 karakter, mengandung minimal 1 Huruf Kapital, dan 1 Angka!")
                    else:
                        if client:
                            try:
                                sheet_users = client.open(NAMA_SPREADSHEET).worksheet("User")
                                sheet_users.append_row([reg_nama, reg_sekolah, reg_email, reg_role, reg_pass])
                                st.success("✅ Pendaftaran Berhasil! Silakan klik tombol 'Masuk' di atas untuk Login.")
                                st.balloons()
                            except Exception as e:
                                st.error(f"Gagal menulis ke Google Sheets. Pastikan robot sudah diundang sebagai Editor. Detail: {e}")
                        else:
                            st.error(f"Gagal terhubung ke database. Detail: {conn_status}")

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
        sub_menu = st.sidebar.radio("Menu Pengawas", ["Dashboard Admin", "Validasi Dokumen", "Upload Materi Pusat", "Log Out"])
    elif st.session_state.user_role == "Kepala Sekolah":
        sub_menu = st.sidebar.radio("Menu Kepala Sekolah", ["Dashboard Kepala Sekolah", "Monitoring Capaian", "Persetujuan Akhir", "Log Out"])
    elif st.session_state.user_role == "Operator":
        sub_menu = st.sidebar.radio("Menu Operator", ["Dashboard Operator", "Upload Artefak", "Riwayat Revisi", "Log Out"])
    else:
        sub_menu = "Beranda Publik"
        
    if sub_menu == "Log Out":
        st.session_state.logged_in = False
        st.session_state.user_role = "Public"
        st.session_state.user_name = "Guest"
        st.rerun()
else:
    sub_menu = "Beranda Publik"
    st.sidebar.info("Silakan klik tombol **🔒 Masuk** atau **🚀 Request Akses**.")

# ==========================================
# 5. HALAMAN UTAMA (PUBLIC VIEW)
# ==========================================
if sub_menu in ["Beranda Publik", "Log Out"]:
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
    row_f1.markdown("<div class='saas-card'><div class='icon-box' style='background:#eff6ff; color:#1D4ED8;'>📤</div><h5>Pengumpulan Artefak</h5></div>", unsafe_allow_html=True)
    row_f2.markdown("<div class='saas-card'><div class='icon-box' style='background:#f0fdf4; color:#10b981;'>🛡️</div><h5>Validasi & Evaluasi</h5></div>", unsafe_allow_html=True)
    row_f3.markdown("<div class='saas-card'><div class='icon-box' style='background:#f5f3ff; color:#7c3aed;'>📥</div><h5>Download Materi</h5></div>", unsafe_allow_html=True)

    st.markdown("<div id='portofolio'></div><br><hr style='opacity:0.5;'><br><h4>📋 Pengumpulan Terbaru</h4>", unsafe_allow_html=True)
    df_artefak = load_data("Artefak_Portofolio")
    if not df_artefak.empty:
        st.dataframe(df_artefak[["Nama_Sekolah", "Nama_Tugas", "Timestamp"]], use_container_width=True)
    else:
        st.info("Belum ada data artefak dari Google Sheets.")

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

# ==========================================
# 6. KONTEN PRIVATE BEDA ROLE
# ==========================================
elif sub_menu == "Dashboard Admin":
    st.title(f"📊 Panel Kontrol Utama Pengawas")
    st.markdown(f"Selamat bertugas kembali, **{st.session_state.user_name}**.")

elif sub_menu == "Upload Materi Pusat":
    st.title("📤 Publikasi Materi Instruksional Pusat")
    
    with st.form("form_materi"):
        judul_materi = st.text_input("Judul Materi")
        kategori_materi = st.selectbox("Kategori", ["Regulasi", "Modul Ajar", "Template"])
        file_materi = st.file_uploader("Upload File")
        
        if st.form_submit_button("Publikasikan ke Website"):
            if judul_materi and file_materi and client:
                sheet_materi = client.open(NAMA_SPREADSHEET).worksheet("Materi_Publik")
                tgl = datetime.datetime.now().strftime("%d %b %Y")
                ukuran = f"{round(file_materi.size / (1024*1024), 2)} MB"
                sheet_materi.append_row([judul_materi, kategori_materi, tgl, ukuran, "🆕"])
                st.success("Berhasil tersimpan ke Google Sheets! Silakan cek Beranda Publik.")
                st.balloons()
            else:
                st.error("Gagal! Pastikan file dipilih dan koneksi terhubung.")

elif sub_menu == "Dashboard Kepala Sekolah":
    st.title(f"🏛️ Ruang Kerja Manajerial")
    st.markdown(f"Selamat datang, **{st.session_state.user_name}**.")

elif sub_menu == "Dashboard Operator":
    st.title(f"🔧 Ruang Teknis Operator")
    st.markdown(f"Selamat bekerja, **{st.session_state.user_name}**.")

elif sub_menu == "Upload Artefak":
    st.title("📤 Unggah Berkas Komponen Mutu")
    
    df_tagihan = load_data("Tagihan_Tugas")
    daftar_tugas = df_tagihan["Nama_Tugas"].tolist() if not df_tagihan.empty else ["Belum ada tagihan tugas"]
    
    with st.form("form_artefak"):
        tugas = st.selectbox("Pilih Tugas yang Ingin Dikumpulkan", daftar_tugas)
        file_art = st.file_uploader("Upload Bukti Dokumen (Maks 5MB)")
        
        if st.form_submit_button("Kirim Artefak"):
            if file_art and client:
                sheet_art = client.open(NAMA_SPREADSHEET).worksheet("Artefak_Portofolio")
                tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet_art.append_row([tgl, st.session_state.user_name, tugas, "File_Terkirim", "Menunggu Validasi", ""])
                st.success("Terkirim ke Pengawas! Mohon tunggu proses validasi.")
                st.balloons()
            else:
                st.error("Pilih file terlebih dahulu.")
else:
    st.title(sub_menu)
