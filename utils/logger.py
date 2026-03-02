"""
Comprehensive Logging Utility for Material Export Application
Tracks all data sources, calculations, and rule applications
"""

from datetime import datetime
from typing import Any, Optional, Dict, List
from config import LogConfig
import os


class CalculationLogger:
    """
    Comprehensive logger for tracking all calculations, data sources, and rule applications
    """
    
    def __init__(self, config: LogConfig):
        self.config = config
        self.logs = []
        self.current_material = None
        self.current_supplier = None
        
        # Initialize file logging if enabled
        if self.config.LOG_TO_FILE:
            self._init_log_file()
    
    def _init_log_file(self):
        """Initialize log file with header"""
        if not self.config.ENABLED:
            return
            
        try:
            with open(self.config.LOG_FILE_PATH, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Material Export Calculation Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*80}\n\n")
        except Exception as e:
            print(f"Warning: Could not initialize log file: {e}")
    
    def _write(self, message: str, level: str = "INFO"):
        """Write message to logs"""
        if not self.config.ENABLED:
            return
        
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        formatted_msg = f"[{timestamp}] [{level}] {message}"
        
        self.logs.append(formatted_msg)
        
        # Write to file if enabled
        if self.config.LOG_TO_FILE:
            try:
                with open(self.config.LOG_FILE_PATH, 'a', encoding='utf-8') as f:
                    f.write(formatted_msg + '\n')
            except Exception as e:
                print(f"Warning: Could not write to log file: {e}")
    
    def set_context(self, material: str = None, supplier: str = None):
        """Set current context for logging"""
        if material:
            self.current_material = material
        if supplier:
            self.current_supplier = supplier
    
    def log_section(self, title: str):
        """Log a section header"""
        if not self.config.ENABLED:
            return
        
        separator = "-" * 60
        self._write(f"\n{separator}")
        self._write(f"  {title}")
        self._write(separator)
    
    def log_data_source(
        self, 
        field: str, 
        value: Any, 
        source: str, 
        fallback: Any = None,
        material: str = None
    ):
        """
        Track where a data value came from
        
        Args:
            field: Name of the field (e.g., "AC", "L", "GSM")
            value: The actual value used
            source: Description of source (e.g., "DB Column 'Printing & Die Cutting'")
            fallback: What the fallback value would have been
            material: Material number (uses context if not provided)
        """
        if not self.config.ENABLED or not self.config.LOG_DATA_SOURCE:
            return
        
        mat = material or self.current_material or "Unknown"
        msg = f"[DATA SOURCE] {mat} | Field: {field}\n"
        msg += f"  ✓ Source: {source}\n"
        msg += f"  ✓ Value: {value}"
        
        if fallback is not None:
            msg += f"\n  ℹ Fallback would be: {fallback}"
        
        self._write(msg)
    
    def log_calculation_step(
        self,
        step_name: str,
        formula: str,
        result: Any,
        inputs: Dict[str, Any] = None,
        row: int = None
    ):
        """
        Log a calculation step
        
        Args:
            step_name: Name of the calculation (e.g., "Sheet Size T")
            formula: The formula used
            result: The result of the calculation
            inputs: Dictionary of input values
            row: Row number (1, 2, or 3)
        """
        if not self.config.ENABLED or not self.config.LOG_CALCULATIONS:
            return
        
        mat = self.current_material or "Unknown"
        sup = self.current_supplier or "Unknown"
        row_str = f"Row {row}" if row else ""
        
        msg = f"[CALC] {mat} | {sup} {row_str}\n"
        msg += f"  Step: {step_name}\n"
        
        if inputs:
            msg += "  Inputs:\n"
            for key, val in inputs.items():
                msg += f"    {key} = {val}\n"
        
        msg += f"  Formula: {formula}\n"
        msg += f"  Result: {result}"
        
        self._write(msg)
    
    def log_rule_application(
        self,
        rule_type: str,
        sino: int,
        rule_data: Dict[str, Any],
        applied: bool = True,
        reason: str = None
    ):
        """
        Log which supplier rule was applied (or not)
        
        Args:
            rule_type: Type of rule (TU, V, AD, AE)
            sino: Sl#No# value
            rule_data: The rule configuration
            applied: Whether the rule was applied
            reason: Why it was or wasn't applied
        """
        if not self.config.ENABLED or not self.config.LOG_RULES:
            return
        
        sup = self.current_supplier or "Unknown"
        status = "✓ APPLIED" if applied else "✗ NOT APPLIED"
        
        msg = f"[RULE] {sup} | Type: {rule_type} | SINo: {sino}\n"
        msg += f"  {status}\n"
        
        if reason:
            msg += f"  Reason: {reason}\n"
        
        if rule_data:
            msg += "  Rule Configuration:\n"
            for key, val in rule_data.items():
                if val is not None and val != '':
                    msg += f"    {key}: {val}\n"
        
        self._write(msg)
    
    def log_db_query(
        self,
        query_name: str,
        sql: str = None,
        params: List = None,
        row_count: int = None,
        execution_time: float = None
    ):
        """
        Log database query execution
        
        Args:
            query_name: Description of the query
            sql: SQL statement (can be truncated for readability)
            params: Query parameters
            row_count: Number of rows returned
            execution_time: Execution time in seconds
        """
        if not self.config.ENABLED or not self.config.LOG_DB_QUERIES:
            return
        
        msg = f"[DB QUERY] {query_name}\n"
        
        if sql:
            # Truncate long SQL for readability
            sql_display = sql if len(sql) < 200 else sql[:200] + "..."
            msg += f"  SQL: {sql_display}\n"
        
        if params:
            params_str = str(params) if len(str(params)) < 100 else str(params)[:100] + "..."
            msg += f"  Params: {params_str}\n"
        
        if row_count is not None:
            msg += f"  Results: {row_count} row(s)\n"
        
        if execution_time is not None:
            msg += f"  Execution time: {execution_time:.3f}s"
        
        self._write(msg)
    
    def log_parsing(
        self,
        input_str: str,
        parsed_result: Dict,
        parse_type: str = "dimensions"
    ):
        """
        Log parsing operations
        
        Args:
            input_str: The input string that was parsed
            parsed_result: The parsing result
            parse_type: Type of parsing (dimensions, material_input, etc.)
        """
        if not self.config.ENABLED or not self.config.LOG_PARSING:
            return
        
        msg = f"[PARSE] Type: {parse_type}\n"
        msg += f"  Input: {input_str}\n"
        msg += f"  Result: {parsed_result}"
        
        self._write(msg)
    
    def log_triplet_calculation(
        self,
        material: str,
        supplier: str,
        triplet_data: List[Dict],
        sino_triplet: List[int],
        AJ_values: List[float],
        AK_total: float
    ):
        """
        Log complete triplet calculation summary
        
        Args:
            material: Material number
            supplier: Supplier name
            triplet_data: The 3 rows of data
            sino_triplet: The 3 SINo values
            AJ_values: Calculated AJ for each row
            AK_total: Total cost
        """
        if not self.config.ENABLED or not self.config.LOG_CALCULATIONS:
            return
        
        msg = f"[TRIPLET SUMMARY] {material} | {supplier}\n"
        msg += f"  SINo: {sino_triplet}\n"
        
        for i in range(3):
            msg += f"  Row {i+1}: AJ = {AJ_values[i]:.6f}\n"
        
        msg += f"  Total: AK = {AK_total:.2f}"
        
        self._write(msg)
    
    def log_error(self, context: str, error_message: str):
        """Log an error"""
        msg = f"[ERROR] {context}\n  {error_message}"
        self._write(msg, level="ERROR")
    
    def log_warning(self, context: str, warning_message: str):
        """Log a warning"""
        msg = f"[WARNING] {context}\n  {warning_message}"
        self._write(msg, level="WARN")
    
    def log_info(self, message: str):
        """Log general information"""
        self._write(message, level="INFO")
    
    def get_logs(self) -> str:
        """Return all logs as a single string"""
        return '\n'.join(self.logs)
    
    def get_logs_for_material(self, material: str) -> str:
        """Get logs filtered for a specific material"""
        filtered = [log for log in self.logs if material in log]
        return '\n'.join(filtered)
    
    def clear_logs(self):
        """Clear all logs"""
        self.logs = []
    
    def get_log_summary(self) -> Dict[str, int]:
        """Get a summary of log entries by type"""
        summary = {
            'total': len(self.logs),
            'data_source': sum(1 for log in self.logs if '[DATA SOURCE]' in log),
            'calculations': sum(1 for log in self.logs if '[CALC]' in log),
            'rules': sum(1 for log in self.logs if '[RULE]' in log),
            'db_queries': sum(1 for log in self.logs if '[DB QUERY]' in log),
            'errors': sum(1 for log in self.logs if '[ERROR]' in log),
            'warnings': sum(1 for log in self.logs if '[WARNING]' in log),
        }
        return summary
