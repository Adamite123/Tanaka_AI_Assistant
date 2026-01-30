# Perbaikan Alur Kerja Kriteria Screening

## 📋 RINGKASAN PERUBAHAN

Sistem screening CV telah diperbaiki untuk menghilangkan duplikasi data dan inkonsistensi flow dengan mengimplementasikan arsitektur berbasis **Template → Session → CV → Evaluation**.

---

## 🔴 MASALAH YANG DIPERBAIKI

### 1. **Duplikasi Data Kriteria**
**Sebelum:**
- ❌ Kriteria disimpan di 3 tempat berbeda:
  - `criteria.json` (global)
  - `criteria_bank.json` (templates)
  - `screening_sessions.json` (snapshot)
- ❌ CV terhubung ke session, tapi evaluasi menggunakan `criteria.json`
- ❌ Tidak ada sinkronisasi data
- ❌ Batch/Position tidak konsisten

**Sesudah:**
- ✅ Single source of truth: **Sessions**
- ✅ Evaluasi menggunakan kriteria dari session yang terhubung dengan CV
- ✅ Data batch/position konsisten
- ✅ File `criteria.json` dihapus

### 2. **Flow Tidak Konsisten**
**Sebelum:**
```
Upload CV → Terhubung ke Session (batch, position)
      ↓
Evaluasi CV → Ambil kriteria dari criteria.json (SALAH!)
```

**Sesudah:**
```
Template → Session (snapshot criteria) → CV → Evaluasi (gunakan session criteria)
```

### 3. **Menu yang Membingungkan**
**Sebelum:**
- Menu "Atur Kriteria" (redundan dengan Bank Kriteria)
- User bingung kriteria mana yang digunakan

**Sesudah:**
- ✅ Menu "Atur Kriteria" dihapus
- ✅ Flow jelas: Bank Kriteria → Sessions → Upload CV → Screening

---

## ✅ PERUBAHAN YANG DILAKUKAN

### **1. Backend (`index.py`)**

#### a. Fungsi `evaluate_cv()` Diperbaiki
**File:** [index.py:920-1027](index.py#L920-L1027)

**Sebelum:**
```python
# SALAH: Ambil kriteria dari criteria.json global
criteria = load_criteria()
criteria_text = "\n".join([f"- {c}" for c in criteria.get('criteria_points', [])])
```

**Sesudah:**
```python
# BENAR: Ambil kriteria dari session yang terhubung dengan CV
session_id = cv.get('session_id')
session = next((s for s in sessions_data['sessions'] if s['id'] == session_id), None)
criteria_points = session.get('criteria_points', [])
```

**Validasi yang ditambahkan:**
- ✅ CV wajib punya `session_id`
- ✅ Session harus ada dan valid
- ✅ Session harus punya kriteria
- ✅ Update `screened_count` di session

#### b. Hapus File & Kode Deprecated
- ❌ `CRITERIA_FILE` dicomment ([index.py:40](index.py#L40))
- ❌ `load_criteria()` dicomment ([index.py:287-294](index.py#L287-L294))
- ❌ `save_criteria()` dicomment
- ❌ API endpoints `/api/criteria` deprecated ([index.py:499-500](index.py#L499-L500))
- ❌ File `criteria.json` dihapus

### **2. Frontend (`templates/index.html`)**

#### a. Menu Sidebar Diupdate
**File:** [templates/index.html:687-710](templates/index.html#L687-L710)

**Sebelum:**
```html
<div class="menu-item" onclick="navigateTo('criteria')">Kriteria Screening</div>
<div class="menu-item" onclick="navigateTo('bank')">Bank Kriteria</div>
<div class="menu-item" onclick="navigateTo('sessions')">Screening Sessions</div>
```

**Sesudah:**
```html
<!-- Menu "Kriteria Screening" DIHAPUS -->
<div class="menu-item" onclick="navigateTo('bank')">Bank Kriteria</div>
<div class="menu-item" onclick="navigateTo('sessions')">Screening Sessions</div>
```

#### b. Halaman Kriteria Dihapus
- ❌ `<div id="page-criteria">` dihapus lengkap
- ❌ Form input kriteria global dihapus
- ❌ Tombol "Atur Kriteria" di dashboard dihapus

#### c. Fungsi `screenCV()` Diperbaiki
**File:** [templates/index.html:2120-2192](templates/index.html#L2120-L2192)

**Sebelum:**
```javascript
// Validasi criteria.json (SALAH)
if (!criteria.criteria_points || criteria.criteria_points.length === 0) {
    showAlert('Silakan atur kriteria terlebih dahulu');
    navigateTo('criteria'); // Halaman yang salah!
}
```

**Sesudah:**
```javascript
// Validasi session yang terhubung dengan CV (BENAR)
const cv = cvsList.find(c => c.id === cvId);
if (!cv.session_id) {
    showAlert('CV tidak terhubung dengan session!');
    navigateTo('upload');
    return;
}

const session = sessionsList.find(s => s.id === cv.session_id);
if (!session.criteria_points || session.criteria_points.length === 0) {
    showAlert('Session tidak memiliki kriteria!');
    navigateTo('sessions');
    return;
}
```

#### d. Fungsi Deprecated
**File:** [templates/index.html:1156-1161](templates/index.html#L1156-L1161)

Fungsi-fungsi ini di-stub (kosong):
- `loadCriteria()` → Empty function
- `renderCriteria()` → Empty function
- `addCriteria()` → Empty function
- `removeCriteria()` → Empty function
- `saveCriteria()` → Empty function

---

## 🎯 ARSITEKTUR BARU

```
┌─────────────────────┐
│  Bank Kriteria      │  Template kriteria yang bisa digunakan ulang
│  (Templates)        │  - Buat template dengan kriteria
└──────────┬──────────┘
           │
           ↓ (Gunakan template)
┌─────────────────────┐
│  Screening Sessions │  Session screening dengan snapshot kriteria
│                     │  - Pilih template
└──────────┬──────────┘  - Set batch, position, tanggal
           │
           ↓ (Upload CV ke session)
┌─────────────────────┐
│  CV Database        │  CV terhubung dengan session
│                     │  - session_id: "xxx"
└──────────┬──────────┘  - batch, position dari session
           │
           ↓ (Screening)
┌─────────────────────┐
│  Evaluation         │  Gunakan kriteria dari session
│                     │  - Ambil criteria_points dari session
└─────────────────────┘  - Save hasil ke screenings
```

---

## 📝 FLOW PENGGUNAAN BARU

### **1. Setup Kriteria (One-time)**
1. Buka **Bank Kriteria**
2. Klik **"Buat Template Baru"**
3. Isi nama template & kriteria
4. Simpan template

### **2. Buat Session Screening**
1. Buka **Screening Sessions**
2. Klik **"Buat Session Baru"**
3. Pilih template yang sudah dibuat
4. Isi batch, position, tanggal
5. Simpan session

### **3. Upload CV**
1. Buka **Upload CV**
2. **WAJIB pilih session** terlebih dahulu
3. Upload CV (manual atau PDF)
4. CV otomatis terhubung dengan session

### **4. Screening CV**
1. Buka **Daftar CV**
2. Klik tombol **"Screening"** pada CV
3. Sistem:
   - ✅ Validasi CV punya session
   - ✅ Ambil kriteria dari session
   - ✅ Evaluasi dengan AI
   - ✅ Simpan hasil dengan metadata session

---

## 🔒 VALIDASI & ERROR HANDLING

### **Validasi di Backend (`evaluate_cv`)**
```python
# 1. CV harus ada
if not cv:
    return error("CV not found")

# 2. CV harus terhubung dengan session
if not cv.get('session_id'):
    return error("CV tidak terhubung dengan session")

# 3. Session harus ada
if not session:
    return error("Session tidak ditemukan")

# 4. Session harus punya kriteria
if not session.get('criteria_points'):
    return error("Session tidak memiliki kriteria")
```

### **Validasi di Frontend (`screenCV`)**
```javascript
// 1. CV harus ada di list
const cv = cvsList.find(c => c.id === cvId);
if (!cv) {
    showAlert('CV tidak ditemukan');
    return;
}

// 2. CV harus punya session_id
if (!cv.session_id) {
    showAlert('CV tidak terhubung dengan session!');
    navigateTo('upload');
    return;
}

// 3. Session harus ada
const session = sessionsList.find(s => s.id === cv.session_id);
if (!session) {
    showAlert('Session tidak ditemukan!');
    return;
}

// 4. Session harus punya kriteria
if (!session.criteria_points || session.criteria_points.length === 0) {
    showAlert('Session tidak memiliki kriteria!');
    navigateTo('sessions');
    return;
}
```

---

## 📊 DATA STRUCTURE

### **Template (Bank Kriteria)**
```json
{
  "id": "uuid",
  "name": "Senior Full Stack Developer",
  "description": "Template untuk posisi Senior Developer",
  "criteria_points": [
    "Menguasai Python/JavaScript",
    "Pengalaman 5+ tahun",
    "Leadership skills"
  ],
  "created_at": "2025-12-10T10:00:00",
  "usage_count": 3
}
```

### **Session**
```json
{
  "id": "uuid",
  "screening_name": "Recruitment Batch 1",
  "template_id": "template-uuid",
  "batch": "Batch 1",
  "position": "Backend Developer",
  "screening_date": "2025-12-10",
  "criteria_points": [ /* snapshot dari template */ ],
  "cv_count": 10,
  "screened_count": 7
}
```

### **CV**
```json
{
  "id": "uuid",
  "name": "John Doe",
  "session_id": "session-uuid",  // WAJIB
  "batch": "Batch 1",             // Dari session
  "position": "Backend Developer", // Dari session
  "screening_status": "screened"
}
```

### **Screening Result**
```json
{
  "id": "uuid",
  "cv_id": "cv-uuid",
  "session_id": "session-uuid",  // BARU: Link ke session
  "evaluation": "AI evaluation result",
  "final_score": 85.5,
  "batch": "Batch 1",
  "position": "Backend Developer",
  "screening_name": "Recruitment Batch 1"
}
```

---

## 🚀 KEUNTUNGAN ARSITEKTUR BARU

### **1. Konsistensi Data**
- ✅ Single source of truth (Sessions)
- ✅ Batch & Position konsisten
- ✅ Kriteria yang digunakan jelas

### **2. Traceability**
- ✅ Setiap CV tahu sessionnya
- ✅ Setiap screening result tahu sessionnya
- ✅ Mudah tracking: "CV ini dievaluasi dengan kriteria apa?"

### **3. Flexibility**
- ✅ Template bisa digunakan ulang
- ✅ Session bisa diedit kriterianya (snapshot)
- ✅ Multi-batch/position screening mudah

### **4. User Experience**
- ✅ Flow jelas: Template → Session → CV → Screening
- ✅ Tidak ada menu redundan
- ✅ Error message jelas dan actionable

### **5. Scalability**
- ✅ Mudah manage multiple screening sessions
- ✅ Mudah export data per session
- ✅ Mudah analisis per batch/position

---

## 🔄 MIGRATION NOTES

### **File yang Dihapus**
- ❌ `screening_data/criteria.json` (deprecated)
- ❌ Menu "Atur Kriteria" di UI

### **File Backup**
- ✅ `screening_data/criteria.json.backup` (jika ada data lama)

### **Backward Compatibility**
- API `/api/criteria` masih ada tapi deprecated
- Fungsi frontend di-stub untuk avoid errors
- Data lama di `cvs.json` dan `screenings.json` tetap bisa dibaca

### **Data Migration (Jika Diperlukan)**
Jika ada CV lama tanpa `session_id`:
1. Buat session default dari template
2. Update CV dengan `session_id`
3. Update screening results dengan `session_id`

---

## 📚 REFERENSI KODE

### **Backend**
- [index.py:920-1027](index.py#L920-L1027) - Fungsi `evaluate_cv()` baru
- [index.py:40](index.py#L40) - CRITERIA_FILE deprecated
- [index.py:499-500](index.py#L499-L500) - API deprecated notice

### **Frontend**
- [templates/index.html:687-710](templates/index.html#L687-L710) - Menu sidebar
- [templates/index.html:2120-2192](templates/index.html#L2120-L2192) - Fungsi `screenCV()`
- [templates/index.html:1156-1161](templates/index.html#L1156-L1161) - Deprecated functions

---

## ✅ CHECKLIST TESTING

- [x] Server Flask bisa start tanpa error
- [x] Menu sidebar tidak ada "Kriteria Screening"
- [x] Bank Kriteria bisa buat template
- [x] Sessions bisa dibuat dari template
- [x] Upload CV wajib pilih session
- [x] Screening CV validasi session
- [x] Evaluasi menggunakan kriteria dari session
- [x] Hasil screening punya `session_id`
- [x] Dashboard stats update dengan benar

---

## 🎓 KESIMPULAN

**Sistem screening CV sekarang menggunakan arsitektur yang clean dan konsisten:**

```
✅ Template → Session → CV → Evaluation
❌ criteria.json (DEPRECATED)
```

**Prinsip:**
1. **Template** = Kriteria yang bisa digunakan ulang
2. **Session** = Instance screening dengan snapshot kriteria
3. **CV** = Terhubung dengan session
4. **Evaluation** = Gunakan kriteria dari session CV

**Hasil:**
- ✅ Tidak ada duplikasi data
- ✅ Flow konsisten
- ✅ User experience jelas
- ✅ Data traceability bagus
- ✅ Mudah di-maintain

---

**Dokumentasi dibuat:** 2025-12-10
**Versi:** 2.0 (Session-based Architecture)
