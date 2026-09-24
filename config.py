"""
Configuration for Material Export Application
"""

import os
from datetime import datetime


class Config:
    """Application configuration"""

    # Application settings

    # Database settings
    DB_SERVER = os.environ.get('DB_SERVER', 'Saaplegl001')
    DB_PORT = int(os.environ.get('DB_PORT', '1433'))
    DB_NAME = os.environ.get('DB_NAME', 'Export_DB')
    DB_USE_WINDOWS_AUTH = os.environ.get('DB_USE_WINDOWS_AUTH', 'true').lower() == 'true'
    DB_USER = os.environ.get('DB_USER', '')  # Only used if DB_USE_WINDOWS_AUTH = False
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')  # Only used if DB_USE_WINDOWS_AUTH = False

    # Debug settings
    DEBUG_SHEET = os.environ.get('DEBUG_SHEET', 'true').lower() == 'true'

    # Constants for calculations
    EXTRA_MM_T = float(os.environ.get('EXTRA_MM_T', '10.0'))  # T-Offset: +10 mm
    EXTRA_MM_U_INNER = float(os.environ.get('EXTRA_MM_U_INNER', '55.0'))  # U-Formula: ((L+M+55) * 2) / 25.4

    # Rounding settings
    V_ROUND_DECIMALS = int(os.environ.get('V_ROUND_DECIMALS', '2'))

    # Excel-based calculation settings
    EXCEL_FOLDER = os.environ.get('EXCEL_FOLDER', os.path.join(os.path.dirname(__file__), 'Excel'))
    EXCEL_BASE_FOLDER = os.environ.get('EXCEL_BASE_FOLDER', os.path.join(os.path.dirname(__file__), 'Excel_base'))
    EXCEL_ENABLED = os.environ.get('EXCEL_ENABLED', 'true').lower() == 'true'
    EXCEL_CACHE_MODELS = os.environ.get('EXCEL_CACHE_MODELS', 'true').lower() == 'true'


class LogConfig:
    """Logging configuration"""
    
    # Master switch
    ENABLED = True
    
    # Granular control - what to log
    LOG_DB_QUERIES = True      # SQL queries + results
    LOG_PARSING = True         # Dimensions parsing
    LOG_CALCULATIONS = True    # Each calculation step
    LOG_RULES = True          # Which supplier rule was used
    LOG_DATA_SOURCE = True    # Where each value came from (DB column, fallback, etc.)
    
    # Output options
    LOG_TO_FILE = True
    LOG_TO_UI = True          # In Streamlit as expandable section
    
    # File settings
    LOG_FILE_PATH = os.path.join(
        os.path.dirname(__file__), 
        'logs', 
        f'material_export_{datetime.now().strftime("%Y%m%d")}.log'
    )
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
