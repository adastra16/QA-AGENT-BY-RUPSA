import os
import sys

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Change to backend directory for file operations
os.chdir(backend_dir)

# Import after path is set
try:
    from main import app
    import uvicorn
    
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 8000))
        print(f"Starting server on port {port}")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True,
            loop="asyncio"
        )
except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

