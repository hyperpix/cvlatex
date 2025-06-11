
        document.addEventListener('DOMContentLoaded', function() {
            const urlParams = new URLSearchParams(window.location.search);
            
            const pdfUrl = urlParams.get('pdf') || (urlParams.get('pdf_file') ? `/preview/${urlParams.get('pdf_file')}` : null);
            const latexUrl = (urlParams.get('latex') ? `/download/${urlParams.get('latex')}` : null) || 
                    (urlParams.get('latex_file') ? `/download/${urlParams.get('latex_file')}` : null);
            
            const pdfDownloadUrl = (urlParams.get('pdf') ? `/download/${urlParams.get('pdf')}` : null) || 
                    urlParams.get('pdf_download') || 
                    (urlParams.get('pdf_file') ? `/download/${urlParams.get('pdf_file')}` : null);

            console.log('URL Parameters:', {
                pdf: urlParams.get('pdf'),
                latex: urlParams.get('latex'),
                pdf_download: urlParams.get('pdf_download'),
                pdf_file: urlParams.get('pdf_file'),
                latex_file: urlParams.get('latex_file')
            });

            console.log('Resolved URLs:', {
                pdfUrl,
                latexUrl,
                pdfDownloadUrl
            });

            if (pdfUrl) {
                const pdfViewer = document.getElementById('pdfViewer');
                pdfViewer.innerHTML = `<iframe src="/preview/${urlParams.get('pdf')}" width="100%" height="100%" frameborder="0"></iframe>`;
            }

            if (pdfDownloadUrl) {
                const pdfDownloadBtn = document.getElementById('pdfDownloadBtn');
                pdfDownloadBtn.href = pdfDownloadUrl;
                pdfDownloadBtn.addEventListener('click', function(e) {
                    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Downloading...';
                    setTimeout(() => {
                        this.innerHTML = '<i class="fas fa-check"></i> Downloaded!';
                        setTimeout(() => {
                            this.innerHTML = '<i class="fas fa-download"></i> Download PDF';
                        }, 2000);
                    }, 1000);
                });
            } else {
                const pdfDownloadBtn = document.getElementById('pdfDownloadBtn');
                pdfDownloadBtn.style.opacity = '0.5';
                pdfDownloadBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> PDF not available';
                pdfDownloadBtn.onclick = function(e) {
                    e.preventDefault();
                    alert('PDF compilation failed on the server. This might be due to missing LaTeX packages.\n\nYou can:\n1. Download the LaTeX source and compile it locally\n2. Use Overleaf to compile the LaTeX code\n3. Contact support if this issue persists');
                };
                
                const pdfViewer = document.getElementById('pdfViewer');
                pdfViewer.innerHTML = `
                    <div class="no-preview">
                        <div class="no-preview-icon">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <h4>PDF Compilation Failed</h4>
                        <p>The LaTeX source was generated successfully, but PDF compilation failed on the server.</p>
                        <p><strong>Solutions:</strong></p>
                        <ul style="text-align: left; max-width: 400px; margin: 16px auto;">
                            <li>Download the LaTeX source below</li>
                            <li>Compile it using <a href="https://www.overleaf.com" target="_blank">Overleaf</a></li>
                            <li>Or use a local LaTeX installation</li>
                        </ul>
                    </div>
                `;
            }

            if (latexUrl) {
                const latexDownloadBtn = document.getElementById('latexDownloadBtn');
                latexDownloadBtn.href = latexUrl;
                latexDownloadBtn.addEventListener('click', function(e) {
                    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Downloading...';
                    setTimeout(() => {
                        this.innerHTML = '<i class="fas fa-check"></i> Downloaded!';
                        setTimeout(() => {
                            this.innerHTML = '<i class="fas fa-download"></i> Download LaTeX';
                        }, 2000);
                    }, 1000);
                });
            }
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, { threshold: 0.1 });

            document.querySelectorAll('.animate-fadeup').forEach(el => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px)';
                el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                observer.observe(el);
            });
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
            document.querySelectorAll('.download-card').forEach(card => {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-4px)';
                });
                
                card.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0)';
                });
            });
        });