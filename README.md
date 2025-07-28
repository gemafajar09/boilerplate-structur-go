# 🚀 Go Project Boilerplate Generator

Script Python ini secara otomatis membuat struktur project Golang dengan pendekatan Clean Architecture.

---

## 📁 Struktur Folder

```bash
go-project/
├── api/
├── cmd/server/main.go
├── docs/
├── internal/
│   ├── auth
│   │   ├── hash.go
│   │   ├── jwt.go
│   ├── config/config.go
│   ├── db/mysql/
│   │   ├── connection.go
│   │   ├── migration.go
│   ├── delivery/http/
│   │   ├── http
│   │   |   ├── handler
│   │   |   |    ├── auth_handler.go
│   │   |   |    └── handler.go
│   │   |   ├── response
│   │   |   |    ├── error_response.go
│   │   |   |    └── success_response.go
│   │   |   ├──validator
│   │   |   |    └── validator.go
│   │   |   └── router.go
│   │   ├── middleware
│   │   |   ├── auth.go
│   │   |   ├── cors.go
│   │   |   └── logger.go
│   ├── domain/user.go
│   ├── usecase/user_usecase.go
│   └── repository/user_repository.go
├── migrations/
├── scripts/migrate.sh
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
task gomod
task deps
```

Setelah task selesai baru jalanakn project sperti biasa:

```bash
go run cmd/server/main.go
```

**Tambahan**
```
Unutk nama project bisa disesuaikan. silahkan ganti go-project pada file boilerplate dengan nama project sendiri
```