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
    page_title="STT Pro", 
    page_icon="🎙️", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS (UNTUK TAMPILAN MODERN) ---
st.markdown("""
<style>
    /* Mengubah background utama menjadi abu-abu sangat muda */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Membuat Container 'Card' putih dengan shadow */
    .css-card {
        border-radius: 15px;
        padding: 25px;
        background-color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #E0E0E0;
    }
    
    /* Judul Aplikasi yang Modern */
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        color: #1E1E1E;
        text-align: center;
        margin-bottom: 10px;
        font-size: 2rem;
    }
    
    .sub-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: #757575;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 30px;
    }

    /* Styling Tombol Utama */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #FF4B4B 0%, #FF6B6B 100%);
        color: white;
        border: none;
        padding: 12px 20px;
        font-weight: 600;
        border-radius: 12px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(255, 75, 75, 0.2);
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(255, 75, 75, 0.3);
        background: linear-gradient(90deg, #FF3B3B 0%, #FF5B5B 100%);
        border: none;
        color: white;
    }

    /* Styling File Uploader agar lebih rapi */
    .stFileUploader {
        padding: 10px;
    }

    /* Text Area Hasil */
    .stTextArea textarea {
        border-radius: 10px;
        border: 1px solid #E0E0E0;
        font-family: 'Courier New', Courier, monospace;
        font-size: 14px;
    }
    
    /* Footer Styling */
    .footer-link {
        text-decoration: none; 
        font-weight: 600; 
        color: #FF4B4B;
        transition: color 0.3s;
    }
    .footer-link:hover {
        color: #D32F2F;
        text-decoration: underline;
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
st.markdown('<div class="main-header">🎙️ STT Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Konversi Audio ke Teks (Unlimited Duration)</div>', unsafe_allow_html=True)

# --- CONTAINER 1: INPUT ---
st.markdown('<div class="css-card">', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "📂 Pilih File Audio (AAC, MP3, WAV, M4A, OPUS)", 
    type=["aac", "mp3", "wav", "m4a", "opus"]
)

col1, col2 = st.columns(2)
with col1:
    lang_choice = st.selectbox("Bahasa Audio", ("Indonesia", "Inggris"))
with col2:
    # Spacer agar sejajar jika perlu, atau fitur lain
    st.write("") 
    st.write("") # Spacer visual

submit_btn = st.button("🚀 Mulai Proses Transkrip")

st.markdown('</div>', unsafe_allow_html=True) # End Card 1


# --- CONTAINER 2: PROCESS & OUTPUT ---
if submit_btn and uploaded_file:
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    
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
                    
                    # Update Preview dalam card
                    result_area.text_area(
                        "📝 Live Preview:", 
                        " ".join(full_transcript), 
                        height=250
                    )
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
        
        # Tombol Download dengan gaya Streamlit standar (karena download button sulit di-style CSS custom)
        st.markdown("---")
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

    st.markdown('</div>', unsafe_allow_html=True) # End Card 2


# ==========================================
# 4. FOOTER
# ==========================================
st.markdown("<br><br>", unsafe_allow_html=True) # Spacer
st.markdown("---") 
st.markdown(
    """
    <div style="text-align: center; font-size: 13px; color: #888; font-family: sans-serif;">
        Powered by &nbsp;
        <a href="https://espeje.com" target="_blank" class="footer-link">espeje.com</a> 
        &nbsp;&bull;&nbsp; 
        <a href="https://link-gr.id" target="_blank" class="footer-link">link-gr.id</a>
    </div>
    <div style="text-align: center; font-size: 11px; color: #BBB; margin-top: 5px;">
        Versi 2.0 &copy; 2026
    </div>
    """,
    unsafe_allow_html=True
)
