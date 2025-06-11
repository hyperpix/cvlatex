#!/usr/bin/env python3
"""
Test script for Pastebin URL compilation method
"""

import requests
import time
import os

# Test configuration
PASTEBIN_API_KEY = "1_J_KOk9b1JXrVXtA0o62dYW9osTWI5n"
PASTEBIN_API_URL = "https://pastebin.com/api/api_post.php"
LATEXONLINE_URL = "https://latexonline.cc/compile"

def test_fixed_latex_template():
    """Test with the fixed LaTeX template (no problematic commands)"""
    
    # Fixed LaTeX template without problematic commands
    latex_content = r"""
%-------------------------
% Resume in Latex - Fixed for latexonline.cc
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

% Sections formatting - FIXED: removed \scshape, added \bfseries
\titleformat{\section}{
  \vspace{-4pt}\raggedright\large\bfseries
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

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

\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\begin{document}

% FIXED: removed \scshape from name heading
\begin{center}
    \textbf{\Huge Test Resume} \\ \vspace{1pt}
    \small test@email.com $|$ 123-456-7890
\end{center}

\section{Education}
\begin{itemize}
    \resumeItem{Test University - Computer Science Degree}
\end{itemize}

\section{Experience}
\begin{itemize}
    \resumeItem{Software Developer - Test Company}
    \resumeItem{Developed web applications using modern frameworks}
\end{itemize}

\section{Skills}
\begin{itemize}
    \resumeItem{\textbf{Languages}: Python, JavaScript, Java}
    \resumeItem{\textbf{Frameworks}: React, Flask, Django}
\end{itemize}

\end{document}
"""
    
    print("🧪 Testing Pastebin URL compilation method...")
    print(f"📄 LaTeX content length: {len(latex_content)} characters")
    
    # Step 1: Create Pastebin paste
    print("\n📋 Step 1: Creating Pastebin paste...")
    pastebin_data = {
        'api_dev_key': PASTEBIN_API_KEY,
        'api_option': 'paste',
        'api_paste_code': latex_content,
        'api_paste_name': 'LaTeX Resume Test',
        'api_paste_expire_date': '10M',  # 10 minutes
        'api_paste_private': '0',  # Public
        'api_paste_format': 'latex'
    }
    
    try:
        response = requests.post(PASTEBIN_API_URL, data=pastebin_data, timeout=30)
        
        if response.status_code == 200 and response.text.startswith('https://pastebin.com/'):
            paste_url = response.text.strip()
            paste_id = paste_url.split('/')[-1]
            raw_url = f"https://pastebin.com/raw/{paste_id}"
            
            print(f"✅ Pastebin paste created successfully")
            print(f"🔗 Paste URL: {paste_url}")
            print(f"📄 Raw URL: {raw_url}")
            
            # Step 2: Wait a moment for the paste to be available
            print("\n⏳ Waiting 2 seconds for paste to be available...")
            time.sleep(2)
            
            # Step 3: Test latexonline.cc with URL method
            print("\n🌐 Step 2: Testing latexonline.cc URL compilation...")
            latex_params = {'url': raw_url}
            
            latex_response = requests.get(LATEXONLINE_URL, params=latex_params, timeout=60)
            
            print(f"📊 latexonline.cc response: {latex_response.status_code}")
            
            if latex_response.status_code == 200:
                # Save the PDF
                output_filename = "test_pastebin_fixed_template.pdf"
                with open(output_filename, 'wb') as f:
                    f.write(latex_response.content)
                
                pdf_size = len(latex_response.content)
                print(f"✅ PDF generated successfully!")
                print(f"📁 Saved as: {output_filename}")
                print(f"📏 PDF size: {pdf_size:,} bytes ({pdf_size/1024:.1f} KB)")
                
                return True
                
            else:
                print(f"❌ latexonline.cc compilation failed")
                print(f"📄 Response: {latex_response.text[:500]}...")
                return False
                
        else:
            print(f"❌ Pastebin paste creation failed")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        return False

def test_fixed_1tex_template():
    """Test with the actual fixed 1.tex template"""
    
    print("\n🧪 Testing with fixed 1.tex template...")
    
    # Read the fixed 1.tex template
    if not os.path.exists('1.tex'):
        print("❌ 1.tex file not found")
        return False
    
    with open('1.tex', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    print(f"📄 Template content length: {len(template_content)} characters")
    
    # Check for problematic commands
    problems = []
    if '\\input{glyphtounicode}' in template_content:
        problems.append('\\input{glyphtounicode}')
    if '\\pdfgentounicode=1' in template_content:
        problems.append('\\pdfgentounicode=1')
    if '\\scshape' in template_content:
        problems.append('\\scshape')
    
    if problems:
        print(f"❌ Template still contains problematic commands: {problems}")
        return False
    else:
        print("✅ Template is clean - no problematic commands found")
    
    # Test the template with Pastebin
    print("\n📋 Creating Pastebin paste with 1.tex template...")
    pastebin_data = {
        'api_dev_key': PASTEBIN_API_KEY,
        'api_option': 'paste',
        'api_paste_code': template_content,
        'api_paste_name': 'Fixed 1.tex Template Test',
        'api_paste_expire_date': '10M',
        'api_paste_private': '0',
        'api_paste_format': 'latex'
    }
    
    try:
        response = requests.post(PASTEBIN_API_URL, data=pastebin_data, timeout=30)
        
        if response.status_code == 200 and response.text.startswith('https://pastebin.com/'):
            paste_url = response.text.strip()
            paste_id = paste_url.split('/')[-1]
            raw_url = f"https://pastebin.com/raw/{paste_id}"
            
            print(f"✅ Pastebin paste created successfully")
            print(f"🔗 Paste URL: {paste_url}")
            print(f"📄 Raw URL: {raw_url}")
            
            # Wait and test compilation
            print("\n⏳ Waiting 2 seconds for paste to be available...")
            time.sleep(2)
            
            print("\n🌐 Testing latexonline.cc URL compilation...")
            latex_params = {'url': raw_url}
            
            latex_response = requests.get(LATEXONLINE_URL, params=latex_params, timeout=60)
            
            print(f"📊 latexonline.cc response: {latex_response.status_code}")
            
            if latex_response.status_code == 200:
                output_filename = "test_1tex_fixed_template.pdf"
                with open(output_filename, 'wb') as f:
                    f.write(latex_response.content)
                
                pdf_size = len(latex_response.content)
                print(f"✅ PDF generated successfully!")
                print(f"📁 Saved as: {output_filename}")
                print(f"📏 PDF size: {pdf_size:,} bytes ({pdf_size/1024:.1f} KB)")
                
                return True
                
            else:
                print(f"❌ latexonline.cc compilation failed")
                print(f"📄 Response: {latex_response.text[:500]}...")
                return False
                
        else:
            print(f"❌ Pastebin paste creation failed")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Pastebin URL compilation method with fixed LaTeX templates")
    print("=" * 60)
    
    # Test 1: Custom fixed template
    success1 = test_fixed_latex_template()
    
    print("\n" + "=" * 60)
    
    # Test 2: Fixed 1.tex template
    success2 = test_fixed_1tex_template()
    
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print(f"✅ Custom fixed template: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Fixed 1.tex template: {'PASSED' if success2 else 'FAILED'}")
    
    if success1 and success2:
        print("\n🎉 All tests PASSED! Pastebin URL method is working with fixed templates.")
    else:
        print("\n❌ Some tests FAILED. Check the output above for details.") 