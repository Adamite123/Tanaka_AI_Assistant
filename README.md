# 📋 CV Screening System dengan RAG

Sistem screening CV untuk SDM (Sumber Daya Manusia) yang menggunakan teknologi **RAG (Retrieval-Augmented Generation)** dengan backend Flask dan database JSON lokal.

## ✨ Fitur Utama

### 1. **Manajemen Kriteria Screening** ⚙️
- Buat kriteria screening sesuai kebutuhan posisi yang dicari
- Tambah/hapus poin-poin kriteria evaluasi dengan mudah
- Simpan kriteria dalam format JSON lokal

### 2. **Input & Manajemen CV** 👥
- Input CV dengan detail lengkap (nama, email, pengalaman, skill, pendidikan)
- Penyimpanan otomatis ke database JSON lokal
- List CV yang dapat dihapus

### 3. **Screening Otomatis dengan RAG** 🤖
- Evaluasi CV secara otomatis menggunakan RAG
- AI menganalisis CV berdasarkan kriteria yang telah ditentukan
- Memberikan score untuk setiap kriteria
- Rekomendasi LOLOS/TIDAK LOLOS

### 4. **Hasil Screening** 📊
- Lihat hasil evaluasi lengkap per CV
- Penyimpanan hasil screening dalam JSON
- Export/download hasil screening

### 5. **Database JSON Lokal** 💾
- Semua data tersimpan dalam JSON file (tidak perlu database eksternal)
- Struktur folder: `screening_data/`
  - `criteria.json` - Kriteria screening
  - `cvs.json` - Data CV
  - `screenings.json` - Hasil screening
  - `chroma_db/` - Vector database untuk RAG

## 🛠️ Tech Stack

### Backend
- **Flask** - Web framework Python
- **LangChain** - Framework untuk RAG
- **OpenAI GPT-3.5-turbo** - LLM untuk evaluasi
- **ChromaDB** - Vector database untuk RAG

### Frontend
- **HTML5** - Struktur halaman
- **CSS3** - Styling responsif
- **JavaScript ES6+** - Interaktivitas frontend

### Data Storage
- **JSON Files** - Penyimpanan data lokal
- **ChromaDB** - Vector store untuk RAG

## 📦 Instalasi

### 1. Clone atau Setup Project
```bash
cd rag_projek5_screening
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables
Buat file `.env` di root project:
```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
FLASK_SECRET_KEY=cv-screening-secret-key-2025
```

### 4. Run Aplikasi
```bash
python index.py
```

Akses di: `http://127.0.0.1:5000`

## 📁 Struktur Project

```
rag_projek5_screening/
├── index.py                     # Backend Flask
├── requirements.txt             # Dependencies
├── .env                        # Environment variables
├── README.md                   # Dokumentasi ini
├── LICENSE                     # MIT License
├── templates/
│   └── index.html             # Frontend utama
├── static/
│   ├── fix-glitch.css         # Assets CSS (jika ada)
│   ├── certificates/
│   └── projects/
├── screening_data/            # Data lokal (otomatis dibuat)
│   ├── criteria.json          # Kriteria screening
│   ├── cvs.json               # Data CV
│   ├── screenings.json        # Hasil screening
│   └── chroma_db/             # Vector database
├── genezio.yaml              # Deployment config (opsional)
└── .gitignore               # Git ignore rules
```

## 🚀 Cara Penggunaan

### Step 1: Setup Kriteria
1. Di panel **"⚙️ Kriteria Screening"**, masukkan nama screening (contoh: "Senior Developer")
2. Tambahkan poin-poin kriteria yang ingin dievaluasi:
   - Contoh: "Pengalaman Python 5+ tahun"
   - Contoh: "Familiar dengan Django Framework"
   - Contoh: "Pernah lead tim development"
3. Klik **"Simpan Kriteria"**

### Step 2: Input CV Kandidat
1. Di tab **"Input CV"**, isi data lengkap kandidat:
   - Nama Lengkap
   - Email
   - Nomor Telepon
   - Pengalaman Kerja (deskripsi detail)
   - Skill & Teknologi
   - Pendidikan
   - Ringkasan Singkat
2. Klik **"Upload CV"** untuk menyimpan

### Step 3: Lakukan Screening
1. Di panel **"📄 Daftar CV"**, klik tombol **"🔍 Screen"** pada CV yang ingin di-evaluasi
2. Sistem akan menggunakan RAG untuk menganalisis CV berdasarkan kriteria
3. Hasil evaluasi akan ditampilkan dalam modal popup

### Step 4: Review Hasil
1. Di tab **"Hasil Screening"**, lihat semua hasil screening
2. Klik **"👁️ Lihat"** untuk melihat detail evaluasi
3. Klik **"Hapus"** untuk menghapus hasil screening jika diperlukan

## 📊 Format Data JSON

### criteria.json
```json
{
  "screening_name": "Senior Developer",
  "criteria_points": [
    "Pengalaman Python 5+ tahun",
    "Familiar dengan Django Framework",
    "Pernah lead tim development"
  ],
  "created_at": "2025-12-03T10:00:00",
  "updated_at": "2025-12-03T10:00:00"
}
```

### cvs.json
```json
{
  "cvs": [
    {
      "id": "uuid-1234",
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+62812345678",
      "experience": "5 tahun di PT XYZ sebagai Senior Developer",
      "skills": "Python, Django, JavaScript, React",
      "education": "S1 Informatika Universitas Indonesia",
      "summary": "Berpengalaman dalam development backend",
      "uploaded_at": "2025-12-03T10:00:00"
    }
  ]
}
```

### screenings.json
```json
{
  "screenings": [
    {
      "id": "uuid-5678",
      "cv_id": "uuid-1234",
      "cv_name": "John Doe",
      "evaluation": "JSON hasil evaluasi dari AI",
      "created_at": "2025-12-03T10:05:00"
    }
  ]
}
```

## 🔌 API Endpoints

### Criteria
- `GET /api/criteria` - Ambil kriteria saat ini
- `POST /api/criteria` - Buat kriteria baru
- `PUT /api/criteria` - Update kriteria

### CV
- `GET /api/cvs` - Ambil semua CV
- `POST /api/cvs` - Upload CV baru
- `DELETE /api/cvs/<cv_id>` - Hapus CV

### Screening
- `POST /api/screening/evaluate` - Evaluasi CV dengan RAG
- `GET /api/screenings` - Ambil semua hasil screening
- `DELETE /api/screenings/<screening_id>` - Hapus hasil screening

## ⚙️ Konfigurasi

### Environment Variables (.env)
```env
# OpenAI API Key (wajib untuk RAG)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Flask Secret Key (untuk session)
FLASK_SECRET_KEY=cv-screening-secret-key-2025
```

### Settings (di index.py)
- **Model LLM**: `gpt-3.5-turbo` (bisa diganti dengan gpt-4)
- **Temperature**: 0.3 (untuk hasil lebih konsisten)
- **K (retriever)**: 5 (jumlah CV yang diambil sebagai context)
- **Port**: 5000

## 🔐 Security

- Data tersimpan lokal (tidak ada server eksternal)
- Session management dengan Flask secret key
- Input validation pada semua endpoint
- CORS bisa diatur sesuai kebutuhan

## 🐛 Troubleshooting

### Error: "OPENAI_API_KEY not found"
- Pastikan `.env` sudah dibuat dan berisi API key yang valid
- Restart server setelah update `.env`

### Error: "Failed to save criteria"
- Pastikan folder `screening_data/` dapat diakses
- Check permission folder dan file

### CV tidak muncul setelah upload
- Pastikan browser tidak sedang offline
- Check console browser untuk error messages
- Refresh halaman

### Screening tidak berjalan
- Pastikan OPENAI_API_KEY valid
- Check internet connection
- Monitor server log untuk detail error

## 🎯 Best Practices

### 1. Kriteria yang Efektif
- Buat kriteria yang spesifik dan terukur
- Prioritaskan kriteria yang paling penting
- Contoh baik: "Python 5+ tahun" vs Buruk: "Pintar programming"

### 2. Input CV yang Lengkap
- Isi semua field dengan informasi yang detail
- Lebih detail = hasil evaluasi lebih akurat
- Gunakan kata kunci yang relevan dengan kriteria

### 3. Backup Data
- Backup folder `screening_data/` secara berkala
- Simpan JSON file ke cloud storage (Google Drive, etc)

### 4. Monitoring
- Monitor usage OpenAI API untuk manage cost
- Log semua screening untuk audit trail

## 📈 Roadmap

- [ ] Multi-user authentication
- [ ] PDF CV upload & parsing
- [ ] Batch evaluation
- [ ] Export hasil ke CSV/PDF
- [ ] Analytics & dashboard
- [ ] Candidate ranking system
- [ ] Interview scheduling
- [ ] Notification system

## 📝 License

MIT License - bebas digunakan untuk keperluan komersial dan non-komersial

## 💬 Support

Untuk pertanyaan atau issues:
1. Check dokumentasi
2. Review server log
3. Test API dengan Postman/Thunder Client

## 🙋 Kontribusi

Silakan submit pull request atau issue untuk improvement

---

**Version**: 1.0 (Initial Release)  
**Last Updated**: December 3, 2025  
**Status**: Active & Ready to Use
