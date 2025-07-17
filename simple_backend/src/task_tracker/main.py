from pydantic import BaseModel
from typing import List
from fastapi import FastAPI, HTTPException
import json
import requests
from dotenv import load_dotenv
import os


load_dotenv()

API_KEY = os.getenv("JSONBIN_API_KEY")
BIN_ID = os.getenv("JSONBIN_BIN_ID")

HEADERS = {
    "X-Master-Key": API_KEY,
    "Content-Type": "application/json"
}
BASE_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"


app = FastAPI()


class TaskFileManager:

    def read_tasks(self) -> List['Task']:
        response = requests.get(BASE_URL, headers=HEADERS)
        data = response.json()["record"]
        return [Task(**task) for task in data]

    def write_tasks(self, tasks: List['Task']):
        task_dicts = [task.dict() for task in tasks]
        response = requests.put(BASE_URL, headers=HEADERS, json=task_dicts)
        response.raise_for_status()


manager = TaskFileManager()


class Task(BaseModel):
    id: int
    title: str
    status: str


class TaskCreate(BaseModel):
    title: str
    status: str


class TaskUpdate(BaseModel):
    title: str
    status: str


@app.get("/tasks")
def get_tasks() -> List[Task]:
    return manager.read_tasks()

@app.post("/tasks")
def create_task(task: TaskCreate) -> Task:
    tasks = manager.read_tasks()
    new_id = max([t.id for t in tasks]) + 1 if tasks else 1
    new_task = Task(id=new_id, **task.dict())
    tasks.append(new_task)
    manager.write_tasks(tasks)
    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task_data: TaskUpdate) -> Task:
    tasks = manager.read_tasks()
    for i, task in enumerate(tasks):
        if task.id == task_id:
            tasks[i] = Task(id=task_id, **updated_task_data.dict())
            manager.write_tasks(tasks)
            return tasks[i]
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int) -> dict:
    tasks = manager.read_tasks()
    task_to_delete = next((task for task in tasks if task.id == task_id), None)
    if task_to_delete is None:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks.remove(task_to_delete)
    manager.write_tasks(tasks)
    return {"message": "Task deleted successfully"}