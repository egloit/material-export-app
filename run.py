"""
Startskript für die Material Export App.
Kann direkt in PyCharm ausgeführt werden.
"""
import sys
from streamlit.web import cli as stcli


def main():
    sys.argv = ["streamlit", "run", "app.py", "--server.headless=true"]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
