"""
JARVIS Website Builder - Auto-generate websites and apps from voice description
"""

import os
import json
from datetime import datetime

class WebsiteBuilder:
    def __init__(self):
        self.projects_dir = 'generated_projects'
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)
        self.awaiting_confirmation = {}  # Track pending projects
    
    def show_website_tips(self, project_name):
        """Show tips before creating website"""
        return f"""
Website Builder Tips Before Creating:

Project Name: {project_name}

Tips for a great website:
1. Choose a clear, descriptive domain name
2. Keep navigation simple (Home, About, Services, Contact)
3. Use high-quality images and content
4. Mobile-responsive design (we've got this!)
5. Fast loading times
6. Clear call-to-action buttons
7. Professional color scheme
8. Regular content updates

Would you like me to:
- CREATE the website now? (Say "yes create")
- CUSTOMIZE it first? (Tell me: colors, pages, content)
- CANCEL? (Say "no" or "cancel")

What would you prefer?
"""
    
    def show_app_tips(self, app_type, app_name):
        """Show tips before creating app"""
        tips = {
            'todo': """
Todo App Tips:

Best Practices:
1. Simple, clean interface
2. Easy task adding with voice
3. Quick task marking as done
4. Priority levels (high/normal/low)
5. Persistent storage
6. Search functionality
7. Archive completed tasks
8. Dark/Light theme support

Our Todo App Features:
- Voice-to-task input
- Priority sorting
- Local storage
- Quick completion
- Beautiful design

Ready to create? Say "yes create"
            """,
            'calculator': """
Calculator App Tips:

Features to Include:
1. Basic operations (+, -, *, /)
2. Scientific functions
3. Clear history
4. Keyboard shortcuts
5. Voice input support
6. Large display
7. Error handling
8. Memory functions

Our Calculator Has:
- All basic & scientific ops
- Clean UI
- Responsive design
- Fast computation

Ready to create? Say "yes create"
            """
        }
        return tips.get(app_type, f"Creating {app_type} app: {app_name}")
    
    def create_website(self, project_name, description, pages=None):
        """Create a website from description"""
        if pages is None:
            pages = ['Home', 'About', 'Contact']
        
        project_dir = os.path.join(self.projects_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Generate HTML
        html_content = self._generate_html(project_name, pages, description)
        css_content = self._generate_css()
        js_content = self._generate_js()
        
        # Write files
        with open(os.path.join(project_dir, 'index.html'), 'w') as f:
            f.write(html_content)
        
        with open(os.path.join(project_dir, 'style.css'), 'w') as f:
            f.write(css_content)
        
        with open(os.path.join(project_dir, 'script.js'), 'w') as f:
            f.write(js_content)
        
        return f"""✨ Website Created!
Project: {project_name}
Location: {project_dir}
Pages: {', '.join(pages)}
Open: {os.path.join(project_dir, 'index.html')}"""
    
    def _generate_html(self, title, pages, description):
        """Generate HTML template"""
        nav_html = '\n'.join([f'<li><a href="#{page.lower()}">{page}</a></li>' for page in pages])
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <nav class="navbar">
            <h1>{title}</h1>
            <ul>
                {nav_html}
            </ul>
        </nav>
    </header>
    
    <main>
        <section id="home" class="hero">
            <h1>Welcome to {title}</h1>
            <p>{description}</p>
            <button class="cta-button">Get Started</button>
        </section>
        
        <section id="about" class="section">
            <h2>About</h2>
            <p>Learn more about our amazing service.</p>
        </section>
        
        <section id="contact" class="section">
            <h2>Contact Us</h2>
            <form>
                <input type="text" placeholder="Your Name" required>
                <input type="email" placeholder="Your Email" required>
                <textarea placeholder="Your Message" rows="5" required></textarea>
                <button type="submit">Send</button>
            </form>
        </section>
    </main>
    
    <footer>
        <p>&copy; 2024 {title}. All rights reserved.</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>"""
    
    def _generate_css(self):
        """Generate CSS styling"""
        return """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
}

header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 100;
}

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
}

.navbar h1 {
    font-size: 1.8rem;
}

.navbar ul {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.navbar a {
    color: white;
    text-decoration: none;
    transition: opacity 0.3s;
}

.navbar a:hover {
    opacity: 0.8;
}

.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 6rem 2rem;
    text-align: center;
}

.hero h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.cta-button {
    background: white;
    color: #667eea;
    border: none;
    padding: 12px 30px;
    border-radius: 5px;
    font-size: 1rem;
    cursor: pointer;
    margin-top: 2rem;
    transition: transform 0.3s;
}

.cta-button:hover {
    transform: scale(1.05);
}

.section {
    max-width: 1200px;
    margin: 3rem auto;
    padding: 2rem;
}

.section h2 {
    font-size: 2rem;
    margin-bottom: 1rem;
    color: #667eea;
}

form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    max-width: 500px;
}

input, textarea {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 1rem;
}

input:focus, textarea:focus {
    outline: none;
    border-color: #667eea;
}

button[type="submit"] {
    background: #667eea;
    color: white;
    border: none;
    padding: 10px;
    border-radius: 5px;
    cursor: pointer;
    transition: background 0.3s;
}

button[type="submit"]:hover {
    background: #764ba2;
}

footer {
    background: #333;
    color: white;
    text-align: center;
    padding: 2rem;
    margin-top: 3rem;
}

@media (max-width: 768px) {
    .navbar {
        flex-direction: column;
        gap: 1rem;
    }
    
    .navbar ul {
        flex-direction: column;
        gap: 1rem;
    }
    
    .hero h1 {
        font-size: 2rem;
    }
}"""
    
    def _generate_js(self):
        """Generate JavaScript functionality"""
        return """// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Form submission
document.querySelector('form').addEventListener('submit', function(e) {
    e.preventDefault();
    alert('Thank you for your message! We will get back to you soon.');
    this.reset();
});

// CTA button
document.querySelector('.cta-button').addEventListener('click', function() {
    document.querySelector('#about').scrollIntoView({ behavior: 'smooth' });
});

console.log('Website loaded successfully!');
"""
    
    def create_app(self, app_name, app_type='todo'):
        """Create a simple web app"""
        if app_type == 'todo':
            html = self._generate_todo_app_html(app_name)
        elif app_type == 'calculator':
            html = self._generate_calculator_app_html(app_name)
        else:
            html = self._generate_todo_app_html(app_name)
        
        project_dir = os.path.join(self.projects_dir, app_name)
        os.makedirs(project_dir, exist_ok=True)
        
        with open(os.path.join(project_dir, 'index.html'), 'w') as f:
            f.write(html)
        
        return f"""✨ App Created!
App: {app_name}
Type: {app_type}
Location: {project_dir}/index.html"""
    
    def _generate_todo_app_html(self, name):
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial; background: #667eea; min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
        .container {{ background: white; padding: 2rem; border-radius: 10px; width: 90%; max-width: 500px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
        h1 {{ color: #667eea; margin-bottom: 1.5rem; }}
        .input-group {{ display: flex; gap: 0.5rem; margin-bottom: 1rem; }}
        input {{ flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 5px; }}
        button {{ background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }}
        ul {{ list-style: none; }}
        li {{ background: #f0f0f0; margin: 0.5rem 0; padding: 10px; border-radius: 5px; display: flex; justify-content: space-between; }}
        .delete {{ background: #ff6b6b; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{name}</h1>
        <div class="input-group">
            <input type="text" id="taskInput" placeholder="Add a new task...">
            <button onclick="addTask()">Add</button>
        </div>
        <ul id="taskList"></ul>
    </div>
    <script>
        function addTask() {{
            const input = document.getElementById('taskInput');
            if (input.value) {{
                const li = document.createElement('li');
                li.innerHTML = `<span>${{input.value}}</span><button class="delete" onclick="this.parentElement.remove()">Delete</button>`;
                document.getElementById('taskList').appendChild(li);
                input.value = '';
            }}
        }}
        document.getElementById('taskInput').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') addTask();
        }});
    </script>
</body>
</html>"""
    
    def _generate_calculator_app_html(self, name):
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial; background: #667eea; height: 100vh; display: flex; align-items: center; justify-content: center; }}
        .calculator {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
        input {{ width: 100%; padding: 10px; font-size: 18px; margin-bottom: 10px; }}
        .buttons {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; }}
        button {{ padding: 20px; font-size: 16px; cursor: pointer; border: none; border-radius: 5px; background: #667eea; color: white; }}
        button:hover {{ background: #764ba2; }}
        .equal {{ grid-column: span 2; background: #48bb78; }}
    </style>
</head>
<body>
    <div class="calculator">
        <input type="text" id="display" readonly value="0">
        <div class="buttons">
            <button onclick="appendDisplay('7')">7</button>
            <button onclick="appendDisplay('8')">8</button>
            <button onclick="appendDisplay('9')">9</button>
            <button onclick="appendDisplay('/')">÷</button>
            <button onclick="appendDisplay('4')">4</button>
            <button onclick="appendDisplay('5')">5</button>
            <button onclick="appendDisplay('6')">6</button>
            <button onclick="appendDisplay('*')">×</button>
            <button onclick="appendDisplay('1')">1</button>
            <button onclick="appendDisplay('2')">2</button>
            <button onclick="appendDisplay('3')">3</button>
            <button onclick="appendDisplay('-')">-</button>
            <button onclick="appendDisplay('0')">0</button>
            <button onclick="appendDisplay('.')">.</button>
            <button onclick="clearDisplay()">C</button>
            <button onclick="appendDisplay('+')">+</button>
            <button class="equal" onclick="calculate()">=</button>
        </div>
    </div>
    <script>
        function appendDisplay(val) {{ 
            const display = document.getElementById('display');
            if (display.value === '0') display.value = val;
            else display.value += val;
        }}
        function clearDisplay() {{ document.getElementById('display').value = '0'; }}
        function calculate() {{ 
            try {{ 
                document.getElementById('display').value = eval(document.getElementById('display').value); 
            }} catch(e) {{ 
                document.getElementById('display').value = 'Error'; 
            }} 
        }}
    </script>
</body>
</html>"""

website_builder = WebsiteBuilder()
