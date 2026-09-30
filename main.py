import fastapi
from fastapi import FastAPI, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from pydantic import BaseModel
import os
import dotenv
import bcrypt
import jwt
from datetime import datetime, timedelta

from starlette import status

dotenv.load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
secret = os.getenv("SECRET")
engine = create_engine(DATABASE_URL, echo=True)

metadata = MetaData()

logins = Table("logins", metadata, Column("id", Integer, primary_key=True), Column("email", String), Column("password", String))
notes = Table("notes", metadata, Column("id", Integer, primary_key=True), Column("user_id", Integer), Column("content", String))
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

class CreateNoteRequest(BaseModel):
    content: str

@app.post("/auth/login", status_code=status.HTTP_200_OK)
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
            user_id = row.id
            payload = {"user_id": user_id}
            token = jwt.encode(payload, secret, algorithm="HS256")
            return {"token": token}
        else:
            return {"message": "Wrong Password"}
    else:
        return {"message": "Wrong Email or Password"}

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

@app.post("/notes")
async def add_note(request: CreateNoteRequest, authorization: str = Header(None)):
    print("trying to add a note")
    token = authorization.split(" ")[1]
    print(token)
    decoded_token = jwt.decode(token, secret, algorithms=["HS256"])
    user_id = int(decoded_token["user_id"])
    note_content = request.content
    add_note = notes.insert().values(user_id=user_id, content=note_content)
    connection.execute(add_note)
    connection.commit()
    return


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)