import streamlit as st
from PIL import Image, ImageChops, ImageEnhance
from PIL.ExifTags import TAGS
import numpy as np
import cv2
from skimage import filters
import os

# --- ฟังก์ชัน 1: ELA Analysis ---
def run_ela_analysis(image, quality=90):
    temp_path = "temp_ela.jpg"
    image.convert('RGB').save(temp_path, 'JPEG', quality=quality)
    resaved = Image.open(temp_path)
    ela_image = ImageChops.difference(image.convert('RGB'), resaved)
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    scale = 255.0 / (max_diff if max_diff > 0 else 1)
    return ImageEnhance.Brightness(ela_image).enhance(scale), max_diff

# --- ฟังก์ชัน 2: Noise Pattern Analysis ---
def analyze_noise(image):
    # แปลงภาพเป็นขาวดำและเป็น Numpy array
    img_gray = np.array(image.convert('L'))
    # ใช้ Median Filter เพื่อหาค่าเฉลี่ย และลบออกจากภาพเดิมเพื่อดึงเฉพาะ Noise
    noise_extract = img_gray.astype(np.float32) - cv2.medianBlur(img_gray, 3).astype(np.float32)
    # คำนวณค่าความแปรปรวนของ Noise (Variance)
    noise_std = np.std(noise_extract)
    # ทำภาพ Noise ให้ดูง่ายขึ้นเพื่อแสดงผล
    noise_display = np.abs(noise_extract)
    noise_display = (noise_display / noise_display.max() * 255).astype(np.uint8)
    return noise_display, noise_std

# --- หน้า UI ---
st.set_page_config(page_title="Forensic AI Analyzer", layout="wide")
st.title("🔬 Forensic Image Risk Analyzer (Multi-Check)")

uploaded_file = st.file_uploader("📤 อัปโหลดรูปภาพ...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    risk_score = 0
    reasons = []

    # --- ประมวลผล ---
    ela_display, ela_diff = run_ela_analysis(img)
    noise_display, noise_val = analyze_noise(img)
    
    # --- ตรรกะการประเมินความเสี่ยง ---
    # 1. Check Metadata
    exif = img._getexif()
    if exif:
        soft = str({TAGS.get(t, t): v for t, v in exif.items()}.get("Software", ""))
        if any(x in soft for x in ["Adobe", "Photoshop", "GIMP", "Canva"]):
            risk_score += 35
            reasons.append(f"🚩 ตรวจพบร่องรอยซอฟต์แวร์: {soft}")
    else:
        risk_score += 15
        reasons.append("⚠️ ไม่พบ Metadata (ข้อมูลไฟล์ถูกล้าง)")

    # 2. Check ELA
    if ela_diff > 60:
        risk_score += 35
        reasons.append("🚩 พิกเซลผิดปกติ (ELA High Variance)")

    # 3. Check Noise
    if noise_val < 2.0 or noise_val > 15.0: # ค่า Noise ที่นิ่งเกินไปหรือโดดเกินไป
        risk_score += 30
        reasons.append("🚩 โครงสร้าง Noise ไม่เป็นธรรมชาติ (Noise Inconsistency)")

    # --- แสดงผล ---
    col_img, col_res = st.columns([2, 1])
    
    with col_img:
        t1, t2, t3 = st.tabs(["Original", "ELA Analysis", "Noise Pattern"])
        t1.image(img, use_container_width=True)
        t2.image(ela_display, use_container_width=True)
        t3.image(noise_display, use_container_width=True, clamp=True)

    with col_res:
        st.subheader("📊 ผลการประเมิน")
        st.metric("Total Risk Score", f"{min(risk_score, 100)}%")
        st.progress(min(risk_score, 100) / 100)
        
        if risk_score >= 70: st.error("🚨 ระดับอันตราย: พบหลักฐานการตัดต่อชัดเจน")
        elif risk_score >= 40: st.warning("⚠️ ระดับเฝ้าระวัง: พบความผิดปกติหลายจุด")
        else: st.success("✅ ระดับปลอดภัย: ไม่พบร่องรอยการดัดแปลง")
        
        st.write("**รายละเอียดที่พบ:**")
        for r in reasons: st.write(r)
