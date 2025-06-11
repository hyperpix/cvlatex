# CV to LaTeX Converter

A modern web application that converts CV files (PDF/DOCX) to LaTeX format using Jake's Resume template. Upload your CV and get a professionally formatted LaTeX file ready for compilation or use in Overleaf.

![CV to LaTeX Converter](https://img.shields.io/badge/Built%20with-Flask-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.7+-brightgreen)

## 🚀 Features

- **Multi-Page Flow**: Professional landing page → upload → processing → results
- **AI-Powered Parsing**: Uses Google Gemini AI for intelligent CV text extraction and structuring
- **File Upload Support**: PDF and DOCX file formats with drag & drop interface
- **Smart Text Extraction**: Automatically extracts text from uploaded documents
- **Jake's Resume Template**: Converts to the most popular LaTeX resume template
- **PDF Compilation**: Automatic LaTeX to PDF compilation with instant preview
- **Real-time Processing**: Live progress tracking with visual feedback
- **Download Options**: Get both LaTeX source code and compiled PDF
- **Mobile Friendly**: Responsive design works on all devices
- **Modern UI/UX**: Beautiful, intuitive interface with animations

## 🛠️ Installation

### Prerequisites

- Python 3.7+
- pip (Python package installer)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CVLatex
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment file (optional)**
   ```bash
   cp .env.example .env
   # Edit .env if you want to use OpenAI API for enhanced parsing
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## 📋 Usage

1. **Landing Page**: Visit the homepage and click "Start Converting Now"
2. **Upload your CV**: Drag and drop or browse for your PDF or DOCX CV file
3. **AI Processing**: Gemini AI extracts and structures your CV information
4. **LaTeX Generation**: Automatic conversion to Jake's Resume template
5. **PDF Compilation**: Instant PDF generation with live preview
6. **Download**: Get both LaTeX source code and compiled PDF file

## 📁 Project Structure

```
CVLatex/
├── app.py              # Main Flask application with AI integration
├── requirements.txt    # Python dependencies
├── README.md          # Project documentation
├── .env.example       # Environment variables template
├── resume.tex         # Sample Jake's Resume template
├── templates/
│   ├── landing.html   # Landing page
│   ├── upload.html    # Upload page with drag & drop
│   ├── result.html    # Results page with PDF preview
│   └── index.html     # Original interface (legacy)
├── uploads/           # Temporary upload folder (auto-created)
├── output/            # Generated LaTeX and PDF files (auto-created)
├── test_gemini.py     # Gemini AI integration test
└── test_app.py        # Application functionality test
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Gemini AI API key for CV parsing (recommended for best results)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: OpenAI API key for enhanced text processing
OPENAI_API_KEY=your_openai_api_key_here

# Flask configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### Customization

You can customize the LaTeX template by modifying the `generate_latex_resume()` function in `app.py`. The template is based on Jake's Resume and includes:

- Clean, professional layout
- ATS-friendly formatting
- Sections for education, experience, projects, and skills
- Customizable styling

## 📝 Jake's Resume Template

This application uses the popular Jake's Resume LaTeX template, which features:

- **Clean Design**: Professional and modern appearance
- **ATS Compatible**: Optimized for Applicant Tracking Systems
- **Customizable**: Easy to modify sections and styling
- **Popular**: Widely used and recognized template
- **Open Source**: MIT licensed template

Original template by Jake Gutierrez: [GitHub Repository](https://github.com/jakegut/resume)

## 🧠 Text Parsing Features

The application intelligently parses CV content to extract:

### Contact Information
- Full name
- Email address
- Phone number
- LinkedIn profile
- GitHub profile

### Education
- Degree information
- Institution names
- Graduation dates
- GPA (if present)

### Work Experience
- Job titles
- Company names
- Employment dates
- Job descriptions

### Projects
- Project names
- Technologies used
- Descriptions

### Skills
- Programming languages
- Frameworks and libraries
- Tools and software
- Technical skills

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (Optional)
Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Jake Gutierrez](https://github.com/jakegut) for the original LaTeX resume template
- Flask community for the excellent web framework
- All contributors and users of this project

## 🐛 Known Issues & Limitations

- Complex PDF layouts may not parse perfectly
- Some formatting might be lost during text extraction
- Large files (>16MB) are not supported
- LaTeX compilation requires a LaTeX distribution (not included)

## 🔮 Future Enhancements

- [ ] PDF compilation service
- [ ] Multiple template options
- [ ] Advanced AI-powered parsing
- [ ] Batch processing
- [ ] Template customization interface
- [ ] Export to other formats

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) section
2. Create a new issue with detailed information
3. Contact the maintainers

---

**Made with ❤️ for the developer community** 