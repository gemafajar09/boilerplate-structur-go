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
│   ├── domain/user.go
│   ├── usecase/user_usecase.go
│   └── repository/user_repository.go
├── scripts/migrate.sh
├── migrations/
├── api/
├── docs/
├── Makefile

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