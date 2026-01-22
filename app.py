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

# --- CUSTOM CSS (TAMPILAN FINAL: Tombol Putih, Notif Gelap) ---
st.markdown("""
<style>
    /* Background Putih */
    .stApp { background-color: #FFFFFF; }
    
    /* Header */
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
        margin-bottom: 30px;
        font-weight: 400;
    }

    /* Label Input (Hitam) */
    .stFileUploader label, div[data-testid="stSelectbox"] label, .stAudioInput label {
        width: 100% !important;
        text-align: center !important;
        display: block !important;
        color: #111 !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        margin-bottom: 8px !important;
    }

    /* Notifikasi & Teks Biasa (Abu Gelap) */
    .stCaption, div[data-testid="stCaptionContainer"], small, p {
        color: #444444 !important; 
    }
    
    /* TOMBOL (Hitam Pekat, Teks WAJIB Putih) */
    div.stButton > button, div.stDownloadButton > button {
        width: 100%;
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #000000;
        padding: 14px 20px;
        font-size: 16px;
        font-weight: 700;
        border-radius: 8px;
        transition: all 0.2s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Memaksa teks DI DALAM tombol menjadi PUTIH */
    div.stButton > button p, div.stDownloadButton > button p {
        color: #FFFFFF !important;
    }
    
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #333333 !important;
        color: #FFFFFF !important; 
        transform: translateY(-2px);
    }
    
    /* Tips Box (Kuning) */
    .mobile-tips {
        background-color: #FFF3CD;
        color: #856404;
        padding: 10px;
        border-radius: 8px;
        font-size: 0.9rem;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid #FFEEBA;
    }
    /* Paksa teks di dalam box kuning berwarna coklat (bukan abu) */
    .mobile-tips p, .mobile-tips b, .mobile-tips small { color: #856404 !important; }

    /* Footer */
    .footer-link { text-decoration: none; font-weight: 700; color: #e74c3c !important; }
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

st.markdown('<div class="main-header">🎙️ Tommy\'s STT</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Konversi Rapat & Jarak Jauh (Booster Aktif)</div>', unsafe_allow_html=True)

# --- NOTIFIKASI KEMBALI SEPERTI SEMULA ---
st.markdown("""
<div class="mobile-tips">
    📱 <b>Tips Pengguna HP:</b><br>
    Saat proses upload & transkrip berjalan, <b>jangan biarkan layar mati atau berpindah aplikasi</b> agar koneksi tidak terputus.<br>
    <small>(Fitur Booster Volume 300% Tetap Aktif)</small>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📂 Upload File", "🎙️ Rekam Suara"])
audio_to_process = None
source_name = "audio"

with tab1:
    uploaded_file = st.file_uploader("Pilih File Audio (Support Semua Format)", type=["aac", "mp3", "wav", "m4a", "opus", "mp4", "3gp", "amr", "ogg", "flac", "wma"])
    if uploaded_file:
        audio_to_process = uploaded_file
        source_name = uploaded_file.name

with tab2:
    audio_mic = st.audio_input("Klik ikon mic untuk mulai merekam")
    if audio_mic:
        audio_to_process = audio_mic
        source_name = "rekaman_mic.wav"

st.write("") 
c1, c2, c3 = st.columns([1, 4, 1]) 
with c2:
    lang_choice = st.selectbox("Pilih Bahasa Audio", ("Indonesia", "Inggris"))
    st.write("") 
    if audio_to_process:
        submit_btn = st.button("🚀 Mulai Transkrip", use_container_width=True)
    else:
        st.info("👆 Silakan Upload atau Rekam dulu.")
        submit_btn = False

if submit_btn and audio_to_process:
    st.markdown("---")
    
    status_box = st.empty()
    progress_bar = st.progress(0)
    result_area = st.empty()
    full_transcript = []
    
    if source_name == "rekaman_mic.wav":
        file_ext = ".wav"
    else:
        file_ext = os.path.splitext(source_name)[1]
        if not file_ext: file_ext = ".wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_file.write(audio_to_process.getvalue())
        input_path = tmp_file.name

    try:
        duration_sec = get_duration(input_path)
        if duration_sec == 0:
            st.error("Gagal membaca audio.")
            st.stop()
            
        chunk_len = 59 
        total_chunks = math.ceil(duration_sec / chunk_len)
        status_box.info(f"⏱️ Durasi: {duration_sec:.2f}s | Booster Volume 300% Aktif 🔊")
        
        recognizer = sr.Recognizer()
        # Setting Sensitif
        recognizer.energy_threshold = 300 
        recognizer.dynamic_energy_threshold = True 
        
        lang_code = "id-ID" if lang_choice == "Indonesia" else "en-US"

        for i in range(total_chunks):
            start_time = i * chunk_len
            chunk_filename = f"temp_slice_{i}.wav"
            
            # FFMPEG VOLUME BOOST 3x
            cmd = [
                ffmpeg_cmd, "-y", "-i", input_path,
                "-ss", str(start_time), "-t", str(chunk_len),
                "-filter:a", "volume=3.0", 
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
        st.download_button("💾 Download Hasil (.TXT)", final_text, "transkrip.txt", "text/plain", use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

# Footer
st.markdown("<br><br><hr>", unsafe_allow_html=True) 
st.markdown("""<div style="text-align: center; font-size: 13px; color: #888;">Powered by <a href="https://espeje.com" target="_blank" class="footer-link">espeje.com</a> & <a href="https://link-gr.id" target="_blank" class="footer-link">link-gr.id</a></div>""", unsafe_allow_html=True)
