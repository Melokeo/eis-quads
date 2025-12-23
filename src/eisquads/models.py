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
                all_tasks = [Task(**t) for t in data]
                
                # Create a map for easy lookup
                task_map = {t.id: t for t in all_tasks}

                # Remove dependencies where both sides are completed
                for t in all_tasks:
                    if t.completed:
                        new_deps = []
                        for dep_id in t.dependencies:
                            dep_task = task_map.get(dep_id)
                            # If dependency exists and is completed, remove it
                            if dep_task and dep_task.completed:
                                continue
                            new_deps.append(dep_id)
                        t.dependencies = new_deps
                
                # Identify tasks that are depended upon by others
                depended_upon_ids = set()
                for t in all_tasks:
                    for dep_id in t.dependencies:
                        depended_upon_ids.add(dep_id)

                tasks_to_keep = []
                for t in all_tasks:
                    if not t.completed:
                        tasks_to_keep.append(t)
                    else:
                        # Keep completed task if it is part of a dependency chain (in or out)
                        has_outgoing = len(t.dependencies) > 0
                        has_incoming = t.id in depended_upon_ids
                        
                        if has_outgoing or has_incoming:
                            tasks_to_keep.append(t)
                
                # Clean up dependencies pointing to removed tasks
                kept_ids = {t.id for t in tasks_to_keep}
                for t in tasks_to_keep:
                    t.dependencies = [d for d in t.dependencies if d in kept_ids]
                    
                return tasks_to_keep
        except:
            return []

    @staticmethod
    def save_tasks(tasks):
        file_path = TaskManager.get_storage_path()
        with open(file_path, 'w') as f:
            json.dump([t.to_dict() for t in tasks], f, indent=4)

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
