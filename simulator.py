import numpy as np
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PhysicsConstants:
    gravity: float = 9.81  # m/s²
    air_density: float = 1.225  # kg/m³
    friction_coefficient: float = 0.015  # Lastik sürtünme katsayısı
    rolling_resistance: float = 0.011  # Yuvarlanma direnci
    fuel_consumption_rate: float = 0.03  # L/km
    tire_wear_rate: float = 0.001  # Lastik aşınma oranı
    
    # Motor karakteristikleri
    max_power: float = 735.0  # Motor maksimum gücü (kW)
    max_torque: float = 770.0  # Motor maksimum torku (Nm)
    power_rpm: float = 7500.0  # Maksimum güç devri (rpm)
    torque_rpm: float = 4500.0  # Maksimum tork devri (rpm)
    redline: float = 8500.0  # Maksimum motor devri (rpm)
    gear_ratios: List[float] = None  # Vites oranları
    final_drive: float = 3.42  # Son dişli oranı
    
    # Aerodinamik parametreler
    drag_coefficient: float = 0.28  # Hava sürtünme katsayısı
    frontal_area: float = 2.0  # Ön alan (m²)
    downforce_coefficient: float = 3.0  # Downforce katsayısı
    
    # Lastik parametreleri
    tire_radius: float = 0.33  # Lastik yarıçapı (m)
    tire_width: float = 0.305  # Lastik genişliği (m)
    tire_pressure: float = 2.3  # Lastik basıncı (bar)
    tire_temp_optimal: float = 85.0  # Optimal lastik sıcaklığı (°C)
    tire_grip_curve: List[float] = None  # Lastik tutunma eğrisi
    
    # Hava ve pist koşulları
    air_temperature: float = 25.0  # Hava sıcaklığı (°C)
    track_temperature: float = 30.0  # Pist sıcaklığı (°C)
    humidity: float = 0.6  # Bağıl nem (0-1)
    rain_intensity: float = 0.0  # Yağmur yoğunluğu (0-1)
    track_wetness: float = 0.0  # Pist ıslaklığı (0-1)
    wind_speed: float = 0.0  # Rüzgar hızı (m/s)
    wind_direction: float = 0.0  # Rüzgar yönü (derece)
    
    def __post_init__(self):
        if self.gear_ratios is None:
            self.gear_ratios = [3.23, 2.19, 1.71, 1.39, 1.16, 0.93]  # Varsayılan vites oranları
        if self.tire_grip_curve is None:
            # Lastik tutunma eğrisi (sıcaklığa bağlı)
            self.tire_grip_curve = [0.85, 0.90, 0.95, 1.0, 0.98, 0.94, 0.88]

class Simulator:
    def __init__(self, track_data: Dict[str, float], car_data: Dict[str, float]):
        self.track_data = track_data
        self.car_data = car_data
        self.physics = PhysicsConstants()
        
    def calculate_aero_forces(self, velocity: float) -> tuple[float, float]:
        """Aerodinamik kuvvetleri (sürükleme ve downforce) hesaplar"""
        # Hava yoğunluğu düzeltmesi (sıcaklık ve nem etkisi)
        temp_factor = (273.15 + 15) / (273.15 + self.physics.air_temperature)  # 15°C referans
        humidity_factor = 1 + (self.physics.humidity - 0.5) * 0.1
        adjusted_air_density = self.physics.air_density * temp_factor * humidity_factor
        
        # Rüzgar etkisi
        wind_angle = np.radians(self.physics.wind_direction)
        relative_wind_x = velocity + self.physics.wind_speed * np.cos(wind_angle)
        relative_wind_y = self.physics.wind_speed * np.sin(wind_angle)
        relative_wind = np.sqrt(relative_wind_x**2 + relative_wind_y**2)
        
        # Yaw açısı etkisi
        yaw_angle = np.arctan2(relative_wind_y, relative_wind_x)
        yaw_factor = 1 + 0.2 * abs(np.sin(yaw_angle))  # Yan rüzgar etkisi
        
        # Sürükleme kuvveti
        drag_coefficient = self.physics.drag_coefficient * yaw_factor
        drag_force = 0.5 * adjusted_air_density * drag_coefficient * self.physics.frontal_area * relative_wind**2
        
        # Downforce hesaplama
        ground_effect = 1 + 0.3 * np.exp(-velocity / 50)  # Düşük hızlarda yer etkisi
        ride_height_factor = 1.0  # İdeal sürüş yüksekliği varsayımı
        downforce = 0.5 * adjusted_air_density * self.physics.downforce_coefficient * \
                   self.physics.frontal_area * velocity**2 * ground_effect * ride_height_factor
        
        return drag_force, downforce
    
    def calculate_engine_torque(self, rpm: float) -> float:
        """Motor tork eğrisini hesaplar"""
        if rpm < 1000 or rpm > self.physics.redline:
            return 0.0
        
        # Tork eğrisi modellemesi (basitleştirilmiş)
        x = rpm / self.physics.torque_rpm
        if rpm <= self.physics.torque_rpm:
            torque_factor = (4 * x - 3 * x * x) / 1.0  # Düşük devirlerde artış
        else:
            torque_factor = 1.0 - 0.3 * ((rpm - self.physics.torque_rpm) / (self.physics.redline - self.physics.torque_rpm))
        
        return self.physics.max_torque * max(0, torque_factor)
    
    def calculate_engine_power(self, rpm: float) -> float:
        """Motor gücünü hesaplar"""
        torque = self.calculate_engine_torque(rpm)
        return torque * rpm * 2 * np.pi / 60000  # kW cinsinden güç
    
    def calculate_acceleration(self, velocity: float, gear: int = None) -> float:
        """Anlık ivmelenmeyi hesaplar"""
        if gear is None:
            # Otomatik vites seçimi
            wheel_rpm = velocity * 60 / (2 * np.pi * self.physics.tire_radius)
            for i, ratio in enumerate(self.physics.gear_ratios):
                engine_rpm = wheel_rpm * ratio * self.physics.final_drive
                if engine_rpm <= self.physics.redline:
                    gear = i
                    break
            if gear is None:
                gear = len(self.physics.gear_ratios) - 1
        
        # Motor devri hesaplama
        wheel_rpm = velocity * 60 / (2 * np.pi * self.physics.tire_radius)
        engine_rpm = wheel_rpm * self.physics.gear_ratios[gear] * self.physics.final_drive
        
        # Tork ve güç hesaplama
        engine_torque = self.calculate_engine_torque(engine_rpm)
        wheel_torque = engine_torque * self.physics.gear_ratios[gear] * self.physics.final_drive * 0.9  # %90 aktarma verimi
        
        # Kuvvetler
        drive_force = wheel_torque / self.physics.tire_radius
        drag_force, downforce = self.calculate_aero_forces(velocity)
        rolling_resistance = self.physics.rolling_resistance * 1500 * self.physics.gravity
        
        # Lastik tutuşu
        tire_temp = min(self.physics.track_temperature * 1.2, 120)
        temp_grip = 1 - abs(tire_temp - self.physics.tire_temp_optimal) / 100
        tire_grip = max(0.7, temp_grip * (1 - self.physics.tire_wear_rate * velocity / 50))
        
        # Net kuvvet hesaplama
        net_force = min(drive_force * tire_grip, 1500 * 9.81 * 1.5)  # Maksimum çekiş sınırı
        net_force -= (drag_force + rolling_resistance)
        
        return net_force / 1500  # Araç kütlesi

    def calculate_tire_grip(self, load: float, slip_angle: float) -> float:
        """Lastik tutunma katsayısını hesaplar"""
        # Lastik sıcaklığı etkisi
        tire_temp = min(self.physics.track_temperature * 1.2, 120)
        temp_factor = 1 - abs(tire_temp - self.physics.tire_temp_optimal) / 100
        
        # Lastik basıncı etkisi
        pressure_factor = 1 - abs(self.physics.tire_pressure - 2.3) / 2
        
        # Yük ve kayma açısı etkisi
        load_factor = 1 - (load / (1500 * 9.81) - 0.25) ** 2  # Optimal yük dağılımı
        slip_factor = np.sin(2 * np.arctan(slip_angle / 8))  # Magic Formula benzeri
        
        # Pist koşulları
        wet_grip_reduction = self.physics.track_wetness * 0.4
        rain_effect = 1 - (self.physics.rain_intensity * 0.3)
        track_grip = 0.95 * (1 - wet_grip_reduction) * rain_effect
        
        base_grip = self.physics.friction_coefficient * temp_factor * pressure_factor
        return base_grip * load_factor * slip_factor * track_grip
    
    def calculate_corner_speed(self, radius: float, bank_angle: float = 0) -> float:
        """Viraj hızını hesaplar"""
        # Temel fizik hesaplamaları
        gravity_normal = self.physics.gravity * np.cos(np.radians(bank_angle))
        gravity_lateral = self.physics.gravity * np.sin(np.radians(bank_angle))
        
        def solve_corner_speed(v):
            # Aerodinamik kuvvetler
            drag_force, downforce = self.calculate_aero_forces(v)
            
            # Normal kuvvet (ağırlık + downforce)
            normal_force = 1500 * gravity_normal + downforce
            
            # Merkezcil kuvvet gereksinimi
            centripetal_req = 1500 * v**2 / radius - 1500 * gravity_lateral
            
            # Lastik tutunma hesabı
            slip_angle = np.arctan(v**2 / (radius * gravity_normal))
            grip = self.calculate_tire_grip(normal_force, slip_angle)
            available_force = normal_force * grip
            
            # Net yanal kuvvet kapasitesi
            return available_force - centripetal_req
        
        # İkili arama ile maksimum viraj hızını bul
        v_min, v_max = 0, 100
        for _ in range(10):
            v = (v_min + v_max) / 2
            if solve_corner_speed(v) > 0:
                v_min = v
            else:
                v_max = v
        
        return v_min

    def calculate_lap_time(self) -> float:
        """Gelişmiş tur süresi hesaplaması"""
        # Pist segmentleri ve karakteristikleri
        segments = [
            {'type': 'straight', 'length': 800, 'bank_angle': 0},  # Ana düzlük
            {'type': 'corner', 'radius': 30, 'bank_angle': 5, 'length': 150},  # 1. viraj
            {'type': 'straight', 'length': 400, 'bank_angle': 0},  # Ara düzlük
            {'type': 'corner', 'radius': 25, 'bank_angle': 8, 'length': 200},  # 2. viraj (banked)
            {'type': 'straight', 'length': 300, 'bank_angle': 0},  # Kısa düzlük
            {'type': 'corner', 'radius': 40, 'bank_angle': 0, 'length': 180}   # Son viraj
        ]
        
        total_time = 0
        current_speed = 0
        
        for i, segment in enumerate(segments):
            next_segment = segments[(i + 1) % len(segments)]
            
            if segment['type'] == 'straight':
                # Düz yol hesaplaması
                max_speed = 100  # Maksimum hız (m/s)
                distance = segment['length']
                
                # İvmelenme mesafesi ve süresi
                acceleration = self.calculate_acceleration(current_speed)
                accel_distance = min(distance / 2, (max_speed**2 - current_speed**2) / (2 * acceleration))
                accel_time = (np.sqrt(2 * acceleration * accel_distance + current_speed**2) - current_speed) / acceleration
                
                # Sabit hız mesafesi ve süresi
                const_speed = min(max_speed, np.sqrt(2 * acceleration * accel_distance + current_speed**2))
                const_distance = max(0, distance - 2 * accel_distance)
                const_time = const_distance / const_speed
                
                # Yavaşlama mesafesi ve süresi (bir sonraki viraj için)
                if next_segment['type'] == 'corner':
                    target_speed = self.calculate_corner_speed(next_segment['radius'], next_segment['bank_angle'])
                    decel = self.car_data['viraj_performansi'] * 10  # Frenleme ivmesi
                    brake_distance = min(distance / 2, (const_speed**2 - target_speed**2) / (2 * decel))
                    brake_time = (const_speed - target_speed) / decel
                else:
                    brake_distance = 0
                    brake_time = 0
                
                segment_time = accel_time + const_time + brake_time
                current_speed = target_speed if next_segment['type'] == 'corner' else const_speed
                
            else:  # Viraj hesaplaması
                corner_speed = max(0.1, self.calculate_corner_speed(segment['radius'], segment['bank_angle']))  # Ensure minimum speed
                segment_time = segment['length'] / corner_speed
                current_speed = corner_speed
            
            # Hava ve pist koşulları etkisi
            weather_factor = 1 + (self.physics.rain_intensity * 0.3 + 
                                 max(0, (self.physics.wind_speed - 5) * 0.02) + 
                                 self.physics.track_wetness * 0.2)
            
            total_time += segment_time * weather_factor
        
        return total_time
    
    def run(self):
        """
        Simülasyonu çalıştırır ve sonuçları döndürür.
        """
        lap_time = self.calculate_lap_time()
        fuel_consumption = self.physics.fuel_consumption_rate * self.track_data['pist_uzunlugu']
        tire_wear = self.physics.tire_wear_rate * (self.track_data['viraj_sayisi'] + self.track_data['pist_uzunlugu'] / 100)
        
        # Hava koşulları etkisi
        weather_impact = 1.0
        if self.physics.rain_intensity > 0:
            weather_impact += self.physics.rain_intensity * 0.3  # Yağmur etkisi
        if self.physics.wind_speed > 5:
            weather_impact += (self.physics.wind_speed - 5) * 0.02  # Rüzgar etkisi
        
        # Pist koşulları etkisi
        track_condition = 1.0
        if self.physics.track_wetness > 0:
            track_condition += self.physics.track_wetness * 0.2  # Islak pist etkisi
        if abs(self.physics.track_temperature - 25) > 10:
            track_condition += abs(self.physics.track_temperature - 25) * 0.01  # Sıcaklık etkisi
        
        return {
            'tur_suresi': lap_time * weather_impact,
            'detaylar': {
                'temel_sure': self.track_data['pist_uzunlugu'] / self.car_data['ortalama_hiz'],
                'viraj_etkisi': self.track_data['viraj_sayisi'] * (1 / self.car_data['viraj_performansi']),
                'duz_yol_etkisi': self.track_data['duz_yol_yuzdesi'] * (1 / self.car_data['ivmelenme']),
                'hava_direnci': self.car_data['hava_direnci'] * self.track_data['pist_uzunlugu'] / 1000,
                'yakit_tuketimi': fuel_consumption * weather_impact,
                'lastik_asinmasi': tire_wear * track_condition,
                'hava_kosullari': {
                    'sicaklik': self.physics.air_temperature,
                    'nem': self.physics.humidity,
                    'yagmur': self.physics.rain_intensity,
                    'ruzgar_hizi': self.physics.wind_speed,
                    'ruzgar_yonu': self.physics.wind_direction
                },
                'pist_kosullari': {
                    'sicaklik': self.physics.track_temperature,
                    'islaklik': self.physics.track_wetness
                }
            }
        }