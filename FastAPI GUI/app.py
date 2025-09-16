# app.py
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

class TodoIn(BaseModel):
    title: str
    done: bool = False

class Todo(TodoIn):
    id: int

TODOS: List[Todo] = []
sequence = 1

@app.get("/todos", response_model=List[Todo])
def list_todos():
    return TODOS

@app.post("/todos", response_model=Todo)
def create(todo: TodoIn):
    global sequence
    item = Todo(id=sequence, **todo.model_dump())
    sequence += 1
    TODOS.append(item)
    return item

def main():
    import uvicorn
    uvicorn.run(
        "app:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()