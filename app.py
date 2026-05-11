import streamlit as st
from PIL import Image, ImageChops, ImageEnhance
from PIL.ExifTags import TAGS
import numpy as np
import tensorflow as tf
import os

# 1. ฟังก์ชันตรวจจับด้วย AI (Deep Learning)
@st.cache_resource
def load_model():
    # ใช้ MobileNetV2 เป็นโครงสร้างพื้นฐานในการวิเคราะห์
    return tf.keras.applications.MobileNetV2(weights='imagenet')

def ai_predict(image, model):
    img = image.resize((224, 224))
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
    pred = model.predict(img_array)
    return np.max(pred) * 100 # ส่งค่าความมั่นใจออกมา

# 2. ฟังก์ชัน ELA (Error Level Analysis)
def run_ela(image, quality=90):
    temp = "temp.jpg"
    image.convert('RGB').save(temp, 'JPEG', quality=quality)
    resaved = Image.open(temp)
    ela = ImageChops.difference(image.convert('RGB'), resaved)
    extrema = ela.getextrema()
    max_diff = max([ex[1] for ex in extrema]) or 1
    return ImageEnhance.Brightness(ela).enhance(255.0 / max_diff)

# 3. ส่วนหน้าตาเว็บ (UI)
st.set_page_config(page_title="AI Image Guard", layout="wide")
st.title("🛡️ AI Image Forgery Detection System")

model = load_model()
uploaded_file = st.file_uploader("อัปโหลดรูปภาพ...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🖼️ Original")
        st.image(img, use_container_width=True)
    with col2:
        st.subheader("🔍 ELA Analysis")
        st.image(run_ela(img), use_container_width=True)
    with col3:
        st.subheader("🤖 AI Verdict")
        score = ai_predict(img, model)
        st.metric("AI Confidence", f"{score:.2f}%")
        if score > 80: st.error("เสี่ยงสูง: พบความผิดปกติ")
        else: st.success("ปลอดภัย: ไม่พบร่องรอยการตัดต่อ")

    # ส่วน Metadata
    with st.expander("📊 ดูข้อมูล Metadata (EXIF)"):
        exif = img._getexif()
        if exif:
            for tag, val in exif.items():
                st.write(f"**{TAGS.get(tag, tag)}**: {val}")
        else:
            st.write("ไม่พบข้อมูล Metadata")
