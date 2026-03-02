# 🚀 Quick Start Guide

## Installation (5 Minuten)

### 1. Python installieren
- Download: https://www.python.org/downloads/
- ✅ Wichtig: "Add Python to PATH" anhaken!

### 2. Projekt entpacken
```
C:\material-export-app\
```

### 3. Datenbank konfigurieren
Öffne `config.py` und trage ein:
```python
DB_NAME = 'Export_DB'          # Dein Datenbankname
DB_USER = 'dein_user'           # Dein Username
DB_PASSWORD = 'dein_passwort'   # Dein Passwort
```

### 4. Starten
Doppelklick auf `start.bat`

✅ Das war's! Die App öffnet sich automatisch im Browser.

---

## Erste Schritte

### Material eingeben
```
KM0290 680x380x535
KM1234
KM5678;120;95;80
```

### Button klicken
🔍 Submit & Show Table

### Ergebnisse ansehen
- ✅ Haupttabelle mit allen Materialien
- ✅ Lieferanten-Details aufklappbar
- ✅ Berechnete Kosten pro Triplet

### CSV exportieren
💾 Download CSV

---

## Logging aktivieren (optional)

In der Sidebar:
- ✅ Enable Logging
- ✅ Show in UI (um Logs zu sehen)
- ✅ Write to File (um Logs zu speichern)

---

## Debug Mode

Für detaillierte Berechnungsschritte:
- ✅ Debug Output aktivieren

---

## Probleme?

### "Python not found"
→ Python installieren und PATH setzen

### "Module not found"
→ Command Prompt öffnen:
```batch
cd C:\material-export-app
pip install -r requirements.txt
```

### "Database connection failed"
→ config.py prüfen (Server/User/Password)

---

## Support

📖 Vollständige Dokumentation: `README.md`
📧 Bei Problemen: Logs in `logs/` Ordner prüfen
