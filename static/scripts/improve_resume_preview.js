
        function switchTab(tabName) {
            document.querySelectorAll('.preview-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');

            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            document.getElementById(tabName + '-tab').classList.add('active');

            if (tabName === 'latex') {
                loadLatexContent();
            }
        }

        function loadLatexContent() {
            const latexContent = document.getElementById('latex-content');
            const latexLoading = document.getElementById('latex-loading');
            
            if (latexContent.textContent.trim() === '') {
                fetch('/view-improved/{{ session_id }}/{{ latex_filename }}')
                    .then(response => response.text())
                    .then(data => {
                        latexContent.textContent = data;
                        latexLoading.style.display = 'none';
                        latexContent.style.display = 'block';
                    })
                    .catch(error => {
                        console.error('Error loading LaTeX:', error);
                        latexContent.textContent = 'Error loading LaTeX content.';
                        latexLoading.style.display = 'none';
                        latexContent.style.display = 'block';
                    });
            } else {
                latexLoading.style.display = 'none';
                latexContent.style.display = 'block';
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            if (typeof window.pdf_available === "undefined" || !window.pdf_available) {
                loadLatexContent();
            }
        });

        // Function to hide PDF loading state
        function hidePdfLoading() {
            const pdfLoading = document.getElementById('pdf-loading');
            const pdfViewer = document.querySelector('.pdf-viewer');
            
            if (pdfLoading) {
                pdfLoading.style.display = 'none';
            }
            if (pdfViewer) {
                pdfViewer.style.display = 'block';
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            const scoreValues = document.querySelectorAll('.score-value');
            scoreValues.forEach(score => {
                const finalValue = parseInt(score.textContent);
                let currentValue = 0;
                const increment = finalValue / 30;
                
                const timer = setInterval(() => {
                    currentValue += increment;
                    if (currentValue >= finalValue) {
                        score.textContent = finalValue;
                        clearInterval(timer);
                    } else {
                        score.textContent = Math.floor(currentValue);
                    }
                }, 50);
            });
        });
