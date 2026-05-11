import streamlit as st
from PIL import Image, ImageChops, ImageEnhance
from PIL.ExifTags import TAGS
import numpy as np
import os

# --- ฟังก์ชัน AI วิเคราะห์พิกเซล (ELA) ---
def run_ela(original_image, quality=90):
    temp_path = "temp_resaved.jpg"
    if original_image.mode != 'RGB':
        original_image = original_image.convert('RGB')
    
    # บันทึกภาพใหม่เพื่อเช็กระดับการบีบอัด
    original_image.save(temp_path, 'JPEG', quality=quality)
    resaved_image = Image.open(temp_path)
    
    # คำนวณหาความต่าง (จุดที่ถูกตัดต่อจะมีความต่างสูง)
    ela_image = ImageChops.difference(original_image, resaved_image)
    
    # ปรับความสว่างเพื่อให้ตาคนมองเห็นจุดผิดปกติได้ชัดเจน
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0: max_diff = 1
    scale = 255.0 / max_diff
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
    return ela_image

# --- ฟังก์ชันดึงข้อมูล Metadata ---
def get_exif_data(image):
    exif_data = {}
    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif_data[decoded] = value
    except:
        return None
    return exif_data

# --- ส่วนแสดงผลบนหน้าเว็บ (UI) ---
st.set_page_config(page_title="AI Image Guard", layout="wide")

st.title("🛡️ AI Image Forgery Detection")
st.write("ระบบตรวจสอบการปลอมแปลงรูปภาพด้วยเทคนิค ELA และ Metadata Analysis")

uploaded_file = st.file_uploader("📤 อัปโหลดรูปภาพ (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    
    # สร้างคอลัมน์เพื่อเปรียบเทียบ
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🖼️ ภาพต้นฉบับ")
        st.image(img, use_container_width=True)
        
    with col2:
        st.subheader("🔍 วิเคราะห์พิกเซล (ELA)")
        ela_result = run_ela(img)
        st.image(ela_result, use_container_width=True)
        st.info("คำแนะนำ: จุดที่สว่างโดดเด่นออกมาผิดปกติ คือบริเวณที่มีโอกาสถูกตัดต่อสูง")

    st.divider()

    # วิเคราะห์ข้อมูล Metadata
    st.subheader("📋 ข้อมูลเบื้องหลังไฟล์ (Metadata)")
    metadata = get_exif_data(img)
    
    if metadata:
        software = str(metadata.get("Software", "ไม่พบข้อมูลโปรแกรม"))
        st.write(f"**ซอฟต์แวร์ที่ใช้:** {software}")
        if "Adobe" in software or "Photoshop" in software:
            st.error("🚨 ตรวจพบร่องรอยการใช้โปรแกรม Adobe Photoshop")
        else:
            st.success("✅ ไม่พบชื่อโปรแกรมตัดต่อยอดนิยมในไฟล์")
            
        with st.expander("คลิกเพื่อดูรายละเอียด Metadata ทั้งหมด"):
            st.write(metadata)
    else:
        st.warning("⚠️ ไม่พบข้อมูล Metadata (ภาพอาจถูกลบข้อมูลออก หรือถูกส่งผ่านแอปแชท)")
