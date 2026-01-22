import streamlit as st
import speech_recognition as sr
import os
import subprocess
import math
import tempfile
import streamlit.components.v1 as components
from shutil import which

# ==========================================
# 1. SETUP & CONFIG
# ==========================================
st.set_page_config(
    page_title="TOM'STT", 
    page_icon="🎙️", 
    layout="centered",
    initial_sidebar_state="expanded" # Sidebar dibuka untuk tombol Reset
)

# --- CUSTOM CSS (FINAL UI) ---
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF !important; }
    
    /* Header Style */
    .main-header {
        font-family: 'Arial Black', sans-serif;
        font-weight: 900;
        color: #111111 !important;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 5px;
        font-size: 2.5rem;
        letter-spacing: -1px;
        text-transform: uppercase;
    }
    .sub-header {
        font-family: -apple-system, sans-serif;
        color: #666666 !important;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 30px;
        font-weight: 500;
    }

    /* Label & Input */
    .stFileUploader label, div[data-testid="stSelectbox"] label, .stAudioInput label {
        color: #000000 !important;
        text-align: center !important;
        font-weight: 700 !important;
        display: block !important;
        width: 100% !important;
    }

    /* Uploader Area */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #F0F2F6 !important; 
        border: 1px dashed #444 !important;
        border-radius: 12px;
    }
    [data-testid="stFileUploaderDropzone"] div div::before { color: #333333 !important; }
    [data-testid="stFileUploaderDropzone"] small { display: none !important; }
    [data-testid="stFileUploaderDropzone"] > div > div::after {
        content: "Limit 200MB per file";
        color: #555555;
        font-size: 0.85rem;
        margin-top: 5px;
        display: block;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    div[data-testid="stFileUploaderFileName"] { color: #000000 !important; font-weight: 600 !important; }

    /* Tombol Utama */
    div.stButton > button, div.stDownloadButton > button {
        width: 100%;
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #000000;
        padding: 14px 20px;
        font-size: 16px;
        font-weight: 700;
        border-radius: 10px;
        transition: all 0.2s;
    }
    div.stButton > button p, div.stDownloadButton > button p { color: #FFFFFF !important; }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #333333 !important;
        transform: translateY(-2px);
    }

    /* Tips & Info Box */
    .mobile-tips {
        background-color: #FFF3CD;
        color: #856404;
        padding: 12px;
        border-radius: 10px;
        font-size: 0.9rem;
        text-align: center;
        margin-bottom: 25px;
        border: 1px solid #FFEEBA;
    }
    .mobile-tips b { color: #856404 !important; }
    
    .custom-info-box {
        background-color: #e6f3ff;
        color: #0068c9;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: 600;
        border: 1px solid #cce5ff;
        margin-bottom: 20px;
    }

    /* Footer */
    .footer-link { text-decoration: none; font-weight: 700; color: #e74c3c !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIKA FFMPEG
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
        # Fallback jika error, jangan stop dulu agar Tab Live tetap jalan
        ffmpeg_cmd = "ffmpeg" 
        ffprobe_cmd = "ffprobe"

def get_duration(file_path):
    cmd = [ffprobe_cmd, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    try:
        return float(subprocess.check_output(cmd, stderr=subprocess.STDOUT))
    except:
        return 0.0

# ==========================================
# 3. SIDEBAR (RESET BUTTON)
# ==========================================
with st.sidebar:
    st.header("Menu")
    st.write("Jika ganti file tidak merespon, klik tombol ini:")
    if st.button("🔄 Reset / Mulai Baru", use_container_width=True):
        st.rerun()

# ==========================================
# 4. MAIN LAYOUT
# ==========================================
st.markdown("""
<div class="main-header">
    🎙️ TOM'<span style="color: #e74c3c;">STT</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="sub-header">Speech-to-Text | Konversi Audio ke Teks</div>', unsafe_allow_html=True)

st.markdown("""
<div class="mobile-tips">
    <b>Tips Pengguna Handphone:</b><br>
    Saat proses upload berjalan, <b>jangan biarkan layar mati</b>.<br>
    Untuk rapat panjang, gunakan menu <b>Live Transkrip</b>.
</div>
""", unsafe_allow_html=True)

# --- TAB SELECTION ---
tab1, tab2, tab3 = st.tabs(["📂 Upload File", "🎙️ Rekam (File)", "🔴 Live Transkrip"])

# --- TAB 1 & 2: LOGIKA FILE (EXISTING) ---
audio_to_process = None
source_name = "audio"

with tab1:
    uploaded_file = st.file_uploader("Pilih File Audio", type=["aac", "mp3", "wav", "m4a", "opus", "mp4", "3gp", "amr", "ogg", "flac", "wma"])
    if uploaded_file:
        audio_to_process = uploaded_file
        source_name = uploaded_file.name

with tab2:
    st.caption("Mode ini merekam file audio (.wav) lalu diproses setelah stop.")
    audio_mic = st.audio_input("Klik ikon mic untuk mulai merekam")
    if audio_mic:
        audio_to_process = audio_mic
        source_name = "rekaman_mic.wav"

# --- TAB 3: LIVE TRANSCRIPT (HTML/JS INJECTION) ---
with tab3:
    st.info("💡 Mode ini menggunakan Browser API. Teks muncul langsung (Real-time). Tidak menghasilkan file audio, hanya teks.")
    
    # HTML/JS Script untuk Web Speech API
    components.html(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Live STT</title>
            <style>
                body { font-family: sans-serif; text-align: center; color: #333; }
                #start_btn {
                    background-color: #e74c3c; color: white; border: none; padding: 15px 30px;
                    font-size: 18px; border-radius: 50px; cursor: pointer; font-weight: bold;
                    margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                }
                #start_btn:hover { background-color: #c0392b; }
                #final_span { color: #000; font-weight: 600; }
                #interim_span { color: #888; }
                #results {
                    border: 2px dashed #ccc; padding: 20px; min-height: 150px;
                    text-align: left; background: #f9f9f9; border-radius: 10px;
                    margin-top: 20px; font-size: 1.1rem; line-height: 1.6;
                }
                select { padding: 10px; margin-bottom: 20px; border-radius: 5px; border: 1px solid #ddd; }
            </style>
        </head>
        <body>
            <div>
                <select id="lang_select">
                    <option value="id-ID">Bahasa Indonesia</option>
                    <option value="en-US">English (US)</option>
                </select>
                <br>
                <button id="start_btn" onclick="toggleStart()">🎙️ Mulai Live Transkrip</button>
            </div>
            <div id="results">
                <span id="final_span"></span>
                <span id="interim_span"></span>
            </div>
            <p style="font-size: 12px; color: #999;">Silakan Copy teks manual setelah selesai.</p>

            <script>
                var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.continuous = true;
                recognition.interimResults = true;
                
                var recognizing = false;
                var final_transcript = '';
                var start_btn = document.getElementById('start_btn');
                var lang_select = document.getElementById('lang_select');

                recognition.onstart = function() {
                    recognizing = true;
                    start_btn.innerHTML = "⏹️ Stop Transkrip";
                    start_btn.style.backgroundColor = "#333";
                };

                recognition.onerror = function(event) {
                    console.log('Error: ' + event.error);
                };

                recognition.onend = function() {
                    recognizing = false;
                    start_btn.innerHTML = "🎙️ Mulai Live Transkrip";
                    start_btn.style.backgroundColor = "#e74c3c";
                };

                recognition.onresult = function(event) {
                    var interim_transcript = '';
                    for (var i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) {
                            final_transcript += event.results[i][0].transcript + '. ';
                            // Auto Scroll
                            window.scrollTo(0,document.body.scrollHeight);
                        } else {
                            interim_transcript += event.results[i][0].transcript;
                        }
                    }
                    document.getElementById('final_span').innerHTML = final_transcript;
                    document.getElementById('interim_span').innerHTML = interim_transcript;
                };

                function toggleStart() {
                    if (recognizing) {
                        recognition.stop();
                        return;
                    }
                    final_transcript = '';
                    recognition.lang = lang_select.value;
                    recognition.start();
                    document.getElementById('final_span').innerHTML = '';
                    document.getElementById('interim_span').innerHTML = '';
                }
            </script>
        </body>
        </html>
        """,
        height=500, # Tinggi area HTML
        scrolling=True
    )

# --- PROSESOR UNTUK TAB 1 & 2 ---
if (tab1 or tab2) and not tab3: # Logika UI biasa
    st.write("") 
    c1, c2, c3 = st.columns([1, 4, 1]) 
    with c2:
        # Hanya tampilkan tombol proses di Tab 1 & 2
        if audio_to_process:
            lang_choice = st.selectbox("Pilih Bahasa Audio", ("Indonesia", "Inggris"))
            st.write("") 
            submit_btn = st.button("🚀 Mulai Transkrip", use_container_width=True)
        elif not audio_to_process and (source_name == "audio" or source_name == "rekaman_mic.wav"):
            # Jika belum ada file di tab 1/2, tampilkan pesan
            # Kita cek tab mana yg aktif agak susah di streamlit murni, 
            # jadi kita tampilkan pesan di placeholder yang aman.
            st.markdown("""
                <div class="custom-info-box">
                    👆 Silakan Upload atau Rekam terlebih dahulu.
                </div>
            """, unsafe_allow_html=True)
            submit_btn = False
        else:
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
                st.error("Gagal membaca audio. File corrupt atau format tak didukung.")
                st.stop()
                
            chunk_len = 59 
            total_chunks = math.ceil(duration_sec / chunk_len)
            status_box.info(f"⏱️ Durasi: {duration_sec:.2f}s")
            
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300 
            recognizer.dynamic_energy_threshold = True 
            
            lang_code = "id-ID" if lang_choice == "Indonesia" else "en-US"

            for i in range(total_chunks):
                start_time = i * chunk_len
                chunk_filename = f"temp_slice_{i}.wav"
                
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
            
            base_name = os.path.splitext(source_name)[0]
            output_filename = f"{base_name}.txt"
            
            st.download_button(
                label=f"💾 Download {output_filename}", 
                data=final_text, 
                file_name=output_filename, 
                mime="text/plain", 
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)

st.markdown("<br><br><hr>", unsafe_allow_html=True) 
st.markdown("""<div style="text-align: center; font-size: 13px; color: #888;">Powered by <a href="https://espeje.com" target="_blank" class="footer-link">espeje.com</a> & <a href="https://link-gr.id" target="_blank" class="footer-link">link-gr.id</a></div>""", unsafe_allow_html=True)
