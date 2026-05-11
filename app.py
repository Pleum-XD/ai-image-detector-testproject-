import streamlit as st
from PIL import Image, ImageChops, ImageEnhance
from PIL.ExifTags import TAGS
import numpy as np
import os

# --- ฟังก์ชัน ELA และส่งคืนค่าความต่างสูงสุด ---
def run_ela_analysis(image, quality=90):
    temp_path = "temp_ela.jpg"
    image.convert('RGB').save(temp_path, 'JPEG', quality=quality)
    resaved = Image.open(temp_path)
    ela_image = ImageChops.difference(image.convert('RGB'), resaved)
    
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    
    # ปรับแสงโชว์ผู้ใช้
    scale = 255.0 / (max_diff if max_diff > 0 else 1)
    ela_display = ImageEnhance.Brightness(ela_image).enhance(scale)
    
    os.remove(temp_path)
    return ela_display, max_diff

# --- ส่วน UI ---
st.set_page_config(page_title="AI Risk Analyzer", layout="wide")
st.title("🛡️ Advanced Image Risk Analysis")
st.write("วิเคราะห์ความเสี่ยงจากการปลอมแปลงภาพด้วยการตรวจสอบหลายมิติ")

uploaded_file = st.file_uploader("📤 อัปโหลดรูปภาพ...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    risk_score = 0
    reasons = []

    # 1. ตรวจสอบ Metadata
    exif = img._getexif()
    if exif:
        metadata = {TAGS.get(tag, tag): val for tag, val in exif.items() if tag in TAGS}
        software = str(metadata.get("Software", ""))
        if "Adobe" in software or "Photoshop" in software:
            risk_score += 40
            reasons.append("🚩 ตรวจพบการใช้ซอฟต์แวร์ตัดต่อระดับมืออาชีพ (Photoshop)")
    else:
        risk_score += 20
        reasons.append("⚠️ ไม่พบข้อมูล Metadata (ภาพอาจถูกลบข้อมูลเพื่อปกปิดร่องรอย)")

    # 2. ตรวจสอบ ELA
    ela_img, diff_value = run_ela_analysis(img)
    if diff_value > 50: # ค่าความต่างพิกเซลสูง
        risk_score += 40
        reasons.append("🚩 ตรวจพบความผิดปกติของระดับพิกเซล (ELA High Variance)")

    # --- แสดงผลลัพธ์ ---
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🖼️ ภาพวิเคราะห์")
        st.image(img, use_container_width=True, caption="Original")
        st.image(ela_img, use_container_width=True, caption="ELA Analysis")

    with col2:
        st.subheader("📊 การประเมินความเสี่ยง")
        
        # แสดง Gauge คะแนนความเสี่ยง
        if risk_score >= 70:
            st.error(f"ระดับความเสี่ยง: {risk_score}% (อันตรายสูง)")
        elif risk_score >= 30:
            st.warning(f"ระดับความเสี่ยง: {risk_score}% (ปานกลาง)")
        else:
            st.success(f"ระดับความเสี่ยง: {risk_score}% (ปลอดภัย)")

        st.progress(risk_score / 100)
        
        st.write("**รายละเอียดที่ตรวจพบ:**")
        if reasons:
            for r in reasons:
                st.write(r)
        else:
            st.write("✅ ไม่พบสิ่งผิดปกติเบื้องต้น")

    st.divider()
    st.info("💡 หมายเหตุ: ระบบนี้ใช้การประมวลผลเชิงสถิติพิกเซลและข้อมูลไฟล์ ผลลัพธ์เป็นการประเมินเบื้องต้นเท่านั้น")
