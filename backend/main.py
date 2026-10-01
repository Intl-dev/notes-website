
import fastapi
from fastapi import FastAPI, Depends, Header, Body
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from pydantic import BaseModel
import os
import dotenv
import bcrypt
import jwt
from datetime import datetime, timedelta, UTC
from fastapi.responses import JSONResponse
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

def create_user(request: LoginRequest):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(request.password.encode("utf-8"), salt)
    hashed_password_str = hashed_password.decode("utf-8")
    save_acc_data = logins.insert().values(email=request.email, password=hashed_password_str)
    with engine.begin() as connection:
        connection.execute(save_acc_data)


def token_get_user_id(authorization: str):
    token = authorization.split(" ")[1]
    decoded_token = jwt.decode(token, secret, algorithms=["HS256"])
    user_id = int(decoded_token["user_id"])
    return user_id

@app.post("/auth/login", status_code=status.HTTP_200_OK)
async def login(request: LoginRequest):
    check_user = logins.select().where(logins.c.email == request.email)
    result = connection.execute(check_user)
    row = result.first()
    if row:
        stored_hashed_password = row.password
        is_correct = bcrypt.checkpw(request.password.encode('utf-8'), stored_hashed_password.encode('utf-8'))
        if is_correct:
            user_id = row.id
            payload = {"user_id": user_id,
                       "exp": datetime.now(UTC) + timedelta(hours=1)}
            token = jwt.encode(payload, secret, algorithm="HS256")
            return {"token": token}
        else:
            return {"message": "Wrong Password"}
    else:
        return {"message": "Wrong Email or Password"}

@app.post("/auth/signup", status_code=status.HTTP_200_OK)
async def signup(request: LoginRequest):
    create_user(request)
    row = connection.execute(logins.select().where(logins.c.email == request.email)).fetchone()
    user_id = row.id
    payload = {"user_id": user_id,
               "exp": datetime.now(UTC) + timedelta(hours=1)}
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"token": token}

@app.post("/notes", status_code=status.HTTP_200_OK)
async def add_note(request: CreateNoteRequest, authorization: str = Header(None)):
    user_id = token_get_user_id(authorization)
    note_content = request.content
    add_note = notes.insert().values(user_id=user_id, content=note_content)
    with engine.begin() as connection:
        connection.execute(add_note)
    return

@app.get("/notes", status_code=status.HTTP_200_OK)
async def send_notes(authorization: str = Header(None)):
    user_id = token_get_user_id(authorization)
    notes_rows = notes.select().where(notes.c.user_id == user_id)
    notes_list = []
    with engine.begin() as connection:
        for row in connection.execute(notes_rows):
            notes_list.append({"createdAt": "N/A", "content": row.content, "id": row.id})
        json_to_send = JSONResponse(notes_list)
        return json_to_send

@app.delete("/notes/{id}", status_code=status.HTTP_200_OK)
async def delete_note(id: int, authorization: str = Header(None)):
    user_id = token_get_user_id(authorization)
    with engine.begin() as connection:
        note_row = connection.execute(notes.select().where(notes.c.id == id)).fetchone()
        note_user_id = note_row.user_id
        if note_user_id == user_id:
            delete_note = notes.delete().where(notes.c.id == id)
            with engine.begin() as connection:
                connection.execute(delete_note)


@app.put("/notes/{id}", status_code=status.HTTP_200_OK)
async def update_note(id: int, request: dict = Body(...), authorization: str = Header(None)):
    user_id = token_get_user_id(authorization)
    with engine.begin() as connection:
        note = connection.execute(notes.select().where(notes.c.id == id))
        note_user_id = note.fetchone().user_id
        if note_user_id == user_id:
            content = request["content"]
            update_note = notes.update().where(notes.c.id == id).values(content=content)
            with engine.begin() as connection:
                connection.execute(update_note)



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)