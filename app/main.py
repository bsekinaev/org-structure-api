from fastapi import FastAPI

app = FastAPI(title='API организационной структуры', version='1.0.0')

@app.get('/')
def root():
    return {'status': 'ok'}


