# 🚀 Go Project Boilerplate Generator

Script Python ini secara otomatis membuat struktur project Golang dengan pendekatan Clean Architecture.

---

## 📁 Struktur Folder

```bash
go-project/
├── cmd/server/main.go
├── internal/
│   ├── config/config.go
│   ├── delivery/http/
│   │   ├── handler.go
│   │   └── router.go
│   ├── db/mysql/connection.go
│   ├── domain/user.go
│   ├── usecase/user_usecase.go
│   └── repository/user_repository.go
├── scripts/migrate.sh
├── migrations/
├── api/
├── docs/
├── Taskfile

```
## ⚙️ Cara Menggunakan

**Jalankan Script Generator**
```bash
python generate_boilerplate.py
```

Script ini akan membuat struktur folder dan file di direktori saat ini.


**Jalankan Task**
```bash
task tasks
```

Setelah task selesai baru jalanakn project sperti biasa:

```bash
go run cmd/server/main.go
```

**Tambahan**
```
Unutk nama project bisa disesuaikan. silahkan ganti go-project pada file boilerplate dengan nama project sendiri
```