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
# 1. PAGE CONFIGURATION & PREMIUM CSS
# ==========================================
st.set_page_config(page_title="GIPANG M3 BANTEN", page_icon="🏫", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
    html { scroll-behavior: smooth; }
    body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
        background: linear-gradient(180deg, #eef5ff 0%, #ffffff 400px, #ffffff 100%); 
        font-family: 'Poppins', sans-serif !important; 
        color: #0B1F52; 
    }
    .premium-navbar { display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); padding: 12px 40px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.5); box-shadow: 0 4px 20px rgba(11, 31, 82, 0.04); margin-bottom: 25px; }
    .nav-brand { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 22px; color: #0B1F52; }
    .nav-brand span { color: #1D4ED8; }
    .tagline-badge { background-color: #1D4ED8; color: white; padding: 6px 16px; border-radius: 30px; font-size: 13px; font-weight: 600; display: inline-block; margin-bottom: 15px; }
    .hero-h1 { font-size: 45px; font-weight: 800; color: #0B1F52; line-height: 1.15; margin: 0 0 10px 0; }
    .hero-h1 span { color: #1D4ED8; }
    .saas-card { background: white; border-radius: 20px; padding: 24px; border: 1px solid #e2e8f0; box-shadow: 0 10px 30px rgba(11, 31, 82, 0.02); transition: all 0.4s ease; height: 100%; }
    .saas-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(11, 31, 82, 0.06); border-color: #60a5fa; }
    .icon-box { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-bottom: 12px; }
    .stButton button { border-radius: 10px !important; font-weight: 600 !important; }
    .btn-download { background-color: #1D4ED8; color: white !important; display: block; text-align: center; padding: 8px; border-radius: 8px; font-weight: 600; text-decoration: none; margin-top: 15px; transition: 0.3s; }
    .btn-download:hover { background-color: #1e3a8a; }
    .status-badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. STATE INITIALIZATION & DATABASE
# ==========================================
for key in ["logged_in", "show_login", "show_register"]:
    if key not in st.session_state: st.session_state[key] = False
if "user_role" not in st.session_state: st.session_state.user_role = "Public"
if "user_name" not in st.session_state: st.session_state.user_name = "Guest"
if "asal_sekolah" not in st.session_state: st.session_state.asal_sekolah = ""

NAMA_SPREADSHEET = "Database_Portofolio_Pengawas"

@st.cache_resource
def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp" not in st.secrets or "kunci_json" not in st.secrets["gcp"]:
            return None, "Kunci Secrets GCP belum disetting."
        kunci_mentah = st.secrets["gcp"]["kunci_json"]
        import ast
        try: creds_dict = json.loads(kunci_mentah, strict=False)
        except: creds_dict = ast.literal_eval(kunci_mentah.replace('\n', ''))
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds), "Sukses"
    except Exception as e:
        return None, f"Error: {str(e)}"

client, conn_status = get_gspread_client()

def load_data(sheet_name):
    if client:
        try: return pd.DataFrame(client.open(NAMA_SPREADSHEET).worksheet(sheet_name).get_all_records())
        except: return pd.DataFrame()
    return pd.DataFrame()

# Mesin Upload Gambar (ImgBB)
def upload_to_imgbb(image_file):
    try:
        if "imgbb" in st.secrets and "api_key" in st.secrets["imgbb"]:
            res = requests.post("https://api.imgbb.com/1/upload", data={
                "key": st.secrets["imgbb"]["api_key"], 
                "image": base64.b64encode(image_file.getvalue()).decode("utf-8")
            })
            if res.status_code == 200: return res.json()['data']['url'], "OK"
        return "", "Error Upload"
    except: return "", "Error"

# Mesin Parser Google Drive Link
def auto_convert_drive_url(url):
    if not url or not isinstance(url, str): return ""
    url = url.strip()
    if "drive.google.com" in url:
        if "/file/d/" in url:
            parts = url.split("/file/d/")
            if len(parts) > 1:
                file_id = parts[1].split("/")[0].split("?")[0]
                return f"https://drive.google.com/uc?id={file_id}"
        elif "id=" in url:
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            if "id" in qs: return f"https://drive.google.com/uc?id={qs['id'][0]}"
    return url

# ==========================================
# 3. PUBLIC VIEW & AUTHENTICATION
# ==========================================
if not st.session_state.logged_in:
    
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
        </div>
    """, unsafe_allow_html=True)

    col_nav1, col_nav2, col_nav3 = st.columns([7, 1.2, 1.5])
    with col_nav2:
        if st.button("🔒 Masuk", use_container_width=True):
            st.session_state.show_login = True; st.session_state.show_register = False; st.rerun()
    with col_nav3:
        if st.button("🚀 Request Akses", type="primary", use_container_width=True):
            st.session_state.show_register = True; st.session_state.show_login = False; st.rerun()

    # --- POPUPS ---
    if st.session_state.show_login:
        with st.container(border=True):
            st.markdown("#### 🔐 Portal Autentikasi Ruang Kerja")
            e_log = st.text_input("📧 Email")
            p_log = st.text_input("🔑 Password", type="password")
            if st.button("Login Sekarang", type="primary"):
                df_users = load_data("User")
                if not df_users.empty and 'Email' in df_users.columns:
                    match = df_users[(df_users['Email'].astype(str) == e_log) & (df_users['Password'].astype(str) == p_log)]
                    if not match.empty:
                        if match.iloc[0].get('Status_Akun', 'Pending') == 'Aktif':
                            st.session_state.logged_in = True
                            st.session_state.user_role = match.iloc[0].get('Role', 'Operator')
                            st.session_state.asal_sekolah = match.iloc[0].get('Asal_Sekolah', 'Pusat')
                            st.session_state.user_name = match.iloc[0].get('Nama_Lengkap', 'User')
                            st.session_state.show_login = False
                            st.rerun()
                        else: st.warning("⏳ Akun Anda masih PENDING. Menunggu persetujuan Pengawas.")
                    else: st.error("❌ Email atau Password salah!")
                else: st.error("Koneksi Database / User Kosong.")

    if st.session_state.show_register:
        with st.container(border=True):
            st.markdown("#### 🚀 Formulir Permohonan Akses")
            with st.form("f_reg"):
                c1, c2 = st.columns(2)
                r_nama = c1.text_input("👤 Nama Lengkap")
                r_sek = c2.text_input("🏫 Asal Sekolah")
                r_em = st.text_input("📧 Alamat Email")
                c3, c4 = st.columns(2)
                r_role = c3.selectbox("💼 Role", ["Kepala Sekolah", "Operator"])
                r_pass = c4.text_input("🔑 Password (Wajib 1 Kapital & 1 Angka)", type="password")
                if st.form_submit_button("Daftar", type="primary"):
                    if all([r_nama, r_sek, r_em, r_pass]):
                        if any(c.isupper() for c in r_pass) and any(c.isdigit() for c in r_pass) and len(r_pass) >= 6:
                            if client:
                                client.open(NAMA_SPREADSHEET).worksheet("User").append_row([r_nama, r_sek, r_em, r_role, r_pass, "Pending"])
                                st.success("✅ Pendaftaran Berhasil! Menunggu validasi Admin.")
                            else: st.error("Database terputus.")
                        else: st.error("❌ Password WAJIB min 6 karakter, 1 Huruf Kapital & 1 Angka!")
                    else: st.error("⚠️ Lengkapi seluruh kolom!")

    # --- KONTEN BERANDA ---
    st.markdown("<hr style='opacity:0.2;'>", unsafe_allow_html=True)
    c_h1, c_h2 = st.columns([1.3, 1])
    with c_h1:
        st.markdown("<div class='tagline-badge'>💻 Platform Pengawas Sekolah Modern</div><div class='hero-h1'>GIPANG <span>M3</span> BANTEN</div><div class='hero-sub'>Gerakan Inovatif Pendampingan Memantau, Mengevaluasi, Menilai Bantuan Teknologi</div><div class='hero-desc'>Platform digital untuk memudahkan pengawas sekolah dalam mengumpulkan, memantau, mengevaluasi, dan menilai portofolio artefak dari sekolah binaan secara transparan, dan terstruktur.</div>", unsafe_allow_html=True)
    with c_h2:
        st.markdown("""<div class='mockup-container'><div style='background: white; border: 12px solid #1e293b; border-bottom-width: 24px; border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(11,31,82,0.25); overflow: hidden;'><div style='background: #f8fafc; padding: 12px; text-align: left; font-size: 11px; border-bottom: 1px solid #e2e8f0; font-weight: 600;'>📊 Dashboard Workspace - Pengawas Sekolah Banten</div><div style='padding: 20px; background: white; height: 210px; text-align: left;'><div style='display: flex; gap: 10px; margin-bottom: 15px;'><div style='flex:1; background:#eff6ff; padding: 10px; border-radius: 8px; border-left: 4px solid #1D4ED8;'><small style='color:#64748b;'>Sekolah Binaan</small><br><b style='font-size: 16px; color:#0B1F52;'>24</b></div><div style='flex:1; background:#f0fdf4; padding: 10px; border-radius: 8px; border-left: 4px solid #10b981;'><small style='color:#64748b;'>Diterima</small><br><b style='font-size: 16px; color:#065f46;'>156</b></div></div></div></div></div>""", unsafe_allow_html=True)

    st.markdown("<div id='fitur'></div><br>", unsafe_allow_html=True)
    r_f1, r_f2, r_f3 = st.columns(3)
    r_f1.markdown("<div class='saas-card'><div class='icon-box' style='background:#eff6ff; color:#1D4ED8;'>📤</div><h5>Pengumpulan Artefak</h5><p style='font-size:13px; color:#64748b;'>Upload berkas portofolio aman maksimal 3MB per file.</p></div>", unsafe_allow_html=True)
    r_f2.markdown("<div class='saas-card'><div class='icon-box' style='background:#f0fdf4; color:#10b981;'>🛡️</div><h5>Validasi & Evaluasi</h5><p style='font-size:13px; color:#64748b;'>Tinjauan kualitas real-time dan anti duplikasi file.</p></div>", unsafe_allow_html=True)
    r_f3.markdown("<div class='saas-card'><div class='icon-box' style='background:#f5f3ff; color:#7c3aed;'>📥</div><h5>Download Materi</h5><p style='font-size:13px; color:#64748b;'>Unduh materi pembinaan dan Juknis dari Pengawas.</p></div>", unsafe_allow_html=True)

    st.markdown("<div id='portofolio'></div><br><hr style='opacity:0.5;'><br><h4>📸 Galeri Portofolio Kegiatan</h4>", unsafe_allow_html=True)
    df_gal = load_data("Galeri_Portofolio")
    if not df_gal.empty and 'Link_Foto1' in df_gal.columns:
        df_gal_valid = df_gal[(df_gal['Link_Foto1'].astype(str) != "") & (df_gal['Link_Foto1'].astype(str) != "nan")]
        if not df_gal_valid.empty:
            gal_cols = st.columns(3)
            for i, row in df_gal_valid.iterrows():
                with gal_cols[i % 3]:
                    with st.container(border=True):
                        foto_u = str(row.get('Link_Foto1', '')).strip()
                        if foto_u: st.image(foto_u, caption=f"🏫 {row.get('Asal_Sekolah', '')}", use_container_width=True)
                        sub_img_list = [str(row.get(c, '')).strip() for c in ['Link_Foto2', 'Link_Foto3'] if str(row.get(c, '')).strip() not in ['', 'nan']]
                        if sub_img_list:
                            sub_cols = st.columns(len(sub_img_list))
                            for idx, s_url in enumerate(sub_img_list):
                                with sub_cols[idx]: st.image(s_url, use_container_width=True)
                        st.write(f"📝 *{row.get('Deskripsi_Kegiatan', '')}*")
        else: st.info("Belum ada data foto portofolio valid.")
    else: st.info("Belum ada portofolio kegiatan.")

    st.markdown("<div id='materi'></div><br><hr style='opacity:0.5;'><br><h4>📥 Pusat Download Materi Publik</h4>", unsafe_allow_html=True)
    df_mat = load_data("Materi_Publik")
    if not df_mat.empty and 'Judul' in df_mat.columns:
        mat_cols = st.columns(3)
        for i, row in df_mat.iterrows():
            with mat_cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"### {row.get('Icon', '📄')} {row.get('Judul', '')}")
                    st.write(f"🏷️ {row.get('Kategori', '')} | 📅 {row.get('Tanggal', '')}")
                    link_dl = str(row.get('Link_Download', '#')).strip()
                    if link_dl not in ['#', '', 'nan']:
                        if not link_dl.startswith('http'): link_dl = 'https://' + link_dl
                        st.link_button("⬇️ Download Materi", link_dl, use_container_width=True)
                    else:
                        st.button("⚠️ Tautan Belum Tersedia", disabled=True, use_container_width=True)
    else: st.info("Belum ada materi publik yang diterbitkan.")

else:
    # ==========================================
    # 4. PRIVATE VIEW (WORKSPACE ROUTING)
    # ==========================================
    st.sidebar.markdown(f"""
        <div style='background-color: #f0fdf4; padding: 12px; border-radius: 8px; border: 1px solid #bbf7d0; margin-bottom: 15px;'>
            <small style='color: #166534; font-weight: 600;'>🔑 USER LOGIN:</small><br>
            <b style='color: #0b1f52; font-size: 13px;'>{st.session_state.user_name}</b><br>
            <small style='color:#475569;'>{st.session_state.asal_sekolah}</small><br>
            <span style='background: #1D4ED8; color: white; font-size: 10px; padding: 2px 8px; border-radius: 10px;'>{st.session_state.user_role}</span>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.user_role == "Admin":
        menu = st.sidebar.radio("Navigasi Pengawas", ["Dashboard Admin", "Cek Artefak Sekolah", "Sistem Reminder Email", "Validasi Akun Baru", "Manajemen Tagihan Tugas", "Upload Materi Pusat", "Manajemen Jadwal Pendampingan", "Manajemen Galeri Publik", "Upload Galeri Kegiatan", "🚪 Keluar"])
    elif st.session_state.user_role == "Kepala Sekolah":
        menu = st.sidebar.radio("Navigasi Kepsek", ["Dashboard Kepala Sekolah", "Booking Jadwal Pendampingan", "Pakta Integritas & Pengesahan", "Layanan Konsultasi", "Upload Galeri Kegiatan", "🚪 Keluar"])
    elif st.session_state.user_role == "Operator":
        menu = st.sidebar.radio("Navigasi Operator", ["Dashboard Operator", "Upload Artefak", "Riwayat & Perbaikan", "Upload Galeri Kegiatan", "🚪 Keluar"])

    if menu == "🚪 Keluar":
        st.session_state.logged_in = False; st.rerun()

    # --- [A] FITUR UPLOAD GALERI (DUAL MODE, SEMUA ROLE) ---
    if menu == "Upload Galeri Kegiatan":
        st.title("📸 Upload Dokumentasi Foto Kegiatan")
        with st.container(border=True):
            metode = st.radio("Metode Upload:", ["📂 Unggah File (JPG/PNG)", "🔗 Gunakan Link Google Drive"])
            desc = st.text_input("Judul / Deskripsi Singkat")
            if metode == "📂 Unggah File (JPG/PNG)":
                fotos = st.file_uploader("Pilih Maks 3 File (@2MB)", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
                if st.button("🚀 Publish (Upload)", type="primary"):
                    if desc and fotos:
                        if len(fotos) > 3: st.error("Maksimal 3 foto!")
                        elif not all(f.size <= 2*1024*1024 for f in fotos): st.error("Ada file melebihi 2 MB!")
                        elif client:
                            with st.spinner("Mengunggah aman..."):
                                urls = []
                                for f in fotos:
                                    link, msg = upload_to_imgbb(f)
                                    if link: urls.append(link)
                                if len(urls) > 0:
                                    while len(urls) < 3: urls.append("")
                                    client.open(NAMA_SPREADSHEET).worksheet("Galeri_Portofolio").append_row([datetime.datetime.now().strftime("%Y-%m-%d"), st.session_state.asal_sekolah, desc, urls[0], urls[1], urls[2]])
                                    st.success("🎉 Berhasil Tayang di Galeri!")
                                else: st.error("Gagal diproses. Cek API Key Secrets.")
            else:
                l1 = st.text_input("Link Foto 1 (Wajib)")
                l2 = st.text_input("Link Foto 2 (Opsional)")
                l3 = st.text_input("Link Foto 3 (Opsional)")
                if st.button("🚀 Publish (Google Drive)", type="primary"):
                    if desc and l1:
                        client.open(NAMA_SPREADSHEET).worksheet("Galeri_Portofolio").append_row([datetime.datetime.now().strftime("%Y-%m-%d"), st.session_state.asal_sekolah, desc, auto_convert_drive_url(l1), auto_convert_drive_url(l2), auto_convert_drive_url(l3)])
                        st.success("🎉 Tautan terkonversi dan disematkan!")

    # --- [B] FITUR ADMIN (PENGAWAS) ---
    elif menu == "Dashboard Admin":
        st.title("📊 Panel Kontrol Utama Pengawas")
        df_art = load_data("Artefak_Portofolio")
        pending = len(df_art[df_art['Status'] == 'Menunggu Validasi']) if not df_art.empty and 'Status' in df_art.columns else 0
        st.metric("Tugas Menunggu Pemeriksaan", f"{pending} Dokumen")
        if not df_art.empty and 'Timestamp' in df_art.columns: st.dataframe(df_art.tail(10), use_container_width=True)

    elif menu == "Cek Artefak Sekolah":
        st.title("🛡️ Pemeriksaan Portofolio")
        df_art = load_data("Artefak_Portofolio")
        if not df_art.empty and 'Status' in df_art.columns:
            df_pending = df_art[df_art['Status'].isin(['Menunggu Validasi', 'Perlu Revisi ♻️'])]
            if not df_pending.empty:
                st.dataframe(df_pending, use_container_width=True)
                with st.form("f_n"):
                    baris = st.selectbox("Pilih Dokumen", df_pending.apply(lambda x: f"{x.get('Timestamp')} | {x.get('Nama_Sekolah')}", axis=1).tolist())
                    stat_baru = st.radio("Keputusan", ["Disetujui ✅", "Perlu Revisi ♻️"])
                    catatan = st.text_area("Catatan")
                    if st.form_submit_button("Simpan Keputusan"):
                        ts, sek = baris.split(" | ")[0], baris.split(" | ")[1]
                        sheet_art = client.open(NAMA_SPREADSHEET).worksheet("Artefak_Portofolio")
                        for idx, row in enumerate(sheet_art.get_all_records()):
                            if str(row.get('Timestamp')) == ts and str(row.get('Nama_Sekolah')) == sek:
                                sheet_art.update_cell(idx + 2, 5, stat_baru)
                                sheet_art.update_cell(idx + 2, 6, catatan)
                                st.success("Tersimpan!")
                                st.rerun()
            else: st.success("Semua dokumen telah diperiksa.")

    elif menu == "Manajemen Jadwal Pendampingan":
        st.title("🗓️ Manajemen Kalender Pendampingan")
        st.write("Setujui atau tolak permintaan kunjungan/pendampingan dari Kepala Sekolah.")
        df_jadwal = load_data("Jadwal_Pendampingan")
        if not df_jadwal.empty and 'Status' in df_jadwal.columns:
            df_pend = df_jadwal[df_jadwal['Status'] == 'Menunggu Persetujuan']
            st.markdown("### Daftar Ajuan Masuk")
            if not df_pend.empty:
                st.dataframe(df_pend, use_container_width=True)
                with st.form("f_acc_jadwal"):
                    pilihan = st.selectbox("Pilih Ajuan", df_pend.apply(lambda x: f"{x.get('Timestamp')} | {x.get('Asal_Sekolah')} | {x.get('Tanggal_Booking')}", axis=1).tolist())
                    keputusan = st.radio("Persetujuan", ["Disetujui ✅", "Ditolak ❌"])
                    if st.form_submit_button("Simpan Status"):
                        ts = pilihan.split(" | ")[0]
                        sheet_j = client.open(NAMA_SPREADSHEET).worksheet("Jadwal_Pendampingan")
                        for idx, row in enumerate(sheet_j.get_all_records()):
                            if str(row.get('Timestamp')) == ts:
                                sheet_j.update_cell(idx + 2, 5, keputusan)
                                st.success("Status jadwal diperbarui!")
                                st.rerun()
                                break
            else: st.info("Tidak ada ajuan jadwal baru.")
            
            st.markdown("### Seluruh Jadwal (Kalender Pengawas)")
            st.dataframe(df_jadwal[['Tanggal_Booking', 'Asal_Sekolah', 'Tujuan_Pendampingan', 'Status']].sort_values(by='Tanggal_Booking'), use_container_width=True)
        else: st.info("Belum ada data jadwal masuk dari Kepala Sekolah.")

    elif menu == "Manajemen Galeri Publik":
        st.title("🗑️ Hapus Galeri (Khusus Admin)")
        df_gal = load_data("Galeri_Portofolio")
        if not df_gal.empty and 'Timestamp' in df_gal.columns:
            st.dataframe(df_gal[['Timestamp', 'Asal_Sekolah', 'Deskripsi_Kegiatan']], use_container_width=True)
            with st.form("f_del"):
                pilih_gal = st.selectbox("Pilih Target Hapus", df_gal.apply(lambda x: f"{x.get('Timestamp')} | {x.get('Deskripsi_Kegiatan')}", axis=1))
                if st.form_submit_button("❌ Hapus Permanen", type="primary"):
                    ts_gal = pilih_gal.split(" | ")[0]
                    sheet_gal = client.open(NAMA_SPREADSHEET).worksheet("Galeri_Portofolio")
                    for idx, row in enumerate(sheet_gal.get_all_records()):
                        if str(row.get('Timestamp')) == ts_gal:
                            sheet_gal.delete_rows(idx + 2)
                            st.success("Dihapus!")
                            st.rerun()

    elif menu == "Sistem Reminder Email":
        st.title("🔔 Pengingat Otomatis Sekolah")
        df_tag = load_data("Tagihan_Tugas")
        df_usr = load_data("User")
        df_art = load_data("Artefak_Portofolio")
        if not df_tag.empty and not df_usr.empty:
            t_pilih = st.selectbox("Pilih Tugas", df_tag['Nama_Tugas'].tolist())
            s_sudah = df_art[df_art['Nama_Tugas'] == t_pilih]['Nama_Sekolah'].unique().tolist() if not df_art.empty else []
            s_belum = df_usr[(df_usr.get('Role', '') != 'Admin') & (df_usr.get('Status_Akun', '') == 'Aktif') & (~df_usr.get('Asal_Sekolah', '').isin(s_sudah))]
            if not s_belum.empty:
                d_email = ",".join(s_belum['Email'].astype(str).tolist())
                st.markdown(f'<a href="mailto:?bcc={d_email}&subject=REMINDER" target="_blank"><button style="background-color: #d93025; color: white; border: none; padding: 10px 20px; border-radius: 8px;">📧 Kirim Email Massal</button></a>', unsafe_allow_html=True)

    elif menu == "Upload Materi Pusat":
        st.title("📤 Publikasi Juknis & Materi Download")
        with st.form("f_mat"):
            jm = st.text_input("Judul Materi")
            link_dl = st.text_input("🔗 Link Google Drive (Pastikan Public)")
            if st.form_submit_button("Publish"):
                if jm and link_dl:
                    client.open(NAMA_SPREADSHEET).worksheet("Materi_Publik").append_row([jm, "Regulasi", datetime.datetime.now().strftime("%d %b %Y"), "File Tautan", "🆕", link_dl])
                    st.success("Tersimpan!")

    elif menu == "Validasi Akun Baru":
        st.title("🛡️ Validasi Akun")
        df_usr = load_data("User")
        if not df_usr.empty and 'Status_Akun' in df_usr.columns:
            df_pend = df_usr[df_usr['Status_Akun'] == 'Pending']
            if not df_pend.empty:
                with st.form("f_acc"):
                    em = st.selectbox("Pilih Email", df_pend['Email'].tolist())
                    if st.form_submit_button("✅ Aktifkan"):
                        s_usr = client.open(NAMA_SPREADSHEET).worksheet("User")
                        cell = s_usr.find(em)
                        if cell:
                            s_usr.update_cell(cell.row, 6, "Aktif")
                            st.success("Aktif!")
                            st.rerun()

    elif menu == "Manajemen Tagihan Tugas":
        st.title("📋 Buat Tugas Baru")
        with st.form("f_tugas"):
            nt = st.text_input("Judul Tugas")
            if st.form_submit_button("Terbitkan"):
                if nt:
                    client.open(NAMA_SPREADSHEET).worksheet("Tagihan_Tugas").append_row([nt, "Umum", "-", "-"])
                    st.success("Tugas diterbitkan!")

    elif menu == "Respon Konsultasi":
        st.title("💬 Jawaban Keluhan")
        df_k = load_data("Konsultasi_Sekolah")
        if not df_k.empty and 'Status' in df_k.columns:
            df_in = df_k[df_k['Status'] == 'Menunggu Respon']
            if not df_in.empty:
                with st.form("f_resp"):
                    pilih = st.selectbox("Pilih", df_in.apply(lambda x: f"{x.get('Timestamp')} | {x.get('Asal_Sekolah')}", axis=1))
                    tang = st.text_area("Tanggapan")
                    if st.form_submit_button("Kirim Jawaban"):
                        ts = pilih.split(" | ")[0]
                        s_k = client.open(NAMA_SPREADSHEET).worksheet("Konsultasi_Sekolah")
                        for idx, row in enumerate(s_k.get_all_records()):
                            if str(row.get('Timestamp')) == ts:
                                s_k.update_cell(idx + 2, 6, tang)
                                s_k.update_cell(idx + 2, 7, "Dijawab ✅")
                                st.success("Terkirim!")
                                st.rerun()

    # --- [C] FITUR KEPALA SEKOLAH ---
    elif menu == "Dashboard Kepala Sekolah":
        st.title(f"🏛️ Dasbor Manajerial - {st.session_state.asal_sekolah}")
        df_tag = load_data("Tagihan_Tugas")
        total = len(df_tag) if not df_tag.empty else 0
        df_art = load_data("Artefak_Portofolio")
        df_saya = pd.DataFrame()
        if not df_art.empty and 'Nama_Sekolah' in df_art.columns:
            df_saya = df_art[df_art['Nama_Sekolah'] == st.session_state.asal_sekolah]
        disetujui = len(df_saya[df_saya['Status'] == 'Disetujui ✅']) if not df_saya.empty and 'Status' in df_saya.columns else 0
        if total > 0: st.progress(min(disetujui / total, 1.0))
        st.markdown("### 📋 Detail Status Artefak Anda")
        if not df_saya.empty: st.dataframe(df_saya[['Nama_Tugas', 'Status', 'Catatan_Pengawas']], use_container_width=True)

    elif menu == "Booking Jadwal Pendampingan":
        st.title("📅 Booking Jadwal Kunjungan/Pendampingan Pengawas")
        st.write("Silakan ajukan tanggal kunjungan. Jadwal yang sudah dibooking oleh sekolah lain atau telah disetujui akan terlihat di tabel bawah ini.")
        
        df_jadwal = load_data("Jadwal_Pendampingan")
        booked_dates = []
        if not df_jadwal.empty and 'Tanggal_Booking' in df_jadwal.columns:
            st.markdown("### 🗓️ Kalender Jadwal Terkini (Seluruh Sekolah)")
            st.dataframe(df_jadwal[['Tanggal_Booking', 'Asal_Sekolah', 'Status']].sort_values(by='Tanggal_Booking'), use_container_width=True)
            # Kumpulkan semua tanggal yang statusnya Pending atau Disetujui (tidak ditolak)
            booked_dates = df_jadwal[df_jadwal['Status'].isin(['Menunggu Persetujuan', 'Disetujui ✅'])]['Tanggal_Booking'].astype(str).tolist()
        else:
            st.info("Belum ada sekolah yang melakukan booking jadwal.")

        st.markdown("### ✍️ Ajukan Jadwal Sekolah Anda")
        with st.form("form_booking"):
            tgl = st.date_input("Pilih Tanggal Pendampingan")
            tujuan = st.text_input("Tujuan / Agenda Pendampingan (Misal: Review RKT/KTSP)")
            
            if st.form_submit_button("Ajukan Jadwal ke Pengawas", type="primary"):
                if tgl.strftime("%Y-%m-%d") in booked_dates:
                    st.error("❌ GAGAL: Tanggal ini sudah dibooking oleh sekolah lain atau sedang menunggu persetujuan. Silakan pilih tanggal yang kosong.")
                elif tujuan and client:
                    client.open(NAMA_SPREADSHEET).worksheet("Jadwal_Pendampingan").append_row(
                        [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tgl.strftime("%Y-%m-%d"), st.session_state.asal_sekolah, tujuan, "Menunggu Persetujuan"]
                    )
                    st.success("✅ Jadwal berhasil diajukan! Silakan tunggu persetujuan Ibu Pengawas.")
                    st.rerun()
                else:
                    st.error("⚠️ Mohon isi Tujuan / Agenda pendampingan.")

    elif menu == "Pakta Integritas & Pengesahan":
        st.title("📜 Pengesahan Digital Pimpinan")
        df_sah = load_data("Pengesahan")
        if not df_sah.empty and st.session_state.asal_sekolah in df_sah['Asal_Sekolah'].values:
            st.success("✅ Pengesahan Selesai & Terkunci Permanen.")
        else:
            setuju = st.checkbox("Saya menyetujui pakta integritas ini.")
            if st.button("🔒 Klik Sekali untuk Sahkan", type="primary", disabled=not setuju):
                client.open(NAMA_SPREADSHEET).worksheet("Pengesahan").append_row([datetime.datetime.now().strftime("%Y-%m-%d"), st.session_state.asal_sekolah, st.session_state.user_name])
                st.rerun()

    elif menu == "Layanan Konsultasi":
        st.title("💬 Kotak Keluhan & Arahan Pengawas")
        with st.form("f_kel"):
            top = st.text_input("Topik")
            psn = st.text_area("Detail")
            if st.form_submit_button("Kirim"):
                if top and psn:
                    client.open(NAMA_SPREADSHEET).worksheet("Konsultasi_Sekolah").append_row([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state.asal_sekolah, st.session_state.user_name, top, psn, "", "Menunggu Respon"])
                    st.success("Terkirim!")
        df_k = load_data("Konsultasi_Sekolah")
        if not df_k.empty and 'Asal_Sekolah' in df_k.columns:
            df_saya = df_k[df_k['Asal_Sekolah'] == st.session_state.asal_sekolah]
            for idx, row in df_saya.iterrows(): st.info(f"**Topik:** {row.get('Topik_Keluhan')}\n\n**Arahan:** {row.get('Tanggapan_Pengawas', '⏳ Belum dibalas')}")

    # --- [D] FITUR OPERATOR ---
    elif menu == "Dashboard Operator":
        st.title(f"🔧 Dasbor Teknis - {st.session_state.asal_sekolah}")
        st.warning("⚠️ Dokumen wajib di-kompres di bawah batas maksimal 3 MB per file!")

    elif menu == "Upload Artefak":
        st.title("📤 Unggah Berkas Tagihan")
        df_tag = load_data("Tagihan_Tugas")
        daftar = df_tag["Nama_Tugas"].tolist() if not df_tag.empty else ["Kosong"]
        with st.form("f_up"):
            st.info("💡 Jika dokumen Anda direvisi, upload ulang di sini. Sistem akan **MENIMPA** file lama (Anti-Double).")
            tugas = st.selectbox("Pilih Tagihan", daftar)
            file_art = st.file_uploader("Upload Dokumen (MAKS 3 MB)")
            if st.form_submit_button("Kirim Dokumen"):
                if file_art and file_art.size <= 3 * 1024 * 1024:
                    sheet_art = client.open(NAMA_SPREADSHEET).worksheet("Artefak_Portofolio")
                    recs = sheet_art.get_all_records()
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    found = False
                    for idx, row in enumerate(recs):
                        if str(row.get('Nama_Sekolah')) == st.session_state.asal_sekolah and str(row.get('Nama_Tugas')) == tugas:
                            sheet_art.update_cell(idx + 2, 1, ts)
                            sheet_art.update_cell(idx + 2, 4, "File_Revisi_Terkumpul")
                            sheet_art.update_cell(idx + 2, 5, "Menunggu Validasi")
                            sheet_art.update_cell(idx + 2, 6, "")
                            found = True; break
                    if not found: sheet_art.append_row([ts, st.session_state.asal_sekolah, tugas, "File_Baru_Masuk", "Menunggu Validasi", ""])
                    st.success("✅ Berkas berhasil dikirim/ditimpa!")
                else: st.error("Pilih file (Maks 3 MB).")

    elif menu == "Riwayat & Perbaikan":
        st.title("♻️ Log Catatan Perbaikan & Revisi")
        df_art = load_data("Artefak_Portofolio")
        if not df_art.empty and 'Status' in df_art.columns and 'Nama_Sekolah' in df_art.columns:
            df_rev = df_art[(df_art['Nama_Sekolah'] == st.session_state.asal_sekolah) & (df_art['Status'] == 'Perlu Revisi ♻️')]
            if not df_rev.empty:
                for idx, row in df_rev.iterrows(): st.error(f"❌ **Tugas:** {row.get('Nama_Tugas')}\n\n**Catatan Pengawas:** {row.get('Catatan_Pengawas')}")
            else: st.success("🎉 Bersih! Tidak ada tugas Anda yang berstatus revisi.")
