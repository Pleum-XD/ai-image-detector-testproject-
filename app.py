import streamlit as st
from PIL import Image, ImageChops, ImageEnhance
from PIL.ExifTags import TAGS
import numpy as np
import cv2
import os

# --- 1. ELA: ตรวจการตัดต่อพิกเซล ---
def run_ela_analysis(image, quality=90):
    temp_path = "temp_ela.jpg"
    image.convert('RGB').save(temp_path, 'JPEG', quality=quality)
    resaved = Image.open(temp_path)
    ela_image = ImageChops.difference(image.convert('RGB'), resaved)
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    scale = 255.0 / (max_diff if max_diff > 0 else 1)
    return ImageEnhance.Brightness(ela_image).enhance(scale), max_diff

# --- 2. FFT Analysis: ตรวจสอบความผิดปกติของความถี่ภาพ (AI Signature) ---
def analyze_fft(image):
    img_gray = np.array(image.convert('L'))
    dft = np.fft.fft2(img_gray)
    dft_shift = np.fft.fftshift(dft)
    magnitude_spectrum = 20 * np.log(np.abs(dft_shift) + 1)
    
    # คำนวณหาค่าความผิดปกติในย่านความถี่สูง 
    # (ภาพจริงจะมี Noise กระจายตัวเป็นธรรมชาติ แต่ AI มักมีรูปแบบซ้ำๆ)
    h, w = img_gray.shape
    center_h, center_w = h // 2, w // 2
    inner_radius = min(h, w) // 4
    
    # สร้าง Mask เพื่อดูเฉพาะความถี่รอบนอก (High Frequency)
    y, x = np.ogrid[:h, :w]
    mask = (x - center_w)**2 + (y - center_h)**2 > inner_radius**2
    high_freq_mean = np.mean(magnitude_spectrum[mask])
    
    # ปรับภาพ FFT ให้ดูง่าย
    fft_display = (magnitude_spectrum / magnitude_spectrum.max() * 255).astype(np.uint8)
    return fft_display, high_freq_mean

# --- 3. Noise & Sharpness (ตรวจความเนียนผิดปกติ) ---
def analyze_noise_stat(image):
    img_gray = np.array(image.convert('L'))
    noise_extract = img_gray.astype(np.float32) - cv2.medianBlur(img_gray, 3).astype(np.float32)
    noise_std = np.std(noise_extract)
    laplacian_var = cv2.Laplacian(img_gray, cv2.CV_64F).var()
    return noise_std, laplacian_var

# --- หน้า UI ---
st.set_page_config(page_title="AI Forensic Specialist", layout="wide")
st.title("🛡️ Ultimate Forensic & AI Image Analyzer")

uploaded_file = st.file_uploader("📤 อัปโหลดรูปภาพ...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    risk_score = 0
    reasons = []

    with st.spinner('ระบบกำลังสแกนพิกเซลและโครงสร้างความถี่...'):
        ela_img, ela_diff = run_ela_analysis(img)
        fft_img, fft_val = analyze_fft(img)
        n_std, l_var = analyze_noise_stat(img)

        # --- ตรรกะการให้คะแนน (Multi-Criteria Scoring) ---
        
        # 1. ตรวจ Metadata
        exif = img._getexif()
        if exif:
            meta = {TAGS.get(t, t): v for t, v in exif.items()}
            if "Software" in meta:
                risk_score += 30
                reasons.append(f"🚩 พบร่องรอยซอฟต์แวร์แก้ไขภาพ: {meta['Software']}")
        else:
            risk_score += 10
            reasons.append("ℹ️ ไม่พบ Metadata (ปกติสำหรับภาพจากโซเชียล)")

        # 2. ตรวจการตัดต่อ (ELA)
        if ela_diff > 60:
            risk_score += 30
            reasons.append("🚩 พบร่องรอยการบีบอัดพิกเซลไม่เท่ากัน (เสี่ยงต่อการตัดต่อ)")

        # 3. ตรวจสอบร่องรอย AI (FFT & Sharpness)
        # ภาพ AI มักจะมีความถี่บางส่วนที่ "เป็นระเบียบเกินไป" หรือ "เนียนผิดปกติ"
        if l_var < 80:
            risk_score += 25
            reasons.append("🤖 ภาพมีความเนียนผิดปกติ (AI Smoothness Pattern)")
        if fft_val < 100:
            risk_score += 15
            reasons.append("🤖 โครงสร้างความถี่ภาพไม่สมบูรณ์ (Synthetic Signature)")

    # --- แสดงผลลัพธ์ ---
    col_v, col_r = st.columns([2, 1])

    with col_v:
        t1, t2, t3 = st.tabs(["Original", "ELA Analysis", "Frequency Spectrum (FFT)"])
        t1.image(img, use_container_width=True)
        t2.image(ela_img, use_container_width=True, caption="จุดที่สว่างคือจุดที่น่าสงสัย")
        t3.image(fft_img, use_container_width=True, caption="ลายเส้นในนี้บ่งบอกถึงโครงสร้างดิจิทัลของภาพ")

    with col_r:
        st.subheader("📊 ผลการประเมิน")
        total_risk = min(risk_score, 100)
        
        if total_risk >= 70:
            st.error(f"ระดับความเสี่ยง: {total_risk}% (อันตรายสูง)")
        elif total_risk >= 40:
            st.warning(f"ระดับความเสี่ยง: {total_risk}% (น่าสงสัย)")
        else:
            st.success(f"ระดับความเสี่ยง: {total_risk}% (ปลอดภัย)")
            
        st.progress(total_risk / 100)
        
        st.write("**สิ่งที่ตรวจพบ:**")
        for r in reasons: st.markdown(f"- {r}")
        
        with st.expander("ดูค่าทางเทคนิค"):
            st.write(f"ELA Diff: {ela_diff:.2f}")
            st.write(f"FFT Mean: {fft_val:.2f}")
            st.write(f"Sharpness (Laplacian): {l_var:.2f}")

st.info("💡 หมายเหตุ: ระบบนี้ใช้การวิเคราะห์ทางสถิติพิกเซล หากต้องการตรวจสอบภาพ AI จาก Google อย่างเป็นทางการ แนะนำให้ใช้เครื่องมือที่รองรับ SynthID โดยตรง")
