"""
Export Service for Material Export Application
Handles CSV export functionality
"""

import csv
import io
from typing import List, Dict
from datetime import datetime


class ExportService:
    """
    Handles data export to CSV
    """
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def export_to_csv(self, enhanced_rows: List[Dict]) -> str:
        """
        Export enhanced rows to CSV format
        
        Args:
            enhanced_rows: List of dictionaries with material data
            
        Returns:
            CSV data as string
        """
        if not enhanced_rows:
            return ""
        
        # Create CSV in memory
        output = io.StringIO()
        
        # Use semicolon as delimiter (as in PHP version)
        fieldnames = list(enhanced_rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        
        # Write header and rows
        writer.writeheader()
        writer.writerows(enhanced_rows)
        
        csv_data = output.getvalue()
        output.close()
        
        if self.logger:
            self.logger.log_info(f"Exported {len(enhanced_rows)} row(s) to CSV")
        
        return csv_data
