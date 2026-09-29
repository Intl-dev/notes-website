import fastapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from pydantic import BaseModel
import os
import dotenv
import bcrypt
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
    check_user = logins.select().where(logins.c.email == request.email)
    print(check_user)
    result = connection.execute(check_user)
    row = result.first()
    print(result)
    if row:
        stored_hashed_password = row.password
        print(stored_hashed_password)
        is_correct = bcrypt.checkpw(request.password.encode('utf-8'), stored_hashed_password.encode('utf-8'))
        if is_correct:
            print("its correct YAY")
            return

@app.post("/auth/signup", status_code=200)
async def signup(request: LoginRequest):
    print(f"Signup request for {request.email}")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(request.password.encode("utf-8"), salt)
    hashed_password_str = hashed_password.decode("utf-8")
    signup = logins.insert().values(email=request.email, password=hashed_password_str)
    connection.execute(signup)
    connection.commit()
    return


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)