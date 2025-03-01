import uvicorn
from src.front_display.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8500,
        ws='websockets'
    ) 