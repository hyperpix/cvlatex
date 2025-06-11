import os
import re
import json
import requests
from flask import Flask, request, render_template, jsonify, send_file, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document
import openai
from dotenv import load_dotenv
import tempfile
import tarfile
import time
import traceback
import uuid
from sheets_integration import save_cv_to_sheets
import pdfplumber
import urllib.parse

# Load environment variables
load_dotenv()

# Get Google Sheets configuration
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')

# LaTeX compilation is handled entirely by latexonline.cc - no local installation needed

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Create a directory for storing CV data
CV_DATA_FOLDER = 'cv_data'
os.makedirs(CV_DATA_FOLDER, exist_ok=True)

# All LaTeX compilation is handled by latexonline.cc - no local installation needed

# Startup message
print(f"🌍 Environment: {os.getenv('FLASK_ENV', 'development')}")
print(f"🐍 Python: {os.sys.version.split()[0]}")
print(f"📁 Working Directory: {os.getcwd()}")
print("✅ PDF generation enabled via latexonline.cc")
print("🌐 No local LaTeX installation required")

# API keys
openai.api_key = os.getenv('OPENAI_API_KEY')

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
GEMINI_KEY_FILE = 'gemini_key.txt'

def load_gemini_key():
    if os.path.exists(GEMINI_KEY_FILE):
        with open(GEMINI_KEY_FILE, 'r') as f:
            return f.read().strip()
    return os.getenv('GEMINI_API_KEY', '')

def save_gemini_key(new_key):
    with open(GEMINI_KEY_FILE, 'w') as f:
        f.write(new_key.strip())

def get_gemini_key():
    return load_gemini_key()

GEMINI_API_KEY = get_gemini_key()

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'admin_logged_in' not in session:
        if request.method == 'POST':
            password = request.form.get('password', '')
            if password == ADMIN_PASSWORD:
                session['admin_logged_in'] = True
                return redirect(url_for('admin_panel'))
            else:
                flash('Incorrect password', 'danger')
        return '''
        <form method="post">
            <h2>Admin Login</h2>
            <input type="password" name="password" placeholder="Password" required />
            <button type="submit">Login</button>
        </form>
        '''
    # If logged in, show API key form
    if request.method == 'POST' and 'new_key' in request.form:
        new_key = request.form.get('new_key', '').strip()
        if new_key:
            save_gemini_key(new_key)
            global GEMINI_API_KEY
            GEMINI_API_KEY = new_key
            flash('Gemini API key updated!', 'success')
        else:
            flash('API key cannot be empty.', 'danger')
    current_key = get_gemini_key()
    masked_key = current_key[:4] + '*' * (len(current_key)-8) + current_key[-4:] if len(current_key) > 8 else '*' * len(current_key)
    return f'''
    <h2>Gemini API Key Admin Panel</h2>
    <form method="post">
        <label>Current Gemini API Key:</label><br>
        <input type="text" value="{masked_key}" readonly style="width:400px;" /><br><br>
        <label>New Gemini API Key:</label><br>
        <input type="text" name="new_key" style="width:400px;" required /><br><br>
        <button type="submit">Update Key</button>
    </form>
    <form method="post" action="/admin-logout"><button type="submit">Logout</button></form>
    '''

@app.route('/admin-logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_panel'))


ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file using pdfplumber for better accuracy"""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    print("=== Extracted PDF Text Start ===")
    print(text[:1000])
    print("=== Extracted PDF Text End ===")
    return text

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
    print("=== Extracted DOCX Text Start ===")
    print(text[:1000])
    print("=== Extracted DOCX Text End ===")
    return text

def enhance_parsing_with_gemini(text):
    """Use Gemini AI to parse CV text and extract structured information"""
    
    prompt = f"""
    Parse the following CV/Resume text and extract structured information in JSON format. 
    IMPORTANT: Only include information that actually exists in the CV text. Do not add placeholder or example data.
    If a field doesn't exist in the CV, either omit it entirely or set it to null/empty.
    
    Required JSON structure (only include fields that have actual data):
    {{
        "name": "Full name (only if found)",
        "email": "Email address (only if found)",
        "phone": "Phone number (only if found)",
        "linkedin": "LinkedIn URL (only if found)",
        "github": "GitHub URL (only if found)",
        "website": "Personal website (only if found)",
        "address": "Address/Location (only if found)",
        "education": [
            {{
                "degree": "Degree name",
                "institution": "Institution name",
                "date": "Date range",
                "location": "Location (if mentioned)",
                "gpa": "GPA (if mentioned)",
                "details": "Additional details (if any)"
            }}
        ],
        "experience": [
            {{
                "title": "Job title",
                "company": "Company name",
                "date": "Date range",
                "location": "Location (if mentioned)",
                "description": ["List of responsibilities and achievements"]
            }}
        ],
        "projects": [
            {{
                "title": "Project name",
                "description": "Project description",
                "technologies": "Technologies used",
                "date": "Date or duration (if mentioned)",
                "link": "Project link (if mentioned)"
            }}
        ],
        "skills": {{
            "languages": ["Programming languages (only if mentioned)"],
            "frameworks": ["Frameworks and libraries (only if mentioned)"],
            "tools": ["Tools and software (only if mentioned)"],
            "libraries": ["Additional libraries (only if mentioned)"],
            "databases": ["Databases (only if mentioned)"],
            "other": ["Other technical skills (only if mentioned)"]
        }},
        "certifications": [
            {{
                "name": "Certification name",
                "issuer": "Issuing organization",
                "date": "Date obtained (if mentioned)"
            }}
        ],
        "awards": ["Awards and honors (only if mentioned)"],
        "languages": ["Spoken languages (only if mentioned)"],
        "custom_sections": [
            {{
                "title": "Section title",
                "content": "Section content"
            }}
        ]
    }}
    
    CV Text:
    {text}
    
    Return only the JSON object with actual data from the CV, no additional text:
    """
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            # Extract the text from Gemini response
            generated_text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Clean the response to extract JSON
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_text = generated_text[json_start:json_end]
                parsed_data = json.loads(json_text)
                return parsed_data
            else:
                print("Failed to extract JSON from Gemini response")
                return None
        else:
            print(f"Gemini API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return None

def parse_cv_text(text):
    """Parse CV text and extract structured information with fallback"""
    
    print("=== SCRAPED CV TEXT ===")
    print(text[:1000] + "..." if len(text) > 1000 else text)
    print("=== END SCRAPED TEXT ===")
    
    # First try with Gemini AI
    gemini_result = enhance_parsing_with_gemini(text)
    if gemini_result:
        print("=== GEMINI PARSED DATA ===")
        print(json.dumps(gemini_result, indent=2))
        print("=== END GEMINI DATA ===")
        return gemini_result
    
    # Fallback to regex-based parsing if Gemini fails
    print("Gemini failed, using fallback parsing...")
    
    # Initialize the parsed data structure with only empty containers
    parsed_data = {
        'name': '',
        'email': '',
        'phone': '',
        'linkedin': '',
        'github': '',
        'website': '',
        'address': '',
        'education': [],
        'experience': [],
        'projects': [],
        'skills': {
            'languages': [],
            'frameworks': [],
            'tools': [],
            'libraries': [],
            'databases': [],
            'other': []
        },
        'certifications': [],
        'awards': [],
        'languages': [],
        'custom_sections': []
    }
    
    lines = text.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    # Extract basic contact information
    for line in lines:
        # Email pattern
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line)
        if email_match and not parsed_data['email']:
            parsed_data['email'] = email_match.group()
        
        # Phone pattern
        phone_match = re.search(r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})', line)
        if phone_match and not parsed_data['phone']:
            parsed_data['phone'] = phone_match.group()
        
        # LinkedIn pattern
        if 'linkedin.com' in line.lower() and not parsed_data['linkedin']:
            parsed_data['linkedin'] = line.strip()
        
        # GitHub pattern
        if 'github.com' in line.lower() and not parsed_data['github']:
            parsed_data['github'] = line.strip()
        
        # Website pattern (basic)
        if ('http' in line.lower() or 'www.' in line.lower()) and 'linkedin' not in line.lower() and 'github' not in line.lower() and not parsed_data['website']:
            parsed_data['website'] = line.strip()
    
    # Extract name (usually the first significant line)
    if lines and not parsed_data['name']:
        # Look for a line that might be a name (usually at the top, not an email/phone)
        for line in lines[:5]:
            if not re.search(r'[@()]', line) and len(line.split()) <= 4 and len(line) > 2:
                parsed_data['name'] = line
                break
    
    # Extract education, experience, projects, and skills
    current_section = None
    current_item = {}
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Identify sections
        if any(keyword in line_lower for keyword in ['education', 'academic']):
            current_section = 'education'
            continue
        elif any(keyword in line_lower for keyword in ['experience', 'work', 'employment', 'professional']):
            current_section = 'experience'
            continue
        elif any(keyword in line_lower for keyword in ['project', 'portfolio']):
            current_section = 'projects'
            continue
        elif any(keyword in line_lower for keyword in ['skill', 'technical', 'programming', 'languages']):
            current_section = 'skills'
            continue
        
        # Process content based on current section
        if current_section == 'education' and line:
            # Look for degree patterns
            if any(degree in line_lower for degree in ['bachelor', 'master', 'phd', 'associate', 'certificate']):
                if current_item:
                    parsed_data['education'].append(current_item)
                current_item = {'degree': line, 'institution': '', 'date': ''}
            elif current_item and not current_item['institution']:
                current_item['institution'] = line
            elif current_item and re.search(r'\d{4}', line):
                current_item['date'] = line
        
        elif current_section == 'experience' and line:
            # Look for job titles or company names
            if any(char in line for char in ['-', '|']) or re.search(r'\d{4}', line):
                if current_item:
                    parsed_data['experience'].append(current_item)
                current_item = {'title': line, 'company': '', 'date': '', 'description': []}
            elif current_item and not current_item.get('description'):
                current_item['description'] = [line]
            elif current_item:
                current_item['description'].append(line)
        
        elif current_section == 'projects' and line:
            if current_item and 'title' in current_item:
                parsed_data['projects'].append(current_item)
                current_item = {}
            current_item = {'title': line, 'description': '', 'technologies': ''}
        
        elif current_section == 'skills' and line:
            # Parse skills line by line
            if any(keyword in line_lower for keyword in ['language', 'programming']):
                skills_text = line.split(':')[-1] if ':' in line else line
                parsed_data['skills']['languages'] = [s.strip() for s in skills_text.split(',') if s.strip()]
            elif any(keyword in line_lower for keyword in ['framework']):
                skills_text = line.split(':')[-1] if ':' in line else line
                parsed_data['skills']['frameworks'] = [s.strip() for s in skills_text.split(',') if s.strip()]
            elif any(keyword in line_lower for keyword in ['tool', 'software']):
                skills_text = line.split(':')[-1] if ':' in line else line
                parsed_data['skills']['tools'] = [s.strip() for s in skills_text.split(',') if s.strip()]
    
    # Add the last item if it exists
    if current_item:
        if current_section == 'education':
            parsed_data['education'].append(current_item)
        elif current_section == 'experience':
            parsed_data['experience'].append(current_item)
        elif current_section == 'projects':
            parsed_data['projects'].append(current_item)
    
    # Clean up empty fields
    cleaned_data = {}
    for key, value in parsed_data.items():
        if key == 'skills':
            # Only include skill categories that have actual skills
            skills_cleaned = {k: v for k, v in value.items() if v}
            if skills_cleaned:
                cleaned_data[key] = skills_cleaned
        elif isinstance(value, list):
            # Only include lists that have items
            if value:
                cleaned_data[key] = value
        elif isinstance(value, str):
            # Only include strings that are not empty
            if value:
                cleaned_data[key] = value
        else:
            if value:
                cleaned_data[key] = value
    
    return cleaned_data

def clean_text_for_latex(text):
    """Clean text to be LaTeX-safe"""
    if not text:
        return ""
    
    # Handle case where text might be a list
    if isinstance(text, list):
        return [clean_text_for_latex(item) for item in text]
    
    # Convert to string if not already
    text = str(text)
    
    # First handle backslashes to avoid conflicts
    text = text.replace('\\', '\\textbackslash{}')
    
    # Replace problematic Unicode characters
    replacements = {
        '○': '\\textbullet',  # Unicode bullet
        '●': '\\textbullet',  # Black circle
        '•': '\\textbullet',  # Bullet
        '◦': '\\textbullet',  # White bullet
        '▪': '\\textbullet',  # Black small square
        '▫': '\\textbullet',  # White small square
        '–': '--',           # En dash
        '—': '---',          # Em dash
        '‘': "'",            # Left single quotation mark
        '’': "'",            # Right single quotation mark
        '“': '"',            # Left double quotation mark
        '”': '"',            # Right double quotation mark
        '…': '...',          # Horizontal ellipsis
        '°': '\\textdegree', # Degree symbol
        '±': '\\textpm',     # Plus-minus
        '×': '\\texttimes',  # Multiplication sign
        '÷': '\\textdiv',    # Division sign
        '€': '\\texteuro',   # Euro sign
        '£': '\\textsterling', # Pound sign
        '¥': '\\textyen',    # Yen sign
        '©': '\\textcopyright', # Copyright
        '®': '\\textregistered', # Registered trademark
        '™': '\\texttrademark', # Trademark
    }
    
    # Apply replacements
    for unicode_char, latex_replacement in replacements.items():
        text = text.replace(unicode_char, latex_replacement)
    
    # Escape special LaTeX characters (excluding backslash which we handled first)
    latex_special_chars = {
        '&': '\\&',
        '%': '\\%',
        '$': '\\$',
        '#': '\\#',
        '^': '\\textasciicircum{}',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
    }
    
    for char, replacement in latex_special_chars.items():
        text = text.replace(char, replacement)
    
    return text

def generate_latex_resume(parsed_data):
    """Generate LaTeX resume using Jake's Resume template"""
    
    # Jake's Resume template with Unicode support
    latex_template = r"""
%-------------------------
% Resume in Latex
% Author : Jake Gutierrez
% Based off of: https://github.com/sb2nov/resume
% License : MIT
%------------------------

\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{textcomp}

%----------FONT OPTIONS----------
% sans-serif
% \usepackage[sfdefault]{FiraSans}
% \usepackage[sfdefault]{roboto}
% \usepackage[sfdefault]{noto-sans}
% \usepackage[default]{sourcesanspro}

% serif
% \usepackage{CormorantGaramond}
% \usepackage{charter}

\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\raggedright\large\bfseries
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% Ensure compatibility with online LaTeX compilers

%-------------------------
% Custom commands
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubSubheading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-------------------------------------------
%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%

\begin{document}

%----------HEADING----------
\begin{center}
    \textbf{\Huge """ + clean_text_for_latex(parsed_data.get('name', 'Name Not Found')) + r"""} \\ \vspace{1pt}"""

    # Build contact information dynamically
    contact_parts = []
    
    if parsed_data.get('phone'):
        contact_parts.append(clean_text_for_latex(parsed_data['phone']))
    
    if parsed_data.get('email'):
        email = clean_text_for_latex(parsed_data['email'])
        contact_parts.append(f"\\href{{mailto:{email}}}{{\\underline{{{email}}}}}")
    
    if parsed_data.get('linkedin'):
        linkedin_url = parsed_data['linkedin']
        if not linkedin_url.startswith('http'):
            linkedin_url = 'https://' + linkedin_url
        contact_parts.append(f"\\href{{{linkedin_url}}}{{\\underline{{LinkedIn}}}}")
    
    if parsed_data.get('github'):
        github_url = parsed_data['github']
        if not github_url.startswith('http'):
            github_url = 'https://' + github_url
        contact_parts.append(f"\\href{{{github_url}}}{{\\underline{{GitHub}}}}")
    
    if parsed_data.get('website'):
        website_url = parsed_data['website']
        if not website_url.startswith('http'):
            website_url = 'https://' + website_url
        contact_parts.append(f"\\href{{{website_url}}}{{\\underline{{Website}}}}")
    
    if contact_parts:
        latex_template += f"""
    \\small {' $|$ '.join(contact_parts)}"""
    
    latex_template += r"""
\end{center}"""

    # Add Professional Summary section only if summary data exists
    if parsed_data.get('summary'):
        summary = clean_text_for_latex(parsed_data['summary'])
        latex_template += f"""

%-----------PROFESSIONAL SUMMARY-----------
\\section{{Professional Summary}}
 \\begin{{itemize}}[leftmargin=0.15in, label={{}}]
    \\small{{\\item{{
     {summary}
    }}}}
 \\end{{itemize}}"""

    # Add Education section only if education data exists
    if parsed_data.get('education'):
        latex_template += r"""

%-----------EDUCATION-----------
\section{Education}
  \resumeSubHeadingListStart"""
        
        for edu in parsed_data['education']:
            degree = clean_text_for_latex(edu.get('degree', ''))
            institution = clean_text_for_latex(edu.get('institution', ''))
            date = clean_text_for_latex(edu.get('date', ''))
            location = clean_text_for_latex(edu.get('location', ''))
            gpa = clean_text_for_latex(edu.get('gpa', ''))
            details = clean_text_for_latex(edu.get('details', ''))
            
            # Build the education entry
            latex_template += f"""
    \\resumeSubheading
      {{{degree}}}{{{date}}}
      {{{institution}}}{{{location}}}"""
            
            # Add GPA or details if they exist
            if gpa or details:
                latex_template += r"""
      \resumeItemListStart"""
                if gpa:
                    latex_template += f"""
        \\resumeItem{{GPA: {gpa}}}"""
                if details:
                    latex_template += f"""
        \\resumeItem{{{details}}}"""
                latex_template += r"""
      \resumeItemListEnd"""
        
        latex_template += r"""
  \resumeSubHeadingListEnd"""

    # Add Experience section only if experience data exists
    if parsed_data.get('experience'):
        latex_template += r"""

%-----------EXPERIENCE-----------
\section{Experience}
  \resumeSubHeadingListStart"""
        
        for exp in parsed_data['experience']:
            title = clean_text_for_latex(exp.get('title', ''))
            company = clean_text_for_latex(exp.get('company', ''))
            date = clean_text_for_latex(exp.get('date', ''))
            location = clean_text_for_latex(exp.get('location', ''))
            description = exp.get('description', [])
            
            latex_template += f"""
    \\resumeSubheading
      {{{title}}}{{{date}}}
      {{{company}}}{{{location}}}"""
            
            if description:
                latex_template += r"""
      \resumeItemListStart"""
                for desc in description[:4]:  # Limit to 4 bullet points
                    clean_desc = clean_text_for_latex(desc)
                    latex_template += f"""
        \\resumeItem{{{clean_desc}}}"""
                latex_template += r"""
      \resumeItemListEnd"""
        
        latex_template += r"""
  \resumeSubHeadingListEnd"""

    # Add Projects section only if projects data exists
    if parsed_data.get('projects'):
        latex_template += r"""

%-----------PROJECTS-----------
\section{Projects}
    \resumeSubHeadingListStart"""
        
        for project in parsed_data['projects']:
            title = clean_text_for_latex(project.get('title', ''))
            description = project.get('description', '')
            if isinstance(description, list):
                description = clean_text_for_latex(' '.join(description))
            else:
                description = clean_text_for_latex(description)
            technologies = clean_text_for_latex(project.get('technologies', ''))
            date = clean_text_for_latex(project.get('date', ''))
            link = project.get('link', '')
            
            # Build project title with technologies
            project_title = title
            if technologies:
                project_title += f" $|$ \\emph{{{technologies}}}"
            
            latex_template += f"""
      \\resumeProjectHeading
          {{\\textbf{{{project_title}}}}}{{{date}}}"""
            
            if description:
                latex_template += f"""
          \\resumeItemListStart
            \\resumeItem{{{description}}}"""
                if link:
                    latex_template += f"""
            \\resumeItem{{Link: \\href{{{link}}}{{\\underline{{{link}}}}}}}"""
                latex_template += r"""
          \resumeItemListEnd"""
        
        latex_template += r"""
    \resumeSubHeadingListEnd"""

    # Add Technical Skills section only if skills data exists
    if parsed_data.get('skills'):
        skills = parsed_data['skills']
        skill_lines = []
        
        if skills.get('languages'):
            clean_languages = [clean_text_for_latex(lang) for lang in skills['languages']]
            skill_lines.append(f"\\textbf{{Languages}}: {', '.join(clean_languages)}")
        
        if skills.get('frameworks'):
            clean_frameworks = [clean_text_for_latex(fw) for fw in skills['frameworks']]
            skill_lines.append(f"\\textbf{{Frameworks}}: {', '.join(clean_frameworks)}")
        
        if skills.get('tools'):
            clean_tools = [clean_text_for_latex(tool) for tool in skills['tools']]
            skill_lines.append(f"\\textbf{{Developer Tools}}: {', '.join(clean_tools)}")
        
        if skills.get('libraries'):
            clean_libraries = [clean_text_for_latex(lib) for lib in skills['libraries']]
            skill_lines.append(f"\\textbf{{Libraries}}: {', '.join(clean_libraries)}")
        
        if skills.get('databases'):
            clean_databases = [clean_text_for_latex(db) for db in skills['databases']]
            skill_lines.append(f"\\textbf{{Databases}}: {', '.join(clean_databases)}")
        
        if skills.get('other'):
            clean_other = [clean_text_for_latex(other) for other in skills['other']]
            skill_lines.append(f"\\textbf{{Other}}: {', '.join(clean_other)}")
        
        if skill_lines:
            latex_template += r"""

%-----------PROGRAMMING SKILLS-----------
\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     """ + ' \\\\\n     '.join(skill_lines) + r"""
    }}
 \end{itemize}"""

    # Add Certifications section only if certifications data exists
    if parsed_data.get('certifications'):
        latex_template += r"""

%-----------CERTIFICATIONS-----------
\section{Certifications}
  \resumeSubHeadingListStart"""
        
        for cert in parsed_data['certifications']:
            name = clean_text_for_latex(cert.get('name', ''))
            issuer = clean_text_for_latex(cert.get('issuer', ''))
            date = clean_text_for_latex(cert.get('date', ''))
            
            latex_template += f"""
    \\resumeSubheading
      {{{name}}}{{{date}}}
      {{{issuer}}}{{}}"""
        
        latex_template += r"""
  \resumeSubHeadingListEnd"""

    # Add Awards section only if awards data exists
    if parsed_data.get('awards'):
        latex_template += r"""

%-----------AWARDS-----------
\section{Awards \& Honors}
  \resumeItemListStart"""
        
        for award in parsed_data['awards']:
            clean_award = clean_text_for_latex(award)
            latex_template += f"""
    \\resumeItem{{{clean_award}}}"""
        
        latex_template += r"""
  \resumeItemListEnd"""

    # Add Languages section only if language data exists
    if parsed_data.get('languages'):
        latex_template += r"""

%-----------LANGUAGES-----------
\section{Languages}
  \resumeItemListStart"""
        
        for lang in parsed_data['languages']:
            clean_lang = clean_text_for_latex(lang)
            latex_template += f"""
    \\resumeItem{{{clean_lang}}}"""
        
        latex_template += r"""
  \resumeItemListEnd"""

    # Add Custom Sections
    if parsed_data.get('custom_sections'):
        for section in parsed_data['custom_sections']:
            title = clean_text_for_latex(section.get('title', ''))
            content = clean_text_for_latex(section.get('content', ''))
            
            # Convert title to uppercase for section header
            title_upper = title.upper()
            
            latex_template += f"""

%-----------{title_upper}-----------
\\section{{{title}}}"""
            
            # Check if content contains bullet points or line breaks
            content_lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            if len(content_lines) > 1:
                # Multiple lines - treat as list
                latex_template += r"""
  \resumeItemListStart"""
                
                for line in content_lines:
                    # Remove bullet points if they exist
                    clean_line = line.lstrip('•*-+ ').strip()
                    if clean_line:
                        latex_template += f"""
    \\resumeItem{{{clean_line}}}"""
                
                latex_template += r"""
  \resumeItemListEnd"""
            else:
                # Single line or paragraph - treat as simple text
                if content:
                    latex_template += f"""
 \\begin{{itemize}}[leftmargin=0.15in, label={{}}]
    \\small{{\\item{{
     {content}
    }}}}
 \\end{{itemize}}"""

    latex_template += r"""

%-------------------------------------------
\end{document}
"""

    return latex_template


def compile_latex_online(latex_content, output_filename):
    """Compile LaTeX using latexonline.cc service with Pastebin URL-based approach."""
    try:
        print("🌐 Using latexonline.cc for compilation with Pastebin URL method")
        
        # Try Pastebin URL method first
        pastebin_url = create_pastebin_paste(latex_content)
        
        if pastebin_url:
            print(f"📄 LaTeX hosted at: {pastebin_url}")
            
            # Call latexonline.cc with the URL parameter
            compile_url = f"https://latexonline.cc/compile?url={urllib.parse.quote(pastebin_url)}"
            print(f"🔗 Calling: {compile_url}")
            
            resp = requests.get(compile_url, timeout=60)
            
            content_type = resp.headers.get('Content-Type', '')
            if resp.status_code == 200 and 'pdf' in content_type:
                output_dir = os.path.abspath(app.config['OUTPUT_FOLDER'])
                os.makedirs(output_dir, exist_ok=True)
                pdf_path = os.path.join(output_dir, output_filename)
                with open(pdf_path, 'wb') as f:
                    f.write(resp.content)
                print(f"✅ Online PDF created at: {pdf_path}")
                return True
            else:
                print(f"❌ latexonline response {resp.status_code}")
                if resp.status_code == 400:
                    print("🔍 LaTeX compilation error - likely due to unsupported packages or syntax")
                    print("📝 Error details:")
                print(resp.text[:500])
        
        # If Pastebin method fails, fallback to text method for short content
        print("🔄 Attempting fallback to text method...")
        encoded_content = urllib.parse.quote(latex_content)
        estimated_url_length = len(f"https://latexonline.cc/compile?text={encoded_content}")
        
        if estimated_url_length < 8000:  # Safe URL length limit
            print("📄 Using GET text method for short content")
            url = f"https://latexonline.cc/compile?text={encoded_content}"
            resp = requests.get(url, timeout=60)
            
            content_type = resp.headers.get('Content-Type', '')
            if resp.status_code == 200 and 'pdf' in content_type:
                output_dir = os.path.abspath(app.config['OUTPUT_FOLDER'])
                os.makedirs(output_dir, exist_ok=True)
                pdf_path = os.path.join(output_dir, output_filename)
                with open(pdf_path, 'wb') as f:
                    f.write(resp.content)
                print(f"✅ Fallback PDF created at: {pdf_path}")
                return True
            else:
                print(f"❌ Text fallback failed: {resp.status_code}")
        else:
            # Use multipart form data for longer content
            print("📄 Content too long for text method, using multipart upload")
            import tempfile
            import tarfile
            
            with tempfile.TemporaryDirectory() as tmpdir:
                tex_path = os.path.join(tmpdir, 'main.tex')
                with open(tex_path, 'w', encoding='utf-8') as f:
                    f.write(latex_content)

                tar_path = os.path.join(tmpdir, 'texfiles.tar')
                with tarfile.open(tar_path, 'w') as tar:
                    tar.add(tex_path, arcname='main.tex')

                with open(tar_path, 'rb') as f:
                    files = {'file': ('texfiles.tar', f, 'application/x-tar')}
                    resp = requests.post(
                        'https://latexonline.cc/data?target=main.tex',
                        files=files,
                        timeout=60
                    )
            
            content_type = resp.headers.get('Content-Type', '')
            if resp.status_code == 200 and 'pdf' in content_type:
                output_dir = os.path.abspath(app.config['OUTPUT_FOLDER'])
                os.makedirs(output_dir, exist_ok=True)
                pdf_path = os.path.join(output_dir, output_filename)
                with open(pdf_path, 'wb') as f:
                    f.write(resp.content)
                print(f"✅ Multipart PDF created at: {pdf_path}")
                return True
            else:
                print(f"❌ Multipart fallback also failed: {resp.status_code}")
                
    except Exception as e:
        print(f"❌ Error during online LaTeX compilation: {e}")
    return False

def create_pastebin_paste(latex_content):
    """Create a public Pastebin paste to host LaTeX content."""
    try:
        print("🔧 Creating Pastebin paste...")
        
        # Pastebin API configuration
        PASTEBIN_API_KEY = os.getenv('PASTEBIN_API_KEY')
        if not PASTEBIN_API_KEY:
            print("❌ PASTEBIN_API_KEY not set in environment variables.")
            return None
        
        # Pastebin API parameters
        api_data = {
            'api_dev_key': PASTEBIN_API_KEY,
            'api_option': 'paste',
            'api_paste_code': latex_content,
            'api_paste_name': 'LaTeX Document for Compilation',
            'api_paste_format': 'latex',
            'api_paste_private': 0,  # 0 = public, 1 = unlisted, 2 = private
            'api_paste_expire_date': '10M'  # Expire in 10 minutes
        }
        
        # Create the paste
        response = requests.post(
            'https://pastebin.com/api/api_post.php',
            data=api_data,
            timeout=30
        )
        
        if response.status_code == 200:
            paste_url = response.text.strip()
            
            # Check if we got an error response
            if paste_url.startswith('Bad API request'):
                print(f"❌ Pastebin API error: {paste_url}")
                return None
            elif paste_url.startswith('https://pastebin.com/'):
                # Convert to raw URL
                paste_id = paste_url.split('/')[-1]
                raw_url = f"https://pastebin.com/raw/{paste_id}"
                
                print(f"✅ Pastebin paste created!")
                print(f"📄 Paste URL: {paste_url}")
                print(f"🔗 Raw URL: {raw_url}")
                return raw_url
            else:
                print(f"❌ Unexpected Pastebin response: {paste_url}")
                return None
        else:
            print(f"❌ Failed to create Pastebin paste: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None
    
    except Exception as e:
        print(f"❌ Error creating Pastebin paste: {e}")
        return None



def compile_latex_to_pdf(latex_content, output_filename):
    """Compile LaTeX content to PDF using latexonline.cc (hybrid approach: GET for short content, multipart for long content)."""
    print(f"🔍 compile_latex_to_pdf called with output_filename: {output_filename}")
    return compile_latex_online(latex_content, output_filename)

def save_cv_data(cv_id, cv_data, metadata=None):
    """Save CV data to JSON file for future editing"""
    try:
        cv_data_with_meta = {
            'id': cv_id,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'metadata': metadata or {},
            'data': cv_data
        }
        
        cv_file_path = os.path.join(CV_DATA_FOLDER, f"{cv_id}.json")
        with open(cv_file_path, 'w', encoding='utf-8') as f:
            json.dump(cv_data_with_meta, f, indent=2, ensure_ascii=False)
        
        print(f"✅ CV data saved: {cv_file_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving CV data: {e}")
        return False

def load_cv_data(cv_id):
    """Load CV data from JSON file"""
    try:
        cv_file_path = os.path.join(CV_DATA_FOLDER, f"{cv_id}.json")
        if not os.path.exists(cv_file_path):
            return None
        
        with open(cv_file_path, 'r', encoding='utf-8') as f:
            cv_data = json.load(f)
        
        return cv_data
    except Exception as e:
        print(f"❌ Error loading CV data: {e}")
        return None

def update_cv_data(cv_id, cv_data):
    """Update existing CV data"""
    try:
        existing_data = load_cv_data(cv_id)
        if not existing_data:
            return False
        
        existing_data['data'] = cv_data
        existing_data['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        cv_file_path = os.path.join(CV_DATA_FOLDER, f"{cv_id}.json")
        with open(cv_file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ CV data updated: {cv_file_path}")
        return True
    except Exception as e:
        print(f"❌ Error updating CV data: {e}")
        return False

def list_cv_data():
    """List all saved CV data"""
    try:
        cv_list = []
        for filename in os.listdir(CV_DATA_FOLDER):
            if filename.endswith('.json'):
                cv_id = filename[:-5]  # Remove .json extension
                cv_data = load_cv_data(cv_id)
                if cv_data:
                    cv_summary = {
                        'id': cv_id,
                        'name': cv_data.get('data', {}).get('name', 'Unnamed CV'),
                        'email': cv_data.get('data', {}).get('email', ''),
                        'created_at': cv_data.get('created_at', ''),
                        'updated_at': cv_data.get('updated_at', ''),
                    }
                    cv_list.append(cv_summary)
        
        # Sort by updated_at (most recent first)
        cv_list.sort(key=lambda x: x['updated_at'], reverse=True)
        return cv_list
    except Exception as e:
        print(f"❌ Error listing CV data: {e}")
        return []

def delete_cv_data(cv_id):
    """Delete CV data and associated files"""
    try:
        # Delete JSON data file
        cv_file_path = os.path.join(CV_DATA_FOLDER, f"{cv_id}.json")
        if os.path.exists(cv_file_path):
            os.remove(cv_file_path)
        
        # Delete associated LaTeX and PDF files
        for ext in ['.tex', '.pdf']:
            file_path = os.path.join(app.config['OUTPUT_FOLDER'], f"resume_{cv_id}{ext}")
            if os.path.exists(file_path):
                os.remove(file_path)
        
        print(f"✅ CV data deleted: {cv_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting CV data: {e}")
        return False

def enhance_cv_for_job(parsed_data, job_description):
    """Use Gemini AI to enhance CV content for a specific job description"""
    
    # Convert parsed data to text for processing
    current_cv_text = f"""
Name: {parsed_data.get('name', '')}
Email: {parsed_data.get('email', '')}
Phone: {parsed_data.get('phone', '')}

Education:
{chr(10).join([f"- {edu.get('degree', '')} at {edu.get('institution', '')} ({edu.get('date', '')})" for edu in parsed_data.get('education', [])])}

Experience:
{chr(10).join([f"- {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('date', '')}):{chr(10)}  {chr(10).join(exp.get('description', []))}" for exp in parsed_data.get('experience', [])])}

Projects:
{chr(10).join([f"- {proj.get('title', '')}: {proj.get('description', '')} (Technologies: {proj.get('technologies', '')})" for proj in parsed_data.get('projects', [])])}

Skills:
{chr(10).join([f"- {category}: {', '.join(skills)}" for category, skills in parsed_data.get('skills', {}).items() if skills])}
"""

    prompt = f"""
    You are a professional resume writer. Given the candidate's current CV and a job description, enhance the CV content to better match the job requirements while keeping all information truthful and accurate.

    IMPORTANT GUIDELINES:
    1. Keep all factual information (names, dates, companies, degrees) exactly the same
    2. Enhance descriptions to highlight relevant skills and experiences
    3. Add relevant keywords from the job description naturally
    4. Reorganize or emphasize experiences that match the job requirements
    5. Return the enhanced data in the same JSON structure provided
    6. Do not add fake experiences, degrees, or skills

    Current CV:
    {current_cv_text}

    Job Description:
    {job_description}

    Please enhance the CV content and return it in this exact JSON structure:
    {{
        "name": "Keep exactly the same",
        "email": "Keep exactly the same", 
        "phone": "Keep exactly the same",
        "linkedin": "Keep exactly the same",
        "github": "Keep exactly the same",
        "website": "Keep exactly the same",
        "address": "Keep exactly the same",
        "education": [
            {{
                "degree": "Keep exactly the same",
                "institution": "Keep exactly the same", 
                "date": "Keep exactly the same",
                "location": "Keep exactly the same",
                "gpa": "Keep exactly the same",
                "details": "Can enhance to highlight relevant coursework/projects"
            }}
        ],
        "experience": [
            {{
                "title": "Keep exactly the same",
                "company": "Keep exactly the same",
                "date": "Keep exactly the same", 
                "location": "Keep exactly the same",
                "description": ["Enhanced descriptions that highlight job-relevant skills and achievements"]
            }}
        ],
        "projects": [
            {{
                "title": "Can slightly enhance if relevant",
                "description": "Enhanced description highlighting job-relevant aspects",
                "technologies": "Can add relevant technologies if they were actually used",
                "date": "Keep exactly the same",
                "link": "Keep exactly the same"
            }}
        ],
        "skills": {{
            "languages": ["Enhanced list emphasizing job-relevant languages"],
            "frameworks": ["Enhanced list emphasizing job-relevant frameworks"],
            "tools": ["Enhanced list emphasizing job-relevant tools"],
            "databases": ["Enhanced list emphasizing job-relevant databases"],
            "other": ["Enhanced list emphasizing other job-relevant skills"]
        }},
        "certifications": "Keep all existing, can add if candidate likely has them",
        "awards": "Keep exactly the same",
        "languages": "Keep exactly the same",
        "custom_sections": "Keep exactly the same"
    }}

    Return only the JSON object with enhanced content:
    """
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            # Extract the text from Gemini response
            generated_text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Clean the response to extract JSON
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_text = generated_text[json_start:json_end]
                enhanced_data = json.loads(json_text)
                print("=== ENHANCED CV DATA ===")
                print(json.dumps(enhanced_data, indent=2))
                print("=== END ENHANCED DATA ===")
                return enhanced_data
            else:
                print("Failed to extract JSON from Gemini response")
                return parsed_data
        else:
            print(f"Gemini API error: {response.status_code} - {response.text}")
            return parsed_data
            
    except Exception as e:
        print(f"Error enhancing CV with Gemini API: {e}")
        return parsed_data

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get mode and job description from form data
    mode = request.form.get('mode', 'professional')
    job_description = request.form.get('job_description', '')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Extract text based on file type
        if filename.lower().endswith('.pdf'):
            extracted_text = extract_text_from_pdf(file_path)
        elif filename.lower().endswith('.docx'):
            extracted_text = extract_text_from_docx(file_path)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        if not extracted_text.strip():
            return jsonify({'error': 'Could not extract text from your file. Please upload a text-based PDF or DOCX.'}), 400
        
        # Parse the extracted text using Gemini AI
        parsed_data = parse_cv_text(extracted_text)
        
        # Enhance CV for job if in tailored mode
        if mode == 'tailored' and job_description:
            print(f"=== TAILORING CV FOR JOB ===")
            print(f"Job Description (first 200 chars): {job_description[:200]}...")
            parsed_data = enhance_cv_for_job(parsed_data, job_description)
        
        # Save CV data to Google Sheets if configured
        if GOOGLE_SHEETS_SPREADSHEET_ID:
            try:
                save_cv_to_sheets(parsed_data, GOOGLE_SHEETS_SPREADSHEET_ID)
            except Exception as e:
                print(f"⚠️ Failed to save CV data to Google Sheets: {e}")
                # Continue with the process even if sheets save fails
        
        # Clean up uploaded file (with error handling)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ Cleaned up uploaded file: {file_path}")
        except Exception as cleanup_error:
            print(f"⚠️ Could not clean up uploaded file: {cleanup_error}")
            # Don't let cleanup errors affect the main process
        
        # Generate unique session ID for this CV data
        session_id = str(uuid.uuid4())
        
        # Save CV data to session storage (you could also use database)
        cv_data = {
            'parsed_data': parsed_data,
            'mode': mode,
            'job_description': job_description,
            'original_filename': filename
        }
        
        # Save to temporary storage (using file system for simplicity)
        import json
        session_file = os.path.join('temp_sessions', f'{session_id}.json')
        os.makedirs('temp_sessions', exist_ok=True)
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(cv_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'redirect_url': f'/preview-cv/{session_id}',
            'extracted_text': extracted_text
        })
    
    return jsonify({'error': 'Invalid file type. Please upload PDF or DOCX files only.'}), 400

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/preview/<filename>')
def preview_pdf(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(file_path) and filename.endswith('.pdf'):
        return send_file(file_path, mimetype='application/pdf')
    return jsonify({'error': 'PDF file not found'}), 404

@app.route('/result')
def result_page():
    return render_template('result.html')

@app.route('/preview-cv/<session_id>')
def preview_cv_page(session_id):
    """Display extracted/enhanced CV data for preview and editing"""
    import json
    import os
    
    session_file = os.path.join('temp_sessions', f'{session_id}.json')
    
    if not os.path.exists(session_file):
        return render_template('error.html', error='CV session not found or expired'), 404
    
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            cv_data = json.load(f)
        
        return render_template('preview_cv.html', 
                             cv_data=cv_data, 
                             session_id=session_id)
    except Exception as e:
        return render_template('error.html', error=f'Error loading CV data: {str(e)}'), 500

@app.route('/create-cv')
def create_cv_page():
    return render_template('create_cv.html')

@app.route('/api/create-cv', methods=['POST'])
def create_cv():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        # Validate required fields
        if not data.get('name') or not data.get('email'):
            return jsonify({'success': False, 'error': 'Name and email are required fields'})
        
        # Process the data to match our existing structure
        parsed_data = {
            'name': data.get('name', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'linkedin': data.get('linkedin', ''),
            'github': data.get('github', ''),
            'website': data.get('website', ''),
            'address': data.get('address', ''),
            'summary': data.get('summary', ''),
            'education': [],
            'experience': [],
            'projects': [],
            'skills': {
                'languages': [],
                'frameworks': [],
                'tools': [],
                'databases': [],
                'other': []
            },
            'custom_sections': []
        }
        
        # Process education
        if data.get('education'):
            for edu in data['education']:
                if edu.get('degree') or edu.get('institution'):
                    parsed_data['education'].append({
                        'degree': edu.get('degree', ''),
                        'institution': edu.get('institution', ''),
                        'date': edu.get('date', ''),
                        'location': edu.get('location', ''),
                        'gpa': edu.get('gpa', ''),
                        'details': edu.get('details', '')
                    })
        
        # Process experience
        if data.get('experience'):
            for exp in data['experience']:
                if exp.get('title') or exp.get('company'):
                    # Split description by lines for bullet points
                    description_lines = []
                    if exp.get('description'):
                        description_lines = [line.strip() for line in exp['description'].split('\n') if line.strip()]
                    
                    parsed_data['experience'].append({
                        'title': exp.get('title', ''),
                        'company': exp.get('company', ''),
                        'date': exp.get('date', ''),
                        'location': exp.get('location', ''),
                        'description': description_lines
                    })
        
        # Process projects
        if data.get('projects'):
            for proj in data['projects']:
                if proj.get('title'):
                    parsed_data['projects'].append({
                        'title': proj.get('title', ''),
                        'description': proj.get('description', ''),
                        'technologies': proj.get('technologies', ''),
                        'date': proj.get('date', ''),
                        'link': proj.get('link', '')
                    })
        
        # Process skills
        if data.get('skills'):
            skills = data['skills']
            
            # Convert comma-separated strings to lists
            for skill_type in ['languages', 'frameworks', 'tools', 'databases', 'other']:
                if skills.get(skill_type):
                    parsed_data['skills'][skill_type] = [
                        item.strip() for item in skills[skill_type].split(',') if item.strip()
                    ]
        
        # Process custom sections
        if data.get('custom'):
            for custom in data['custom']:
                if custom.get('title') and custom.get('content'):
                    parsed_data['custom_sections'].append({
                        'title': custom['title'],
                        'content': custom['content']
                    })
        
        # Generate LaTeX
        latex_content = generate_latex_resume(parsed_data)
        
        # Save LaTeX file
        timestamp = int(time.time())
        latex_filename = f"cv_{timestamp}.tex"
        latex_path = os.path.join(app.config['OUTPUT_FOLDER'], latex_filename)
        
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        print(f"Generated LaTeX saved to: {latex_path}")
        print("=== GENERATED LATEX CONTENT (first 500 chars) ===")
        print(latex_content[:500] + "..." if len(latex_content) > 500 else latex_content)
        
        # Compile to PDF
        pdf_filename = f"cv_{timestamp}.pdf"
        pdf_compiled = compile_latex_to_pdf(latex_content, pdf_filename)
        
        response_data = {
            'success': True,
            'latex_content': latex_content,
            'latex_download_url': f'/download/{latex_filename}',
            'pdf_compiled': pdf_compiled,
            'latex_available': True
        }
        
        if pdf_compiled:
            response_data.update({
                'pdf_download_url': f'/download/{pdf_filename}',
                'pdf_preview_url': f'/preview/{pdf_filename}'
            })
        else:
            response_data['warning'] = 'PDF compilation failed via latexonline.cc. LaTeX source is still available for download.'
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in create_cv: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing your CV',
            'details': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/preview', methods=['POST'])
def preview_latex():
    """Generate a preview of the LaTeX content"""
    data = request.get_json()
    latex_content = data.get('latex_content', '')
    
    if not latex_content:
        return jsonify({'error': 'No LaTeX content provided'}), 400
    
    # Save to temporary file and compile (optional feature)
    # This requires LaTeX installation on the server
    return jsonify({'success': True, 'message': 'LaTeX content ready for download'})

@app.route('/manage-cvs')
def manage_cvs_page():
    """Page to manage existing CVs"""
    return render_template('manage_cvs.html')

@app.route('/api/cvs', methods=['GET'])
def list_cvs():
    """API endpoint to list all saved CVs"""
    try:
        cv_list = list_cv_data()
        return jsonify({'success': True, 'cvs': cv_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/edit-cv/<cv_id>')
def edit_cv_page(cv_id):
    """Page to edit an existing CV"""
    cv_data = load_cv_data(cv_id)
    if not cv_data:
        return render_template('error.html', error='CV not found'), 404
    
    return render_template('edit_cv.html', cv_id=cv_id, cv_data=cv_data)

@app.route('/api/cv/<cv_id>', methods=['GET'])
def get_cv_data(cv_id):
    """API endpoint to get CV data for editing"""
    try:
        cv_data = load_cv_data(cv_id)
        if not cv_data:
            return jsonify({'success': False, 'error': 'CV not found'}), 404
        
        return jsonify({'success': True, 'cv_data': cv_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cv/<cv_id>', methods=['PUT'])
def update_cv(cv_id):
    """API endpoint to update an existing CV"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        # Validate required fields
        if not data.get('name') or not data.get('email'):
            return jsonify({'success': False, 'error': 'Name and email are required fields'})
        
        # Process the data same as create_cv
        parsed_data = {
            'name': data.get('name', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'linkedin': data.get('linkedin', ''),
            'github': data.get('github', ''),
            'website': data.get('website', ''),
            'address': data.get('address', ''),
            'summary': data.get('summary', ''),
            'education': [],
            'experience': [],
            'projects': [],
            'skills': {
                'languages': [],
                'frameworks': [],
                'tools': [],
                'databases': [],
                'other': []
            },
            'custom_sections': []
        }
        
        # Process education, experience, projects, skills, and custom sections
        # (Same logic as create_cv)
        if data.get('education'):
            for edu in data['education']:
                if edu.get('degree') or edu.get('institution'):
                    parsed_data['education'].append({
                        'degree': edu.get('degree', ''),
                        'institution': edu.get('institution', ''),
                        'date': edu.get('date', ''),
                        'location': edu.get('location', ''),
                        'gpa': edu.get('gpa', ''),
                        'details': edu.get('details', '')
                    })
        
        if data.get('experience'):
            for exp in data['experience']:
                if exp.get('title') or exp.get('company'):
                    description_lines = []
                    if exp.get('description'):
                        description_lines = [line.strip() for line in exp['description'].split('\n') if line.strip()]
                    
                    parsed_data['experience'].append({
                        'title': exp.get('title', ''),
                        'company': exp.get('company', ''),
                        'date': exp.get('date', ''),
                        'location': exp.get('location', ''),
                        'description': description_lines
                    })
        
        if data.get('projects'):
            for proj in data['projects']:
                if proj.get('title'):
                    parsed_data['projects'].append({
                        'title': proj.get('title', ''),
                        'description': proj.get('description', ''),
                        'technologies': proj.get('technologies', ''),
                        'date': proj.get('date', ''),
                        'link': proj.get('link', '')
                    })
        
        if data.get('skills'):
            skills = data['skills']
            for skill_type in ['languages', 'frameworks', 'tools', 'databases', 'other']:
                if skills.get(skill_type):
                    parsed_data['skills'][skill_type] = [
                        item.strip() for item in skills[skill_type].split(',') if item.strip()
                    ]
        
        if data.get('custom'):
            for custom in data['custom']:
                if custom.get('title') and custom.get('content'):
                    parsed_data['custom_sections'].append({
                        'title': custom['title'],
                        'content': custom['content']
                    })
        
        # Update CV data
        success = update_cv_data(cv_id, parsed_data)
        if not success:
            return jsonify({'success': False, 'error': 'Failed to update CV data'})
        
        # Generate new LaTeX content
        latex_content = generate_latex_resume(parsed_data)
        
        # Update files
        latex_filename = f"resume_{cv_id}.tex"
        pdf_filename = f"resume_{cv_id}.pdf"
        
        # Save updated LaTeX file
        latex_path = os.path.join(app.config['OUTPUT_FOLDER'], latex_filename)
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        # Compile to PDF
        pdf_success = compile_latex_to_pdf(latex_content, pdf_filename)
        
        response_data = {
            'success': True,
            'cv_id': cv_id,
            'latex_file': latex_filename,
            'latex_available': True
        }
        
        if pdf_success:
            response_data['pdf_file'] = pdf_filename
        else:
            response_data['pdf_file'] = None
            response_data['warning'] = 'PDF compilation failed. LaTeX source is still available.'
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in update_cv: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cv/<cv_id>', methods=['DELETE'])
def delete_cv(cv_id):
    """Delete a CV"""
    try:
        success = delete_cv_data(cv_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to delete CV'}), 500
    except Exception as e:
        print(f"❌ Error deleting CV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/static/<filename>')
def static_files(filename):
    """Serve static files like images"""
    return send_file(os.path.join('static', filename))

@app.route('/static/temp/<filename>')
def static_temp_files(filename):
    """Serve temporary static files for LaTeX compilation"""
    return send_file(os.path.join('static', 'temp', filename))

@app.route('/debug/system')
def debug_system():
    """Debug endpoint to check system configuration"""
    try:
        import platform
        import shutil
        
        debug_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'current_dir': os.getcwd(),
            'output_folder': app.config.get('OUTPUT_FOLDER', 'Not set'),
            'upload_folder': app.config.get('UPLOAD_FOLDER', 'Not set'),
            'latex_compilation': 'latexonline.cc'
        }
        
        # Check if directories exist
        debug_info['directories'] = {
            'output_exists': os.path.exists(app.config.get('OUTPUT_FOLDER', '')),
            'upload_exists': os.path.exists(app.config.get('UPLOAD_FOLDER', '')),
        }
        
        # LaTeX compilation info
        debug_info['latex'] = {
            'compilation_method': 'latexonline.cc',
            'local_installation_required': False,
            'pdf_generation_available': True
        }
        
        # List files in output directory
        try:
            output_dir = app.config.get('OUTPUT_FOLDER', '')
            if os.path.exists(output_dir):
                debug_info['output_files'] = os.listdir(output_dir)[:10]  # First 10 files
            else:
                debug_info['output_files'] = 'Directory does not exist'
        except Exception as e:
            debug_info['output_files_error'] = str(e)
        
        # Environment variables (non-sensitive)
        debug_info['environment'] = {
            'RENDER': os.getenv('RENDER', 'Not set'),
            'FLASK_ENV': os.getenv('FLASK_ENV', 'Not set'),
            'PATH_latex_locations': [p for p in os.getenv('PATH', '').split(':') if 'tex' in p.lower()][:5]
        }
        
        return jsonify(debug_info)
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()})

@app.route('/debug/test-latex')
def debug_test_latex():
    """Test LaTeX compilation with a simple document"""
    try:
        simple_latex = """
\\documentclass{article}
\\begin{document}
\\title{Test Document}
\\author{System Test}
\\maketitle
This is a test document to verify LaTeX compilation.
\\end{document}
"""
        
        test_filename = f"test_{int(time.time())}.pdf"
        success = compile_latex_to_pdf(simple_latex, test_filename)
        
        result = {
            'compilation_success': success,
            'test_filename': test_filename,
            'timestamp': int(time.time())
        }
        
        if success:
            test_path = os.path.join(app.config['OUTPUT_FOLDER'], test_filename)
            if os.path.exists(test_path):
                result['file_size'] = os.path.getsize(test_path)
                result['download_url'] = f'/download/{test_filename}'
            else:
                result['error'] = 'File compilation reported success but file not found'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()})

@app.route('/debug/test-latex-comprehensive')
def debug_test_latex_comprehensive():
    """Comprehensive LaTeX testing endpoint for deployment debugging"""
    try:
        import platform
        import shutil
        import tempfile
        import glob
        
        debug_info = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'compilation': {
                'method': 'latexonline.cc',
                'local_installation_required': False,
                'pdf_generation_available': True,
            },
            'system': {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'current_dir': os.getcwd(),
                'user': os.getenv('USER', 'unknown'),
                'home': os.getenv('HOME', 'unknown'),
            },
            'latex': {
                'compilation_method': 'latexonline.cc',
                'online_service': True,
                'local_installation': 'not required',
            },
            'directories': {
                'output_exists': os.path.exists(app.config.get('OUTPUT_FOLDER', '')),
                'upload_exists': os.path.exists(app.config.get('UPLOAD_FOLDER', '')),
                'tmp_writable': os.access('/tmp', os.W_OK),
            },
            'files': {
                'build_files': []
            },
            'environment': {
                'render': os.getenv('RENDER'),
                'debian_frontend': os.getenv('DEBIAN_FRONTEND'),
                'texmfcache': os.getenv('TEXMFCACHE'),
            }
        }
        
        # Check for build-related files
        build_files = glob.glob('*.log') + glob.glob('*.txt') + glob.glob('build.*')
        debug_info['files']['build_files'] = build_files[:10]  # Limit to first 10
        
        # Test online LaTeX compilation
        debug_info['latex']['compilation_test'] = test_latex_compilation()
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/debug/latex-warning')
def debug_latex_warning():
    """Show LaTeX compilation information"""
    try:
        info = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'compilation_method': 'latexonline.cc',
            'latex_available': True,
            'local_installation_required': False,
            'status': 'PDF generation available via latexonline.cc'
        }
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

def test_latex_compilation():
    """Test LaTeX compilation with a simple document"""
    try:
        test_latex = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\begin{document}
\title{Test Document}
\author{CVLatex Test}
\date{\today}
\maketitle

This is a test document to verify LaTeX compilation works correctly.

\section{Introduction}
If you can see this PDF, LaTeX compilation is working.

\end{document}
"""
        
        filename = f"test_{uuid.uuid4().hex}.pdf"
        success = compile_latex_to_pdf(test_latex, filename)
        return {
            'status': 'success' if success else 'failed',
            'output_file': filename,
        }
            
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }

@app.route('/api/generate-from-preview', methods=['POST'])
def generate_from_preview():
    """Generate LaTeX and PDF from preview CV data"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        updated_cv_data = data.get('cv_data')
        
        if not session_id or not updated_cv_data:
            return jsonify({'error': 'Missing session ID or CV data'}), 400
        
        # Load original session data for metadata
        import json
        import os
        session_file = os.path.join('temp_sessions', f'{session_id}.json')
        
        if not os.path.exists(session_file):
            return jsonify({'error': 'Session not found or expired'}), 404
        
        with open(session_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        mode = original_data.get('mode', 'professional')
        original_filename = original_data.get('original_filename', 'resume')
        
        # Generate LaTeX
        latex_content = generate_latex_resume(updated_cv_data)
        
        # Save LaTeX file
        base_filename = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
        mode_suffix = "_tailored" if mode == 'tailored' else "_professional"
        latex_filename = f"{base_filename}{mode_suffix}_resume.tex"
        latex_path = os.path.join(app.config['OUTPUT_FOLDER'], latex_filename)
        
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        print(f"Generated LaTeX saved to: {latex_path}")
        print("=== GENERATED LATEX CONTENT (first 500 chars) ===")
        print(latex_content[:500] + "..." if len(latex_content) > 500 else latex_content)
        
        # Compile to PDF
        pdf_filename = f"{base_filename}{mode_suffix}_resume.pdf"
        pdf_compiled = compile_latex_to_pdf(latex_content, pdf_filename)
        
        # Clean up session file
        try:
            if os.path.exists(session_file):
                os.remove(session_file)
                print(f"✅ Cleaned up session file: {session_file}")
        except Exception as cleanup_error:
            print(f"⚠️ Could not clean up session file: {cleanup_error}")
            # Don't let cleanup errors affect the main response
        
        response_data = {
            'success': True,
            'mode': mode,
            'latex_content': latex_content,
            'latex_download_url': f'/download/{latex_filename}',
            'pdf_compiled': pdf_compiled,
            'latex_available': True,
            'latex_filename': latex_filename,
            'pdf_filename': pdf_filename if pdf_compiled else None
        }
        
        if pdf_compiled:
            response_data.update({
                'pdf_download_url': f'/download/{pdf_filename}',
                'pdf_preview_url': f'/preview/{pdf_filename}'
            })
        else:
            response_data['warning'] = 'PDF compilation failed via latexonline.cc. LaTeX source is still available for download.'
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in generate_from_preview: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/generate-job-desc', methods=['POST'])
def generate_job_desc():
    data = request.get_json()
    role = data.get('role', '').strip()
    if not role:
        return jsonify({'error': 'No role provided'}), 400
    
    # Create cache key for the role
    import hashlib
    cache_key = hashlib.md5(role.lower().encode()).hexdigest()
    
    # Check if we have cached JD for this role
    if cache_key in jd_cache:
        print(f"🎯 Using cached job description for role: {role}")
        return jsonify({'description': jd_cache[cache_key]})
    
    print(f"🔄 Generating new job description for role: {role}")
    
    prompt = f"""
Write a professional job description for the role of '{role}'. The description should be suitable for a resume or job application and include key responsibilities, required skills, and qualifications. Be concise and relevant to modern industry standards.
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyANT0edzcgHlcS-4tOLKVY8XKjYYrswVEM"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [
            {"parts": [
                {"text": prompt}
            ]}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            desc = result['candidates'][0]['content']['parts'][0]['text']
            
            # Cache the result
            jd_cache[cache_key] = desc
            print(f"💾 Cached job description for role: {role}")
            
            return jsonify({'description': desc})
        else:
            return jsonify({'error': 'Gemini API error', 'details': response.text}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/review-cv', methods=['POST'])
def review_cv():
    data = request.get_json()
    cv_text = data.get('cv_text')
    if not cv_text:
        return jsonify({'error': 'Missing CV text'}), 400
    
    # Generate or get session ID
    if 'session_id' not in session:
        import uuid
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']
    
    # Get review data from Gemini
    review_data = review_cv_with_gemini(cv_text)
    
    # Store review data and CV text for improved resume generation
    stored_review_data[session_id] = review_data
    stored_cv_text[session_id] = cv_text
    
    print(f"📝 Stored review data for session: {session_id}")
    print(f"🔗 Redirect URL: /review/{session_id}")
    
    # Return success with redirect URL
    return jsonify({
        'success': True,
        'review_data': review_data,
        'redirect_url': f'/review/{session_id}'
    })

@app.route('/review/<session_id>')
def show_review(session_id):
    """Display the review page for a specific session"""
    review_data = stored_review_data.get(session_id)
    if not review_data:
        flash('Review data not found. Please upload and review a CV first.', 'error')
        return redirect(url_for('upload_file'))
    
    return render_template('review.html', review_data=review_data)

def review_cv_with_gemini(cv_text):
    prompt = f"""
Analyze the following CV and provide a detailed review. Return your response as a valid JSON object with exactly these keys:

{{
  "strengths": ["strength1", "strength2", "strength3"],
  "weaknesses": ["weakness1", "weakness2", "weakness3"],
  "suggestions": ["suggestion1", "suggestion2", "suggestion3"],
  "rating": 85
}}

Requirements:
- strengths: List of 3-5 positive aspects of the CV
- weaknesses: List of 3-5 areas that need improvement
- suggestions: List of 3-5 specific actionable recommendations
- rating: Numeric score from 0-100 (integer only) - Evaluate based on: content quality, formatting, completeness, relevance, clarity, and professional presentation. Be authentic and vary the score based on actual CV quality.

Scoring Guidelines:
- 90-100: Exceptional CV with excellent content, perfect formatting, strong achievements with metrics, complete sections
- 80-89: Very good CV with solid content, good formatting, most important sections covered, some quantified achievements
- 70-79: Good CV with decent content, acceptable formatting, basic sections present, could use more specific achievements
- 60-69: Average CV with basic content, some formatting issues, missing some important elements
- 50-59: Below average CV with limited content, poor formatting, significant gaps or issues
- 40-49: Poor CV with major deficiencies in content, structure, or presentation
- Below 40: Very poor CV requiring substantial improvement

CV Text:
{cv_text}

Return only the JSON object, no additional text or formatting:
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            generated_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            
            print(f"🤖 Gemini response: {generated_text[:200]}...")
            
            # Clean up the response - remove markdown formatting
            if generated_text.startswith('```json'):
                generated_text = generated_text.replace('```json', '').replace('```', '').strip()
            elif generated_text.startswith('```'):
                generated_text = generated_text.replace('```', '').strip()
            
            # Extract JSON from the response
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_text = generated_text[json_start:json_end]
                
                try:
                    parsed_data = json.loads(json_text)
                    
                    # Validate the structure
                    if all(key in parsed_data for key in ['strengths', 'weaknesses', 'suggestions', 'rating']):
                        # Ensure rating is an integer
                        if isinstance(parsed_data['rating'], str):
                            parsed_data['rating'] = int(''.join(filter(str.isdigit, parsed_data['rating'])))
                        
                        print(f"✅ Successfully parsed CV review with rating: {parsed_data['rating']}")
                        return parsed_data
                    else:
                        print("⚠️ Missing required keys in JSON response")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing error: {e}")
                    print(f"Raw JSON text: {json_text[:500]}...")
            else:
                print("⚠️ No valid JSON found in response")
        else:
            print(f"❌ Gemini API error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error calling Gemini API: {e}")
    
    # Return default values if parsing fails
    print("🔄 Returning default review data due to parsing failure")
    return {
        "strengths": [
            "Professional presentation",
            "Relevant experience listed",
            "Contact information provided"
        ],
        "weaknesses": [
            "Could benefit from more specific achievements",
            "Skills section could be more detailed",
            "Missing quantifiable results"
        ],
        "suggestions": [
            "Add specific metrics and achievements",
            "Improve formatting and structure",
            "Include more relevant keywords",
            "Expand on technical skills",
            "Add professional summary"
        ],
        "rating": 68
    }

# Global storage for session data (in production, use Redis or database)
stored_review_data = {}
stored_cv_text = {}
jd_cache = {}  # Cache for job descriptions

@app.route('/api/generate-improved-resume', methods=['POST'])
def generate_improved_resume():
    """Generate an improved resume using Gemini AI based on review suggestions and 1.tex template"""
    try:
        # Get session ID from Flask session or generate a new one
        session_id = session.get('session_id')
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            print(f"🆔 Generated new session ID: {session_id}")
        
        # Get stored review data and CV text
        review_data = stored_review_data.get(session_id)
        cv_text = stored_cv_text.get(session_id)
        
        if not review_data or not cv_text:
            # Try to provide a helpful error message and redirect
            return jsonify({
                'error': 'No review data found. Please upload and review a CV first.',
                'redirect': '/upload'
            }), 400
        
        print(f"🔄 Generating improved resume for session: {session_id}")
        
        # Read the 1.tex template
        template_path = '1.tex'
        if not os.path.exists(template_path):
            return jsonify({'error': '1.tex template file not found'}), 500
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Create improvement prompt for Gemini
        suggestions_text = '\n'.join([f"- {suggestion}" for suggestion in review_data.get('suggestions', [])])
        weaknesses_text = '\n'.join([f"- {weakness}" for weakness in review_data.get('weaknesses', [])])
        
        prompt = f"""
You are an expert resume writer. I need you to create an improved LaTeX resume based on the following:

ORIGINAL CV TEXT:
{cv_text}

REVIEW SUGGESTIONS:
{suggestions_text}

WEAKNESSES TO ADDRESS:
{weaknesses_text}

LATEX TEMPLATE TO FOLLOW:
{template_content}

INSTRUCTIONS:
1. Use the provided LaTeX template structure and formatting
2. Improve the CV content based on the suggestions and weaknesses identified
3. DO NOT make up fake information - only enhance and reorganize existing content
4. Improve wording, structure, and presentation while keeping all information truthful
5. Follow the exact LaTeX structure from the template
6. Return ONLY the complete LaTeX code, no explanations

Generate the improved LaTeX resume:
"""

        # Call Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }
        
        print("🤖 Calling Gemini API for improved resume generation...")
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ Gemini API error: {response.status_code} - {response.text}")
            return jsonify({'error': f'Gemini API error: {response.status_code}'}), 500
        
        result = response.json()
        improved_latex = result['candidates'][0]['content']['parts'][0]['text']
        
        # Clean up the LaTeX content (remove markdown formatting if present)
        if improved_latex.startswith('```latex'):
            improved_latex = improved_latex.replace('```latex', '').replace('```', '').strip()
        elif improved_latex.startswith('```'):
            improved_latex = improved_latex.replace('```', '').strip()
        
        print("✅ Improved LaTeX generated successfully")
        
        # Generate unique filename using session_id
        latex_filename = f"improved_resume_{session_id}.tex"
        pdf_filename = f"improved_resume_{session_id}.pdf"
        
        # Save LaTeX file
        latex_path = os.path.join(app.config['OUTPUT_FOLDER'], latex_filename)
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write(improved_latex)
        
        print(f"💾 Saved improved LaTeX to: {latex_path}")
        
        # Compile to PDF
        print("🔨 Compiling LaTeX to PDF...")
        pdf_compiled = compile_latex_to_pdf(improved_latex, pdf_filename)
        
        if pdf_compiled:
            print("✅ PDF compilation successful")
        else:
            print("⚠️ PDF compilation failed, but LaTeX is available")
        
        # Calculate new score using Gemini
        print("📊 Calculating improved score...")
        score_prompt = f"""
Rate this improved resume on a scale of 0-100 based on professional standards, clarity, and impact.
Consider: formatting, content quality, relevance, and overall presentation.
Return only the numeric score (e.g., 85).

Resume content:
{improved_latex}
"""
        
        score_payload = {
            "contents": [
                {"parts": [{"text": score_prompt}]}
            ]
        }
        
        score_response = requests.post(url, headers=headers, json=score_payload, timeout=30)
        new_score = 85  # Default score
        
        if score_response.status_code == 200:
            try:
                score_result = score_response.json()
                score_text = score_result['candidates'][0]['content']['parts'][0]['text'].strip()
                new_score = int(''.join(filter(str.isdigit, score_text)))
                if new_score > 100:
                    new_score = 100
                elif new_score < 0:
                    new_score = 0
            except:
                new_score = 85
        
        print(f"📈 New score calculated: {new_score}")
        
        # Store improved resume data
        improved_data = {
            'latex_content': improved_latex,
            'latex_filename': latex_filename,
            'pdf_filename': pdf_filename if pdf_compiled else None,
            'pdf_compiled': pdf_compiled,
            'original_score': review_data.get('rating', 0),
            'new_score': new_score,
            'improvements': review_data.get('suggestions', [])[:5],  # Top 5 improvements
            'session_id': session_id
        }
        
        # Store in session for the preview page
        stored_improved_data = getattr(app, '_stored_improved_data', {})
        stored_improved_data[session_id] = improved_data
        app._stored_improved_data = stored_improved_data
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'latex_filename': latex_filename,
            'pdf_filename': pdf_filename if pdf_compiled else None,
            'pdf_compiled': pdf_compiled,
            'original_score': review_data.get('rating', 0),
            'new_score': new_score
        })
        
    except Exception as e:
        print(f"❌ Error in generate_improved_resume: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/improved-resume-preview/<session_id>')
def improved_resume_preview(session_id):
    """Show the improved resume preview page"""
    try:
        # Try to get data from app storage first
        stored_improved_data = getattr(app, '_stored_improved_data', {})
        improved_data = stored_improved_data.get(session_id)
        
        if not improved_data:
            # Try to reconstruct data from files if they exist
            output_files = os.listdir(app.config['OUTPUT_FOLDER'])
            latex_files = [f for f in output_files if f.startswith(f'improved_resume_') and f.endswith('.tex') and session_id in f]
            pdf_files = [f for f in output_files if f.startswith(f'improved_resume_') and f.endswith('.pdf') and session_id in f]
            
            if latex_files:
                latex_filename = latex_files[0]
                pdf_filename = pdf_files[0] if pdf_files else None
                
                # Read latex content
                latex_path = os.path.join(app.config['OUTPUT_FOLDER'], latex_filename)
                with open(latex_path, 'r', encoding='utf-8') as f:
                    latex_content = f.read()
                
                # Create minimal data structure
                improved_data = {
                    'latex_content': latex_content,
                    'latex_filename': latex_filename,
                    'pdf_filename': pdf_filename,
                    'pdf_compiled': pdf_filename is not None,
                    'original_score': 0,
                    'new_score': 85,
                    'improvements': ['Resume has been improved based on AI analysis'],
                    'session_id': session_id
                }
            else:
                return "Session not found or expired. Please generate a new improved resume.", 404
        
        # Check if template exists
        template_path = os.path.join('templates', 'improved_resume_preview.html')
        if not os.path.exists(template_path):
            return f"""
            <html>
            <head><title>Improved Resume</title></head>
            <body>
                <h1>Improved Resume Generated</h1>
                <p>Session ID: {session_id}</p>
                <p>LaTeX file: <a href="/view-improved/{session_id}/{improved_data.get('latex_filename', 'N/A')}">{improved_data.get('latex_filename', 'N/A')}</a></p>
                {f'<p>PDF file: <a href="/view-improved/{session_id}/{improved_data.get("pdf_filename", "N/A")}">{improved_data.get("pdf_filename", "N/A")}</a></p>' if improved_data.get('pdf_compiled') else '<p>PDF compilation failed</p>'}
                <p><a href="/upload">Upload New CV</a> | <a href="/">Home</a></p>
            </body>
            </html>
            """, 200
        
        # Remove session_id from improved_data to avoid duplicate keyword argument
        template_data = improved_data.copy()
        template_data.pop('session_id', None)
        
        # Add pdf_available for template compatibility
        template_data['pdf_available'] = template_data.get('pdf_compiled', False)
        
        # Ensure all required variables are present
        if 'original_score' not in template_data:
            template_data['original_score'] = 0
        if 'new_score' not in template_data:
            template_data['new_score'] = 85
        
        # Add improved_score as alias for new_score (for compatibility)
        template_data['improved_score'] = template_data['new_score']
        
        # Debug: Print template data
        print(f"🔍 Template data keys: {list(template_data.keys())}")
        print(f"🔍 Template data: {template_data}")
        
        # Write debug info to file
        with open('debug_template_data.txt', 'w') as f:
            f.write(f"Session ID: {session_id}\n")
            f.write(f"Template data keys: {list(template_data.keys())}\n")
            f.write(f"Template data: {template_data}\n")
        
        return render_template('improved_resume_preview.html', 
                             session_id=session_id,
                             **template_data)
    except Exception as e:
        print(f"Error in improved_resume_preview: {str(e)}")
        traceback.print_exc()
        return f"Error loading improved resume: {str(e)}", 500

@app.route('/view-improved/<session_id>/<filename>')
def view_improved_file(session_id, filename):
    """Serve improved resume files for inline viewing"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if not os.path.exists(file_path):
            return "File not found", 404
        
        if filename.endswith('.pdf'):
            return send_file(file_path, mimetype='application/pdf')
        elif filename.endswith('.tex'):
            return send_file(file_path, mimetype='text/plain')
        else:
            return send_file(file_path)
    except Exception as e:
        print(f"Error serving file: {e}")
        return "Error serving file", 500

@app.route('/download-improved/<session_id>/<filename>')
def download_improved_file(session_id, filename):
    """Download improved resume files"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if not os.path.exists(file_path):
            return "File not found", 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        print(f"Error downloading file: {e}")
        return "Error downloading file", 500

@app.route('/debug/test-improved-resume')
def debug_test_improved_resume():
    """Debug endpoint to test improved resume generation"""
    try:
        # Create a test session
        import uuid
        test_session_id = str(uuid.uuid4())
        
        # Create dummy review data
        test_review_data = {
            'rating': 65,
            'strengths': ['Good technical skills', 'Clear formatting'],
            'weaknesses': ['Lacks quantified achievements', 'Missing keywords'],
            'suggestions': ['Add metrics to achievements', 'Include relevant keywords', 'Improve summary section']
        }
        
        test_cv_text = """
        John Doe
        Software Engineer
        
        Experience:
        - Software Developer at Tech Company (2020-2023)
        - Developed web applications
        - Worked with team
        
        Education:
        - Bachelor's in Computer Science
        
        Skills:
        - Python, JavaScript, HTML, CSS
        """
        
        # Store test data
        stored_review_data[test_session_id] = test_review_data
        stored_cv_text[test_session_id] = test_cv_text
        
        return f"""
        <html>
        <head><title>Test Improved Resume Generation</title></head>
        <body>
            <h1>Test Improved Resume Generation</h1>
            <p>Test session created: {test_session_id}</p>
            <p>Review data stored: {test_review_data}</p>
            <p>CV text stored: {len(test_cv_text)} characters</p>
            
            <button onclick="testGeneration()">Test Generate Improved Resume</button>
            
            <div id="result"></div>
            
            <script>
            async function testGeneration() {{
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = 'Testing...';
                
                try {{
                    // Set session
                    await fetch('/debug/set-test-session/{test_session_id}');
                    
                    // Call generate API
                    const response = await fetch('/api/generate-improved-resume', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}}
                    }});
                    
                    const result = await response.json();
                    resultDiv.innerHTML = '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
                    
                    if (result.success) {{
                        resultDiv.innerHTML += '<p><a href="/improved-resume-preview/' + result.session_id + '">View Preview</a></p>';
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = 'Error: ' + error.message;
                }}
            }}
            </script>
        </body>
        </html>
        """
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/debug/set-test-session/<session_id>')
def set_test_session(session_id):
    """Set test session ID"""
    session['session_id'] = session_id
    return jsonify({'success': True, 'session_id': session_id})

@app.route('/debug/test-template')
def debug_test_template():
    """Test the improved resume preview template with dummy data"""
    test_data = {
        'latex_content': 'Test LaTeX content',
        'latex_filename': 'test.tex',
        'pdf_filename': 'test.pdf',
        'pdf_compiled': True,
        'pdf_available': True,
        'original_score': 68,
        'new_score': 85,
        'improvements': ['Test improvement 1', 'Test improvement 2'],
    }
    
    return render_template('improved_resume_preview.html', 
                         session_id='test-session',
                         **test_data)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
