import numpy as np

class DataProcessor:
    def __init__(self):
        self.processed_data = {}

    def get_formatted_data(self):
        """
        İşlenmiş verileri Formula 1 formatına uygun şekilde döndürür.
        """
        formatted_data = {}
        for key, value in self.processed_data.items():
            if isinstance(value, float):
                formatted_data[key] = f"{value:.3f}"
            else:
                formatted_data[key] = str(value)
        return formatted_data

    def clear_data(self):
        """
        İşlenmiş verileri temizler.
        """
        self.processed_data = {}
        return self.processed_data
    def process_data(self, data_input):
        """
        Pist ve araç verilerini işler ve sözlük formatında döndürür.
        Formula 1 verileri için özel işlemler eklenmiştir.
        """
        try:
            # Formula 1 verileri için özel ayırıcı
            if '|' in data_input:
                data_lines = data_input.strip().split('|')
            else:
                data_lines = data_input.strip().split('\n')

            processed_data = {}

            for line in data_lines:
                if ':' in line:
                    key, value = line.split(':')
                    try:
                        # Formula 1 özel sayısal formatlama
                        if key.strip().lower() in ['lap_time', 'top_speed', 'bhp', 'torque', 'weight', 'topspeed', 'acceleration', 'pwratio']:
                            processed_data[key.strip()] = float(value.strip())
                        else:
                            processed_data[key.strip()] = value.strip()
                    except ValueError:
                        processed_data[key.strip()] = value.strip()
                else:
                    processed_data[line.strip()] = True

            return processed_data
        except Exception as e:
            raise ValueError(f"Veri işleme hatası: {str(e)}")
        """
        Pist ve araç verilerini işler ve sözlük formatında döndürür.
        Formula 1 verileri için özel işlemler eklenmiştir.
        """
        try:
            data_lines = data_input.strip().split('\n')
            processed_data = {}
            
            for line in data_lines:
                if ':' in line:
                    key, value = line.split(':')
                    try:
                        processed_data[key.strip()] = float(value.strip())
                    except ValueError:
                        processed_data[key.strip()] = value.strip()
                else:
                    processed_data[line.strip()] = True
            
            return processed_data
        except Exception as e:
            raise ValueError(f"Veri işleme hatası: {str(e)}")

    def add_manual_data(self, data_dict):
        """
        Manuel olarak veri eklemek için kullanılır.
        Parametre olarak bir sözlük alır ve mevcut verilere ekler.
        """
        try:
            for key, value in data_dict.items():
                if isinstance(value, (int, float)):
                    self.processed_data[key] = float(value)
                else:
                    self.processed_data[key] = value
            return self.processed_data
        except Exception as e:
            raise ValueError(f"Manuel veri ekleme hatası: {str(e)}")

    def add_track_properties(self, track_length, corner_count, average_speed, width=None, pitboxes=None):
        """
        Ring pistinin özelliklerini eklemek için kullanılır.
        Parametre olarak pist uzunluğu, viraj sayısı, ortalama hız, genişlik ve pitbox sayısı alır.
        """
        try:
            self.processed_data['track_length'] = float(track_length)
            self.processed_data['corner_count'] = int(corner_count)
            self.processed_data['average_speed'] = float(average_speed)
            if width:
                self.processed_data['width'] = float(width)
            if pitboxes:
                self.processed_data['pitboxes'] = int(pitboxes)
            return self.processed_data
        except Exception as e:
            raise ValueError(f"Pist özellikleri ekleme hatası: {str(e)}")

    def add_manual_entry(self, key, value):
        """
        Tek bir manuel veri girişi eklemek için kullanılır.
        Parametre olarak bir anahtar ve değer alır.
        """
        try:
            if isinstance(value, (int, float)):
                self.processed_data[key] = float(value)
            else:
                self.processed_data[key] = value
            return self.processed_data
        except Exception as e:
            raise ValueError(f"Tekli veri ekleme hatası: {str(e)}")