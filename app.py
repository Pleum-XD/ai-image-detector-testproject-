import streamlit as st
from PIL import Image, ImageChops, ImageEnhance
from PIL.ExifTags import TAGS
import numpy as np
import cv2
import os

# --- 🎨 Custom Styling (CSS) ---
st.set_page_config(page_title="AI Forensic Pro", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stAlert {
        border-radius: 10px;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3e4255;
    }
    div[data-testid="stExpander"] {
        border: none !important;
        background-color: #161b22;
        border-radius: 10px;
    }
    h1 {
        color: #00ffcc;
        font-family: 'Courier New', Courier, monospace;
        text-align: center;
        text-shadow: 2px 2px #000;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🧪 Core Functions (เหมือนเดิมแต่ปรับจูนความเร็ว) ---
def run_ela(image, quality=90):
    temp = "temp_ela.jpg"
    image.convert('RGB').save(temp, 'JPEG', quality=quality)
    resaved = Image.open(temp)
    ela = ImageChops.difference(image.convert('RGB'), resaved)
    extrema = ela.getextrema()
    max_diff = max([ex[1] for ex in extrema]) or 1
    os.remove(temp)
    return ImageEnhance.Brightness(ela).enhance(255.0/max_diff), max_diff

def analyze_patterns(image):
    img_gray = np.array(image.convert('L'))
    noise = img_gray.astype(np.float32) - cv2.medianBlur(img_gray, 3).astype(np.float32)
    lap_var = cv2.Laplacian(img_gray, cv2.CV_64F).var()
    noise_disp = (np.abs(noise) / (np.abs(noise).max() or 1) * 255).astype(np.uint8)
    return noise_disp, np.std(noise), lap_var

# --- 🛠️ Sidebar Configuration ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2092/2092663.png", width=100)
    st.title("Settings")
    st.info("ระบบจะวิเคราะห์ภาพโดยอัตโนมัติเมื่ออัปโหลดเสร็จ")
    ela_quality = st.slider("ELA Sensitivity", 50, 100, 90)
    st.divider()
    st.markdown("### 👤 พัฒนาโดย\n[ชื่อของคุณ/GitHub]")

# --- 🚀 Main UI ---
st.markdown("<h1>🛡️ AI FORENSIC ANALYSIS ENGINE</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e;'>ตรวจสอบความถูกต้องของรูปภาพด้วยระบบ Multi-Layer Forensic</p>", unsafe_allow_html=True)
st.divider()

uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    
    # วิเคราะห์ข้อมูล
    with st.spinner('🛠️ กำลังถอดรหัสพิกเซล...'):
        ela_img, ela_val = run_ela(img, ela_quality)
        noise_img, n_std, l_var = analyze_patterns(img)
        
        # คำนวณความเสี่ยง (Logic)
        risk = 0
        reasons = []
        if ela_val > 60: risk += 40; reasons.append("พิกเซลผิดปกติ (ELA)")
        if l_var < 100: risk += 30; reasons.append("ความเนียนของภาพสูงผิดปกติ (AI Smoothness)")
        if n_std < 1.0: risk += 20; reasons.append("ไม่พบเม็ด Noise ตามธรรมชาติ")
        
    # --- Layout การแสดงผล ---
    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        tab_orig, tab_ela, tab_noise = st.tabs(["🖼️ ภาพต้นฉบับ", "🔍 ELA Scan", "📡 Noise Pattern"])
        tab_orig.image(img, use_container_width=True)
        tab_ela.image(ela_img, use_container_width=True)
        tab_noise.image(noise_img, use_container_width=True)

    with col_right:
        st.subheader("📊 ผลการวิเคราะห์")
        
        # Risk Score UI
        final_risk = min(risk, 100)
        color = "#00ffcc" if final_risk < 40 else "#ffcc00" if final_risk < 70 else "#ff4b4b"
        
        st.markdown(f"""
            <div style="text-align: center; border: 2px solid {color}; padding: 20px; border-radius: 15px;">
                <h2 style="margin: 0; color: {color};">{final_risk}%</h2>
                <p style="margin: 0; color: white;">Risk Probability</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.progress(final_risk / 100)
        
        if final_risk >= 70: st.error("🚨 ตรวจพบร่องรอยการดัดแปลงชัดเจน")
        elif final_risk >= 40: st.warning("⚠️ พบความเสี่ยงปานกลาง")
        else: st.success("✅ ภาพมีแนวโน้มเป็นของจริง")

        with st.expander("📝 รายละเอียดทางเทคนิค"):
            for r in reasons: st.write(f"- {r}")
            st.code(f"ELA Diff: {ela_val:.2f}\nNoise Std: {n_std:.2f}\nSharpness: {l_var:.2f}")

    # --- Metadata Section ---
    st.divider()
    with st.expander("🔍 ตรวจสอบ Metadata เชิงลึก (EXIF)"):
        exif = img._getexif()
        if exif:
            meta = {TAGS.get(t, t): v for t, v in exif.items() if t in TAGS}
            st.json(meta)
        else:
            st.info("ไม่พบข้อมูล Metadata ในไฟล์นี้")
