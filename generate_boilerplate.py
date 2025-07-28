import os

structure = {
    "cmd/server": ["main.go"],
    "internal/config": ["config.go"],
    "internal/delivery/http": ["handler.go", "router.go"],
    "internal/domain": ["user.go"],
    "internal/db/mysql": ["connection.go"],
    "internal/usecase": ["user_usecase.go"],
    "internal/repository": ["user_repository.go"],
    "scripts": ["migrate.sh"],
    "migrations": [],
    "api": [],
    "docs": [],
}

main_go = '''package main

import (
    "log"
    "go-project/internal/config"
    "go-project/internal/db/mysql"
    "go-project/internal/delivery/http"
)

func main() {
    cfg := config.LoadConfig()

    db, err := mysql.NewMySQLConnection(
        cfg.DBUser,
        cfg.DBPassword,
        cfg.DBHost,
        cfg.DBName,
        cfg.DBPort,
    )
    if err != nil {
        log.Fatalf("Gagal terhubung ke DB: %v", err)
    }

    r := http.NewRouter(cfg)
    log.Fatal(r.Run(cfg.ServerPort))
}
'''

handler_go = '''package http

import (
    "github.com/gin-gonic/gin"
    "net/http"
)

func GetHealth(c *gin.Context) {
    c.JSON(http.StatusOK, gin.H{"status": "ok"})
}
'''

router_go = '''package http

import (
    "github.com/gin-gonic/gin"
    "go-project/internal/config"
)

func NewRouter(cfg config.Config) *gin.Engine {
    r := gin.Default()
    r.GET("/health", GetHealth)
    return r
}
'''

config_go = '''package config

import (
    "github.com/spf13/viper"
)

type Config struct {
    ServerPort string
    DBUser     string
    DBPassword string
    DBHost     string
    DBPort     int
    DBName     string
}

func LoadConfig() Config {
    viper.SetDefault("SERVER_PORT", ":8080")
    viper.SetDefault("DB_USER", "root")
    viper.SetDefault("DB_PASSWORD", "")
    viper.SetDefault("DB_HOST", "127.0.0.1")
    viper.SetDefault("DB_PORT", 3306)
    viper.SetDefault("DB_NAME", "mydb")

    viper.AutomaticEnv()

    return Config{
        ServerPort: viper.GetString("SERVER_PORT"),
        DBUser:     viper.GetString("DB_USER"),
        DBPassword: viper.GetString("DB_PASSWORD"),
        DBHost:     viper.GetString("DB_HOST"),
        DBPort:     viper.GetInt("DB_PORT"),
        DBName:     viper.GetString("DB_NAME"),
    }
}
'''

connection_go = '''package mysql

import (
    "fmt"
    "gorm.io/driver/mysql"
    "gorm.io/gorm"
)

func NewMySQLConnection(user, password, host, dbname string, port int) (*gorm.DB, error) {
    dsn := fmt.Sprintf("%s:%s@tcp(%s:%d)/%s?parseTime=true",
        user, password, host, port, dbname,
    )
    db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
    if err != nil {
        return nil, err
    }

    return db, nil
}
'''

taskfile_yaml = '''version: '3'

tasks:
  gomod:
    desc: "Initialize dan tidy Go modules"
    cmds:
      - go mod init go-project || echo "module sudah diinisialisasi"
      - go mod tidy

  deps:
    desc: "Download required dependencies"
    cmds:
      - go get github.com/spf13/viper
      - go get gorm.io/gorm
      - go get gorm.io/driver/mysql
      - go get github.com/gin-gonic/gin
      - go get github.com/go-playground/validator/v10
      - go get github.com/golang-jwt/jwt/v5

  run:
    desc: "Run the main Go server"
    cmds:
      - go run cmd/server/main.go

  test:
    desc: "Run all tests"
    cmds:
      - go test ./...

  lint:
    desc: "Run golangci-lint"
    cmds:
      - golangci-lint run

  migrate-up:
    desc: "Run goose migrations"
    cmds:
      - goose -dir migrations mysql "user=root password=yourpassword dbname=yourdb sslmode=disable" up

  swag:
    desc: "Generate Swagger docs"
    cmds:
      - swag init -g cmd/server/main.go
'''

files_content = {
    "cmd/server/main.go": main_go,
    "internal/delivery/http/handler.go": handler_go,
    "internal/delivery/http/router.go": router_go,
    "internal/config/config.go": config_go,
    "internal/db/mysql/connection.go": connection_go,
}

# Buat folder dan file
for folder, files in structure.items():
    os.makedirs(folder, exist_ok=True)
    for file in files:
        filepath = os.path.join(folder, file)
        content = files_content.get(filepath, "")
        with open(filepath, "w") as f:
            f.write(content)

# Buat Taskfile.yml
with open("Taskfile.yml", "w") as f:
    f.write(taskfile_yaml)

print("✅ Boilerplate Go dengan koneksi MySQL dan Taskfile berhasil dibuat!")
