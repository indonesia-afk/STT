import streamlit as st
import speech_recognition as sr
import os
import subprocess
import math
import tempfile
from shutil import which

# ==========================================
# 1. SETUP & CONFIG
# ==========================================
st.set_page_config(
    page_title="Tommy's STT", 
    page_icon="🎙️", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS (TAMPILAN BERSIH & CENTERED) ---
st.markdown("""
<style>
    /* Background Bersih */
    .stApp {
        background-color: #FFFFFF; 
    }
    
    /* Judul Header */
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

    /* --- UPDATE: LABEL RATA TENGAH --- */
    /* Target Label File Uploader & Selectbox agar Center */
    .stFileUploader label, div[data-testid="stSelectbox"] label {
        width: 100% !important;
        text-align: center !important;
        display: block !important;
        color: #111 !important; /* Warna Hitam Jelas */
        font-size: 1rem !important;
        font-weight: 600 !important;
        margin-bottom: 8px !important;
    }
    
    /* Tombol Utama */
    div.stButton > button {
        width: 100%;
        background: #000000; /* Hitam Elegan */
        color: white;
        border: none;
        padding: 14px 20px;
        font-size: 16px;
        font-weight: 700;
        border-radius: 8px;
        transition: all 0.2s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    div.stButton > button:hover {
        background: #333333;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        color: white;
    }
    
    /* Footer Link */
    .footer-link {
        text-decoration: none; 
        font-weight: 700; 
        color: #e74c3c;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIKA FFMPEG (HYBRID)
# ==========================================
project_folder = os.getcwd()
local_ffmpeg = os.path.join(project_folder, "ffmpeg.exe")
local_ffprobe = os.path.join(project_folder, "ffprobe.exe")

if os.path.exists(local_ffmpeg) and os.path.exists(local_ffprobe):
    ffmpeg_cmd = local_ffmpeg
    ffprobe_cmd = local_ffprobe
    os.environ["PATH"] += os.pathsep + project_folder
else:
    if which("ffmpeg") and which("ffprobe"):
        ffmpeg_cmd = "ffmpeg"
        ffprobe_cmd = "ffprobe"
    else:
        st.error("❌ Critical Error: FFmpeg tools not found.")
        st.stop()

def get_duration(file_path):
    cmd = [ffprobe_cmd, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    try:
        return float(subprocess.check_output(cmd, stderr=subprocess.STDOUT))
    except:
        return 0.0

# ==========================================
# 3. UI LAYOUT
# ==========================================

# Header
st.markdown('<div class="main-header">🎙️ Tommy\'s STT</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Konversi Audio ke Teks (Unlimited)</div>', unsafe_allow_html=True)

# 1. INPUT SECTION
# File Uploader
uploaded_file = st.file_uploader(
    "📂 Pilih File Audio (AAC, MP3, WAV, M4A, OPUS)", 
    type=["aac", "mp3", "wav", "m4a", "opus"]
)

st.write("") # Spacer

# Pilihan Bahasa & Tombol (Rata Tengah)
c1, c2, c3 = st.columns([1, 4, 1]) 

with c2:
    lang_choice = st.selectbox("Pilih Bahasa", ("Indonesia", "Inggris"))
    st.write("") 
    submit_btn = st.button("🚀 Mulai Transkrip", use_container_width=True)

# 2. OUTPUT SECTION
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
            st.error("File audio corrupt atau format tidak didukung.")
            st.stop()
            
        chunk_len = 59 
        total_chunks = math.ceil(duration_sec / chunk_len)
        
        status_box.info(f"⏱️ Durasi: {duration_sec:.2f} detik | Memproses {total_chunks} bagian...")
        
        recognizer = sr.Recognizer()
        lang_code = "id-ID" if lang_choice == "Indonesia" else "en-US"

        for i in range(total_chunks):
            start_time = i * chunk_len
            chunk_filename = f"temp_slice_{i}.wav"
            
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
# 4. FOOTER (UPDATED)
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
