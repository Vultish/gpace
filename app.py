import streamlit as st

# Streamlit sayfa yapılandırması en başta olmalı
st.set_page_config(layout="wide")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from data_processor import DataProcessor
from simulator import Simulator
import json
import os

def load_saved_configs():
    if os.path.exists('saved_configs.json'):
        with open('saved_configs.json', 'r') as f:
            return json.load(f)
    return {'tracks': {}, 'cars': {}}

def save_config(configs, config_type, name, data):
    configs[config_type][name] = data
    with open('saved_configs.json', 'w') as f:
        json.dump(configs, f)

def main():
    st.title("🏎️ Yarış Pistleri Tur Süresi Simülasyonu")
    
    configs = load_saved_configs()
    
    # Yan menü
    with st.sidebar:
        st.header("Simülasyon Modu")
        simulation_mode = st.radio(
            "Mod Seçin:",
            ["Tek Araç Simülasyonu", "Araç Karşılaştırma"]
        )
    
    # Ana içerik alanı
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🏁 Pist Verileri")
        track_name = st.text_input("Pist Adı (Kaydetmek için)")
        track_data_input = st.text_area(
            "Pist Özellikleri:", 
            """pist_uzunlugu: 5.4
viraj_sayisi: 16
duz_yol_yuzdesi: 0.6""",
            help="Pist özelliklerini 'anahtar: değer' formatında girin"
        )
        
        if track_name and st.button("Pisti Kaydet"):
            try:
                track_data = DataProcessor().process_data(track_data_input)
                save_config(configs, 'tracks', track_name, track_data)
                st.success(f"{track_name} pisti kaydedildi!")
            except ValueError as e:
                st.error(str(e))
        
        saved_track = st.selectbox(
            "Kayıtlı Pistler",
            options=["Yeni Pist"] + list(configs['tracks'].keys())
        )
        if saved_track != "Yeni Pist":
            track_data = configs['tracks'][saved_track]
        else:
            try:
                track_data = DataProcessor().process_data(track_data_input)
            except ValueError as e:
                st.error(str(e))
                return
    
    with col2:
        st.header("🚗 Araç Özellikleri")
        if simulation_mode == "Tek Araç Simülasyonu":
            car_configs = ["Araç 1"]
        else:
            car_configs = ["Araç 1", "Araç 2"]
        
        car_data_list = []
        for car_idx, car_label in enumerate(car_configs):
            st.subheader(car_label)
            car_name = st.text_input(f"Araç Adı (Kaydetmek için)", key=f"car_name_{car_idx}")
            car_data_input = st.text_area(
                f"Araç Özellikleri:",
                """ortalama_hiz: 180
viraj_performansi: 0.8
ivmelenme: 0.7
hava_direnci: 0.3""",
                key=f"car_data_{car_idx}",
                help="Araç özelliklerini 'anahtar: değer' formatında girin"
            )
            
            if car_name and st.button(f"Aracı Kaydet", key=f"save_car_{car_idx}"):
                try:
                    car_data = DataProcessor().process_data(car_data_input)
                    save_config(configs, 'cars', car_name, car_data)
                    st.success(f"{car_name} aracı kaydedildi!")
                except ValueError as e:
                    st.error(str(e))
            
            saved_car = st.selectbox(
                "Kayıtlı Araçlar",
                options=["Yeni Araç"] + list(configs['cars'].keys()),
                key=f"saved_car_{car_idx}"
            )
            
            if saved_car != "Yeni Araç":
                car_data = configs['cars'][saved_car]
            else:
                try:
                    car_data = DataProcessor().process_data(car_data_input)
                except ValueError as e:
                    st.error(str(e))
                    return
            car_data_list.append(car_data)
    
    # Simülasyon başlatma
    if st.button("🚦 Simülasyonu Başlat", type="primary"):
        st.header("📊 Simülasyon Sonuçları")
        
        results_list = []
        for idx, car_data in enumerate(car_data_list):
            simulator = Simulator(track_data, car_data)
            results = simulator.run()
            results_list.append(results)
        
        # Sonuçları göster
        if simulation_mode == "Tek Araç Simülasyonu":
            results = results_list[0]
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Pistin Tamamını Tamamlama Süresi", f"{results['tur_suresi']:.2f} saniye")
            with col2:
                straight_time = results['detaylar']['duz_yol_etkisi']
                st.metric("Düz Yol Süresi", f"{straight_time:.2f} saniye")
            with col3:
                corner_time = results['detaylar']['viraj_etkisi']
                st.metric("Viraj Süresi", f"{corner_time:.2f} saniye")
            
            # Detaylı grafik
            fig = plt.figure(figsize=(10, 6))
            components = list(results['detaylar'].keys())
            values = [float(v) if isinstance(v, (int, float, str)) and str(v).replace('.', '').isdigit() else 0.0 for v in results['detaylar'].values()]
            plt.bar(components, values, color='skyblue')
            plt.title("Tur Süresine Etki Eden Faktörler")
            plt.ylabel("Süre (saniye)")
            plt.xticks(rotation=45)
            st.pyplot(fig)
            
        else:
            # Karşılaştırmalı sonuçlar
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Araç 1 Pistin Tamamını Tamamlama Süresi",
                    f"{results_list[0]['tur_suresi']:.2f} saniye"
                )
            with col2:
                st.metric(
                    "Araç 2 Pistin Tamamını Tamamlama Süresi",
                    f"{results_list[1]['tur_suresi']:.2f} saniye",
                    delta=f"{results_list[1]['tur_suresi'] - results_list[0]['tur_suresi']:.2f}"
                )
            
            # Karşılaştırma grafiğiToplam Tur Süresi


            fig = plt.figure(figsize=(12, 6))
            
            # Sadece temel performans metriklerini seç
            performance_metrics = ['temel_sure', 'viraj_etkisi', 'duz_yol_etkisi', 'hava_direnci', 'yakit_tuketimi', 'lastik_asinmasi']
            car1_values = [results_list[0]['detaylar'][metric] for metric in performance_metrics]
            car2_values = [results_list[1]['detaylar'][metric] for metric in performance_metrics]
            
            x = np.arange(len(performance_metrics))
            width = 0.35
            
            plt.bar(x - width/2, car1_values, width, label='Araç 1')
            plt.bar(x + width/2, car2_values, width, label='Araç 2')
            
            plt.title("Araç Performans Karşılaştırması")
            plt.ylabel("Süre (saniye)")
            plt.xticks(x, performance_metrics, rotation=45)
            plt.legend()
            st.pyplot(fig)
            
            # Detaylı karşılaştırma tablosu
            comparison_data = {
                'Faktör': performance_metrics,
                'Araç 1': [float(value) for value in car1_values],
                'Araç 2': [float(value) for value in car2_values],
                'Fark': [float(car2) - float(car1) for car1, car2 in zip(car1_values, car2_values)]
            }
            st.dataframe(
                pd.DataFrame(comparison_data).style.background_gradient(
                    subset=['Fark'],
                    cmap='RdYlGn_r'
                )
            )

if __name__ == "__main__":
    main()