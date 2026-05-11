import streamlit as st
from PIL import Image, ImageChops, ImageEnhance
from PIL.ExifTags import TAGS
import os

# --- ฟังก์ชันที่ 1: ตรวจสอบการบีบอัดภาพ (ELA) ---
def run_ela(original_image, quality=90):
    temp_path = "temp_resaved.jpg"
    if original_image.mode != 'RGB':
        original_image = original_image.convert('RGB')
    
    # บันทึกภาพใหม่ด้วยคุณภาพที่กำหนด
    original_image.save(temp_path, 'JPEG', quality=quality)
    resaved_image = Image.open(temp_path)
    
    # หาความต่างระหว่างภาพเดิมกับภาพที่บีบอัดใหม่
    ela_image = ImageChops.difference(original_image, resaved_image)
    
    # ขยายค่าความสว่างเพื่อให้เห็นจุดที่ถูกแก้ไขได้ชัดเจน
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0: max_diff = 1
    scale = 255.0 / max_diff
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
    return ela_image

# --- ฟังก์ชันที่ 2: ดึงข้อมูล Metadata (EXIF) ---
def get_exif_data(image):
    exif_data = {}
    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif_data[decoded] = value
    except Exception as e:
        return {"Error": "ไม่สามารถดึงข้อมูลได้ หรือไฟล์ไม่มี Metadata"}
    return exif_data

# --- ส่วนของการจัดหน้าตาเว็บไซต์ (UI) ---
st.set_page_config(page_title="AI Image Guard", layout="wide")

st.title("🛡️ AI Image Forgery Detection System")
st.markdown("""
ระบบนี้ใช้เทคนิค **ELA** และ **Metadata Analysis** เพื่อช่วยตรวจสอบความโปร่งใสของรูปภาพ 
โดยมองหาจุดบกพร่องจากการบีบอัดพิกเซลและการแก้ไขผ่านซอฟต์แวร์
""")

uploaded_file = st.file_uploader("📤 อัปโหลดรูปภาพที่ต้องการตรวจสอบ (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    
    # แบ่งหน้าจอเป็น 2 คอลัมน์
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🖼️ ภาพต้นฉบับ")
        st.image(img, use_container_width=True)
        
    with col2:
        st.subheader("🔍 วิเคราะห์ด้วย ELA")
        with st.spinner('กำลังประมวลผล...'):
            ela_result = run_ela(img)
            st.image(ela_result, use_container_width=True)
            st.caption("จุดที่สว่างผิดปกติในโซนเดียวกัน อาจเป็นร่องรอยการตัดต่อ")

    st.divider()

    # ส่วนแสดง Metadata
    st.subheader("📋 ข้อมูลเบื้องหลังภาพ (Metadata / EXIF)")
    metadata = get_exif_data(img)
    
    if metadata and "Error" not in metadata:
        # แสดงผลในรูปแบบตารางหรือ JSON ให้ดูง่าย
        col_meta1, col_meta2 = st.columns(2)
        
        # ค้นหาชื่อ Software ที่ใช้แต่งภาพ
        software = metadata.get("Software", "ไม่ระบุ")
        model = metadata.get("Model", "ไม่ระบุอุปกรณ์")
        date_time = metadata.get("DateTime", "ไม่ระบุเวลาถ่าย")

        with col_meta1:
            st.metric("ซอฟต์แวร์ที่ตรวจพบ", software)
            if "Adobe" in software or "Photoshop" in software:
                st.error("⚠️ พบหลักฐานการใช้โปรแกรมตกแต่งภาพ (Adobe Family)")
            else:
                st.success("✅ ไม่พบชื่อซอฟต์แวร์ตัดต่อยอดนิยมใน Metadata")

        with col_meta2:
            st.write(f"**รุ่นกล้อง:** {model}")
            st.write(f"**วันที่ถ่าย:** {date_time}")
            
        with st.expander("ดูข้อมูล Metadata ทั้งหมด"):
            st.write(metadata)
    else:
        st.warning("⚠️ ไม่พบข้อมูล Metadata: ภาพนี้อาจถูกลบข้อมูลออก หรือถูกเซฟมาจาก Social Media ซึ่งปกติจะลบค่า EXIF ทิ้ง")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tips:** ภาพจริงผล ELA จะดูเรียบกลืนกันทั้งภาพ ส่วนภาพตัดต่อ จุดที่แก้มักจะสว่างโดดออกมา")
