import streamlit as st
from PIL import Image, ImageChops, ImageEnhance
import os

# ฟังก์ชันหัวใจหลัก: ตรวจสอบระดับการบีบอัดภาพ (ELA)
def run_ela(original_image, quality=90):
    temp_path = "temp_resaved.jpg"
    # เซฟภาพใหม่ด้วยคุณภาพ 90% เพื่อดูความต่าง
    original_image.save(temp_path, 'JPEG', quality=quality)
    resaved_image = Image.open(temp_path)
    
    # คำนวณหาจุดที่พิกเซลเปลี่ยนไป
    ela_image = ImageChops.difference(original_image, resaved_image)
    
    # ปรับแสงให้จุดที่ต่างกันสว่างขึ้นเพื่อให้คนดูง่าย
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0: max_diff = 1
    scale = 255.0 / max_diff
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
    
    os.remove(temp_path)
    return ela_image

# ส่วนหน้าตาเว็บ (UI)
st.set_page_config(page_title="Image Forgery Detector", layout="wide")
st.title("🔍 AI Image Forgery Detector")
st.write("เครื่องมือตรวจจับการตัดต่อรูปภาพด้วยเทคนิค Error Level Analysis (ELA)")

uploaded_file = st.file_uploader("ลากไฟล์รูปภาพมาวางที่นี่ (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file).convert('RGB')
    
    col1, col2 = st.columns(2)
    with col1:
        st.header("Original Image")
        st.image(img, use_container_width=True)
        
    with col2:
        st.header("ELA Analysis")
        with st.spinner('กำลังวิเคราะห์...'):
            ela_result = run_ela(img)
            st.image(ela_result, use_container_width=True)
            st.info("คำแนะนำ: จุดที่สว่างโดดออกมาจากพื้นหลังอย่างผิดปกติ มักจะเป็นบริเวณที่มีการตัดต่อหรือแก้ไข")
