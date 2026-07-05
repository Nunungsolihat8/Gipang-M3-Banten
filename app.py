import streamlit as st
import pandas as pd
import datetime

# ==========================================
# 1. PREMIUM COGNITIVE COMPONENT & INTERFACE DESIGN
# ==========================================
st.set_page_config(
    page_title="GIPANG M3 BANTEN - Platform Pengawas Sekolah Modern", 
    page_icon="🏫", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
    
    html { scroll-behavior: smooth; }
    
    body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background: linear-gradient(180deg, #eef5ff 0%, #ffffff 400px, #ffffff 100%);
        font-family: 'Poppins', sans-serif !important;
        color: #0B1F52;
    }
    
    /* Top Sticky Premium Header */
    .premium-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 12px 40px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 4px 20px rgba(11, 31, 82, 0.04);
        margin-bottom: 25px;
    }
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 800;
        font-size: 22px;
        color: #0B1F52;
    }
    .nav-brand span { color: #1D4ED8; }
    
    .tagline-badge {
        background-color: #1D4ED8;
        color: white;
        padding: 6px 16px;
        border-radius: 30px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(29, 78, 216, 0.2);
    }
    
    .hero-h1 { font-size: 45px; font-weight: 800; color: #0B1F52; line-height: 1.15; margin: 0 0 10px 0; }
    .hero-h1 span { color: #1D4ED8; }
    .hero-sub { font-size: 19px; color: #0B1F52; font-weight: 600; margin-bottom: 15px; line-height: 1.3; }
    .hero-desc { font-size: 14px; color: #475569; line-height: 1.6; margin-bottom: 25px; }
    
    .mockup-container {
        position: relative;
        background: radial-gradient(circle, rgba(96,165,254,0.15) 0%, rgba(255,255,255,0) 70%);
        text-align: center;
        padding: 20px;
    }
    
    .saas-card {
        background: white;
        border-radius: 20px;
        padding: 24px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 30px rgba(11, 31, 82, 0.02);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        height: 100%;
    }
    .saas-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(11, 31, 82, 0.06);
        border-color: #60a5fa;
    }
    .icon-box {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        margin-bottom: 12px;
    }
    
    .custom-table-container { background: white; border-radius: 20px; padding: 20px; border: 1px solid #e2e8f0; }
    
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    .stButton button { border-radius: 10px !important; font-weight: 600 !important; }
    
    .btn-action-view {
        color: #1D4ED8;
        background: #eff6ff;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 600;
        text-decoration: none;
        display: inline-block;
        border: 1px solid #bfdbfe;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. STATE MANAGEMENT & SIMULASI DATABASE
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = "Public"
    st.session_state.user_name = "Guest"

# Simulasi Database Materi Publik (Akan bertambah saat Admin upload)
if "db_materi" not in st.session_state:
    st.session_state.db_materi = [
        {"judul": "Juknis Kurikulum Merdeka Banten 2026", "kategori": "Regulasi", "tanggal": "01 Jul 2026", "ukuran": "2.4 MB", "icon": "📄"},
        {"judul": "Template Instrumen SIRAJA (Excel)", "kategori": "Template", "tanggal": "02 Jul 2026", "ukuran": "1.1 MB", "icon": "📊"},
        {"judul": "Panduan Desain Backward Design", "kategori": "Modul Ajar", "tanggal": "04 Jul 2026", "ukuran": "4.5 MB", "icon": "📚"}
    ]

# TITIK JANGKAR: Beranda
st.markdown("<div id='beranda'></div>", unsafe_allow_html=True)

# ==========================================
# 3. DYNAMIC WEB STICKY NAVBAR COMPONENT
# ==========================================
st.markdown("""
    <div class='premium-navbar'>
        <div class='nav-brand'>🏛️ GIPANG <span>M3</span> BANTEN</div>
        <div style='display: flex; gap: 30px; font-weight: 500; font-size: 14px;'>
            <a href='#beranda' style='color:#1D4ED8; text-decoration:none; border-bottom:2px solid #1D4ED8; padding-bottom:4px;'>Beranda</a>
            <a href='#fitur' style='color:#475569; text-decoration:none;'>Fitur</a>
            <a href='#portofolio' style='color:#475569; text-decoration:none;'>Portofolio</a>
            <a href='#materi' style='color:#475569; text-decoration:none;'>Materi Publik</a>
        </div>
        <div style='visibility: hidden; width: 0px;'>Nav Spacer</div>
    </div>
""", unsafe_allow_html=True)

col_nav1, col_nav2, col_nav3 = st.columns([7, 1.2, 1.5])
with col_nav2:
    btn_masuk = st.button("🔒 Masuk", use_container_width=True)
with col_nav3:
    btn_req = st.button("🚀 Request Akses", type="primary", use_container_width=True)

if btn_masuk:
    st.session_state.logged_in = True
    st.session_state.user_role = "Admin"
    st.session_state.user_name = "Ibu Pengawas"

st.sidebar.markdown("### ⚙️ Workspace Router")
if st.session_state.logged_in:
    st.sidebar.success(f"Login: {st.session_state.user_name}")
    if st.session_state.user_role == "Admin":
        sub_menu = st.sidebar.radio("Menu Pengawas", ["Dashboard Admin", "Validasi Dokumen", "Upload Materi Pusat", "Log Out"])
    else:
        sub_menu = st.sidebar.radio("Menu Sekolah", ["Dashboard Sekolah", "Upload Artefak", "Riwayat Revisi", "Log Out"])
        
    if sub_menu == "Log Out":
        st.session_state.logged_in = False
        st.session_state.user_role = "Public"
        st.session_state.user_name = "Guest"
        st.rerun()
else:
    sub_menu = "Beranda Publik"
    st.sidebar.info("Klik tombol **🔒 Masuk** di sudut kanan atas untuk mengakses ruang kerja.")

# ==========================================
# 4. CONTENT AREA - HERO & MOCKUP LAYOUT
# ==========================================
if sub_menu in ["Beranda Publik", "Log Out"]:
    
    # Hero Grid Layout
    col_hero1, col_hero2 = st.columns([1.3, 1])
    
    with col_hero1:
        st.markdown("<div class='tagline-badge'>💻 Platform Pengawas Sekolah Modern</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-h1'>GIPANG <span>M3</span> BANTEN</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-sub'>Gerakan Inovatif Pendampingan Memantau, Mengevaluasi, Menilai Bantuan Teknologi</div>", unsafe_allow_html=True)
        st.markdown("""
            <div class='hero-desc'>
                Platform digital untuk memudahkan pengawas sekolah dalam mengumpulkan, memantau, 
                mengevaluasi, dan menilai portofolio artefak dari sekolah binaan secara efektif, 
                transparan, dan terstruktur.
            </div>
        """, unsafe_allow_html=True)
        
        c_btn1, c_btn2, c_btn3 = st.columns([1.5, 1.5, 2])
        c_btn1.button("➕ Pelajari Lebih Lanjut", type="primary", use_container_width=True)
        c_btn2.button("👁️ Lihat Portofolio", use_container_width=True)

    with col_hero2:
        st.markdown("""
            <div class='mockup-container'>
                <div style='background: white; border: 12px solid #1e293b; border-bottom-width: 24px; border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(11,31,82,0.25); overflow: hidden;'>
                    <div style='background: #f8fafc; padding: 12px; text-align: left; font-size: 11px; border-bottom: 1px solid #e2e8f0; font-weight: 600;'>
                        📊 Dashboard Workspace - Pengawas Sekolah Banten
                    </div>
                    <div style='padding: 20px; background: white; height: 210px; text-align: left;'>
                        <div style='display: flex; gap: 10px; margin-bottom: 15px;'>
                            <div style='flex:1; background:#eff6ff; padding: 10px; border-radius: 8px; border-left: 4px solid #1D4ED8;'>
                                <small style='color:#64748b;'>Sekolah Binaan</small><br><b style='font-size: 16px; color:#0B1F52;'>24</b>
                            </div>
                            <div style='flex:1; background:#f0fdf4; padding: 10px; border-radius: 8px; border-left: 4px solid #10b981;'>
                                <small style='color:#64748b;'>Diterima</small><br><b style='font-size: 16px; color:#065f46;'>156</b>
                            </div>
                        </div>
                        <div style='width: 100%; height: 75px; background: #f8fafc; border-radius: 8px; padding: 10px;'>
                            <small style='color: #94a3b8;'>Grafik Validasi Mingguan</small>
                            <div style='display: flex; align-items: flex-end; gap: 12px; height: 40px; margin-top: 5px; padding-left: 10px;'>
                                <div style='width: 20px; height: 15px; background: #60a5fa; border-radius: 3px;'></div>
                                <div style='width: 20px; height: 28px; background: #1D4ED8; border-radius: 3px;'></div>
                                <div style='width: 20px; height: 22px; background: #60a5fa; border-radius: 3px;'></div>
                                <div style='width: 20px; height: 38px; background: #1D4ED8; border-radius: 3px;'></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # TITIK JANGKAR: Fitur
    st.markdown("<div id='fitur'></div><br>", unsafe_allow_html=True)
    
    row_f1, row_f2, row_f3 = st.columns(3)
    with row_f1:
        st.markdown("<div class='saas-card'><div class='icon-box' style='background:#eff6ff; color:#1D4ED8;'>📤</div><h5>Pengumpulan Artefak</h5><p style='font-size:13px; color:#64748b; margin:0;'>Upload berkas data portofolio aman.</p></div>", unsafe_allow_html=True)
    with row_f2:
        st.markdown("<div class='saas-card'><div class='icon-box' style='background:#f0fdf4; color:#10b981;'>🛡️</div><h5>Validasi & Evaluasi</h5><p style='font-size:13px; color:#64748b; margin:0;'>Status tinjauan kualitas instan.</p></div>", unsafe_allow_html=True)
    with row_f3:
        st.markdown("<div class='saas-card'><div class='icon-box' style='background:#f5f3ff; color:#7c3aed;'>📥</div><h5>Download Materi</h5><p style='font-size:13px; color:#64748b; margin:0;'>Unduh akses materi pendampingan.</p></div>", unsafe_allow_html=True)

    # TITIK JANGKAR: Portofolio
    st.markdown("<div id='portofolio'></div><br><hr style='opacity:0.5;'><br>", unsafe_allow_html=True)

    col_bottom_left, col_bottom_right = st.columns([1.4, 1])
    with col_bottom_left:
        st.markdown("<h4>📋 Pengumpulan Terbaru</h4>", unsafe_allow_html=True)
        st.markdown("""
            <div class='custom-table-container'>
                <table style='width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;'>
                    <thead>
                        <tr style='border-bottom: 2px solid #f1f5f9; color: #475569;'>
                            <th style='padding: 10px 5px;'>Sekolah</th>
                            <th style='padding: 10px 5px;'>Judul Tugas</th>
                            <th style='padding: 10px 5px;'>Tanggal</th>
                            <th style='padding: 10px 5px; text-align: center;'>Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style='border-bottom: 1px solid #f1f5f9;'><td style='padding: 12px 5px; font-weight:600;'>🏫 SDN 1 Serang</td><td style='color:#475569;'>Laporan Implementasi TIK</td><td>25 Mei 2026</td><td style='text-align: center;'><span class='btn-action-view'>👁️ Lihat</span></td></tr>
                        <tr style='border-bottom: 1px solid #f1f5f9;'><td style='padding: 12px 5px; font-weight:600;'>🏫 SMPN 2 Kota Cilegon</td><td style='color:#475569;'>Portofolio Pembelajaran</td><td>24 Mei 2026</td><td style='text-align: center;'><span class='btn-action-view'>👁️ Lihat</span></td></tr>
                        <tr style='border-bottom: 1px solid #f1f5f9;'><td style='padding: 12px 5px; font-weight:600;'>🏫 SDN 3 Pandeglang</td><td style='color:#475569;'>Evaluasi Bantuan Teknologi</td><td>23 Mei 2026</td><td style='text-align: center;'><span class='btn-action-view'>👁️ Lihat</span></td></tr>
                    </tbody>
                </table>
            </div>
        """, unsafe_allow_html=True)

    with col_bottom_right:
        st.markdown("<h4>📊 Statistik Performa Platform</h4>", unsafe_allow_html=True)
        stat_rc1, stat_rc2 = st.columns(2)
        with stat_rc1:
            st.markdown("<div class='saas-card' style='padding:15px; text-align:center; margin-bottom:10px;'><h2 style='color:#1D4ED8; margin:0;'>124</h2><small style='color:#64748b;'>Sekolah Binaan</small></div>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card' style='padding:15px; text-align:center;'><h2 style='color:#7c3aed; margin:0;'>342</h2><small style='color:#64748b;'>Tugas Terkumpul</small></div>", unsafe_allow_html=True)
        with stat_rc2:
            st.markdown("<div class='saas-card' style='padding:15px; text-align:center; margin-bottom:10px;'><h2 style='color:#10b981; margin:0;'>156</h2><small style='color:#64748b;'>Pengguna Aktif</small></div>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card' style='padding:15px; text-align:center;'><h2 style='color:#f59e0b; margin:0;'>256</h2><small style='color:#64748b;'>Disetujui</small></div>", unsafe_allow_html=True)

    # TITIK JANGKAR: MATERI PUBLIK (FITUR BARU)
    st.markdown("<div id='materi'></div><br><hr style='opacity:0.5;'><br>", unsafe_allow_html=True)
    st.markdown("<h4>📥 Pusat Download Materi & Regulasi</h4>", unsafe_allow_html=True)
    st.write("Semua dokumen juknis, materi sosialisasi, dan panduan yang diunggah oleh Pengawas dapat diakses publik di sini.")
    
    # Loop untuk menampilkan semua materi dari database memori sementara
    materi_cols = st.columns(3)
    for index, materi in enumerate(st.session_state.db_materi):
        with materi_cols[index % 3]:
            st.markdown(f"""
                <div class='saas-card' style='padding: 20px; margin-bottom: 15px;'>
                    <div style='font-size: 35px; margin-bottom: 10px;'>{materi['icon']}</div>
                    <h5 style='margin: 0 0 5px 0; color: #0B1F52;'>{materi['judul']}</h5>
                    <p style='font-size: 12px; color: #64748b; margin: 0 0 15px 0;'>
                        🏷️ {materi['kategori']} &nbsp;|&nbsp; 📅 {materi['tanggal']} &nbsp;|&nbsp; 💾 {materi['ukuran']}
                    </p>
                    <a href='#' style='text-decoration: none;'>
                        <button style='width: 100%; background: #eff6ff; color: #1D4ED8; border: 1px solid #bfdbfe; padding: 8px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.3s;'>
                            ⬇️ Download File
                        </button>
                    </a>
                </div>
            """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
        <br><br>
        <div style='background: #0B1F52; padding: 20px 40px; border-radius: 16px; display: flex; justify-content: space-between; align-items: center; color: rgba(255,255,255,0.7); font-size: 13px;'>
            <div>© 2026 GIPANG M3 BANTEN. All rights reserved.</div>
            <div style='display: flex; gap: 20px;'>
                <a href='#' style='color: white; text-decoration: none;'>Privacy Policy</a>
                <a href='#' style='color: white; text-decoration: none;'>❓ Bantuan</a>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 5. AREA KERJA (DASHBOARD INTERNAL)
# ==========================================
elif sub_menu == "Dashboard Admin":
    st.title(f"📊 Dashboard Utama - {st.session_state.user_name}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Dokumen Masuk", "45 Dokumen", "+5 Hari Ini")
    col2.metric("Menunggu Validasi", "12 Dokumen", "-2 Kemarin", delta_color="inverse")
    col3.metric("Ruang Terpakai", "1.2 GB", "Aman")

elif sub_menu == "Validasi Dokumen":
    st.title("🛡️ Panel Validasi")
    st.write("Fitur validasi dokumen sedang dipersiapkan...")

# AREA BARU: UPLOAD MATERI OLEH ADMIN
elif sub_menu == "Upload Materi Pusat":
    st.title("📤 Publikasi Materi & Juknis")
    st.write("Materi yang Anda unggah di sini akan langsung muncul di halaman **Beranda Publik** dan dapat diunduh oleh semua sekolah binaan.")
    
    with st.container(border=True):
        st.markdown("### 📝 Form Unggah Dokumen Baru")
        judul_materi = st.text_input("Judul / Nama Materi")
        kategori_materi = st.selectbox("Kategori Dokumen", ["Regulasi", "Modul Ajar", "Template", "Lainnya"])
        file_materi = st.file_uploader("Pilih File (PDF/Docx/Excel/PPT)", type=["pdf", "docx", "xlsx", "pptx"])
        
        if st.button("🚀 Publikasikan Materi ke Publik", type="primary"):
            if judul_materi and file_materi:
                # Membuat data simulasi baru
                tanggal_hari_ini = datetime.datetime.now().strftime("%d %b %Y")
                ukuran_mb = round(file_materi.size / (1024 * 1024), 2)
                
                materi_baru = {
                    "judul": judul_materi,
                    "kategori": kategori_materi,
                    "tanggal": tanggal_hari_ini,
                    "ukuran": f"{ukuran_mb} MB",
                    "icon": "🆕"
                }
                
                # Memasukkan materi baru ke posisi paling depan (index 0) di database memori
                st.session_state.db_materi.insert(0, materi_baru)
                
                st.success(f"✅ Berhasil! Dokumen **{judul_materi}** telah dipublikasikan.")
                st.balloons()
            else:
                st.error("⚠️ Mohon isi judul materi dan pilih file terlebih dahulu sebelum mengunggah.")

elif sub_menu == "Dashboard Sekolah":
    st.title(f"🏠 Selamat Datang, {st.session_state.user_name}!")
    st.write("Ini adalah area privat sekolah Anda.")

elif sub_menu == "Upload Artefak":
    st.title("📤 Ruang Unggah Artefak")
    st.write("Silakan unggah portofolio sekolah Anda di sini.")

elif sub_menu == "Riwayat Revisi":
    st.title("♻️ Riwayat Revisi")
    st.write("Daftar dokumen yang dikembalikan oleh Pengawas.")