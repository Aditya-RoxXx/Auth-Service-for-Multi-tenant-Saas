from fastapi import FastAPI
from .database import engine, Base
from .routes import router as auth_router
from . import models
import psycopg2
from psycopg2.extras import RealDictCursor
import time


models.Base.metadata.create_all(bind=engine)


app = FastAPI()

while True:

    try:
        conn = psycopg2.connect(host='localhost', database='saas_assignment', user='postgres', password='password@1234',
                                cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("Database connection was succesfull!")
        break
    except Exception as error:
        print("Connecting to database failed")
        print("Error: ", error)
        time.sleep(2)


app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"message": "Multi-tenant SaaS Auth Service is up and running!"}