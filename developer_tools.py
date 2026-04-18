"""
JARVIS Developer Tools - Code explanation, API testing, git commands
"""

import os
import subprocess
import json

class DeveloperTools:
    def __init__(self):
        self.code_snippets = {}
    
    def explain_code(self, code_snippet):
        """Explain a code snippet"""
        # This would integrate with an AI model API
        return f"""📚 Code Explanation:
"{code_snippet}"

This snippet does [AI Analysis would explain here]
Key concepts: variables, functions, loops, conditionals"""
    
    def test_api(self, url, method='GET', headers=None, data=None):
        """Test API endpoint"""
        import requests
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            
            return f"""🔧 API Response:
URL: {url}
Status: {response.status_code}
Response: {response.text[:200]}..."""
        except Exception as e:
            return f"❌ API Error: {str(e)}"
    
    def git_command(self, command):
        """Execute git command"""
        try:
            result = subprocess.run(['git', command], capture_output=True, text=True)
            return f"🔀 Git Output:\n{result.stdout if result.stdout else result.stderr}"
        except Exception as e:
            return f"❌ Git Error: {str(e)}"
    
    def format_code(self, code, language='python'):
        """Format code for readability"""
        return f"""💻 Formatted {language.upper()} Code:
[Would use black/prettier depending on language]
Original: {code[:50]}..."""
    
    def find_syntax_errors(self, file_path):
        """Find syntax errors in code"""
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            compile(code, file_path, 'exec')
            return f"✓ No syntax errors in {file_path}"
        except SyntaxError as e:
            return f"❌ Syntax Error in {file_path}: Line {e.lineno}: {e.msg}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def debug_trace(self, function_name):
        """Get debug trace for function"""
        return f"""🐛 Debug Trace for {function_name}:
[Execution trace would show here]
- Call stack
- Variable states
- Parameter values"""
    
    def generate_documentation(self, code):
        """Generate code documentation"""
        return f"""📖 Auto-Generated Documentation:
Code: {code[:30]}...
[Docstrings and comments would be generated]"""

developer_tools = DeveloperTools()
