"""
Workflow Manager - Save and execute command chains
"""

import json
import os
from datetime import datetime

WORKFLOWS_FILE = "workflows.json"

class WorkflowManager:
    def __init__(self):
        self.workflows = self.load_workflows()
    
    def load_workflows(self):
        """Load workflows from file"""
        if os.path.exists(WORKFLOWS_FILE):
            try:
                with open(WORKFLOWS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_workflows(self):
        """Save workflows to file"""
        try:
            with open(WORKFLOWS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.workflows, f, indent=2)
            return True
        except Exception as e:
            print(f"[WORKFLOW ERROR] Failed to save: {e}")
            return False
    
    def create_workflow(self, name, commands, description=""):
        """Create a new workflow"""
        if name.lower() in [w.lower() for w in self.workflows.keys()]:
            return False, "Workflow already exists"
        
        self.workflows[name] = {
            'description': description,
            'commands': commands,
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'executions': 0
        }
        
        self.save_workflows()
        return True, f"Workflow '{name}' created with {len(commands)} commands"
    
    def delete_workflow(self, name):
        """Delete a workflow"""
        if name in self.workflows:
            del self.workflows[name]
            self.save_workflows()
            return True, f"Workflow '{name}' deleted"
        return False, "Workflow not found"
    
    def list_workflows(self):
        """List all workflows"""
        if not self.workflows:
            return "No workflows created yet"
        
        output = "\n📋 YOUR WORKFLOWS:\n"
        for name, workflow in self.workflows.items():
            output += f"\n  • {name}\n"
            if workflow.get('description'):
                output += f"    Description: {workflow['description']}\n"
            output += f"    Commands: {len(workflow['commands'])}\n"
            output += f"    Run: {workflow['executions']} times\n"
        
        return output
    
    def execute_workflow(self, name, executor_function):
        """Execute a workflow (executor_function should be from main.py)"""
        if name not in self.workflows:
            return False, "Workflow not found"
        
        workflow = self.workflows[name]
        commands = workflow['commands']
        
        print(f"\n🚀 EXECUTING WORKFLOW: {name}")
        print(f"Commands to execute: {len(commands)}")
        print("="*60)
        
        results = []
        for i, command in enumerate(commands, 1):
            print(f"\n[{i}/{len(commands)}] Executing: {command}")
            try:
                # Execute command through the executor
                result = executor_function(command)
                results.append(result)
                print(f"✅ Completed: {command}")
            except Exception as e:
                print(f"❌ Failed: {command} - {e}")
                results.append(f"Failed: {e}")
        
        # Update execution count
        self.workflows[name]['executions'] = workflow.get('executions', 0) + 1
        self.save_workflows()
        
        print("\n" + "="*60)
        print(f"✅ Workflow '{name}' completed!")
        
        return True, results
    
    def get_workflow_info(self, name):
        """Get detailed info about a workflow"""
        if name not in self.workflows:
            return None
        
        workflow = self.workflows[name]
        output = f"\n📝 WORKFLOW: {name}\n"
        output += "="*60 + "\n"
        output += f"Description: {workflow.get('description', 'N/A')}\n"
        output += f"Created: {workflow.get('created', 'N/A')}\n"
        output += f"Executed: {workflow.get('executions', 0)} times\n"
        output += f"\nCommands ({len(workflow['commands'])}):\n"
        
        for i, cmd in enumerate(workflow['commands'], 1):
            output += f"  {i}. {cmd}\n"
        
        return output


# Global instance
workflow_manager = WorkflowManager()

# Example workflows that can be auto-created
DEFAULT_WORKFLOWS = {
    "morning_routine": {
        "description": "Start your day with weather, news, and calendar",
        "commands": [
            "What's the weather today",
            "Tell me the news",
            "What's on my calendar today"
        ]
    },
    "work_mode": {
        "description": "Get ready for work",
        "commands": [
            "What are my system stats",
            "Check my emails",
            "Show me my calendar"
        ]
    },
    "end_of_day": {
        "description": "End your day summary",
        "commands": [
            "What happened while I was away",
            "Summarize my tasks",
            "Show me tomorrow's calendar"
        ]
    }
}

def setup_default_workflows():
    """Setup default workflows on first run"""
    if not workflow_manager.workflows:
        for name, data in DEFAULT_WORKFLOWS.items():
            workflow_manager.create_workflow(
                name,
                data['commands'],
                data['description']
            )
        print("[WORKFLOWS] Default workflows created")
