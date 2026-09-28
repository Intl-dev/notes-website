import fastapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy import create_engine, Column, Integer, String, true, MetaData, Table
from pydantic import BaseModel
import os
import dotenv
dotenv.load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

metadata = MetaData()

logins = Table("logins", metadata, Column("id", Integer, primary_key=True), Column("email", String), Column("password", String))

metadata.create_all(engine)

connection = engine.connect()
app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/login", status_code=200)
async def login(request: LoginRequest):
    print(f"Login request for {request.email}")
    insert_logs = logins.insert().values(email=request.email, password=request.password)
    connection.execute(insert_logs)
    connection.commit()
    return

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)