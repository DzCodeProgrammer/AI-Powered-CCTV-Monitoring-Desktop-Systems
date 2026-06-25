-- Run as MySQL root after server is available.
-- Replace placeholders with values from your local .env (never commit real passwords).
--
-- mysql -u root -p < scripts/init_mysql.sql

CREATE DATABASE IF NOT EXISTS smart_cctv
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Use your DB_USER and DB_PASSWORD from .env
CREATE USER IF NOT EXISTS 'cctv_user'@'localhost' IDENTIFIED BY 'YOUR_DB_PASSWORD';
CREATE USER IF NOT EXISTS 'cctv_user'@'%' IDENTIFIED BY 'YOUR_DB_PASSWORD';

GRANT ALL PRIVILEGES ON smart_cctv.* TO 'cctv_user'@'localhost';
GRANT ALL PRIVILEGES ON smart_cctv.* TO 'cctv_user'@'%';

FLUSH PRIVILEGES;
