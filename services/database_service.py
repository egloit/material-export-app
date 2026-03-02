"""
Database Service for Material Export Application
Handles all database interactions with SQL Server
"""

import pyodbc
from typing import List, Dict
import time
from config import Config


class DatabaseService:
    """
    Handles all database operations
    """
    
    def __init__(self, config: Config, logger=None):
        self.config = config
        self.logger = logger
        self.connection = None
    
    def _get_connection(self):
        """Get or create database connection"""
        if self.connection is None:
            if getattr(self.config, 'DB_USE_WINDOWS_AUTH', False):
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={self.config.DB_SERVER};"
                    f"DATABASE={self.config.DB_NAME};"
                    f"Trusted_Connection=yes"
                )
            else:
                conn_str = (
                    "DRIVER={ODBC Driver 17 for SQL Server};"
                    f"SERVER={self.config.DB_SERVER},{getattr(self.config, 'DB_PORT', 1433)};"
                    f"DATABASE={self.config.DB_NAME};"
                    f"UID={self.config.DB_USER};"
                    f"PWD={self.config.DB_PASSWORD};"
                    "Encrypt=no;"
                    "TrustServerCertificate=yes;"
                    "Connection Timeout=30;"
                )
            
            if self.logger:
                self.logger.log_info(f"Connecting to database: {self.config.DB_SERVER}/{self.config.DB_NAME}")
            
            try:
                self.connection = pyodbc.connect(conn_str)
                if self.logger:
                    self.logger.log_info("Database connection established")
            except Exception as e:
                if self.logger:
                    self.logger.log_error("Database Connection", str(e))
                raise
        
        return self.connection
    
    def get_sap_master_data(self, material_numbers: List[str]) -> List[Dict]:
        """
        Query SAP master data for given material numbers
        
        Args:
            material_numbers: List of material numbers to query
            
        Returns:
            List of dictionaries with SAP Material Nr and SAP Description
        """
        if not material_numbers:
            return []
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build query with placeholders
        placeholders = ','.join(['?' for _ in material_numbers])
        sql = f"""
            SELECT DISTINCT
                zmbest13_matnr AS [SAP Material Nr],
                zmbest13_maktx AS [SAP Description]
            FROM [Export_DB].[dbo].[extr_sap_ZMBEST13]
            WHERE zmbest13_matnr IN ({placeholders})
        """
        
        start_time = time.time()
        
        try:
            cursor.execute(sql, material_numbers)
            columns = [column[0] for column in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            execution_time = time.time() - start_time
            
            if self.logger:
                self.logger.log_db_query(
                    query_name="SAP Master Data",
                    sql=sql,
                    params=material_numbers,
                    row_count=len(rows),
                    execution_time=execution_time
                )
            
            return rows
        
        except Exception as e:
            if self.logger:
                self.logger.log_error("SAP Master Data Query", str(e))
            raise
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            if self.logger:
                self.logger.log_info("Database connection closed")
