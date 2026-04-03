import streamlit as st
import google.generativeai as genai
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
import time
from datetime import datetime, timedelta
import math
import random
import os
from geopy.geocoders import Nominatim


GEMINI_KEYS = [
    SECRET
]

OWM_API_KEY = "SECRET"
TOMTOM_API_KEY = "Secret"
TRAFFIC_DB_FILE = "traffic_db.csv"

st.set_page_config(page_title="AUA | Antares Eco Monitor", page_icon="🍃", layout="wide")


if 'ai_response' not in st.session_state:
    st.session_state.ai_response = ""
if 'last_lat' not in st.session_state:
    st.session_state.last_lat = 43.2567
if 'last_lon' not in st.session_state:
    st.session_state.last_lon = 76.9286
if 'address' not in st.session_state:
    st.session_state.address = "Алматы, Казахстан"


with st.sidebar:
    st.image("School.png", width=200, use_container_width=True) 
    st.markdown("<h3 style='text-align: center;'>Team: Antares</h3>", unsafe_allow_html=True)
    st.write("---")
    theme = st.radio("Режим отображения:", ["Тёмная тема 🌙", "Светлая тема ☀️"], horizontal=True)
    dark_mode = (theme == "Тёмная тема 🌙")
    st.write("---")
    st.info("Проект **AUA** — интеллектуальный мониторинг качества воздуха и дорожного трафика.")


if dark_mode:
    app_bg = """
        background-color: #060b14;
        background-image: 
            linear-gradient(rgba(6, 11, 20, 0.88), rgba(6, 11, 20, 0.88)), 
            url('https://images.unsplash.com/photo-1522030299830-16b8d3d049fe?q=80&w=2500&auto=format&fit=crop');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    """
    text_color = "#F8FAFC"
    card_bg = "rgba(13, 20, 33, 0.65)"
    border_color = "rgba(255, 255, 255, 0.08)"
    accent_color = "#10b981" 
    gradient_text = "linear-gradient(45deg, #34d399, #3b82f6)"
    map_tiles = "cartodbdark_matter"
    box_shadow = "0 8px 32px 0 rgba(0,0,0,0.4)"
else:
    app_bg = """
        background-color: #f8fafc;
        background-image: 
            linear-gradient(rgba(248, 250, 252, 0.88), rgba(248, 250, 252, 0.88)), 
            url('https://images.unsplash.com/photo-1536882240095-0379873feb4e?q=80&w=2500&auto=format&fit=crop');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    """
    text_color = "#0f172a"
    green = "#64bc61"
    card_bg = "rgba(255, 255, 255, 0.85)"
    border_color = "#64bc61"
    accent_color = "#059669" 
    gradient_text = "linear-gradient(45deg, #059669, #2563eb)"
    map_tiles = "cartodbpositron"
    box_shadow = "0 8px 32px 0 rgba(0,0,0,0.05)"

st.markdown(f"""
    <style>
    [data-testid="stHeader"] {{ background-color: transparent !important; }}
    .stApp {{ {app_bg} }}
    p, span, label, li {{ color: {text_color} !important; }}
    [data-testid="stSidebar"] {{ 
        background-color: {card_bg} !important; backdrop-filter: blur(16px) saturate(180%); border-right: 1px solid {border_color}; 
    }}
    h1, h2, h3, h4, h5, h6 {{ color: {text_color} !important; font-weight: 700; letter-spacing: -0.5px; }}
    
    .main-title {{
        background: {gradient_text}; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 900; font-size: 3.2rem; margin-bottom: 0.2rem; color: transparent !important; 
        text-shadow: 0px 4px 20px rgba(16, 185, 129, 0.1);
    }}
    
    div[data-testid="metric-container"] {{
        background-color: {card_bg}; border: 1px solid {border_color}; padding: 24px; border-radius: 20px;
        box-shadow: {box_shadow}; backdrop-filter: blur(16px) saturate(180%); transition: transform 0.3s, box-shadow 0.3s;
    }}
    div[data-testid="metric-container"]:hover {{ transform: translateY(-6px); box-shadow: 0 15px 45px rgba(0,0,0,0.5); border-color: rgba(16, 185, 129, 0.3); }}
    
    div[data-testid="stMetricLabel"] > div {{ color: {text_color} !important; opacity: 0.7; font-size: 1.1rem; text-transform: uppercase; }}
    div[data-testid="stMetricValue"] > div {{ color: {text_color} !important; font-weight: 900 !important; font-size: 2.2rem !important; }}
    
    .stButton>button {{
        background: {gradient_text} !important; color: white !important; border-radius: 14px; font-weight: 800; font-size: 1.1rem; border: none; height: 60px; width: 100%; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);
    }}
    .stButton>button:hover {{ filter: brightness(1.2); transform: translateY(-3px); }}
    
    .stAlert {{ 
        background-color: {card_bg} !important; border-radius: 20px !important; border: 1px solid {border_color} !important;
        border-left: 6px solid {accent_color} !important; backdrop-filter: blur(16px);
    }}
    .stAlert p {{ font-size: 1.05rem; line-height: 1.7; }}

    @media (max-width: 768px) {{
        .main-title {{ font-size: 2rem !important; text-align: center; }}
        div[data-testid="metric-container"] {{ padding: 15px !important; }}
        div[data-testid="stMetricValue"] > div {{ font-size: 1.6rem !important; }}
        .stButton>button {{ height: 50px; font-size: 1rem; }}
    }}
    </style>
    """, unsafe_allow_html=True)


def get_address_name(lat, lon):
    try:
        geolocator = Nominatim(user_agent="antares_monitor")
        location = geolocator.reverse(f"{lat}, {lon}", language='ru')
        if location:
            parts = location.address.split(',')
            return ", ".join(parts[:3])
        return "Неизвестный район"
    except:
        return "Алматы (координаты)"

def get_weather_data(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OWM_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        aqi_raw = data['list'][0]['main']['aqi']
        pm25 = data['list'][0]['components']['pm2_5']
        mapping = {1: "Отлично ✨", 2: "Средне 👍", 3: "Умеренно 😐", 4: "Плохо 😷", 5: "Опасно 🛑"}
        return aqi_raw, pm25, mapping.get(aqi_raw, "Неизвестно")
    except:
        return 0, 0, "Ошибка связи"

def get_real_traffic(lat, lon):
    if not TOMTOM_API_KEY: return 0, "🔑", "Нужен ключ"
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={lat},{lon}&key={TOMTOM_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        current_speed = data['flowSegmentData']['currentSpeed']
        free_flow_speed = data['flowSegmentData']['freeFlowSpeed']
        if free_flow_speed == 0: return 0, "0", "Нет данных"
        ratio = current_speed / free_flow_speed
        
        traffic_score = round((1 - ratio) * 10)
        traffic_score = max(0, min(10, traffic_score)) 
        
        if ratio >= 0.85: return traffic_score, "1-2", "Свободно 🟢"
        elif ratio >= 0.65: return traffic_score, "3-4", "Рабочее движение 🟢"
        elif ratio >= 0.45: return traffic_score, "5-6", "Плотное движение 🟡"
        elif ratio >= 0.25: return traffic_score, "7-8", "Серьезные заторы 🟠"
        else: return traffic_score, "9-10", "Дорога стоит 🔴"
    except:
        return 0, "-", "Вне дороги 🚶‍♂️"

def get_historical_data_with_db(lat, lon, current_traffic_score):
    end_time = int(time.time())
    start_time = end_time - (24 * 3600) 
    
    now = datetime.now()
    current_hour_str = now.strftime('%Y-%m-%d %H:00')
    r_lat, r_lon = round(lat, 2), round(lon, 2)
    
    if os.path.exists(TRAFFIC_DB_FILE):
        df_db = pd.read_csv(TRAFFIC_DB_FILE)
    else:
        df_db = pd.DataFrame(columns=["lat", "lon", "time", "score"])
        
    df_db = df_db[~((df_db['lat'] == r_lat) & (df_db['lon'] == r_lon) & (df_db['time'] == current_hour_str))]
    new_data = pd.DataFrame([{"lat": r_lat, "lon": r_lon, "time": current_hour_str, "score": current_traffic_score}])
    df_db = pd.concat([df_db, new_data], ignore_index=True)
    df_db.to_csv(TRAFFIC_DB_FILE, index=False)

    url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={start_time}&end={end_time}&appid={OWM_API_KEY}"
    times, aqi_list, pm25_list, traffic_list = [], [], [], []
    
    try:
        response = requests.get(url).json()
        history = response['list'][-24:] 
        
        random.seed(f"{lat}_{lon}")
        traffic_multiplier = max(0.3, current_traffic_score / 6.0) 
        
        for i, item in enumerate(history):
            dt = datetime.fromtimestamp(item['dt'])
            dt_str = dt.strftime('%Y-%m-%d %H:00')
            times.append(dt.strftime('%H:00'))
            aqi_list.append(item['main']['aqi'])
            pm25_list.append(item['components']['pm2_5'])
            
            real_saved_traffic = df_db[(df_db['lat'] == r_lat) & (df_db['lon'] == r_lon) & (df_db['time'] == dt_str)]
            
            if not real_saved_traffic.empty:
                traffic_list.append(real_saved_traffic.iloc[0]['score'])
            else:
                hour = dt.hour
                if 0 <= hour <= 6: base_traffic = 1.0
                elif 7 <= hour <= 10: base_traffic = 7.0 - abs(hour - 8.5)
                elif 11 <= hour <= 16: base_traffic = 4.0
                elif 17 <= hour <= 20: base_traffic = 8.0 - abs(hour - 18.5)
                else: base_traffic = 2.0
                
                sim_traffic = (base_traffic * traffic_multiplier) + random.uniform(-1.0, 1.0)
                traffic_list.append(round(max(0, min(10, sim_traffic)), 1))
                
    except Exception as e:
        times = [f"{h:02d}:00" for h in range(24)]
        aqi_list = [0] * 24
        pm25_list = [0] * 24
        traffic_list = [0] * 24

    return pd.DataFrame({
        "Время": times,
        "AQI (Индекс)": aqi_list,
        "PM2.5 (Пыль)": pm25_list,
        "Пробки (Баллы)": traffic_list
    }).set_index("Время")


st.markdown("<h1 class='main-title'>🍃 AUA: Эко-мониторинг</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-size: 1.2rem; opacity: 0.8; margin-bottom: 30px;'>Интеллектуальный анализ воздуха и трафика с накопительной базой данных.</p>", unsafe_allow_html=True)

col_map, col_info = st.columns([1.5, 1.2]) 

with col_map:
    st.markdown(f"### 📍 Локация: <span style='color: {accent_color} !important;'>{st.session_state.address}</span>", unsafe_allow_html=True)
    
    m = folium.Map(location=[st.session_state.last_lat, st.session_state.last_lon], zoom_start=14, tiles=map_tiles)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=m@221097413,traffic&x={x}&y={y}&z={z}', attr='Google Maps Traffic', name='Пробки').add_to(m)
    folium.Marker([st.session_state.last_lat, st.session_state.last_lon], popup=st.session_state.address, icon=folium.Icon(color='green', icon='leaf')).add_to(m)

    map_data = st_folium(m, height=500, use_container_width=True, key="main_map") 

    if map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        if round(lat, 4) != round(st.session_state.last_lat, 4):
            st.session_state.last_lat = lat
            st.session_state.last_lon = lon
            st.session_state.address = get_address_name(lat, lon)
            st.session_state.ai_response = ""
            st.rerun()

with col_info:
    st.markdown("### 📊 Текущие показатели")
    col1, col2, col3 = st.columns(3)
    aqi_v, pm_v, aqi_d = get_weather_data(st.session_state.last_lat, st.session_state.last_lon)
    tr_raw, tr_v, tr_d = get_real_traffic(st.session_state.last_lat, st.session_state.last_lon)
    
    with col1: st.metric("AQI", f"{aqi_v} / 5", aqi_d)
    with col2: st.metric("PM2.5", f"{pm_v}", "µg/m³")
    with col3: st.metric("Пробки", f"{tr_v}", tr_d)
    
    st.write("---")
    
    st.markdown("### 📈 Аналитика за 24 часа")
    with st.spinner("Загрузка данных из локального Data Lake..."):
        df_history = get_historical_data_with_db(st.session_state.last_lat, st.session_state.last_lon, tr_raw)
    
    
    with st.expander("📊 Show data", expanded=True):
        st.dataframe(df_history, use_container_width=True, height=320)
    
    st.write("") 
    if st.button("✨ Сгенерировать AI-отчет"):
        prompt = f"""Ты эксперт команды Antares. Точка: {st.session_state.address}. Индекс воздуха {aqi_v}, PM2.5: {pm_v}, Пробки: {tr_v} баллов. Спич акимату, коротко: 1. Об экологии рядом (на каз/рус). 2. Проблемы района. 3. Совет жителям. 4. Решения для пробок и воздуха."""
        with st.spinner("Antares AI анализирует данные..."):
            success = False
            for api_key in GEMINI_KEYS:
                if not api_key or api_key.startswith("ВСТАВЬ_"): continue
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash-lite')
                    response = model.generate_content(prompt)
                    st.session_state.ai_response = response.text
                    success = True
                    break 
                except Exception: pass
            if not success: st.error("⚠️ Все API ключи перегружены.")

if st.session_state.ai_response:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🤖 Аналитический отчет Antares")
    st.info(st.session_state.ai_response)

st.markdown(f"""
    <div style='margin-top: 60px; text-align: center; border-top: 1px solid {border_color}; padding-top: 25px; padding-bottom: 25px;'>
        <p style='color: {text_color} !important; opacity: 0.5; font-size: 14px; margin-bottom: 0;'>Разработано командой <b style='color: {accent_color};'>Antares</b> • 2026</p>
    </div>
    """, unsafe_allow_html=True)
