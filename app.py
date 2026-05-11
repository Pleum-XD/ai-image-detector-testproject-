import streamlit as st
from PIL import Image, ImageChops, ImageEnhance
from PIL.ExifTags import TAGS
import numpy as np
import cv2
import os

# --- 1. ฟังก์ชัน ELA (ตรวจการตัดต่อ/บีบอัดพิกเซล) ---
def run_ela_analysis(image, quality=90):
    temp_path = "temp_ela.jpg"
    image.convert('RGB').save(temp_path, 'JPEG', quality=quality)
    resaved = Image.open(temp_path)
    ela_image = ImageChops.difference(image.convert('RGB'), resaved)
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    scale = 255.0 / (max_diff if max_diff > 0 else 1)
    return ImageEnhance.Brightness(ela_image).enhance(scale), max_diff

# --- 2. ฟังก์ชัน Noise & AI Pattern (ตรวจความเนียนผิดปกติของ AI) ---
def analyze_advanced_patterns(image):
    img_gray = np.array(image.convert('L'))
    
    # ดึง Noise ออกมา
    noise_extract = img_gray.astype(np.float32) - cv2.medianBlur(img_gray, 3).astype(np.float32)
    noise_std = np.std(noise_extract)
    
    # ตรวจสอบ Laplacian Variance (ความคมชัด/รายละเอียดระดับลึก)
    # ภาพ AI มักจะมีความเนียนในบางจุดที่กล้องจริงทำไม่ได้
    laplacian_var = cv2.Laplacian(img_gray, cv2.CV_64F).var()
    
    noise_display = (np.abs(noise_extract) / (np.abs(noise_extract).max() or 1) * 255).astype(np.uint8)
    return noise_display, noise_std, laplacian_var

# --- หน้าจอหลัก UI ---
st.set_page_config(page_title="AI Forensic Specialist", layout="wide")
st.title("🔬 Advanced Image & AI Content Analyzer")
st.markdown("ระบบวิเคราะห์ความเสี่ยงการตัดต่อและการสร้างภาพด้วย AI แบบมัลติฟังก์ชัน")

uploaded_file = st.file_uploader("📤 อัปโหลดรูปภาพที่สงสัย...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    risk_score = 0
    reasons = []

    # --- เริ่มการประมวลผล ---
    with st.spinner('กำลังวิเคราะห์เชิงลึก...'):
        ela_display, ela_diff = run_ela_analysis(img)
        noise_display, noise_std, lap_var = analyze_advanced_patterns(img)
        
        # --- ตรรกะการคำนวณคะแนน (Logic) ---
        
        # ก) เช็ค Metadata
        exif = img._getexif()
        if exif:
            meta = {TAGS.get(t, t): v for t, v in exif.items() if t in TAGS}
            soft = str(meta.get("Software", ""))
            if any(x in soft for x in ["Adobe", "Photoshop", "GIMP", "Canva"]):
                risk_score += 30
                reasons.append(f"🚩 ตรวจพบโปรแกรมแก้ไขภาพ: {soft}")
        else:
            # ไม่หักคะแนนเยอะเพราะอาจมาจากโซเชียล
            risk_score += 10 
            reasons.append("ℹ️ ไม่พบ Metadata (ปกติสำหรับภาพจาก Facebook/Line)")

        # ข) เช็คการตัดต่อ (ELA)
        if ela_diff > 60:
            risk_score += 35
            reasons.append("🚩 พิกเซลมีความต่างระดับสูง (เสี่ยงต่อการตัดแปะ)")

        # ค) เช็คความผิดปกติแบบ AI (Noise & Smoothness)
        # ภาพ AI มักจะเนียน (Laplacian ต่ำ) หรือไม่มี Noise (STD ต่ำ)
        if lap_var < 100:
            risk_score += 25
            reasons.append("🤖 ภาพมีความเนียนผิดปกติ (AI-Generated Pattern Risk)")
        elif noise_std < 1.0:
            risk_score += 20
            reasons.append("🤖 ไม่พบสัญญาณรบกวนตามธรรมชาติ (Digital Synthetic Risk)")

    # --- ส่วนการแสดงผล ---
    col_view, col_stat = st.columns([2, 1])

    with col_view:
        tab1, tab2, tab3 = st.tabs(["Original", "ELA Analysis", "Digital Noise"])
        tab1.image(img, use_container_width=True)
        tab2.image(ela_display, use_container_width=True, caption="จุดสว่างบ่งบอกถึงการแก้ไข")
        tab3.image(noise_display, use_container_width=True, caption="โครงสร้างเม็ด Noise ของภาพ")

    with col_stat:
        st.subheader("📊 สรุปผลการตรวจสอบ")
        final_score = min(risk_score, 100)
        
        if final_score >= 70:
            st.error(f"ความเสี่ยงโดยรวม: {final_score}%")
            st.write("**สถานะ: อันตรายสูง (High Risk)**")
        elif final_score >= 35:
            st.warning(f"ความเสี่ยงโดยรวม: {final_score}%")
            st.write("**สถานะ: ควรระวัง (Suspicious)**")
        else:
            st.success(f"ความเสี่ยงโดยรวม: {final_score}%")
            st.write("**สถานะ: ปกติ (Likely Original)**")
            
        st.progress(final_score / 100)
        
        st.write("---")
        st.write("**หลักฐานที่พบ:**")
        for r in reasons:
            st.write(r)
        
        st.write(f"**ค่าสถิติเทคนิค:**")
        st.write(f"- ELA Diff: {ela_diff:.2f}")
        st.write(f"- Noise Std: {noise_std:.2f}")
        st.write(f"- Sharpness Score: {lap_var:.2f}")

st.sidebar.markdown("### วิธีอ่านผล")
st.sidebar.info("หากภาพมาจาก Facebook แล้วขึ้นความเสี่ยง 10-20% ถือว่าเป็นเรื่องปกติเพราะระบบ Metadata หาย แต่ถ้าแตะ 40% ขึ้นไป ให้ดูที่แถบ ELA ว่ามีจุดสว่างวาบผิดปกติหรือไม่")
