import os

structure = {
    "cmd/server": ["main.go"],
    "internal/domain": ["user.go"],
    "internal/usecase": ["user_usecase.go"],
    "internal/repository": ["user_repository.go"],
    "internal/delivery/http": ["handler.go", "router.go"],
    "internal/config": ["config.go"],
    "scripts": ["migrate.sh"],
    "migrations": [],
    "api": [],
    "docs": [],
}

main_go = '''package main

import (
    "log"
    "go-expert/internal/config"
    "go-expert/internal/delivery/http"
)

func main() {
    cfg := config.LoadConfig()
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
    "go-expert/internal/config"
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
}

func LoadConfig() Config {
    viper.SetDefault("SERVER_PORT", ":8080")
    viper.AutomaticEnv()
    return Config{
        ServerPort: viper.GetString("SERVER_PORT"),
    }
}
'''

makefile = '''run:
\tgo run cmd/server/main.go

test:
\tgo test ./...

lint:
\tgolangci-lint run

migrate-up:
\tgoose -dir migrations postgres "user=... dbname=..." up

swag:
\tswag init -g cmd/server/main.go
'''

files_content = {
    "cmd/server/main.go": main_go,
    "internal/delivery/http/handler.go": handler_go,
    "internal/delivery/http/router.go": router_go,
    "internal/config/config.go": config_go,
    "Makefile": makefile
}

for folder, files in structure.items():
    os.makedirs(folder, exist_ok=True)
    for file in files:
        filepath = os.path.join(folder, file)
        with open(filepath, "w") as f:
            content = files_content.get(filepath, "")
            f.write(content)

with open("Makefile", "w") as f:
    f.write(makefile)

print("✅ Boilerplate Go Expert berhasil dibuat!")
