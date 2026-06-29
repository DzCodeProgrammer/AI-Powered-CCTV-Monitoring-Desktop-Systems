-- Smart CCTV — full database schema (MySQL 8.x)
-- Run after init_mysql.sql or use with an existing database.
--
-- mysql -u root -p smart_cctv < scripts/schema.sql

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL UNIQUE,
    image_path VARCHAR(500) NOT NULL,
    embedding_path VARCHAR(500) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    phone_number VARCHAR(20) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS detections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    confidence FLOAT NULL,
    screenshot_path VARCHAR(500) NULL,
    camera_source VARCHAR(200) NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_detections_timestamp (timestamp),
    CONSTRAINT fk_detections_user FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS attendance_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    detected_name VARCHAR(100) NOT NULL,
    user_id INT NULL,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    camera_source VARCHAR(200) NOT NULL,
    status VARCHAR(50) NOT NULL,
    confidence FLOAT NULL,
    INDEX ix_attendance_detected_name (detected_name),
    INDEX ix_attendance_detected_at (detected_at),
    CONSTRAINT fk_attendance_user FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS unknown_faces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_path VARCHAR(500) NOT NULL,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    camera_source VARCHAR(200) NULL,
    notes VARCHAR(500) NULL,
    INDEX ix_unknown_faces_detected_at (detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
