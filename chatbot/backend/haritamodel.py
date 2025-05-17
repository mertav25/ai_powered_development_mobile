class HaritaModel:
    def __init__(self, merkez_lat=41.0082, merkez_lon=28.9784, zoom=13):
        # İstanbul merkezli başlangıç
        self.harita = folium.Map(location=[merkez_lat, merkez_lon], zoom_start=zoom)

    def marker_ekle(self, isim, lat, lon, popup_bilgi=None):
        popup_bilgi = popup_bilgi or isim
        folium.Marker(location=[lat, lon], popup=popup_bilgi).add_to(self.harita)

    def haritayi_kaydet(self, dosya_adi="harita.html"):
        self.harita.save(dosya_adi)
