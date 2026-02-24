# Test server startup
$env:PYTHONPATH="."

Write-Host "Starting test server on port 8007..."
python -c "
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get('/')
async def root():
    return {'message': 'Hello World'}

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8007)
" 2>&1
