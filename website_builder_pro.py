"""
JARVIS Pro Website Builder - Premium website generation with modern design
Features: Modern templates, animations, responsive design, hero sections, gradients
"""

import os
import json
from datetime import datetime
from jinja2 import Template

class WebsiteBuilderPro:
    def __init__(self):
        self.projects_dir = 'generated_projects'
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)
        self.awaiting_confirmation = {}
        self.color_schemes = {
            'cars': {'primary': '#e74c3c', 'secondary': '#c0392b', 'accent': '#f39c12'},
            'tech': {'primary': '#3498db', 'secondary': '#2980b9', 'accent': '#1abc9c'},
            'business': {'primary': '#2c3e50', 'secondary': '#34495e', 'accent': '#16a085'},
            'creative': {'primary': '#9b59b6', 'secondary': '#8e44ad', 'accent': '#e74c3c'},
            'clean': {'primary': '#667eea', 'secondary': '#764ba2', 'accent': '#f093fb'},
            'nature': {'primary': '#27ae60', 'secondary': '#229954', 'accent': '#f39c12'},
        }

    def create_website(self, project_name, description, pages=None, theme='clean'):
        """Create premium website with modern design"""
        if pages is None:
            pages = ['Home', 'About', 'Services', 'Contact']
        
        project_dir = os.path.join(self.projects_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Get color scheme
        colors = self.color_schemes.get(theme, self.color_schemes['clean'])
        
        # Generate files
        html_content = self._generate_advanced_html(project_name, pages, description, colors)
        css_content = self._generate_advanced_css(colors)
        js_content = self._generate_advanced_js()
        
        # Write files with UTF-8 encoding
        with open(os.path.join(project_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        with open(os.path.join(project_dir, 'style.css'), 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        with open(os.path.join(project_dir, 'script.js'), 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        return f"""✨ PREMIUM Website Created!
Project: {project_name}
Theme: {theme}
Colors: Primary {colors['primary']}, Secondary {colors['secondary']}
Location: {project_dir}
Pages: {', '.join(pages)}
Open: {os.path.join(project_dir, 'index.html')}"""

    def _generate_advanced_html(self, title, pages, description, colors):
        """Generate modern HTML with better structure"""
        nav_html = '\n                '.join([f'<a href="#{page.lower()}">{page}</a>' for page in pages])
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <!-- Navigation Bar -->
    <nav class="navbar">
        <div class="container">
            <div class="nav-brand">{title}</div>
            <div class="nav-menu">
                {nav_html}
            </div>
            <div class="nav-toggle">☰</div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-content">
            <h1 class="hero-title">{title}</h1>
            <p class="hero-subtitle">{description}</p>
            <button class="cta-button">Get Started</button>
        </div>
        <div class="hero-background">
            <div class="blob blob-1"></div>
            <div class="blob blob-2"></div>
            <div class="blob blob-3"></div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="features" id="features">
        <div class="container">
            <h2>Why Choose Us?</h2>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🚀</div>
                    <h3>Fast & Reliable</h3>
                    <p>Lightning-quick performance optimized for all devices</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🎨</div>
                    <h3>Beautiful Design</h3>
                    <p>Stunning modern interfaces that captivate users</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📱</div>
                    <h3>Mobile Ready</h3>
                    <p>Perfect display on smartphones, tablets, and desktops</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">✅</div>
                    <h3>Easy to Use</h3>
                    <p>Intuitive interface built for everyone</p>
                </div>
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section class="about" id="about">
        <div class="container">
            <h2>About Us</h2>
            <div class="about-content">
                <p>{description}</p>
                <p>We're committed to delivering excellence and innovation in everything we do.</p>
            </div>
        </div>
    </section>

    <!-- Services Section -->
    <section class="services" id="services">
        <div class="container">
            <h2>Our Services</h2>
            <div class="services-grid">
                <div class="service-card">
                    <h3>Premium Service</h3>
                    <p>Experience the best quality with our premium offerings</p>
                </div>
                <div class="service-card">
                    <h3>Expert Support</h3>
                    <p>24/7 dedicated support team ready to help</p>
                </div>
                <div class="service-card">
                    <h3>Custom Solutions</h3>
                    <p>Tailored solutions for your unique needs</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section class="contact" id="contact">
        <div class="container">
            <h2>Get In Touch</h2>
            <form class="contact-form">
                <input type="text" placeholder="Your Name" required>
                <input type="email" placeholder="Your Email" required>
                <textarea placeholder="Your Message" rows="6" required></textarea>
                <button type="submit" class="submit-button">Send Message</button>
            </form>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h4>{title}</h4>
                    <p>Building amazing web experiences</p>
                </div>
                <div class="footer-section">
                    <h4>Quick Links</h4>
                    <ul>
                        <li><a href="#home">Home</a></li>
                        <li><a href="#about">About</a></li>
                        <li><a href="#contact">Contact</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h4>Follow Us</h4>
                    <div class="social-icons">
                        <a href="#" class="social-icon">f</a>
                        <a href="#" class="social-icon">𝕏</a>
                        <a href="#" class="social-icon">in</a>
                    </div>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2024 {title}. All rights reserved. | Made with ❤️ by JARVIS</p>
            </div>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>"""

    def _generate_advanced_css(self, colors):
        """Generate modern CSS with animations and gradients"""
        primary = colors['primary']
        secondary = colors['secondary']
        accent = colors['accent']
        
        return f"""* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

:root {{
    --primary: {primary};
    --secondary: {secondary};
    --accent: {accent};
    --dark: #1a1a1a;
    --light: #f8f9fa;
    --gray: #6c757d;
}}

html {{
    scroll-behavior: smooth;
}}

body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #fff;
    overflow-x: hidden;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
}}

/* NAVBAR */
.navbar {{
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    color: white;
    padding: 1rem 0;
    position: fixed;
    top: 0;
    width: 100%;
    z-index: 1000;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}}

.navbar .container {{
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.nav-brand {{
    font-size: 1.8rem;
    font-weight: bold;
    letter-spacing: 2px;
}}

.nav-menu {{
    display: flex;
    gap: 2.5rem;
    align-items: center;
}}

.nav-menu a {{
    color: white;
    text-decoration: none;
    transition: all 0.3s ease;
    font-weight: 500;
    position: relative;
}}

.nav-menu a:hover {{
    color: var(--accent);
    transform: translateY(-2px);
}}

.nav-menu a::after {{
    content: '';
    position: absolute;
    bottom: -5px;
    left: 0;
    width: 0;
    height: 2px;
    background: var(--accent);
    transition: width 0.3s ease;
}}

.nav-menu a:hover::after {{
    width: 100%;
}}

.nav-toggle {{
    display: none;
    cursor: pointer;
    font-size: 1.5rem;
}}

/* HERO */
.hero {{
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 50%, #667eea 100%);
    color: white;
    padding: 10rem 2rem;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    margin-top: 60px;
    text-align: center;
}}

.hero-background {{
    position: absolute;
    width: 100%;
    height: 100%;
    top: 0;
    left: 0;
    opacity: 0.1;
    z-index: 1;
}}

.blob {{
    position: absolute;
    border-radius: 50%;
    mix-blend-mode: lighten;
    animation: blob-animation 8s infinite;
}}

.blob-1 {{
    width: 200px;
    height: 200px;
    background: white;
    top: 10%;
    right: 10%;
    animation-delay: 0s;
}}

.blob-2 {{
    width: 150px;
    height: 150px;
    background: rgba(255,255,255,0.5);
    bottom: 20%;
    left: 10%;
    animation-delay: 2s;
}}

.blob-3 {{
    width: 180px;
    height: 180px;
    background: rgba(255,255,255,0.3);
    top: 50%;
    right: 20%;
    animation-delay: 4s;
}}

@keyframes blob-animation {{
    0%, 100% {{
        transform: translate(0, 0) scale(1);
    }}
    25% {{
        transform: translate(20px, -20px) scale(1.1);
    }}
    50% {{
        transform: translate(-20px, 20px) scale(0.9);
    }}
    75% {{
        transform: translate(20px, 20px) scale(1.05);
    }}
}}

.hero-content {{
    position: relative;
    z-index: 2;
    max-width: 800px;
}}

.hero-title {{
    font-size: 4rem;
    margin-bottom: 1.5rem;
    animation: slideInDown 0.8s ease-out;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    font-weight: 800;
    letter-spacing: 1px;
}}

.hero-subtitle {{
    font-size: 1.5rem;
    margin-bottom: 2rem;
    opacity: 0.95;
    animation: slideInUp 0.8s ease-out 0.2s both;
}}

@keyframes slideInDown {{
    from {{
        opacity: 0;
        transform: translateY(-30px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

@keyframes slideInUp {{
    from {{
        opacity: 0;
        transform: translateY(30px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.cta-button {{
    background: var(--accent);
    color: white;
    padding: 15px 40px;
    font-size: 1.1rem;
    border: none;
    border-radius: 50px;
    cursor: pointer;
    font-weight: bold;
    transition: all 0.3s ease;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    transform: translateY(0);
    animation: slideInUp 0.8s ease-out 0.4s both;
}}

.cta-button:hover {{
    background: darken({accent}, 10%);
    transform: translateY(-3px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.3);
}}

.cta-button:active {{
    transform: translateY(-1px);
}}

/* FEATURES */
.features {{
    padding: 5rem 2rem;
    background: var(--light);
}}

.features h2 {{
    font-size: 2.5rem;
    text-align: center;
    margin-bottom: 3rem;
    color: var(--primary);
}}

.features-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
}}

.feature-card {{
    background: white;
    padding: 2rem;
    border-radius: 12px;
    text-align: center;
    transition: all 0.3s ease;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    animation: fadeInUp 0.6s ease-out;
}}

.feature-card:hover {{
    transform: translateY(-10px);
    box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    border-top: 4px solid var(--primary);
}}

@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(20px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.feature-icon {{
    font-size: 3rem;
    margin-bottom: 1rem;
}}

.feature-card h3 {{
    color: var(--primary);
    margin-bottom: 1rem;
    font-size: 1.5rem;
}}

.feature-card p {{
    color: var(--gray);
    font-size: 0.95rem;
}}

/* ABOUT */
.about {{
    padding: 5rem 2rem;
    background: white;
}}

.about h2 {{
    font-size: 2.5rem;
    margin-bottom: 2rem;
    color: var(--primary);
}}

.about-content {{
    max-width: 800px;
    font-size: 1.1rem;
    color: var(--gray);
    line-height: 1.8;
}}

.about-content p {{
    margin-bottom: 1.5rem;
}}

/* SERVICES */
.services {{
    padding: 5rem 2rem;
    background: var(--light);
}}

.services h2 {{
    font-size: 2.5rem;
    text-align: center;
    margin-bottom: 3rem;
    color: var(--primary);
}}

.services-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
}}

.service-card {{
    background: white;
    padding: 2.5rem;
    border-radius: 12px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
    border-left: 4px solid var(--primary);
}}

.service-card:hover {{
    box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    transform: translateX(5px);
}}

.service-card h3 {{
    color: var(--primary);
    margin-bottom: 1rem;
    font-size: 1.3rem;
}}

.service-card p {{
    color: var(--gray);
    font-size: 0.95rem;
}}

/* CONTACT */
.contact {{
    padding: 5rem 2rem;
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    color: white;
    text-align: center;
}}

.contact h2 {{
    font-size: 2.5rem;
    margin-bottom: 2rem;
}}

.contact-form {{
    max-width: 600px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}}

.contact-form input,
.contact-form textarea {{
    padding: 15px;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-family: inherit;
    background: rgba(255,255,255,0.95);
    transition: all 0.3s ease;
}}

.contact-form input:focus,
.contact-form textarea:focus {{
    outline: none;
    box-shadow: 0 0 0 3px rgba(255,255,255,0.3);
    background: white;
}}

.submit-button {{
    padding: 15px 30px;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
}}

.submit-button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}}

/* FOOTER */
.footer {{
    background: var(--dark);
    color: white;
    padding: 3rem 2rem 1rem;
}}

.footer-content {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
    margin-bottom: 2rem;
}}

.footer-section h4 {{
    margin-bottom: 1rem;
    color: var(--accent);
}}

.footer-section ul {{
    list-style: none;
}}

.footer-section ul li {{
    margin-bottom: 0.5rem;
}}

.footer-section a {{
    color: #bbb;
    text-decoration: none;
    transition: all 0.3s ease;
}}

.footer-section a:hover {{
    color: var(--accent);
    transform: translateX(5px);
}}

.social-icons {{
    display: flex;
    gap: 1rem;
}}

.social-icon {{
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent);
    border-radius: 50%;
    transition: all 0.3s ease;
    cursor: pointer;
}}

.social-icon:hover {{
    transform: translateY(-5px) rotate(10deg);
    box-shadow: 0 10px 20px rgba(0,0,0,0.2);
}}

.footer-bottom {{
    text-align: center;
    padding-top: 1rem;
    border-top: 1px solid #444;
    color: #999;
}}

/* RESPONSIVE */
@media (max-width: 768px) {{
    .hero-title {{
        font-size: 2.5rem;
    }}
    
    .hero-subtitle {{
        font-size: 1.2rem;
    }}
    
    .nav-menu {{
        gap: 1rem;
        font-size: 0.9rem;
    }}
    
    .nav-toggle {{
        display: block;
    }}
    
    .features h2, .services h2, .contact h2 {{
        font-size: 2rem;
    }}
}}

@media (max-width: 480px) {{
    .hero {{
        padding: 5rem 1rem;
        margin-top: 60px;
    }}
    
    .hero-title {{
        font-size: 1.8rem;
    }}
    
    .cta-button {{
        padding: 12px 25px;
        font-size: 1rem;
    }}
}}
"""

    def _generate_advanced_js(self):
        """Generate modern JavaScript with interactivity"""
        return """// Smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Active navigation highlight
window.addEventListener('scroll', () => {
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('.nav-menu a');
    
    sections.forEach(section => {
        const top = section.offsetTop - 100;
        const bottom = top + section.clientHeight;
        const scroll = window.scrollY;
        
        if (scroll >= top && scroll <= bottom) {
            navLinks.forEach(link => link.classList.remove('active'));
            const id = section.getAttribute('id');
            const link = document.querySelector(`.nav-menu a[href="#${id}"]`);
            if (link) link.classList.add('active');
        }
    });
});

// Form submission
const form = document.querySelector('.contact-form');
if (form) {
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        alert('Thank you for your message! We will get back to you soon.');
        form.reset();
    });
}

// CTA Button animation
const ctaButton = document.querySelector('.cta-button');
if (ctaButton) {
    ctaButton.addEventListener('click', () => {
        alert('Welcome! Let\\'s get started on your journey.');
    });
}

// Mobile menu toggle
const navToggle = document.querySelector('.nav-toggle');
const navMenu = document.querySelector('.nav-menu');
if (navToggle) {
    navToggle.addEventListener('click', () => {
        navMenu.style.display = navMenu.style.display === 'flex' ? 'none' : 'flex';
    });
}

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.feature-card, .service-card').forEach(el => {
    observer.observe(el);
});

// Navbar shadow on scroll
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.boxShadow = '0 8px 30px rgba(0,0,0,0.2)';
    } else {
        navbar.style.boxShadow = '0 4px 20px rgba(0,0,0,0.1)';
    }
});

console.log('Website loaded! Welcome to your new site!');
"""

website_builder_pro = WebsiteBuilderPro()
