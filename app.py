import streamlit as st
import pandas as pd
import gspread
import requests
import json
import ast
import base64
import urllib.parse
import hashlib
import re
import datetime

from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="GIPANG M3 BANTEN",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
<style>

.hero-title{
font-size:52px;
font-weight:800;
line-height:1.1;
color:#0B1F52;
margin-bottom:10px;
}

.hero-blue{
color:#2563EB;
}

.hero-desc{

font-size:17px;

color:#64748B;

line-height:1.8;

margin-top:15px;

margin-bottom:25px;

}

.hero-badge{

display:inline-block;

padding:8px 18px;

background:#DBEAFE;

color:#2563EB;

border-radius:30px;

font-size:13px;

font-weight:600;

margin-bottom:15px;

}

.metric-card{

background:white;

padding:22px;

border-radius:18px;

border:1px solid #E2E8F0;

box-shadow:0px 10px 30px rgba(0,0,0,.05);

text-align:center;

transition:.3s;

}

.metric-card:hover{

transform:translateY(-5px);

}

.metric-value{

font-size:34px;

font-weight:800;

color:#2563EB;

}

.metric-label{

color:#64748B;

font-size:14px;

}

.feature-card{

background:white;

border-radius:20px;

padding:30px;

border:1px solid #E2E8F0;

transition:.35s;

height:100%;

}

.feature-card:hover{

transform:translateY(-8px);

box-shadow:0px 15px 35px rgba(0,0,0,.08);

}

.gallery-card{

background:white;

border-radius:20px;

padding:15px;

border:1px solid #E2E8F0;

margin-bottom:20px;

overflow:hidden;

}

.footer{

padding:40px;

text-align:center;

color:#94A3B8;

font-size:13px;

}

</style>

""", unsafe_allow_html=True)

# ==========================================
# SESSION
# ==========================================

DEFAULT_SESSION = {
    "logged_in": False,
    "show_login": False,
    "show_register": False,
    "user_role": "Public",
    "user_name": "Guest",
    "asal_sekolah": ""
}

for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# DATABASE
# ==========================================

NAMA_SPREADSHEET = "Database_Portofolio_Pengawas"

@st.cache_resource(show_spinner=False)
def get_gspread_client():

    try:

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        raw_secret = st.secrets["gcp"]["kunci_json"]

        try:
            creds_dict = json.loads(raw_secret)

        except:
            creds_dict = ast.literal_eval(raw_secret)

        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_dict,
            scope
        )

        client = gspread.authorize(creds)

        return client

    except Exception as e:

        st.error(f"Gagal koneksi Google Sheet\n\n{e}")

        return None


client = get_gspread_client()

# ENGINE BARU: Membersihkan Spasi Header Google Sheets otomatis
@st.cache_data(ttl=20)
def load_data(sheet_name):

    if client is None:
        return pd.DataFrame()

    try:

        ws = client.open(
            NAMA_SPREADSHEET
        ).worksheet(sheet_name)

        values = ws.get_all_values()

        if len(values) <= 1:
            return pd.DataFrame()

        header = [
            str(x).strip()
            for x in values[0]
        ]

        df = pd.DataFrame(
            values[1:],
            columns=header
        )

        return df

    except Exception as e:

        st.error(e)

        return pd.DataFrame()


# ==========================================
# HELPER BARU
# ==========================================

def append_row(sheet_name, row):

    try:

        client.open(
            NAMA_SPREADSHEET
        ).worksheet(sheet_name).append_row(
            row,
            value_input_option="USER_ENTERED"
        )

        # Refresh cache agar data terbaru langsung terbaca
        load_data.clear()

        return True

    except Exception as e:

        st.error(e)

        return False

# MESIN API IMGBB (Untuk Foto JPG/PNG Langsung)
def upload_to_imgbb(image):

    try:

        api = st.secrets["imgbb"]["api_key"]

        encoded = base64.b64encode(
            image.getvalue()
        ).decode()

        response = requests.post(

            "https://api.imgbb.com/1/upload",

            data={

                "key": api,

                "image": encoded

            },

            timeout=30

        )

        result = response.json()

        if result["success"]:

            return (
                result["data"]["display_url"],
                None
            )

        return None, result

    except Exception as e:

        return None, str(e)

# MESIN PARSER GOOGLE DRIVE (Untuk Link GDrive)
def auto_convert_drive_url(url):

    if not url:
        return ""

    url = url.strip()

    if "drive.google.com" not in url:
        return url

    try:

        if "/file/d/" in url:

            file_id = url.split("/file/d/")[1].split("/")[0]

        elif "id=" in url:

            parsed = urllib.parse.urlparse(url)

            file_id = urllib.parse.parse_qs(
                parsed.query
            )["id"][0]

        else:

            return url

        return f"https://drive.google.com/uc?id={file_id}"

    except:

        return url

# ==========================================
# HELPER FOTO
# ==========================================
def get_photo_list(row):

    photos = []

    for col in [

        "Link_Foto1",

        "Link_Foto2",

        "Link_Foto3"

    ]:

        url = str(

            row.get(col, "")

        ).strip()

        if url != "" and url.lower() != "nan":

            photos.append(url)

    return photos

def valid_url(url):

    try:

        r = requests.get(

            url,

            timeout=10

        )

        return r.status_code == 200

    except:

        return False

# ============================
# LOGIN & REGISTER HELPER
# ============================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def valid_email(email):

    regex = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

    return re.match(regex, email)


def email_exists(email):

    df = load_data("User")

    if df.empty:
        return False

    if "Email" not in df.columns:
        return False

    return email.lower() in [
        str(x).lower().strip()
        for x in df["Email"]
    ]
    
# ==========================================
# 3. PUBLIC VIEW (BERANDA & AUTENTIKASI)
# ==========================================

if not st.session_state.logged_in:

    # ==========================
    # LOAD DATA LANDING PAGE
    # ==========================

    df_gal = load_data("Galeri_Portofolio")
    df_user = load_data("User")
    df_art = load_data("Artefak_Portofolio")

    total_sekolah = 0
    total_art = 0
    total_galeri = 0

    if not df_user.empty:
        total_sekolah = len(df_user["Asal_Sekolah"].unique())

    if not df_art.empty:
        total_art = len(df_art)

    if not df_gal.empty:
        total_galeri = len(df_gal)

   # NAVBAR
st.markdown("""
....navbar....
""", unsafe_allow_html=True)

# =====================================
# LOGIN
# =====================================

if st.session_state.show_login:

    with st.container(border=True):

        st.subheader("🔐 Login Workspace")

        email = st.text_input("Email")

        password = st.text_input(
            "Password",
            type="password"
        )

        c1,c2 = st.columns(2)

        login = c1.button("Login")

        cancel = c2.button("Batal")

        if cancel:
            st.session_state.show_login = False
            st.rerun()

        if login:

            df=load_data("User")

            if df.empty:

                st.error("Database kosong.")

            else:

                email=email.lower().strip()

                password=hash_password(password)

                df["Email"]=df["Email"].str.lower()

                user=df[
                    (df["Email"]==email)
                    &
                    (df["Password"]==password)
                ]

                if user.empty:

                    st.error("Email atau Password salah.")

                else:

                    if user.iloc[0]["Status_Akun"]!="Aktif":

                        st.warning("Akun masih menunggu persetujuan.")

                    else:

                        st.session_state.logged_in=True

                        st.session_state.user_name=user.iloc[0]["Nama_Lengkap"]

                        st.session_state.user_role=user.iloc[0]["Role"]

                        st.session_state.asal_sekolah=user.iloc[0]["Asal_Sekolah"]

                        st.success("Login berhasil.")

                        st.rerun()

    # --- POPUP REGISTER ---
    if st.session_state.show_register:
     with st.container(border=True):

        st.subheader("🚀 Request Akses")

        with st.form("register"):

            nama=st.text_input(
                "Nama Lengkap"
            )

            sekolah=st.text_input(
                "Asal Sekolah"
            )

            email=st.text_input(
                "Email"
            )

            role=st.selectbox(

                "Role",

                [

                    "Operator",

                    "Kepala Sekolah"

                ]

            )

            password=st.text_input(

                "Password",

                type="password"

            )

            submit=st.form_submit_button(

                "Daftar"

            )

            if submit:

                if "" in [

                    nama,

                    sekolah,

                    email,

                    password

                ]:

                    st.error("Lengkapi seluruh data.")

                elif not valid_email(email):

                    st.error("Format email tidak valid.")

                elif email_exists(email):

                    st.error("Email sudah digunakan.")

                elif len(password)<8:

                    st.error("Password minimal 8 karakter.")

                else:

                    besar=any(c.isupper() for c in password)

                    kecil=any(c.islower() for c in password)

                    angka=any(c.isdigit() for c in password)

                    if not all([besar,kecil,angka]):

                        st.error(

                            "Password harus memiliki huruf besar, huruf kecil, dan angka."

                        )

                    else:

                        append_row(

                            "User",

                            [

                                nama,

                                sekolah,

                                email,

                                role,

                                hash_password(password),

                                "Pending"

                            ]

                        )

                        st.success(

                            "Pendaftaran berhasil."

                        )

                        st.balloons()

                        st.session_state.show_register=False

                        st.rerun()

    # --- HERO SECTION ---
    st.markdown("<hr>", unsafe_allow_html=True)

left,right=st.columns([1.2,.8])

with left:

    st.markdown("""
<div class='hero-badge'>
🚀 Platform Digital Pengawas Sekolah
</div>

<div class='hero-title'>
GIPANG <span class='hero-blue'>M3</span> BANTEN
</div>

<div class='hero-desc'>
Gerakan Inovatif Pendampingan Memantau,
Mengevaluasi,
Menilai Bantuan Teknologi.

Platform modern untuk membantu Pengawas Sekolah,
Kepala Sekolah,
dan Operator mengelola portofolio digital.
</div>
""", unsafe_allow_html=True)

    c1,c2=st.columns(2)

    with c1:
        if st.button("🚀 Request Akses",use_container_width=True):
            st.session_state.show_register=True
            st.rerun()

    with c2:
        if st.button("🔐 Login",use_container_width=True):
            st.session_state.show_login=True
            st.rerun()

with right:

    st.image(
        "https://images.unsplash.com/photo-1552664730-d307ca884978?w=900",
        use_container_width=True
    )

st.markdown("<br>",unsafe_allow_html=True)

a,b,c=st.columns(3)

with a:

    st.markdown(f"""

<div class="metric-card">

<div class="metric-value">

{total_sekolah}

</div>

<div class="metric-label">

Sekolah Terdaftar

</div>

</div>

""",unsafe_allow_html=True)

with b:

    st.markdown(f"""

<div class="metric-card">

<div class="metric-value">

{total_art}

</div>

<div class="metric-label">

Artefak Masuk

</div>

</div>

""",unsafe_allow_html=True)

with c:

    st.markdown(f"""

<div class="metric-card">

<div class="metric-value">

{total_galeri}

</div>

<div class="metric-label">

Dokumentasi

</div>

</div>

""",unsafe_allow_html=True)

    st.markdown("## ✨ Fitur Unggulan")

c1,c2,c3=st.columns(3)

fitur=[

("📂","Upload Artefak","Pengumpulan dokumen sekolah secara digital."),

("📷","Galeri Kegiatan","Dokumentasi kegiatan sekolah."),

("📊","Monitoring","Validasi dan evaluasi real-time.")

]

for col,data in zip([c1,c2,c3],fitur):

    with col:

        st.markdown(f"""

<div class="feature-card">

<h1>{data[0]}</h1>

<h4>{data[1]}</h4>

<p>{data[2]}</p>

</div>

""",unsafe_allow_html=True)

    # --- PERBAIKAN GALERI FOTO (MENGGUNAKAN ST.IMAGE ANTI ERROR) ---
    st.markdown("""
<div id='portofolio'></div>

<br>

<hr>

<h3>📸 Galeri Portofolio Kegiatan</h3>

""",unsafe_allow_html=True)

df_gal=load_data("Galeri_Portofolio")

if df_gal.empty:

    st.markdown("""

<div style='

padding:40px;

text-align:center;

border:1px dashed #CBD5E1;

border-radius:18px;

background:#F8FAFC;

'>

<h2>📸</h2>

<h4>Belum Ada Dokumentasi</h4>

Silakan upload kegiatan sekolah pertama Anda.

</div>

""",unsafe_allow_html=True)

else:

    for _,row in df_gal.iterrows():

        photos=get_photo_list(row)

        with st.container(border=True):

            st.subheader(
                row.get(
                    "Asal_Sekolah",
                    "-"
                )
            )

            st.caption(
                row.get(
                    "Deskripsi_Kegiatan",
                    "-"
                )
            )

            total=len(photos)

            if total==1:

                st.image(
                    photos[0],
                    use_container_width=True
                )

            elif total==2:

                c1,c2=st.columns(2)

                c1.image(
                    photos[0],
                    use_container_width=True
                )

                c2.image(
                    photos[1],
                    use_container_width=True
                )

            elif total>=3:

                c1,c2,c3=st.columns(3)

                c1.image(
                    photos[0],
                    use_container_width=True
                )

                c2.image(
                    photos[1],
                    use_container_width=True
                )

                c3.image(
                    photos[2],
                    use_container_width=True
                )

            st.divider()

    # --- PERBAIKAN TOMBOL DOWNLOAD MATERI ---
    st.markdown("<div id='materi'></div><br><hr style='opacity:0.5;'><br><h4>📥 Pusat Download Materi Publik</h4>", unsafe_allow_html=True)
    df_mat = load_data("Materi_Publik")
    if not df_mat.empty and 'Judul' in df_mat.columns:
        mat_cols = st.columns(3)
        for idx, (_, row) in enumerate(df_mat.iterrows()):
            with mat_cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"### {row.get('Icon', '📄')} {row.get('Judul', '')}")
                    st.write(f"🏷️ {row.get('Kategori', '')} | 📅 {row.get('Tanggal', '')}")
                    
                    # Link Button Asli Streamlit (Pasti Merespon)
                    link_dl = str(row.get('Link_Download', '')).strip()
                    if link_dl and link_dl != "nan":
                        if not link_dl.startswith('http'): link_dl = 'https://' + link_dl
                        st.link_button("⬇️ Download Materi", link_dl, use_container_width=True)
                    else:
                        st.button("⚠️ Link Belum Tersedia", disabled=True, use_container_width=True)
    else: st.info("Belum ada materi publik.")

# ==========================================
# CTA
# ==========================================

st.markdown("<br><br>", unsafe_allow_html=True)

st.info("""
🚀 **Siap bergabung bersama GIPANG M3 BANTEN?**

Kelola portofolio sekolah secara digital,
lebih cepat,
lebih aman,
dan lebih transparan.
""")

# ==========================================
# FOOTER
# ==========================================

st.markdown("""

<div class="footer">

© 2026 GIPANG M3 BANTEN

Gerakan Inovatif Pendampingan Memantau, dan

Mengevaluasi,

Menilai Bantuan Teknologi

</div>

""",unsafe_allow_html=True)

else:
    # ==========================================
    # 4. PRIVATE VIEW (WORKSPACE ROUTING)
    # ==========================================
    st.sidebar.markdown(f"""

## 👋 Halo

**{st.session_state.user_name}**

🏫 {st.session_state.asal_sekolah}

🔹 {st.session_state.user_role}

""")

    if st.session_state.user_role == "Admin":
        menu = st.sidebar.radio("Navigasi Pengawas", ["Dashboard Admin", "Cek Artefak Sekolah", "Sistem Reminder Email", "Validasi Akun Baru", "Manajemen Tagihan Tugas", "Upload Materi Pusat", "Manajemen Jadwal Pendampingan", "Manajemen Galeri Publik", "Upload Galeri Kegiatan", "Respon Konsultasi", "🚪 Keluar"])
    elif st.session_state.user_role == "Kepala Sekolah":
        menu = st.sidebar.radio("Navigasi Kepsek", ["Dashboard Kepala Sekolah", "Booking Jadwal Pendampingan", "Pakta Integritas & Pengesahan", "Layanan Konsultasi", "Upload Galeri Kegiatan", "🚪 Keluar"])
    elif st.session_state.user_role == "Operator":
        menu = st.sidebar.radio("Navigasi Operator", ["Dashboard Operator", "Upload Artefak", "Riwayat & Perbaikan", "Upload Galeri Kegiatan", "🚪 Keluar"])

    if menu=="🚪 Keluar":

    for key in DEFAULT_SESSION:

        st.session_state[key]=DEFAULT_SESSION[key]

    st.success("Logout berhasil.")

    st.rerun()

    # --- [A] FITUR BERSAMA ---
    if menu == "Upload Galeri Kegiatan":
        st.title("📸 Upload Dokumentasi Foto Kegiatan")
        with st.container(border=True):
            metode = st.radio("Metode Upload:", ["📂 Unggah File (JPG/PNG)", "🔗 Gunakan Link Google Drive"])
            desc = st.text_input("Judul / Deskripsi Singkat Kegiatan")
            
            if metode == "📂 Unggah File (JPG/PNG)":
                fotos = st.file_uploader("Pilih Maks 3 File (@2MB)", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
if fotos:

    st.write("Preview")

    cols=st.columns(len(fotos))

    for i,f in enumerate(fotos):

        cols[i].image(
            f,
            use_container_width=True
        )
               if st.button(
    "🚀 Publish",
    type="primary"
):

    if not desc:

        st.error("Isi deskripsi.")

    elif not fotos:

        st.error("Pilih minimal satu foto.")

    elif len(fotos)>3:

        st.error("Maksimal tiga foto.")

    else:

        urls=[]

        with st.spinner("Upload..."):

            for f in fotos:

                if f.size>2*1024*1024:

                    st.error(
                        f"{f.name} lebih dari 2MB"
                    )

                    st.stop()

                link,error=upload_to_imgbb(f)

                if error:

                    st.error(error)

                    st.stop()

                urls.append(link)

        while len(urls)<3:

            urls.append("")

        append_row(

            "Galeri_Portofolio",

            [

                datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                st.session_state.asal_sekolah,

                desc,

                urls[0],

                urls[1],

                urls[2]

            ]

        )

        st.success(
            "Berhasil dipublikasikan."
        )

        st.rerun()

            else:
                l1 = st.text_input("Link Foto Utama (Wajib)")
                l2 = st.text_input("Link Foto Pendukung 2 (Opsional)")
                l3 = st.text_input("Link Foto Pendukung 3 (Opsional)")
                if st.button("🚀 Publish (Google Drive)", type="primary"):
                    if desc and l1 and client:
                        client.open(NAMA_SPREADSHEET).append_row(

    "Galeri_Portofolio",

    [

        datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        st.session_state.asal_sekolah,

        desc,

        auto_convert_drive_url(l1),

        auto_convert_drive_url(l2),

        auto_convert_drive_url(l3)

    ]

)

    # --- [B] FITUR ADMIN (PENGAWAS) ---
    elif menu == "Dashboard Admin":

    #LOAD DATA
    st.title("📊 Dashboard Pengawas")

    df_art = load_data("Artefak_Portofolio")
    df_user = load_data("User")
    df_tag = load_data("Tagihan_Tugas")

    total_art = len(df_art)

    total_user = len(df_user)

    total_tugas = len(df_tag)

    pending = 0
    revisi = 0
    disetujui = 0

    if not df_art.empty and "Status" in df_art.columns:

        pending = len(
            df_art[
                df_art["Status"]=="Menunggu Validasi"
            ]
        )

        revisi = len(
            df_art[
                df_art["Status"]=="Perlu Revisi ♻️"
            ]
        )

        disetujui = len(
            df_art[
                df_art["Status"]=="Disetujui ✅"
            ]
        )

#KPI CARD
c1,c2,c3,c4=st.columns(4)

c1.metric(

    "🏫 Sekolah",

    total_user

)

c2.metric(

    "📂 Artefak",

    total_art

)

c3.metric(

    "⏳ Pending",

    pending

)

c4.metric(

    "✅ Disetujui",

    disetujui
)


#PROGRESS
st.markdown("### Progress Validasi")

if total_art>0:

    persen = disetujui/total_art

    st.progress(persen)

    st.write(

        f"{persen*100:.1f}% selesai divalidasi"

    )

#STATISTIK STATUS
st.markdown("### Ringkasan Status")

a,b,c=st.columns(3)

a.success(f"✅ {disetujui}")

b.warning(f"⏳ {pending}")

c.error(f"♻️ {revisi}")

#GRAFIK
if not df_art.empty:

    st.markdown("### Grafik Status")

    chart = (
        df_art["Status"]
        .value_counts()
    )

    st.bar_chart(chart)

#DASHBOARD SEKOLAH
if not df_art.empty:

    st.markdown("### 🏫 Statistik Sekolah")

    sekolah = (

        df_art

        .groupby("Nama_Sekolah")

        .size()

        .sort_values(ascending=False)

    )

    st.bar_chart(sekolah)

#SEARCH
st.markdown("### 🔍 Cari Artefak")

keyword = st.text_input(
    "Cari Nama Sekolah"
)

status = st.selectbox(

    "Filter Status",

    [

        "Semua",

        "Menunggu Validasi",

        "Disetujui ✅",

        "Perlu Revisi ♻️"

    ]

)

#FILTER
df_show = df_art.copy()

if keyword:

    df_show = df_show[

        df_show["Nama_Sekolah"]

        .str.contains(

            keyword,

            case=False,

            na=False

        )

    ]

if status != "Semua":

    df_show = df_show[

        df_show["Status"] == status

    ]

#TABEL
st.markdown("### 📋 Daftar Artefak")

if not df_show.empty:

    st.dataframe(

        df_show[
            [

                "Timestamp",

                "Nama_Sekolah",

                "Nama_Tugas",

                "Status",

                "Catatan_Pengawas"

            ]

        ],

        use_container_width=True,

        hide_index=True

    )

else:

    st.info("Belum ada data.")

#DOWNLOAD CSV
if not df_show.empty:

    csv = df_show.to_csv(index=False)

    st.download_button(

        "⬇ Download CSV",

        csv,

        "Artefak.csv",

        "text/csv"

    )

    elif menu == "Cek Artefak Sekolah":
        st.title("🛡️ Pemeriksaan & Penilaian Portofolio")
        df_art = load_data("Artefak_Portofolio")
        if not df_art.empty and 'Status' in df_art.columns:
            df_pending = df_art[df_art['Status'].isin(['Menunggu Validasi', 'Perlu Revisi ♻️'])]
            if not df_pending.empty:
                st.dataframe(df_pending[['Timestamp', 'Nama_Sekolah', 'Nama_Tugas', 'Status']], use_container_width=True)
                with st.form("f_nilai"):
                    baris = st.selectbox("Pilih Dokumen", df_pending.apply(lambda x: f"{x.get('Timestamp','')} | {x.get('Nama_Sekolah','')} | {x.get('Nama_Tugas','')}", axis=1).tolist())
                    stat_baru = st.radio("Keputusan Akhir", ["Disetujui ✅", "Perlu Revisi ♻️"])
                    catatan = st.text_area("Catatan Pengawas (Wajib diisi jika Revisi)")
                    if st.form_submit_button("Simpan Keputusan", type="primary"):
                        ts, sek = baris.split(" | ")[0], baris.split(" | ")[1]
                        sheet_art = client.open(NAMA_SPREADSHEET).worksheet("Artefak_Portofolio")
                        raw = sheet_art.get_all_values()
                        for i, row in enumerate(raw):
                            if i == 0: continue
                            if str(row[0]).strip() == ts and str(row[1]).strip() == sek:
                                sheet_art.update_cell(i + 1, 5, stat_baru)
                                sheet_art.update_cell(i + 1, 6, catatan)
                                st.success("Keputusan tersimpan!")
                                st.rerun()
                                break
            else: st.success("Semua dokumen telah diperiksa.")

    elif menu == "Manajemen Jadwal Pendampingan":
        st.title("🗓️ Manajemen Kalender Pendampingan")
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
                        raw = sheet_j.get_all_values()
                        for i, row in enumerate(raw):
                            if i == 0: continue
                            if str(row[0]).strip() == ts:
                                sheet_j.update_cell(i + 1, 5, keputusan)
                                st.success("Status jadwal diperbarui!")
                                st.rerun()
                                break
            else: st.info("Tidak ada ajuan jadwal baru.")
            st.markdown("### Seluruh Jadwal (Kalender Pengawas)")
            st.dataframe(df_jadwal[['Tanggal_Booking', 'Asal_Sekolah', 'Tujuan_Pendampingan', 'Status']].sort_values(by='Tanggal_Booking'), use_container_width=True)
        else: st.info("Belum ada data jadwal masuk.")

    elif menu == "Manajemen Galeri Publik":
        st.title("🗑️ Hapus Galeri (Khusus Admin)")
        df_gal = load_data("Galeri_Portofolio")
        if not df_gal.empty and 'Timestamp' in df_gal.columns:
            st.dataframe(df_gal[['Timestamp', 'Asal_Sekolah', 'Deskripsi_Kegiatan']], use_container_width=True)
            with st.form("f_del_gal"):
                pilih_gal = st.selectbox("Pilih Kegiatan Dihapus", df_gal.apply(lambda x: f"{x.get('Timestamp','')} | {x.get('Deskripsi_Kegiatan','')}", axis=1))
                if st.form_submit_button("❌ Hapus Permanen", type="primary"):
                    ts_gal = pilih_gal.split(" | ")[0]
                    sheet_gal = client.open(NAMA_SPREADSHEET).worksheet("Galeri_Portofolio")
                    raw = sheet_gal.get_all_values()
                    for i, row in enumerate(raw):
                        if i == 0: continue
                        if str(row[0]).strip() == ts_gal:
                            sheet_gal.delete_rows(i + 1)
                            st.success("Galeri berhasil dihapus!")
                            st.rerun()
                            break

    elif menu == "Sistem Reminder Email":
        st.title("🔔 Pengingat Otomatis Sekolah Binaan")
        df_tag = load_data("Tagihan_Tugas")
        df_usr = load_data("User")
        df_art = load_data("Artefak_Portofolio")
        if not df_tag.empty and not df_usr.empty:
            t_pilih = st.selectbox("Pilih Tugas yang Akan Dicek", df_tag['Nama_Tugas'].tolist())
            s_sudah = df_art[df_art['Nama_Tugas'] == t_pilih]['Nama_Sekolah'].unique().tolist() if not df_art.empty and 'Nama_Tugas' in df_art.columns else []
            s_belum = df_usr[(df_usr.get('Role', '') != 'Admin') & (df_usr.get('Status_Akun', '') == 'Aktif') & (~df_usr.get('Asal_Sekolah', '').isin(s_sudah))]
            if not s_belum.empty:
                st.warning(f"⚠️ Ada {len(s_belum)} akun yang belum mengumpulkan tugas.")
                d_email = ",".join(s_belum['Email'].astype(str).tolist())
                ml = f"mailto:?bcc={d_email}&subject=REMINDER&body=Segera+lengkapi+tugas."
                st.markdown(f'<a href="{ml}" target="_blank"><button style="background-color: #d93025; color: white; border: none; padding: 10px 20px; border-radius: 8px;">📧 Kirim Reminder Massal</button></a>', unsafe_allow_html=True)
            else: st.success("✅ Seluruh sekolah binaan sudah mengumpulkan tugas ini.")

    elif menu == "Validasi Akun Baru":
        st.title("🛡️ Validasi & Persetujuan Akun")
        df_usr = load_data("User")
        if not df_usr.empty and 'Status_Akun' in df_usr.columns:
            df_pend = df_usr[df_usr['Status_Akun'] == 'Pending']
            if not df_pend.empty:
                st.dataframe(df_pend[['Nama_Lengkap', 'Asal_Sekolah', 'Role', 'Email']], use_container_width=True)
                with st.form("f_acc"):
                    em = st.selectbox("Pilih Email", df_pend['Email'].tolist())
                    if st.form_submit_button("✅ Aktifkan Akun"):
                        s_usr = client.open(NAMA_SPREADSHEET).worksheet("User")
                        cell = s_usr.find(em)
                        if cell:
                            s_usr.update_cell(cell.row, 6, "Aktif")
                            st.success("Akun diaktifkan!")
                            st.rerun()
            else: st.info("✅ Tidak ada akun baru yang menunggu validasi.")

    elif menu == "Manajemen Tagihan Tugas":
        st.title("📋 Pembuatan Tugas Baru")
        with st.form("f_tugas"):
            nt = st.text_input("Judul Tugas")
            kat = st.selectbox("Kategori", ["Manajerial", "Akademik"])
            bt = st.date_input("Batas Waktu")
            dsc = st.text_area("Deskripsi")
            if st.form_submit_button("Terbitkan"):
                if nt and client:
                    client.open(NAMA_SPREADSHEET).worksheet("Tagihan_Tugas").append_row([nt, kat, bt.strftime("%d %B %Y"), dsc])
                    st.success("Tugas diterbitkan!")

    elif menu == "Upload Materi Pusat":
        st.title("📤 Publikasi Juknis Pusat")
        st.info("Pastikan Anda memasukkan Link Google Drive Public. Sistem akan memunculkan tombol Download di beranda.")
        with st.form("f_mat"):
            jm = st.text_input("Judul Materi")
            link_dl = st.text_input("🔗 Link Dokumen Asli (Google Drive dll)")
            if st.form_submit_button("Publish Materi"):
                if jm and link_dl and client:
                    client.open(NAMA_SPREADSHEET).worksheet("Materi_Publik").append_row([jm, "Regulasi", datetime.datetime.now().strftime("%d %b %Y"), "Link Web", "🆕", link_dl])
                    st.success("Materi berhasil dipublikasikan!")

    elif menu == "Respon Konsultasi":
        st.title("💬 Kotak Jawaban Keluhan Sekolah")
        df_k = load_data("Konsultasi_Sekolah")
        if not df_k.empty and 'Status' in df_k.columns:
            df_in = df_k[df_k['Status'] == 'Menunggu Respon']
            if not df_in.empty:
                st.dataframe(df_in[['Timestamp', 'Asal_Sekolah', 'Topik_Keluhan', 'Detail_Pesan']], use_container_width=True)
                with st.form("f_resp"):
                    pilih = st.selectbox("Pilih Keluhan", df_in.apply(lambda x: f"{x.get('Timestamp','')} | {x.get('Asal_Sekolah','')}", axis=1))
                    tang = st.text_area("Berikan Tanggapan")
                    if st.form_submit_button("Kirim Jawaban"):
                        ts = pilih.split(" | ")[0]
                        s_k = client.open(NAMA_SPREADSHEET).worksheet("Konsultasi_Sekolah")
                        raw = s_k.get_all_values()
                        for i, row in enumerate(raw):
                            if i == 0: continue
                            if str(row[0]).strip() == ts:
                                s_k.update_cell(i + 1, 6, tang)
                                s_k.update_cell(i + 1, 7, "Dijawab ✅")
                                st.success("Jawaban terkirim!")
                                st.rerun()
                                break

    # --- [C] FITUR KEPALA SEKOLAH ---
    elif menu == "Dashboard Kepala Sekolah":
        st.title(f"🏛️ Dasbor Manajerial - {st.session_state.asal_sekolah}")
        df_tag = load_data("Tagihan_Tugas")
        total = len(df_tag) if not df_tag.empty else 0
        df_art = load_data("Artefak_Portofolio")
        df_saya = df_art[df_art['Nama_Sekolah'] == st.session_state.asal_sekolah] if not df_art.empty and 'Nama_Sekolah' in df_art.columns else pd.DataFrame()
        disetujui = len(df_saya[df_saya['Status'] == 'Disetujui ✅']) if not df_saya.empty and 'Status' in df_saya.columns else 0
        
        st.markdown("### 📈 Rapor Ketercapaian Administrasi")
        if total > 0: st.progress(min(disetujui / total, 1.0))
        st.markdown("### 📋 Detail Status Artefak Anda")
        if not df_saya.empty: st.dataframe(df_saya[['Nama_Tugas', 'Status', 'Catatan_Pengawas']], use_container_width=True)

    elif menu == "Booking Jadwal Pendampingan":
        st.title("📅 Booking Jadwal Kunjungan/Pendampingan Pengawas")
        df_jadwal = load_data("Jadwal_Pendampingan")
        booked_dates = []
        if not df_jadwal.empty and 'Tanggal_Booking' in df_jadwal.columns:
            st.markdown("### 🗓️ Kalender Jadwal Terkini (Seluruh Sekolah)")
            st.dataframe(df_jadwal[['Tanggal_Booking', 'Asal_Sekolah', 'Status']].sort_values(by='Tanggal_Booking'), use_container_width=True)
            booked_dates = df_jadwal[df_jadwal['Status'].isin(['Menunggu Persetujuan', 'Disetujui ✅'])]['Tanggal_Booking'].astype(str).tolist()
        
        st.markdown("### ✍️ Ajukan Jadwal Sekolah Anda")
        with st.form("f_booking"):
            tgl = st.date_input("Pilih Tanggal Pendampingan")
            tujuan = st.text_input("Tujuan / Agenda")
            if st.form_submit_button("Ajukan Jadwal", type="primary"):
                if tgl.strftime("%Y-%m-%d") in booked_dates: st.error("❌ Tanggal sudah dibooking sekolah lain. Pilih tanggal kosong.")
                elif tujuan and client:
                    client.open(NAMA_SPREADSHEET).worksheet("Jadwal_Pendampingan").append_row([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tgl.strftime("%Y-%m-%d"), st.session_state.asal_sekolah, tujuan, "Menunggu Persetujuan"])
                    st.success("✅ Jadwal berhasil diajukan!")
                    st.rerun()

    elif menu == "Pakta Integritas & Pengesahan":
        st.title("📜 Pengesahan Digital Pimpinan")
        df_sah = load_data("Pengesahan")
        is_signed = not df_sah.empty and 'Asal_Sekolah' in df_sah.columns and st.session_state.asal_sekolah in df_sah['Asal_Sekolah'].values
        if is_signed:
            st.markdown("""<div style='background-color: #d1fae5; padding: 25px; border-radius: 12px; border-left: 8px solid #10b981;'><h3 style='color: #065f46; margin-top:0;'>✅ Pengesahan Selesai</h3><p>Hak pengesahan Anda sudah dikunci permanen oleh sistem.</p></div>""", unsafe_allow_html=True)
        else:
            setuju = st.checkbox("Saya menyetujui pakta integritas ini.")
            if st.button("🔒 Klik Sekali untuk Sahkan", type="primary", disabled=not setuju):
                if client:
                    client.open(NAMA_SPREADSHEET).worksheet("Pengesahan").append_row([datetime.datetime.now().strftime("%Y-%m-%d"), st.session_state.asal_sekolah, st.session_state.user_name])
                    st.rerun()

    elif menu == "Layanan Konsultasi":
        st.title("💬 Kotak Keluhan & Arahan Pengawas")
        with st.form("f_kel"):
            top = st.text_input("Topik")
            psn = st.text_area("Detail Kendala")
            if st.form_submit_button("Kirim"):
                if top and psn and client:
                    client.open(NAMA_SPREADSHEET).worksheet("Konsultasi_Sekolah").append_row([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state.asal_sekolah, st.session_state.user_name, top, psn, "", "Menunggu Respon"])
                    st.success("Terkirim!")
        df_k = load_data("Konsultasi_Sekolah")
        if not df_k.empty and 'Asal_Sekolah' in df_k.columns:
            df_saya = df_k[df_k['Asal_Sekolah'] == st.session_state.asal_sekolah]
            for _, row in df_saya.iterrows(): st.info(f"**Topik:** {row.get('Topik_Keluhan','')}\n\n**Arahan:** {row.get('Tanggapan_Pengawas', '⏳ Belum dibalas')}")

    # --- [D] FITUR OPERATOR ---
    elif menu == "Dashboard Operator":
        st.title(f"🔧 Dasbor Teknis - {st.session_state.asal_sekolah}")
        st.warning("⚠️ Dokumen wajib di-kompres di bawah batas maksimal 3 MB per file!")

    elif menu == "Upload Artefak":
        st.title("📤 Unggah Berkas Tagihan")
        df_tag = load_data("Tagihan_Tugas")
        daftar = df_tag["Nama_Tugas"].tolist() if not df_tag.empty and 'Nama_Tugas' in df_tag.columns else ["Kosong"]
        with st.form("f_up"):
            st.info("💡 FITUR ANTI GANDA: Jika dokumen direvisi, upload ulang di sini. Sistem akan **MENIMPA** file lama secara otomatis.")
            tugas = st.selectbox("Pilih Tagihan", daftar)
            file_art = st.file_uploader("Upload Dokumen (MAKS 3 MB)")
            if st.form_submit_button("Kirim Dokumen"):
                if file_art:
                    if file_art.size > 3 * 1024 * 1024:
                        st.error("❌ FILE TERLALU BESAR: Maksimal 3 MB!")
                    elif client:
                        s_art = client.open(NAMA_SPREADSHEET).worksheet("Artefak_Portofolio")
                        raw = s_art.get_all_values()
                        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        found = False
                        # Pengecekan aman anti-double
                        for i, row in enumerate(raw):
                            if i == 0: continue # Skip header
                            # Index 1: Asal Sekolah, Index 2: Nama Tugas
                            if len(row) > 2 and str(row[1]).strip() == st.session_state.asal_sekolah and str(row[2]).strip() == tugas:
                                s_art.update_cell(i + 1, 1, ts)
                                s_art.update_cell(i + 1, 4, "File_Revisi_Terkumpul")
                                s_art.update_cell(i + 1, 5, "Menunggu Validasi")
                                s_art.update_cell(i + 1, 6, "")
                                found = True
                                break
                                
                        if found: st.success("✅ File lama berhasil ditimpa dengan revisi terbaru (Anti-Double)!")
                        else:
                            s_art.append_row([ts, st.session_state.asal_sekolah, tugas, "File_Baru_Masuk", "Menunggu Validasi", ""])
                            st.success("✅ Berkas baru berhasil dikirim!")
                else: st.error("Pilih file.")

    elif menu == "Riwayat & Perbaikan":
        st.title("♻️ Log Catatan Perbaikan & Revisi")
        df_art = load_data("Artefak_Portofolio")
        if not df_art.empty and 'Status' in df_art.columns and 'Nama_Sekolah' in df_art.columns:
            df_rev = df_art[(df_art['Nama_Sekolah'] == st.session_state.asal_sekolah) & (df_art['Status'] == 'Perlu Revisi ♻️')]
            if not df_rev.empty:
                for _, row in df_rev.iterrows(): st.error(f"❌ **Tugas:** {row.get('Nama_Tugas','')}\n\n**Catatan Pengawas:** {row.get('Catatan_Pengawas','')}")
            else: st.success("🎉 Bersih! Tidak ada tugas Anda yang berstatus revisi.")
