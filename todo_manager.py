"""
JARVIS Todo List Manager - Voice-controlled task management
"""

import json
import os
from datetime import datetime

TODO_FILE = 'todos.json'

class TodoManager:
    def __init__(self):
        self.todos = self.load_todos()
    
    def load_todos(self):
        if os.path.exists(TODO_FILE):
            try:
                with open(TODO_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {'tasks': [], 'completed': []}
        return {'tasks': [], 'completed': []}
    
    def save_todos(self):
        with open(TODO_FILE, 'w') as f:
            json.dump(self.todos, f, indent=2)
    
    def add_task(self, task, priority='normal'):
        """Add a new task"""
        todo_item = {
            'task': task,
            'priority': priority,
            'created': datetime.now().isoformat(),
            'completed': False
        }
        self.todos['tasks'].append(todo_item)
        self.save_todos()
        return f"✓ Task added: {task} (Priority: {priority})"
    
    def list_tasks(self):
        """Show all pending tasks"""
        if not self.todos['tasks']:
            return "No pending tasks"
        
        task_list = "Your tasks:\n"
        for i, todo in enumerate(self.todos['tasks'], 1):
            priority_icon = "🔴" if todo['priority'] == 'high' else "🟡" if todo['priority'] == 'medium' else "🟢"
            task_list += f"{i}. {priority_icon} {todo['task']}\n"
        return task_list
    
    def complete_task(self, task_num):
        """Mark task as complete"""
        try:
            task = self.todos['tasks'].pop(int(task_num) - 1)
            task['completed_at'] = datetime.now().isoformat()
            self.todos['completed'].append(task)
            self.save_todos()
            return f"✓ Completed: {task['task']}"
        except:
            return "Task not found"
    
    def delete_task(self, task_num):
        """Delete a task"""
        try:
            task = self.todos['tasks'].pop(int(task_num) - 1)
            self.save_todos()
            return f"🗑️ Deleted: {task['task']}"
        except:
            return "Task not found"

todo_manager = TodoManager()
