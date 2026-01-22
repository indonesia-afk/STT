import streamlit as st
import speech_recognition as sr
import os
import subprocess
import math
import tempfile
from shutil import which # Wajib ada untuk deteksi di Cloud

# ==========================================
# 1. SETUP & CONFIG
# ==========================================
st.set_page_config(
    page_title="Tommy's STT", 
    page_icon="🎙️", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS (MODERN, CLEAN, FIX ALL BUTTONS) ---
st.markdown("""
<style>
    /* 1. Paksa Background Putih Bersih */
    .stApp {
        background-color: #FFFFFF; 
    }
    
    /* 2. Judul Header */
    .main-header {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 800;
        color: #111;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 5px;
        font-size: 2.2rem;
        letter-spacing: -1px;
    }
    
    .sub-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: #666;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 40px;
        font-weight: 400;
    }

    /* 3. FIX LABEL AGAR TERLIHAT & CENTER */
    .stFileUploader label, div[data-testid="stSelectbox"] label {
        width: 100% !important;
        text-align: center !important;
        display: block !important;
        color: #111 !important; /* Hitam Pekat */
        font-size: 1rem !important;
        font-weight: 600 !important;
        margin-bottom: 8px !important;
    }

    /* 4. FIX TEXT CAPTION */
    .stCaption, div[data-testid="stCaptionContainer"], small, p {
        color: #444444 !important; 
    }
    
    /* 5. FIX SEMUA TOMBOL (Start & Download) */
    /* Kita targetkan stButton DAN stDownloadButton sekaligus */
    div.stButton > button, div.stDownloadButton > button {
        width: 100%;
        background-color: #000000 !important; /* Background Hitam Pekat */
        color: #FFFFFF !important; /* Teks Putih Terang */
        border: 1px solid #000000;
        padding: 14px 20px;
        font-size: 16px;
        font-weight: 700;
        border-radius: 8px;
        transition: all 0.2s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Target khusus elemen text di dalam tombol agar tidak diubah browser */
    div.stButton > button p, div.stDownloadButton > button p {
        color: #FFFFFF !important;
    }
    
    /* Efek Hover untuk kedua tombol */
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #333333 !important;
        color: #FFFFFF !important; 
        border-color: #333333;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    div.stButton > button:active, div.stDownloadButton > button:active {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }
    
    /* 6. Footer Link */
    .footer-link {
        text-decoration: none; 
        font-weight: 700; 
        color: #e74c3c !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIKA FFMPEG (HYBRID: CLOUD & LOCAL)
# ==========================================
project_folder = os.getcwd()
local_ffmpeg = os.path.join(project_folder, "ffmpeg.exe")
local_ffprobe = os.path.join(project_folder, "ffprobe.exe")

# Logika Deteksi: Cek Local Dulu -> Kalau Gak Ada, Cek Sistem (Cloud)
if os.path.exists(local_ffmpeg) and os.path.exists(local_ffprobe):
    # Mode Local (Windows Laptop Mas Tommy)
    ffmpeg_cmd = local_ffmpeg
    ffprobe_cmd = local_ffprobe
    os.environ["PATH"] += os.pathsep + project_folder
else:
    # Mode Cloud (Server Linux Streamlit)
    if which("ffmpeg") and which("ffprobe"):
        ffmpeg_cmd = "ffmpeg"
        ffprobe_cmd = "ffprobe"
    else:
        st.error("❌ Critical Error: FFmpeg tools not found.")
        st.stop()

def get_duration(file_path):
    cmd = [
        ffprobe_cmd, 
        "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        file_path
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return float(output)
    except:
        return 0.0

# ==========================================
# 3. UI LAYOUT
# ==========================================

st.markdown('<div class="main-header">🎙️ Tommy\'s STT</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Konversi Audio ke Teks (Unlimited)</div>', unsafe_allow_html=True)

# --- INPUT SECTION (SUPPORT SEMUA FORMAT HP) ---
uploaded_file = st.file_uploader(
    "📂 Pilih File Audio (Support Semua Format)", 
    type=["aac", "mp3", "wav", "m4a", "opus", "mp4", "3gp", "amr", "ogg", "flac", "wma"]
)

st.write("") 

c1, c2, c3 = st.columns([1, 4, 1]) 

with c2:
    lang_choice = st.selectbox("Pilih Bahasa", ("Indonesia", "Inggris"))
    st.write("") 
    submit_btn = st.button("🚀 Mulai Transkrip", use_container_width=True)

# --- OUTPUT SECTION ---
if submit_btn and uploaded_file:
    st.markdown("---")
    
    status_box = st.empty()
    progress_bar = st.progress(0)
    result_area = st.empty()
    full_transcript = []
    
    file_ext = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        input_path = tmp_file.name

    try:
        duration_sec = get_duration(input_path)
        if duration_sec == 0:
            st.error("Gagal membaca durasi. File mungkin corrupt.")
            st.stop()
            
        chunk_len = 59 
        total_chunks = math.ceil(duration_sec / chunk_len)
        
        status_box.info(f"⏱️ Durasi: {duration_sec:.2f} detik | Memproses {total_chunks} bagian...")
        
        recognizer = sr.Recognizer()
        lang_code = "id-ID" if lang_choice == "Indonesia" else "en-US"

        for i in range(total_chunks):
            start_time = i * chunk_len
            chunk_filename = f"temp_slice_{i}.wav"
            
            # Gunakan variabel ffmpeg_cmd yang sudah dideteksi di atas
            cmd = [
                ffmpeg_cmd, "-y", "-i", input_path,
                "-ss", str(start_time), "-t", str(chunk_len),
                "-ar", "16000", "-ac", "1", chunk_filename
            ]
            
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            try:
                with sr.AudioFile(chunk_filename) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data, language=lang_code)
                    full_transcript.append(text)
                    result_area.text_area("📝 Live Preview:", " ".join(full_transcript), height=250)
            except sr.UnknownValueError:
                pass 
            except Exception:
                full_transcript.append("") 
            finally:
                if os.path.exists(chunk_filename):
                    os.remove(chunk_filename)
            
            pct = int(((i + 1) / total_chunks) * 100)
            progress_bar.progress(pct)
            status_box.caption(f"Sedang memproses... ({pct}%)")

        status_box.success("✅ Selesai!")
        final_text = " ".join(full_transcript)
        
        st.download_button(
            label="💾 Download Hasil (.TXT)", 
            data=final_text, 
            file_name="transkrip.txt", 
            mime="text/plain",
            use_container_width=True 
        )

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

# ==========================================
# 4. FOOTER
# ==========================================
st.markdown("<br><br>", unsafe_allow_html=True) 
st.markdown("---") 
st.markdown(
    """
    <div style="text-align: center; font-size: 13px; color: #888; font-family: sans-serif;">
        Powered by &nbsp;
        <a href="https://espeje.com" target="_blank" class="footer-link">espeje.com</a> 
        &nbsp;&amp;&nbsp; 
        <a href="https://link-gr.id" target="_blank" class="footer-link">link-gr.id</a>
    </div>
    <div style="margin-bottom: 20px;"></div>
    """,
    unsafe_allow_html=True
)
