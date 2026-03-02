"""
Parsing Utilities for Material Export Application
Handles parsing of dimensions, material input, etc.
"""

import re
from typing import Dict, List, Tuple, Optional


def parse_dimensions(desc: str) -> Dict[str, Optional[str]]:
    """
    Parse dimensions and ply from SAP Description
    
    Args:
        desc: SAP description string
        
    Returns:
        Dictionary with L, B, H, and TYPE
        
    Example:
        "BOX 680X380X535 3 PLY" -> {'L': '680', 'B': '380', 'H': '535', 'TYPE': '3 Ply'}
    """
    desc_norm = desc.upper()
    L = B = H = None
    
    # Parse dimensions like 100X200X300 or 500 X 340 X 280mm
    match = re.search(r'(\d+)\s*[X×]\s*(\d+)(?:\s*[X×]\s*(\d+))?', desc_norm)
    if match:
        L = match.group(1)
        B = match.group(2)
        if match.group(3):
            H = match.group(3)
    
    # Parse ply type (must be exact format "N Ply")
    TYPE = None
    ply_match = re.search(r'(\d+)\s*PLY', desc, re.IGNORECASE)
    if ply_match:
        TYPE = f"{ply_match.group(1)} Ply"
    
    return {'L': L, 'B': B, 'H': H, 'TYPE': TYPE}


def parse_material_input(input_text: str, logger=None) -> Tuple[List[str], Dict[str, Dict]]:
    """
    Parse material input from user
    
    Supports multiple formats:
    - MATNR (just material number)
    - MATNR 100x200x300 (with dimensions, x separator)
    - MATNR;100;200;300 (with dimensions, semicolon separator)
    
    Args:
        input_text: Multi-line string with material numbers
        logger: Optional logger instance
        
    Returns:
        Tuple of (material_array, dimension_overrides)
        - material_array: List of unique material numbers
        - dimension_overrides: Dict mapping matnr -> {'L': ..., 'M': ..., 'N': ...}
    """
    raw_lines = input_text.strip().split('\n')
    mat_array = []
    dim_overrides = {}
    
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to parse different formats
        parsed = False
        
        # Format 1: MATNR 100x200x300
        match = re.match(r'^\s*([A-Za-z0-9\-]+)\s+(\d+)[xX×](\d+)(?:[xX×](\d+))?\s*$', line)
        if match:
            mat = match.group(1)
            L = match.group(2)
            M = match.group(3)
            N = match.group(4) if match.group(4) else None
            
            mat_array.append(mat)
            dim_overrides[mat] = {'L': L, 'M': M, 'N': N}
            
            if logger:
                logger.log_parsing(
                    line,
                    {'material': mat, 'dimensions': {'L': L, 'M': M, 'N': N}},
                    "material_input_with_dimensions_x"
                )
            parsed = True
        
        # Format 2: MATNR;L;M;N
        if not parsed:
            match = re.match(r'^\s*([A-Za-z0-9\-]+)\s*;\s*(\d+)\s*;\s*(\d+)\s*(?:;\s*(\d+))?\s*$', line)
            if match:
                mat = match.group(1)
                L = match.group(2)
                M = match.group(3)
                N = match.group(4) if match.group(4) else None
                
                mat_array.append(mat)
                dim_overrides[mat] = {'L': L, 'M': M, 'N': N}
                
                if logger:
                    logger.log_parsing(
                        line,
                        {'material': mat, 'dimensions': {'L': L, 'M': M, 'N': N}},
                        "material_input_with_dimensions_semicolon"
                    )
                parsed = True
        
        # Format 3: Just material number
        if not parsed:
            match = re.match(r'^\s*([A-Za-z0-9\-]+)\s*$', line)
            if match:
                mat = match.group(1)
                mat_array.append(mat)
                
                if logger:
                    logger.log_parsing(
                        line,
                        {'material': mat, 'dimensions': None},
                        "material_input_no_dimensions"
                    )
                parsed = True
        
        # Log unparseable lines
        if not parsed and logger:
            logger.log_warning("Parsing", f"Could not parse line: {line}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_mat_array = []
    for mat in mat_array:
        if mat not in seen:
            seen.add(mat)
            unique_mat_array.append(mat)
    
    if logger:
        logger.log_info(f"Parsed {len(unique_mat_array)} unique material number(s)")
        if dim_overrides:
            logger.log_info(f"Found dimension overrides for {len(dim_overrides)} material(s)")
    
    return unique_mat_array, dim_overrides


def num(v) -> float:
    """
    Convert value to float, accepting comma as decimal separator
    
    Args:
        v: Value to convert (can be string, int, float, or None)
        
    Returns:
        Float value or 0.0 if conversion fails
    """
    if v is None or v == '':
        return 0.0
    
    if isinstance(v, (int, float)):
        return float(v)
    
    # Convert string, replacing comma with dot
    try:
        return float(str(v).replace(',', '.'))
    except (ValueError, TypeError):
        return 0.0


def gv(row: Dict, keys: List[str]) -> Optional[any]:
    """
    Get value from row using multiple key candidates
    Tries each key in order and returns the first non-empty value
    
    Args:
        row: Dictionary to search
        keys: List of possible keys to try
        
    Returns:
        First non-empty value found, or None
        
    Example:
        gv(row, ['Price Quoted 03#10', 'Price Quoted New', 'Price Quoted 03.10'])
    """
    for k in keys:
        if k in row and row[k] not in ('', None):
            return row[k]
    return None


def parse_csv_list(s: str) -> List[str]:
    """
    Parse comma-separated list to uppercase array
    
    Args:
        s: Comma-separated string (e.g., "KM,KB,KL")
        
    Returns:
        List of uppercase strings (e.g., ['KM', 'KB', 'KL'])
    """
    if not s or s == '':
        return []
    
    parts = [p.strip() for p in s.split(',')]
    return [p.upper() for p in parts if p]
