wsgi = '''"""
WSGI entry point for Render.com and production servers.
"""
from app import app

if __name__ == "__main__":
    app.run()
