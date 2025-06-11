        document.addEventListener('DOMContentLoaded', function() {
            const scoreCircle = document.getElementById('scoreCircle');
            const scoreValue = parseInt(document.getElementById('scoreValue').textContent);
            
            if (scoreValue >= 80) {
                scoreCircle.classList.add('score-excellent');
            } else if (scoreValue >= 60) {
                scoreCircle.classList.add('score-good');
            } else if (scoreValue >= 40) {
                scoreCircle.classList.add('score-average');
            } else {
                scoreCircle.classList.add('score-poor');
            }
        });
        
        async function generateImprovedResume() {
            const generateBtn = document.querySelector('.button-primary');
            const loadingBlock = document.getElementById('loadingBlock');
            const originalText = generateBtn.innerHTML;
            
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            generateBtn.disabled = true;
            loadingBlock.style.display = 'block';
            
            try {
                const response = await fetch('/api/generate-improved-resume', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                if (response.ok) {
                    const result = await response.json();
                    if (result.success) {
                        window.location.href = `/improved-resume-preview/${result.session_id}`;
                    } else {
                        alert('Error: ' + (result.error || 'Failed to generate improved resume'));
                    }
                } else {
                    const errorData = await response.json();
                    if (errorData.redirect) {
                        alert('Error: ' + (errorData.error || 'Failed to generate improved resume'));
                        window.location.href = errorData.redirect;
                    } else {
                        alert('Error: ' + (errorData.error || 'Failed to generate improved resume'));
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error generating improved resume. Please try again.');
            } finally {
                generateBtn.innerHTML = originalText;
                generateBtn.disabled = false;
                loadingBlock.style.display = 'none';
            }
        }