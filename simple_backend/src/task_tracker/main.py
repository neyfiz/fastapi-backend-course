from pydantic import BaseModel
from typing import List
from fastapi import FastAPI, HTTPException
import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()


app = FastAPI()


class TaskFileManager:

    def __init__(self):
        self.api_key = os.getenv("JSONBIN_API_KEY")
        self.bin_id = os.getenv("JSONBIN_BIN_ID")
        self.base_url = f"https://api.jsonbin.io/v3/b/{self.bin_id}"
        self.headers = {
            "X-Master-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def read_tasks(self) -> List['Task']:
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()  # Вызовет ошибку для статусов 4xx/5xx
            data = response.json()
            task_data = data.get("record", [])
            return [Task(**task) for task in task_data]
        except requests.exceptions.RequestException as e:
            print(f"Ошибка чтения из jsonbin.io: {e}")
            raise HTTPException(status_code=503, detail="Сервис хранения данных недоступен.")
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Не удалось обработать ответ от сервиса хранения.")

    def write_tasks(self, tasks: List['Task']):
        try:
            task_dicts = [task.dict() for task in tasks]
            response = requests.put(self.base_url, headers=self.headers, json=task_dicts)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка записи в jsonbin.io: {e}")
            raise HTTPException(status_code=503, detail="Не удалось сохранить данные в сервис хранения.")


class CloudflareAIManager:
    def __init__(self):
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        self.api_base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/"
        self.headers = {"Authorization": f"Bearer {api_token}"}
        self.model = "@cf/meta/llama-2-7b-chat-int8"

    def get_solution_for_task(self, task_title: str) -> str:
        prompt = f"Provide a brief, step-by-step plan to solve the following task. Do not add any introductions or conclusions, just the steps. Task: '{task_title}'"
        input_data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that provides concise, actionable steps to solve tasks."},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post(f"{self.api_base_url}{self.model}", headers=self.headers, json=input_data)
            response.raise_for_status()
            result = response.json()
            if result.get("success") and "result" in result and "response" in result["result"]:
                return result["result"]["response"].strip()
            else:
                print(f"Cloudflare AI returned an unsuccessful response: {result}")
                return ""
        except requests.exceptions.RequestException as e:
            print(f"Error calling Cloudflare AI API: {e}")
            return ""


manager = TaskFileManager()
cloudflare_manager = CloudflareAIManager()


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
    print(f"Getting solution for task: '{task.title}'")
    solution = cloudflare_manager.get_solution_for_task(task.title)
    enriched_title = task.title
    if solution:
        enriched_title += f"\n\n--- AI Suggested Steps ---\n{solution}"

    tasks = manager.read_tasks()
    new_id = max([t.id for t in tasks]) + 1 if tasks else 1
    new_task = Task(id=new_id, title=enriched_title, status=task.status)
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
