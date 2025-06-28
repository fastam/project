from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
notes = []
class Note(BaseModel):
    text:str
# @app.get("/")
# def read_road():
#     return{"message": "Hello from server"}
@app.get("/notes")
def get_notes():
    return notes
@app.post("/notes")
def add_note(note: Note):
    notes.append(note)
    return{"status": "ok"}