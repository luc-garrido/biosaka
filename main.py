"""Entrada compativel: uvicorn main:site."""
from backend.app.main import site, app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:site", host="127.0.0.1", port=8000, reload=True)
