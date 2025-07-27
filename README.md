# 🚀 Go Project Generator

Script ini akan membuat struktur boilerplate proyek Golang menggunakan pendekatan **Clean Architecture**.

---

## 📂 Fitur Utama

- ✅ Struktur modular dan scalable (Clean Architecture)
- 🔌 Koneksi ke PostgreSQL
- 🌍 Middleware CORS
- ⚙️ Konfigurasi berbasis `.env`
- 📦 Siap untuk dikembangkan dengan dependency injection, GORM, dll

---

## 🧱 Struktur Project yang Dibuat

```bash
go-project/
├── cmd/server/main.go            # Entry point aplikasi
├── internal/
│   ├── config/config.go          # Load konfigurasi dari .env
│   ├── db/postgres.go            # Koneksi ke PostgreSQL
│   └── delivery/http/
│       ├── handler.go            # Health check endpoint
│       ├── middleware.go         # Middleware CORS
│       └── router.go             # Routing setup
├── .env                          # File konfigurasi environment
├── Makefile                      # Shortcut untuk build/run/test
```
## ⚙️ Cara Menggunakan

**Jalankan Script Generator**
```bash
python generate_boilerplate.py
```

Script ini akan membuat struktur folder dan file di direktori saat ini.

**Buat File .env**
Buat file .env di root folder:
```env
SERVER_PORT=:8080
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=goexpert
```

**Install Dependency Go**
```bash
go mod tidy
go get github.com/gin-gonic/gin
go get github.com/spf13/viper
go get github.com/joho/godotenv
go get github.com/lib/pq
```

**Jalankan Aplikasi**
```bash
go run cmd/server/main.go
```

Atau jika ingin menggunakan Makefile:

```bash
make run
```

**Tambahan**
```
Unutk nama project bisa disesuaikan. silahkan ganti go-project pada file boilerplate dengan nama project sendiri
```