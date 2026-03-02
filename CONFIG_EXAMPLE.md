# Configuration Example

This file shows how to configure the Material Export System.

## Database Configuration

Edit `config.py` and update these values:

```python
# Database settings
DB_SERVER = 'Saaplegl001'      # Your SQL Server name
DB_NAME = 'Export_DB'           # Your database name
DB_USER = 'your_username'       # Your database username
DB_PASSWORD = 'your_password'   # Your database password
```

## Optional: Adjust Constants

```python
# Constants for calculations
EXTRA_MM_T = 10.0              # T-Offset in mm (default: 10)
EXTRA_MM_U_INNER = 55.0        # U-Formula constant (default: 55)

# Rounding settings
V_ROUND_DECIMALS = 2           # Decimals for V calculation (default: 2)
```

## Optional: Logging Configuration

```python
class LogConfig:
    ENABLED = True              # Master switch
    LOG_DB_QUERIES = True       # Log database queries
    LOG_PARSING = True          # Log input parsing
    LOG_CALCULATIONS = True     # Log calculation steps
    LOG_RULES = True           # Log supplier rules
    LOG_DATA_SOURCE = True     # Log data sources
    LOG_TO_FILE = True         # Write logs to file
    LOG_TO_UI = True           # Show logs in UI
```

## Debug Mode

```python
DEBUG_SHEET = True             # Show detailed calculation output
```

## Security Notes

⚠️ **Important:**
- Never commit `config.py` with real credentials to version control
- Use environment variables for production: `os.environ.get('DB_PASSWORD')`
- Restrict file permissions on the config file
- Use a database user with minimal required permissions
