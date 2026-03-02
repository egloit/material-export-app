# Material Export System - Python/Streamlit Version

Converted from PHP to Python/Streamlit for improved maintainability and user experience.

## Features

- ✅ SAP material number search with dimension parsing
- ✅ Complex cost calculations (sheet sizes, weights, pricing)
- ✅ Supplier-specific rules engine (TU, V, AD, AE formulas)
- ✅ Comprehensive logging system (tracks all data sources and calculations)
- ✅ CSV export functionality
- ✅ Debug mode for detailed calculation steps
- ✅ Windows Server compatible

## Installation

### Prerequisites

- Python 3.8 or higher
- SQL Server with ODBC Driver 17
- Access to Export_DB database

### Step 1: Install Python

Download and install Python from https://www.python.org/downloads/

Make sure to check "Add Python to PATH" during installation.

### Step 2: Install Dependencies

Open Command Prompt and navigate to the project folder:

```batch
cd path\to\material-export-app
pip install -r requirements.txt
```

### Step 3: Configure Database

Edit `config.py` and fill in your database credentials:

```python
DB_SERVER = 'Saaplegl001'
DB_NAME = 'Export_DB'  # Your database name
DB_USER = 'your_user'   # Your database user
DB_PASSWORD = 'your_password'  # Your database password
```

## Running the Application

### Method 1: Double-click (Windows)

Simply double-click `start.bat` to launch the application.

### Method 2: Command Line

```batch
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## Usage

### 1. Enter Material Numbers

Enter SAP material numbers in the text area, one per line.

**Formats supported:**
- Just material number: `KM0290`
- With dimensions (x separator): `KM0290 680x380x535`
- With dimensions (semicolon): `KM0290;680;380;535`

### 2. View Results

The system will:
1. Query SAP master data
2. Extract material types (BOX, PLY, SIZE, DESIGN)
3. Find matching suppliers
4. Calculate costs for each supplier (in triplets of 3 rows)
5. Apply supplier-specific rules if available

### 3. Download Results

- **CSV Export**: Download the main material table
- **Log Export**: Download detailed calculation logs

## Configuration Options

### Logging (in Sidebar)

- **Enable Logging**: Master switch for all logging
- **DB Queries**: Log all database queries and results
- **Calculations**: Log each calculation step
- **Supplier Rules**: Log which rules were applied
- **Data Sources**: Track where each value came from
- **Show in UI**: Display logs in the web interface
- **Write to File**: Save logs to `logs/` folder

### Debug Mode

Enable "Debug Output" to see detailed calculation steps for each triplet.

## File Structure

```
material-export-app/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration & settings
├── requirements.txt            # Python dependencies
├── start.bat                   # Windows startup script
├── README.md                   # This file
│
├── services/
│   ├── __init__.py
│   ├── database_service.py     # Database operations
│   ├── calculation_service.py  # Cost calculations
│   └── export_service.py       # CSV export
│
├── utils/
│   ├── __init__.py
│   ├── parsers.py              # Input parsing utilities
│   └── logger.py               # Logging system
│
├── logs/                       # Log files (auto-created)
└── data/                       # Temporary data (auto-created)
```

## Calculation Logic

### Sheet Size Calculation

**Row 1 (Raw values):**
- T1 = (M + N + 10) / 25.4
- U1 = ((L + M + 55) * 2) / 25.4

**Row 2/3 (Rounded + Add-ons):**
- T2 = ceil(T1) + 0.2
- U2 = ceil(U1) + 0.3
- T3 = T2, U3 = U2

### Weight Calculation (V)

- Row 1: Uses T/U from Row 2
- Row 2: Uses T/U from Row 2
- Row 3: Uses T/U from Row 3

**Formula:** `V = (T * U * GSM) / 1550000`

### Cost Calculation

1. **Material Cost (Z):**
   - V = Weight
   - X = V * 0.03 (Wastage)
   - W = V * S (Material)
   - Y = X * S (Wastage cost)
   - Z = W + Y

2. **Process Cost (AF):**
   - AB = (V + X) * AA (Conversion)
   - AC = Printing/Die Cutting
   - AD = Varnish (may use rule formula)
   - AE = Packing (may use rule formula)
   - AF = AB + AC + AD + AE

3. **Final Price (AJ):**
   - AG = Freight charges
   - AH = 0.10 * (Z + AF + AG) (10% profit)
   - AI = Step discounts
   - AJ = Z + AF + AG + AH - AI

4. **Total (AK):**
   - AK = AJ1 + AJ2 + AJ3

### Supplier Rules

The system supports supplier-specific calculation rules stored in the database:

- **TU Rules**: Custom formulas for sheet size calculation
- **V Rules**: Weight multipliers or divisors
- **AD Rules**: Varnish cost formulas (can filter by box type)
- **AE Rules**: Packing cost formulas (can filter by box type)

Rules can be:
- **SINo-specific** (applied to specific Sl#No#)
- **Global** (SINo=0, applied to all if no specific rule exists)

## Troubleshooting

### Database Connection Errors

1. Check that ODBC Driver 17 for SQL Server is installed
2. Verify database credentials in `config.py`
3. Ensure the server is accessible from your machine
4. Check Windows Firewall settings

### "ModuleNotFoundError"

Run: `pip install -r requirements.txt`

### Application Won't Start

1. Check Python version: `python --version` (must be 3.8+)
2. Try: `python -m streamlit run app.py`
3. Check logs in `logs/` folder

### Calculations Don't Match Expected Values

1. Enable "Debug Output" in sidebar
2. Enable all logging options
3. Review the detailed logs to see:
   - Which data sources were used
   - Which formulas were applied
   - Which supplier rules were matched

## Running as Windows Service

For production deployment, you can run the application as a Windows Service:

1. Install NSSM (Non-Sucking Service Manager): https://nssm.cc/
2. Run: `nssm install MaterialExport`
3. Set:
   - Path: `C:\Python\python.exe`
   - Startup directory: `C:\path\to\material-export-app`
   - Arguments: `-m streamlit run app.py --server.port 8501 --server.address 0.0.0.0`

## Support & Maintenance

For questions or issues:
1. Check the logs in `logs/` folder
2. Enable debug mode and review calculation steps
3. Contact your system administrator

## Version History

**2.0 (2026-01-22)**
- Complete rewrite in Python/Streamlit
- Added comprehensive logging system
- Added supplier rules engine
- Improved user interface
- Better error handling

**1.0 (Original PHP version)**
- Initial implementation
