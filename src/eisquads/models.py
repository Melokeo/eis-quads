import json
import os
from dataclasses import dataclass, asdict

@dataclass
class Task:
    id: str
    title: str
    desc: str
    x: float
    y: float
    
    def to_dict(self):
        return asdict(self)

class TaskManager:
    FILE_NAME = "tasks.json"

    @staticmethod
    def load_tasks():
        if not os.path.exists(TaskManager.FILE_NAME):
            return []
        try:
            with open(TaskManager.FILE_NAME, 'r') as f:
                data = json.load(f)
                return [Task(**t) for t in data]
        except:
            return []

    @staticmethod
    def save_tasks(tasks):
        with open(TaskManager.FILE_NAME, 'w') as f:
            json.dump([t.to_dict() for t in tasks], f)
