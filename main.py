import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import pandas as pd
import itertools

print("--- MEMULAI PROSES LATAR BELAKANG (BACKEND) ---")
print("[1/4] Menginisialisasi Variabel Fuzzy...")

harga = ctrl.Antecedent(np.arange(0, 31, 1), 'harga')
ram = ctrl.Antecedent(np.arange(0, 25, 1), 'ram')
rom = ctrl.Antecedent(np.arange(0, 1025, 1), 'rom')
baterai = ctrl.Antecedent(np.arange(0, 8000, 1), 'baterai')
kamera = ctrl.Antecedent(np.arange(0, 201, 1), 'kamera')
antutu = ctrl.Antecedent(np.arange(0, 2001, 1), 'antutu')

skor = ctrl.Consequent(np.arange(0, 101, 1), 'skor')

harga['murah'] = fuzz.trimf(harga.universe, [0, 0, 4])
harga['sedang'] = fuzz.trimf(harga.universe, [2, 5, 9])
harga['mahal'] = fuzz.trapmf(harga.universe, [7, 12, 30, 30])

ram['kecil'] = fuzz.trimf(ram.universe, [0, 0, 5])
ram['sedang'] = fuzz.trimf(ram.universe, [3, 6, 10])
ram['besar'] = fuzz.trapmf(ram.universe, [6, 12, 24, 24])

rom['kecil'] = fuzz.trimf(rom.universe, [0, 32, 90])
rom['sedang'] = fuzz.trimf(rom.universe, [40, 128, 256])
rom['besar'] = fuzz.trapmf(rom.universe, [128, 512, 1024, 1024])

baterai['boros'] = fuzz.trimf(baterai.universe, [0, 0, 4800])
baterai['awet'] = fuzz.trapmf(baterai.universe, [4000, 5000, 8000, 8000])

kamera['biasa'] = fuzz.trimf(kamera.universe, [0, 0, 48])
kamera['bagus'] = fuzz.trapmf(kamera.universe, [32, 50, 200, 200])

antutu['lambat'] = fuzz.trimf(antutu.universe, [0, 0, 400])
antutu['standar'] = fuzz.trimf(antutu.universe, [250, 450, 800])
antutu['ngebut'] = fuzz.trapmf(antutu.universe, [600, 900, 2000, 2000])

skor['buruk'] = fuzz.trimf(skor.universe, [0, 0, 50])
skor['layak'] = fuzz.trimf(skor.universe, [40, 60, 80])
skor['sangat_rekomen'] = fuzz.trimf(skor.universe, [70, 100, 100])

print("[2/4] Men-generate Aturan Logika Fuzzy...")

map_harga = {'murah': harga['murah'], 'sedang': harga['sedang'], 'mahal': harga['mahal']}
map_ram = {'kecil': ram['kecil'], 'sedang': ram['sedang'], 'besar': ram['besar']}
map_rom = {'kecil': rom['kecil'], 'sedang': rom['sedang'], 'besar': rom['besar']}
map_baterai = {'boros': baterai['boros'], 'awet': baterai['awet']}
map_kamera = {'biasa': kamera['biasa'], 'bagus': kamera['bagus']}
map_antutu = {'lambat': antutu['lambat'], 'standar': antutu['standar'], 'ngebut': antutu['ngebut']}

nilai_poin = {
    'murah': 3, 'sedang': 2, 'mahal': 1,
    'kecil': 1, 'lambat': 1, 'boros': 1, 'biasa': 1,
    'standar': 2,
    'besar': 3, 'ngebut': 3, 'awet': 3, 'bagus': 3
}

rules = []
kombinasi = itertools.product(
    map_harga.keys(), map_ram.keys(), map_rom.keys(),
    map_baterai.keys(), map_kamera.keys(), map_antutu.keys()
)

for h, r, rm, b, k, a in kombinasi:
    total = (nilai_poin[h] + nilai_poin[r] + nilai_poin[rm] +
             nilai_poin[b] + nilai_poin[k] + nilai_poin[a])

    if total >= 15: out = skor['sangat_rekomen']
    elif 11 <= total < 15: out = skor['layak']
    else: out = skor['buruk']

    kondisi = (map_harga[h] & map_ram[r] & map_rom[rm] &
               map_baterai[b] & map_kamera[k] & map_antutu[a])
    rules.append(ctrl.Rule(kondisi, out))

ctrl_sistem = ctrl.ControlSystem(rules)
simulasi = ctrl.ControlSystemSimulation(ctrl_sistem)

print("[3/4] Menghitung Skor & Menentukan Keterangan...")

try:
    df = pd.read_csv('data_hp.csv')
    hasil_skor = []
    hasil_ket = []

    for i, row in df.iterrows():
        try:
            simulasi.input['harga'] = float(row['Harga_Juta'])
            simulasi.input['ram'] = float(row['RAM_GB'])
            simulasi.input['rom'] = float(row['ROM_GB'])
            simulasi.input['baterai'] = float(row['Baterai_mAh'])
            simulasi.input['kamera'] = float(row['Kamera_MP'])
            simulasi.input['antutu'] = float(row['AnTuTu_Ribu'])

            simulasi.compute()
            nilai = simulasi.output['skor']
        except:
            nilai = 0

        hasil_skor.append(nilai)

        if nilai >= 70:
            hasil_ket.append("Sangat Rekomen")
        elif nilai >= 40:
            hasil_ket.append("Layak")
        else:
            hasil_ket.append("Kurang")

    df['Skor_Fuzzy'] = hasil_skor
    df['Skor_Fuzzy'] = df['Skor_Fuzzy'].round(2)
    df['Keterangan'] = hasil_ket

    df_sorted = df.sort_values(by='Skor_Fuzzy', ascending=False)

    nama_file_json = 'data_hasil.json'
    df_sorted.to_json(nama_file_json, orient='records', indent=4)

    print("\n" + "="*60)
    print(f"[4/4] SELESAI! Data berhasil diexport ke '{nama_file_json}'")
    print("="*60)
    print("Contoh 3 Data Teratas:")
    print(df_sorted[['Nama_HP', 'Skor_Fuzzy', 'Keterangan']].head(3).to_string(index=False))

except FileNotFoundError:
    print("ERROR: File 'data_hp.csv' tidak ditemukan.")
except Exception as e:
    print(f"TERJADI ERROR: {e}")