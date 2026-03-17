# EduZen — Backend API Hujjatnamasi

## 📁 Loyiha tuzilmasi

```
eduzen/
├── manage.py
├── requirements.txt
├── .env.example          ← Muhit o'zgaruvchilari namunasi
├── setup.sh              ← Bir marta ishga tushirish skripti
├── nginx.conf            ← Production Nginx konfiguratsiyasi
├── eduzen.service        ← Systemd servis fayli
│
├── eduzen/               ← Django asosiy konfiguratsiya
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
└── apps/
    ├── users/            ← Foydalanuvchilar va autentifikatsiya
    ├── courses/          ← Kurslar, darslar, yozilish
    └── payments/         ← Payme va Click integratsiyasi
```

---

## ⚡ Tez boshlash

```bash
# 1. Loyihani klonlash
git clone https://github.com/yourusername/eduzen.git
cd eduzen

# 2. Avtomatik o'rnatish
chmod +x setup.sh
./setup.sh

# 3. .env to'ldirish
nano .env

# 4. Serverni ishga tushirish
source venv/bin/activate
python manage.py runserver
```

---

## 🔐 Autentifikatsiya API

### Ro'yxatdan o'tish
```http
POST /api/v1/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "full_name": "Ism Familiya",
  "phone": "+998901234567",
  "password": "StrongPass123",
  "password2": "StrongPass123"
}
```
**Javob:** `201 Created`
```json
{
  "message": "Ro'yxatdan o'tdingiz. Email tasdiqlang.",
  "user": { "id": 1, "email": "...", "full_name": "..." },
  "access": "eyJ0eXAiOiJKV1Q...",
  "refresh": "eyJ0eXAiOiJKV1Q..."
}
```

---

### Kirish
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "StrongPass123"
}
```

---

### Email tasdiqlash
```http
POST /api/v1/auth/verify-email/
Authorization: Bearer <access_token>

{ "code": "123456" }
```

---

### Token yangilash
```http
POST /api/v1/auth/token/refresh/
{ "refresh": "eyJ0eXAiOiJKV1Q..." }
```

---

### Profil
```http
GET  /api/v1/auth/profile/          ← Ko'rish
PATCH /api/v1/auth/profile/         ← Tahrirlash
Authorization: Bearer <access_token>
```

---

### Parol o'zgartirish
```http
POST /api/v1/auth/change-password/
Authorization: Bearer <access_token>

{
  "old_password": "OldPass123",
  "new_password": "NewPass456"
}
```

---

## 📚 Kurslar API

### Barcha kurslar (filtr bilan)
```http
GET /api/v1/courses/
GET /api/v1/courses/?category=dasturlash
GET /api/v1/courses/?level=beginner
GET /api/v1/courses/?is_free=true
GET /api/v1/courses/?search=python
GET /api/v1/courses/?ordering=-created_at
```

---

### Kurs tafsilotlari
```http
GET /api/v1/courses/{slug}/
```

---

### Kursg yozilish
```http
POST /api/v1/courses/{slug}/enroll/
Authorization: Bearer <access_token>
```
> Pullik kurslarda avval to'lov qilinishi shart.

---

### Mening kurslarim
```http
GET /api/v1/courses/my/
Authorization: Bearer <access_token>
```

---

### Sharh qoldirish
```http
POST /api/v1/courses/{slug}/review/
Authorization: Bearer <access_token>

{
  "rating": 5,
  "comment": "Juda yaxshi kurs!"
}
```

---

## 💳 To'lov API

### To'lov boshlash
```http
POST /api/v1/payments/initiate/
Authorization: Bearer <access_token>

{
  "course_id": 1,
  "method": "payme"   // yoki "click"
}
```
**Javob:**
```json
{
  "payment_id": 42,
  "amount": "299000.00",
  "method": "payme",
  "pay_url": "https://checkout.paycom.uz/..."
}
```
> Foydalanuvchini `pay_url` ga yo'naltiring — u yerda to'lovni amalga oshiradi.

---

### Payme Webhook (Payme chaqiradi)
```http
POST /api/v1/payments/payme/
Authorization: Basic <base64(Paycom:SECRET_KEY)>

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "CheckPerformTransaction",
  "params": {
    "amount": 29900000,
    "account": { "order_id": "42" }
  }
}
```

---

### Click Webhook (Click chaqiradi)
```http
POST /api/v1/payments/click/
Content-Type: application/x-www-form-urlencoded

action=0&click_trans_id=...&merchant_trans_id=42&amount=299000&sign_string=...
```

---

### To'lovlar tarixi
```http
GET /api/v1/payments/history/
Authorization: Bearer <access_token>
```

---

## 🛡️ Admin panel

```
URL:   http://localhost:8000/admin/
Login: setup.sh da yaratilgan superuser
```

Admin panelda quyidagilarni boshqarish mumkin:
- Foydalanuvchilar va rollar
- Kurslar (nashr/yashirish, narx)
- Kategoriyalar
- To'lovlar va tranzaksiyalar
- Yozilishlar

---

## 🚀 Production (Server)ga deploy qilish

```bash
# 1. Server: Ubuntu 22.04 LTS tavsiya etiladi

# 2. Nginx va Certbot o'rnatish
sudo apt install nginx certbot python3-certbot-nginx -y

# 3. nginx.conf nusxalash
sudo cp nginx.conf /etc/nginx/sites-available/eduzen
sudo ln -s /etc/nginx/sites-available/eduzen /etc/nginx/sites-enabled/
# nginx.conf dagi yourdomain.com ni o'zgartiring

# 4. SSL sertifikat
sudo certbot --nginx -d yourdomain.com

# 5. Systemd servis
sudo cp eduzen.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable eduzen
sudo systemctl start eduzen

# 6. Nginx qayta ishga tushirish
sudo systemctl restart nginx
```

---

## 🌍 Muhit o'zgaruvchilari (.env)

| O'zgaruvchi | Tavsif | Misol |
|---|---|---|
| `SECRET_KEY` | Django maxfiy kalit | `django-insecure-...` |
| `DEBUG` | Debug rejimi | `False` (prod) |
| `DB_NAME` | MySQL baza nomi | `eduzen_db` |
| `DB_USER` | MySQL foydalanuvchi | `root` |
| `DB_PASSWORD` | MySQL parol | `StrongPass` |
| `PAYME_MERCHANT_ID` | Payme merchant ID | Payme kabineti |
| `PAYME_SECRET_KEY` | Payme maxfiy kalit | Payme kabineti |
| `CLICK_SERVICE_ID` | Click servis ID | Click kabineti |
| `CLICK_SECRET_KEY` | Click maxfiy kalit | Click kabineti |
| `EMAIL_HOST_USER` | Gmail manzili | `you@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Gmail App Password | Gmail sozlamalari |

---

## 📦 Texnologiyalar

| Texnologiya | Versiya | Maqsad |
|---|---|---|
| Django | 5.0.6 | Asosiy framework |
| Django REST Framework | 3.15.2 | REST API |
| SimpleJWT | 5.3.1 | JWT autentifikatsiya |
| django-cors-headers | 4.4.0 | CORS sozlamalari |
| mysqlclient | 2.2.4 | MySQL ulanish |
| Gunicorn | — | Production WSGI server |
| Nginx | — | Reverse proxy |
