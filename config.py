"""
Centralized configuration management for the application.

This module reads settings from `config.ini` and exposes them through a
single `settings` object. This avoids scattering environment variable lookups
across the codebase and makes configuration easier to manage and test.
"""
import configparser
import os


class AppConfig:
    def __init__(self, config_file="config.ini"):
        parser = configparser.ConfigParser()
        parser.read(config_file)

        allowed_ext_str = parser.get("app", "allowed_ext", fallback="")
        self.ALLOWED_EXTENSIONS = {ext.strip() for ext in allowed_ext_str.split(",") if ext.strip()}
        self.MAX_UPLOAD_MB = parser.getint("app", "max_upload_mb", fallback=100)
        self.INDEX_LINES_PER_CHUNK = parser.getint("file_processing", "index_lines_per_chunk", fallback=1000)

settings = AppConfig()