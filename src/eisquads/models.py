import json
import os
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict, field
from config import get_storage_dir

@dataclass
class Task:
    id: str
    title: str
    desc: str
    x: float
    y: float
    completed: bool = False
    dependencies: list[str] = field(default_factory=list)
    
    def to_dict(self):
        return asdict(self)

class TaskManager:
    @staticmethod
    def get_storage_path():
        return get_storage_dir() / "tasks.json"

    @staticmethod
    def load_tasks():
        file_path = TaskManager.get_storage_path()
        if not file_path.exists():
            return []
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # filter out completed tasks, they are history
                all_tasks = [Task(**t) for t in data]
                return [t for t in all_tasks if not t.completed]
        except:
            return []

    @staticmethod
    def save_tasks(tasks):
        file_path = TaskManager.get_storage_path()
        with open(file_path, 'w') as f:
            json.dump([t.to_dict() for t in tasks], f)

    @staticmethod
    def create_backup():
        path = TaskManager.get_storage_path()
        if path.exists():
            backup_path = path.with_suffix(".bak")
            shutil.copy2(path, backup_path)

    @staticmethod
    def restore_backup():
        path = TaskManager.get_storage_path()
        backup_path = path.with_suffix(".bak")
        if backup_path.exists():
            shutil.copy2(backup_path, path)
