import streamlit as st
import speech_recognition as sr
import os
import subprocess
import math
import tempfile
from shutil import which # Library untuk mendeteksi lokasi ffmpeg di sistem

st.set_page_config(page_title="Tommy's STT Online", page_icon="📲", layout="centered")

# ==========================================
# 🛠️ KONFIGURASI FFMPEG (HYBRID: WINDOWS & LINUX)
# ==========================================
# 1. Cek apakah ada ffmpeg portable di folder project (Untuk Local Windows)
project_folder = os.getcwd()
local_ffmpeg = os.path.join(project_folder, "ffmpeg.exe")
local_ffprobe = os.path.join(project_folder, "ffprobe.exe")

if os.path.exists(local_ffmpeg) and os.path.exists(local_ffprobe):
    # Mode Local (Windows)
    ffmpeg_cmd = local_ffmpeg
    ffprobe_cmd = local_ffprobe
    # Inject path agar subprocess aman
    os.environ["PATH"] += os.pathsep + project_folder
    st.sidebar.success("🟢 Mode: Local Windows (Portable)")
else:
    # Mode Cloud (Linux/Server) - Cek path sistem
    if which("ffmpeg") and which("ffprobe"):
        ffmpeg_cmd = "ffmpeg"
        ffprobe_cmd = "ffprobe"
        st.sidebar.success("☁️ Mode: Cloud Server (Linux)")
    else:
        # Jika tidak ditemukan di manapun
        st.error("❌ FFmpeg tidak ditemukan! (Cek packages.txt atau file .exe)")
        st.stop()

# ==========================================

st.title("🎙️ STT Tommy")
st.markdown("Upload audio, biarkan server yang memprosesnya.")

# Fungsi Helper: Cek Durasi (Menggunakan command yang sudah dideteksi di atas)
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

# Upload File
uploaded_file = st.file_uploader("Upload Audio (AAC/MP3/WAV)", type=["aac", "mp3", "wav", "m4a"])
lang_choice = st.selectbox("Bahasa:", ("Indonesia", "Inggris"))

if st.button("Mulai Transkrip") and uploaded_file:
    st.divider()
    status_box = st.empty()
    progress_bar = st.progress(0)
    result_area = st.empty()
    
    full_transcript = []
    
    # 1. Simpan file fisik sementara
    file_ext = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        input_path = tmp_file.name

    try:
        # 2. Cek Durasi
        duration_sec = get_duration(input_path)
        if duration_sec == 0:
            st.error("Gagal membaca durasi file audio.")
            st.stop()
            
        chunk_len = 59 
        total_chunks = math.ceil(duration_sec / chunk_len)
        
        status_box.info(f"📂 Durasi: {duration_sec:.2f}s | Total: {total_chunks} bagian.")
        
        recognizer = sr.Recognizer()
        lang_code = "id-ID" if lang_choice == "Indonesia" else "en-US"

        # 3. Loop Slicing
        for i in range(total_chunks):
            start_time = i * chunk_len
            chunk_filename = f"temp_slice_{i}.wav"
            
            # Gunakan ffmpeg_cmd yang sudah dideteksi (bisa .exe atau command linux)
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
                    result_area.text_area("📝 Preview:", " ".join(full_transcript), height=300)
            except sr.UnknownValueError:
                pass 
            except Exception as e:
                full_transcript.append("") 
            finally:
                if os.path.exists(chunk_filename):
                    os.remove(chunk_filename)
            
            pct = int(((i + 1) / total_chunks) * 100)
            progress_bar.progress(pct)
            status_box.write(f"⏳ Memproses bagian {i+1} dari {total_chunks}...")

        # Selesai
        status_box.success("✅ Selesai!")
        final_text = " ".join(full_transcript)
        
        st.download_button("Download .TXT", final_text, file_name="transkrip.txt", mime="text/plain")

    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

# ==========================================
# 🦶 FOOTER SECTION
# ==========================================
st.markdown("---") # Garis pembatas
st.markdown(
    """
    <div style="text-align: center; font-size: 14px; color: #666;">
        Powered by 
        <a href="https://espeje.com" target="_blank" style="text-decoration: none; font-weight: bold; color: #FF4B4B;">espeje.com</a> 
        & 
        <a href="https://link-gr.id" target="_blank" style="text-decoration: none; font-weight: bold; color: #FF4B4B;">link-gr.id</a>
    </div>
    """,
    unsafe_allow_html=True
)
