        const uploadArea = document.querySelector('.upload-area');
        const fileInput = document.getElementById('cv_file');
        const uploadText = document.getElementById('uploadText');

        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        let extractedText = '';

        fileInput.addEventListener('change', async (e) => {
            if (fileInput.files.length > 0) {
                const fileName = fileInput.files[0].name;
                uploadText.innerHTML = `
                    <i class="fas fa-check" style="font-size: 48px; color: #28ca42; margin-bottom: 10px;"></i>
                    <div style="font-size: 20px; font-weight: bold;">${fileName}</div>
                    <div style="font-size: 14px; color: #666;">Click to change file</div>
                `;

                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                try {
                    const uploadResponse = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });

                    if (!uploadResponse.ok) {
                        throw new Error('Upload failed');
                    }

                    const uploadData = await uploadResponse.json();

                    if (uploadData.success && uploadData.extracted_text) {
                        extractedText = uploadData.extracted_text;
                    } else {
                        extractedText = '';
                        alert(uploadData.error || 'Failed to extract text from CV.');
                    }
                } catch (err) {
                    extractedText = '';
                    alert('Error uploading CV. Please try again.');
                    console.error('Upload error:', err);
                }
            }
        });

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = 'var(--red-accent)';
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#ccc';
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#ccc';
            fileInput.files = e.dataTransfer.files;
            if (fileInput.files.length > 0) {
                const fileName = fileInput.files[0].name;
                uploadText.innerHTML = `
                    <i class="fas fa-check" style="font-size: 48px; color: #28ca42; margin-bottom: 10px;"></i>
                    <div style="font-size: 20px; font-weight: bold;">${fileName}</div>
                    <div style="font-size: 14px; color: #666;">Click to change file</div>
                `;
            }
        });

        document.getElementById('generateLink').onclick = async function() {
            const role = document.getElementById('jobSelect').value.trim();
            if (!role) {
                alert('Please enter a job role first.');
                return;
            }
            const jobDescArea = document.getElementById('jobDesc');
            jobDescArea.value = 'Generating job description for "' + role + '"...';
            try {
                const response = await fetch('/generate-job-desc', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ role })
                });
                const data = await response.json();
                if (data && data.description) {
                    jobDescArea.value = data.description;
                } else {
                    jobDescArea.value = '';
                    alert('Could not generate job description.');
                }
            } catch (e) {
                jobDescArea.value = '';
                alert('Error generating job description.');
            }
        };

        document.getElementById('reviewBtn').onclick = async function() {
            const role = document.getElementById('jobSelect').value.trim();
            const jobDesc = document.getElementById('jobDesc').value.trim();
            if (!extractedText) {
                alert('Please upload a valid CV file first.');
                return;
            }
            const reviewBtn = document.getElementById('reviewBtn');
            reviewBtn.innerText = 'Reviewing...';
            reviewBtn.disabled = true;
            const reviewResults = document.getElementById('reviewResults');
            reviewResults.style.display = 'none';
            reviewResults.innerHTML = '';
            document.querySelector('.right-col').classList.remove('review-active');
            try {
                console.log('Starting CV review...');
                const response = await fetch('/api/review-cv', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        cv_text: extractedText,
                        job_description: jobDesc
                    })
                });
                console.log('Response status:', response.status);
                const data = await response.json();
                console.log('Review API Response:', data);
                console.log('Data has success:', 'success' in data);
                console.log('Data has redirect_url:', 'redirect_url' in data);
                
                if (data.error) {
                    alert('Error: ' + data.error);
                } else if (data.success && data.redirect_url) {
                    console.log('Redirecting to:', data.redirect_url);
                    console.log('About to redirect...');
                    window.location.href = data.redirect_url;
                    return;
                } else {
                    console.log('Falling back to old review display');
                    console.log('data.success:', data.success);
                    console.log('data.redirect_url:', data.redirect_url);
                    document.getElementById('illustrationBlock').style.display = 'none';
                    let html = '';
                    html += `
                        <div class="cv-review-panel">
                            <div class="cv-review-score">
                                <span id="cvScore">${data.rating ?? '--'}</span>
                                <div class="cv-review-score-label">Score</div>
                            </div>
                            <div class="cv-review-sections">
                                <div class="cv-review-section strengths">
                                    <div class="cv-review-section-title"><i class="fas fa-thumbs-up"></i> Top 5 Strengths</div>
                                    <ul>${(data.strengths || []).slice(0, 5).map(s => `<li>${s}</li>`).join('')}</ul>
                                </div>
                                <div class="cv-review-section weaknesses">
                                    <div class="cv-review-section-title"><i class="fas fa-thumbs-down"></i> Worst 5 Weaknesses</div>
                                    <ul>${(data.weaknesses || []).slice(0, 5).map(w => `<li>${w}</li>`).join('')}</ul>
                                </div>
                                <div class="cv-review-section suggestions">
                                    <div class="cv-review-section-title"><i class="fas fa-lightbulb"></i> Top Suggestions</div>
                                    <ul>${(data.suggestions || []).slice(0, 5).map(s => `<li>${s}</li>`).join('')}</ul>
                                </div>
                            </div>
                        </div>
                    `;
                    document.getElementById('leftCol').style.display = 'none';
                    document.getElementById('rightCol').style.display = 'none';
                    document.getElementById('reviewOverlay').style.display = 'flex';
                    document.getElementById('reviewAnimation').style.display = 'flex';
                    document.getElementById('fullReviewPanel').style.display = 'none';
                    setTimeout(() => {
                        document.getElementById('reviewAnimation').style.display = 'none';
                        document.getElementById('fullReviewPanel').innerHTML = `
                            <div class="review-overlay-content">
                                <div class="review-left">
                                    <div class="full-review-card">
                                        <div class="cv-review-score">
                                            <span id="cvScore">${data.rating ?? '--'}</span>
                                            <div class="cv-review-score-label">Score</div>
                                        </div>
                                        <div class="cv-review-section strengths">
                                            <div class="cv-review-section-title"><i class="fas fa-thumbs-up"></i> Top 5 Strengths</div>
                                            <ul>${(data.strengths || []).slice(0, 5).map(s => `<li>${s}</li>`).join('')}</ul>
                                        </div>
                                        <div class="cv-review-section weaknesses">
                                            <div class="cv-review-section-title"><i class="fas fa-thumbs-down"></i> Worst 5 Weaknesses</div>
                                            <ul>${(data.weaknesses || []).slice(0, 5).map(w => `<li>${w}</li>`).join('')}</ul>
                                        </div>
                                        <div class="cv-review-section suggestions">
                                            <div class="cv-review-section-title"><i class="fas fa-lightbulb"></i> Top Suggestions</div>
                                            <ul>${(data.suggestions || []).slice(0, 5).map(s => `<li>${s}</li>`).join('')}</ul>
                                        </div>
                                        <button class="full-review-close" onclick="window.location.reload()">Upload another CV</button>
                                    </div>
                                </div>
                                <div class="review-right">
                                    <div class="review-cta-title">Generate your perfect resume, today</div>
                                    <div class="review-cta-desc">Transform your CV into a stunning, job-winning resume in seconds. Our AI-powered tool makes it easy!</div>
                                    <button class="review-cta-btn" onclick="generateImprovedResume()">Generate Resume</button>
                                </div>
                            </div>
                        `;
                        document.getElementById('fullReviewPanel').style.display = 'flex';
                    }, 1500);

                    if (data.rating !== undefined && document.getElementById('gaugeScore')) {
                        document.getElementById('gaugeScore').textContent = data.rating;
                    }
                    console.log('Review API response:', data);
                    console.log('Review HTML:', html);
                }
            } catch (e) {
                alert('Error reviewing CV.');
            } finally {
                reviewBtn.innerText = 'Review my resume &rarr;';
                reviewBtn.disabled = false;
            }
        };
        async function generateImprovedResume() {
            const generateBtn = document.querySelector('.review-cta-btn');
            const originalText = generateBtn.textContent;
            
            generateBtn.textContent = 'Generating...';
            generateBtn.disabled = true;
            
            try {
                const response = await fetch('/api/generate-improved-resume', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = `/improved-resume-preview/${data.session_id}`;
                } else {
                    alert('Error generating improved resume: ' + (data.error || 'Unknown error'));
                    generateBtn.textContent = originalText;
                    generateBtn.disabled = false;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error generating improved resume. Please try again.');
                generateBtn.textContent = originalText;
                generateBtn.disabled = false;
            }
        }

        const emojis = ["📄", "🤖", "✨", "📝", "💼"];
        let emojiIndex = 0;
        const emojiSpan = document.getElementById("emojiCycler");
        setInterval(() => {
            emojiSpan.style.opacity = 0;
            setTimeout(() => {
                emojiIndex = (emojiIndex + 1) % emojis.length;
                emojiSpan.textContent = emojis[emojiIndex];
                emojiSpan.style.opacity = 1;
            }, 400);
        }, 5000);