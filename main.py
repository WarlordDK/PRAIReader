from fastapi import FastAPI
from app.router import router as router_analyze
import uvicorn

app = FastAPI()
app.include_router(router_analyze)

@app.get('/')
async def home_page():
    return {'message' : 'uvicorn running'}

if __name__ == "__main__":
    uvicorn.run(app=app, host='127.0.0.1', port=8000)
