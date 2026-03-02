"""
Calculation Service for Material Export Application
Delegates cost calculations to ExcelCalculationService
"""

from typing import Dict, Optional

from config import Config


class CalculationService:
    """
    Handles material cost calculations via Excel-based computation
    """

    def __init__(self, config: Config, logger=None, excel_service=None):
        self.config = config
        self.logger = logger
        self.excel_service = excel_service

    def compute_all_suppliers_from_excel(
        self,
        ply: str,
        box: str,
        size: str,
        design: str,
        L: float,
        B: float,
        H: float,
    ) -> Dict[str, Optional[Dict]]:
        """
        Compute costs from ALL supplier Excel files.

        Delegates to ExcelCalculationService.compute_all_suppliers().
        Returns dict keyed by supplier name with AJ/AK results, or None per supplier on error.
        """
        if not self.excel_service:
            if self.logger:
                self.logger.log_warning("CalculationService", "No excel_service configured")
            return {}

        return self.excel_service.compute_all_suppliers(ply, box, size, design, L, B, H)
