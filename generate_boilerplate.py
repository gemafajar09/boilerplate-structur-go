import os

structure = {
    "cmd/server": ["main.go"],
    "internal/auth": ["jwt.go","hash.go"],
    "internal/config": ["config.go"],
    "internal/db/mysql": ["connection.go","migration.go"],
    "internal/delivery/http/handler": ["auth_handler.go","handler.go"],
    "internal/delivery/http/response": ["error_response.go","success_response.go"],
    "internal/delivery/http/validator": ["validator.go"],
    "internal/delivery/http/": ["router.go"],
    "internal/delivery/middleware": ["auth.go", "logger.go","cors.go"],
    "internal/domain": ["user.go"],
    "internal/repository": ["user_repository.go"],
    "internal/usecase": ["user_usecase.go"],
    "scripts": ["migrate.sh"],
    "migrations": [],
    "api": [],
    "docs": [],
}

main_go = '''package main

import (
	"go-project/internal/config"
	"go-project/internal/db/mysql"
	"go-project/internal/delivery/http"
	"log"
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
		log.Fatalf("Failed to connect to DB: %v", err)
	}

	if err := mysql.AutoMigrate(db); err != nil {
		log.Fatalf("Auto-migrate failed: %v", err)
	}

	port := cfg.ServerPort
	r := http.NewRouter(cfg, db) // kirim db ke router
	if len(port) > 0 && port[0] != ':' {
		port = ":" + port
	}
	log.Fatal(r.Run(port))
}
'''

handler_go = '''package handler

import (
    "github.com/gin-gonic/gin"
    "net/http"
)

func GetHealth(c *gin.Context) {
    c.JSON(http.StatusOK, gin.H{"status": "ok"})
}
'''

auth_handler_go = '''package handler

import (
	"net/http"

	"go-project/internal/delivery/http/response"
	"go-project/internal/delivery/http/validator"
	"go-project/internal/domain"
	"go-project/internal/usecase"

	"github.com/gin-gonic/gin"
)

type AuthHandler struct {
	userUsecase *usecase.UserUsecase
}

func NewAuthHandler(uc *usecase.UserUsecase) *AuthHandler {
	return &AuthHandler{userUsecase: uc}
}

// Request body untuk register
type RegisterRequest struct {
	Name     string `json:"name" binding:"required"`
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required,min=6"`
}

// POST /register
func (h *AuthHandler) Register(c *gin.Context) {
	var req RegisterRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, response.ErrorResponse{
			Success: false,
			Message: "Failed to register user",
			Errors:  validator.PesanError(err),
		})
		return
	}

	user := domain.User{
		Name:     req.Name,
		Email:    req.Email,
		Password: req.Password,
		Role:     domain.UserRole,
	}

	createdUser, err := h.userUsecase.Register(user)
	if err != nil {
		c.JSON(http.StatusBadRequest, response.ErrorResponse{
			Success: false,
			Message: "Failed to register user",
			Errors:  validator.PesanError(err),
		})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"id":    createdUser.Id,
		"name":  createdUser.Name,
		"email": createdUser.Email,
	})
}

// Request body untuk login
type LoginRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required"`
}

// POST /login
func (h *AuthHandler) Login(c *gin.Context) {
	var req LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, response.ErrorResponse{
			Success: false,
			Message: "Failed to login user",
			Errors:  validator.PesanError(err),
		})
		return
	}

	token, err := h.userUsecase.Login(req.Email, req.Password)
	if err != nil {
		c.JSON(http.StatusUnauthorized, response.ErrorResponse{
			Success: false,
			Message: "Invalid email or password",
			Errors:  validator.PesanError(err),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{"token": token})
}
'''

error_response_go = '''package response

type ErrorResponse struct {
	Success bool              `json:"success"`
	Message string            `json:"message"`
	Errors  map[string]string `json:"errors"`
}
'''

success_response_go = '''package response

type SuccessResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Data    any    `json:"data"`
}
'''

router_go = '''package http

import (
	"go-project/internal/config"
	"go-project/internal/delivery/http/handler"
	"go-project/internal/delivery/middleware"
	"go-project/internal/repository"
	"go-project/internal/usecase"

	"go.uber.org/zap"
	"gorm.io/gorm"

	"github.com/gin-gonic/gin"
)

func NewRouter(cfg config.Config, db *gorm.DB) *gin.Engine {
	r := gin.Default()

	// Setup CORS
	r.Use(middleware.CORSMiddleware())

	// setup zap
	cfgzap := zap.NewProductionConfig()
	cfgzap.OutputPaths = []string{"app.log", "stdout"}
	logger, err := cfgzap.Build()
	if err != nil {
		panic(err)
	}
	defer logger.Sync()
	r.Use(middleware.LoggerMiddleware(logger))

	// Setup repository dan usecase
	userRepo := repository.NewUserRepository(db)
	userUsecase := usecase.NewUserUsecase(userRepo)
	authHandler := handler.NewAuthHandler(userUsecase)

	// Public routes
	r.GET("/health", handler.GetHealth)

	// Auth routes group
	authGroup := r.Group("/auth")
	{
		authGroup.POST("/register", authHandler.Register)
		authGroup.POST("/login", authHandler.Login)
	}

	// Protected routes group
	apiGroup := r.Group("/api")
	apiGroup.Use(middleware.JWTAuthMiddleware(cfg.JWT)) // pakai JWT middleware
	{
		// contoh endpoint yang butuh autentikasi
		apiGroup.GET("/profile", func(c *gin.Context) {
			userID := c.GetString("userID") // ambil dari context
			c.JSON(200, gin.H{"userID": userID})
		})
	}

	return r
}
'''

validator_go = '''package validator
    
import (
    "errors"
    "fmt"
    "strings"

    "github.com/go-playground/validator/v10"
    "gorm.io/gorm"
)

func PesanError(err error) map[string]string {
    errorsMap := make(map[string]string)

    var validationErrors validator.ValidationErrors
    if errors.As(err, &validationErrors) {
        for _, fieldError := range validationErrors {
            field := fieldError.Field()

            switch fieldError.Tag() {
            case "required":
                errorsMap[field] = fmt.Sprintf("%s is required", field)
            case "email":
                errorsMap[field] = "Invalid email format"
            case "unique":
                errorsMap[field] = fmt.Sprintf("%s already exists", field)
            case "min":
                errorsMap[field] = fmt.Sprintf("%s must be at least %s characters", field, fieldError.Param())
            case "max":
                errorsMap[field] = fmt.Sprintf("%s must be at most %s characters", field, fieldError.Param())
            case "numeric":
                errorsMap[field] = fmt.Sprintf("%s must be a number", field)
            case "gte":
                errorsMap[field] = fmt.Sprintf("%s must be greater than or equal to %s", field, fieldError.Param())
            case "lte":
                errorsMap[field] = fmt.Sprintf("%s must be less than or equal to %s", field, fieldError.Param())
            case "gt":
                errorsMap[field] = fmt.Sprintf("%s must be greater than %s", field, fieldError.Param())
            case "lt":
                errorsMap[field] = fmt.Sprintf("%s must be less than %s", field, fieldError.Param())
            case "date":
                errorsMap[field] = fmt.Sprintf("%s must be a valid date", field)
            case "time":
                errorsMap[field] = fmt.Sprintf("%s must be a valid time", field)
            case "datetime":
                errorsMap[field] = fmt.Sprintf("%s must be a valid datetime", field)
            case "url":
                errorsMap[field] = fmt.Sprintf("%s must be a valid URL", field)
            case "uuid":
                errorsMap[field] = fmt.Sprintf("%s must be a valid UUID", field)
            case "phone":
                errorsMap[field] = fmt.Sprintf("%s must be a valid phone number", field)
            case "json":
                errorsMap[field] = fmt.Sprintf("%s must be a valid JSON", field)
            default:
                errorsMap[field] = "Invalid value"
            }
        }
    }

    if err != nil {
        if JikaDuplikast(err) {
            switch {
            case strings.Contains(err.Error(), "username"):
                errorsMap["username"] = "Username already exists"
            case strings.Contains(err.Error(), "email"):
                errorsMap["email"] = "Email already exists"
            case strings.Contains(err.Error(), "phone"):
                errorsMap["phone"] = "Phone number already exists"
            case strings.Contains(err.Error(), "uuid"):
                errorsMap["uuid"] = "UUID already exists"
            default:
                errorsMap["duplicate"] = "Duplicate entry"
            }
        } else if errors.Is(err, gorm.ErrRecordNotFound) {
            errorsMap["error"] = "Record not found"
        }
    }

    return errorsMap
}

func JikaDuplikast(err error) bool {
    return err != nil && strings.Contains(err.Error(), "Duplicate entry")
}

'''

config_go = '''package config

import (
	"log"

	"github.com/joho/godotenv"
	"github.com/spf13/viper"
)

type Config struct {
	ServerPort string
	DBUser     string
	DBPassword string
	DBHost     string
	DBPort     int
	DBName     string
	JWT        string
	GIN_MODE   string
}

func LoadConfig() Config {
	err := godotenv.Load()
	if err != nil {
		log.Println(".env file not found, using system env vars")
	}

	viper.SetDefault("SERVER_PORT", ":8080")
	viper.SetDefault("DB_USER", "root")
	viper.SetDefault("DB_PASSWORD", "")
	viper.SetDefault("DB_HOST", "127.0.0.1")
	viper.SetDefault("DB_PORT", 3306)
	viper.SetDefault("DB_NAME", "mydb")
	viper.SetDefault("JWT_SECRET", "secret_key")
	viper.SetDefault("GIN_MODE", "")

	viper.AutomaticEnv()

	return Config{
		ServerPort: viper.GetString("SERVER_PORT"),
		DBUser:     viper.GetString("DB_USER"),
		DBPassword: viper.GetString("DB_PASSWORD"),
		DBHost:     viper.GetString("DB_HOST"),
		DBPort:     viper.GetInt("DB_PORT"),
		DBName:     viper.GetString("DB_NAME"),
		JWT:        viper.GetString("JWT_SECRET"),
		GIN_MODE:   viper.GetString("GIN_MODE"),
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

migration_go = '''package mysql

import (
    "go-project/internal/domain"
    "gorm.io/gorm"
)

func AutoMigrate(db *gorm.DB) error {
    return db.AutoMigrate(
        &domain.User{},
    )
}
'''

hash_go = '''package auth

import "golang.org/x/crypto/bcrypt"

func HashPassword(password string) string {
	hashed, _ := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(hashed)
}

func CheckPasswordHash(password, hashed string) error {
	return bcrypt.CompareHashAndPassword([]byte(hashed), []byte(password))
}
'''

jwt_go = '''package auth

import (
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/spf13/viper"
)

// CustomClaims untuk menyimpan lebih dari satu informasi
type CustomClaims struct {
	UserID uint   `json:"user_id"`
	Email  string `json:"email"`
	Role   string `json:"role"`
	jwt.RegisteredClaims
}

func GenerateToken(userID uint, email string, role string) (string, error) {
	// Secret key untuk JWT
	jwtKey := []byte(viper.GetString("JWT_SECRET"))
	// Atur waktu expired token
	expirationTime := time.Now().Add(60 * time.Minute)

	// Isi klaim dengan user ID dan email
	claims := &CustomClaims{
		UserID: userID,
		Email:  email,
		Role:   role,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expirationTime),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			Subject:   email,
		},
	}

	// Buat token JWT dengan klaim
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString(jwtKey)
	if err != nil {
		return "", err
	}

	return tokenString, nil
}
'''

middleware_auth_go = '''package middleware

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
)

func JWTAuthMiddleware(jwtSecret string) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Authorization header required"})
			return
		}

		// Format Bearer <token>
		parts := strings.SplitN(authHeader, " ", 2)
		if len(parts) != 2 || parts[0] != "Bearer" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Authorization header format must be Bearer {token}"})
			return
		}

		tokenString := parts[1]

		token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
			// Validate signing method
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, jwt.ErrTokenMalformed
			}
			return []byte(jwtSecret), nil
		})

		if err != nil || !token.Valid {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid token"})
			return
		}

		// Optional: Simpan claim/user info ke context
		claims, ok := token.Claims.(jwt.MapClaims)
		if ok {
			c.Set("userID", claims["id"])
			c.Set("email", claims["email"])
			c.Set("role", claims["role"])
		}

		c.Next()
	}
}
'''

logger_go = '''package middleware

import (
	"time"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

func LoggerMiddleware(logger *zap.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()

		c.Next()

		latency := time.Since(start)
		status := c.Writer.Status()

		logger.Info("HTTP request",
			zap.String("method", c.Request.Method),
			zap.String("path", c.Request.URL.Path),
			zap.Int("status", status),
			zap.Duration("latency", latency),
			zap.String("clientIP", c.ClientIP()),
		)
	}
}
'''

cors_go = '''package middleware

import (
	"github.com/gin-gonic/gin"
)

func CORSMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	}
}
'''

domain_user_go = '''package domain   

import "time"

type User struct {
	Id        uint      `json:"id" gorm:"primaryKey"`
	Name      string    `json:"name"`
	Email     string    `json:"email" gorm:"unique;not null"`
	Password  string    `json:"password"`
	Role      Role      `json:"role" gorm:"type:enum('admin','user');default:'user'"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type Role string

const (
	AdminRole Role = "admin"
	UserRole  Role = "user"
)
'''

usecase_user_go = '''package usecase

import (
	"errors"
	"go-project/internal/auth"
	"go-project/internal/domain"
	"go-project/internal/repository"
)

type UserUsecase struct {
	userRepository repository.UserRepository
}

func NewUserUsecase(userRepository repository.UserRepository) *UserUsecase {
	return &UserUsecase{
		userRepository: userRepository,
	}
}

// Register user baru
func (uc *UserUsecase) Register(user domain.User) (domain.User, error) {
	// Hash password sebelum simpan
	user.Password = auth.HashPassword(user.Password)
	return uc.userRepository.CreateUser(user)
}

// Login dengan email & password, return JWT token kalau berhasil
func (uc *UserUsecase) Login(email, password string) (string, error) {
	user, err := uc.userRepository.GetUserByEmail(email)
	if err != nil {
		return "", errors.New("user not found")
	}

	// Verify password bcrypt
	if err := auth.CheckPasswordHash(password, user.Password); err != nil {
		return "", errors.New("invalid credentials")
	}

	// Generate JWT token
	token, err := auth.GenerateToken(user.Id, user.Email, string(user.Role))
	if err != nil {
		return "", err
	}

	return token, nil
}
'''

repository_user_go = '''package repository

import (
	"go-project/internal/domain"

	"gorm.io/gorm"
)

type UserRepository interface {
	GetUsers() ([]domain.User, error)
	GetUserByID(id int) (domain.User, error)
	CreateUser(user domain.User) (domain.User, error)
	UpdateUser(user domain.User) (domain.User, error)
	DeleteUser(id int) error

	GetUserByEmail(email string) (domain.User, error)
}

type userRepository struct {
	db *gorm.DB
}

func NewUserRepository(db *gorm.DB) UserRepository {
	return &userRepository{db: db}
}

func (r *userRepository) GetUsers() ([]domain.User, error) {
	var users []domain.User
	err := r.db.Find(&users).Error
	return users, err
}

func (r *userRepository) GetUserByID(id int) (domain.User, error) {
	var user domain.User
	err := r.db.First(&user, id).Error
	return user, err
}

func (r *userRepository) CreateUser(user domain.User) (domain.User, error) {
	err := r.db.Create(&user).Error
	return user, err
}

func (r *userRepository) UpdateUser(user domain.User) (domain.User, error) {
	err := r.db.Save(&user).Error
	return user, err
}

func (r *userRepository) DeleteUser(id int) error {
	return r.db.Delete(&domain.User{}, id).Error
}

func (r *userRepository) GetUserByEmail(email string) (domain.User, error) {
	var user domain.User
	err := r.db.Where("email = ?", email).First(&user).Error
	return user, err
}
'''

env = '''
SERVER_PORT=8080
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=mydb
GIN_MODE=release
JWT_SECRET=secret_key
'''

taskfile_yaml = '''version: '3'

tasks:
  gomod:
    desc: "Initialize and tidy Go modules"
    cmds:
      - go mod init go-project || echo "module already initialized"
      - go mod tidy

  deps:
    desc: "Download required dependencies"
    cmds:
      - go get github.com/joho/godotenv
      - go get github.com/spf13/viper
      - go get gorm.io/gorm
      - go get github.com/gin-contrib/cors
      - go get go.uber.org/zap
      - go get gorm.io/driver/mysql
      - go get github.com/gin-gonic/gin
      - go get github.com/go-playground/validator/v10
      - go get github.com/golang-jwt/jwt/v5
      - go get golang.org/x/crypto/bcrypt

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
      - goose -dir migrations mysql "user=root password= dbname=go_portofolio sslmode=disable" up

  swag:
    desc: "Generate Swagger docs"
    cmds:
      - swag init -g cmd/server/main.go
'''

files_content = {
    "cmd/server/main.go": main_go,
    "internal/auth/jwt.go": jwt_go,
    "internal/auth/hash.go": hash_go,
    "internal/config/config.go": config_go,
    "internal/db/mysql/connection.go": connection_go,
    "internal/db/mysql/migration.go": migration_go,
    "internal/delivery/http/handler/handler.go": handler_go,
    "internal/delivery/http/handler/auth_handler.go": auth_handler_go,
    "internal/delivery/http/response/error_response.go": error_response_go,
    "internal/delivery/http/response/success_response.go": success_response_go,
    "internal/delivery/http/router.go": router_go,
    "internal/delivery/http/validator/validator.go": validator_go,
    "internal/delivery/middleware/auth.go": middleware_auth_go,
    "internal/delivery/middleware/cors.go": cors_go,
    "internal/delivery/middleware/logger.go": logger_go,
    "internal/domain/user.go": domain_user_go,
    "internal/repository/user_repository.go": repository_user_go,
    "internal/usecase/user_usecase.go": usecase_user_go,
    
}

# Buat folder dan file
for folder, files in structure.items():
    os.makedirs(folder, exist_ok=True)
    for file in files:
        filepath = os.path.join(folder, file)
        filepath_key = f"{folder}/{file}"
        content = files_content.get(filepath_key, "")
        if content:
            with open(filepath, "w") as f:
                f.write(content)
        else:
            open(filepath, "w").close()

# Buat Taskfile.yml
with open("Taskfile.yml", "w") as f:
    f.write(taskfile_yaml)

# Buat file .env
with open(".env", "w") as f:
    f.write(env)

print("✅ Boilerplate Go dengan koneksi MySQL dan Taskfile berhasil dibuat!")
