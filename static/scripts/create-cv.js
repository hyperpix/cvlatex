        let educationCount = 1;
        let experienceCount = 1;
        let projectCount = 1;
        let customFieldCount = 0;

        function addEducation() {
            const container = document.getElementById('education-section');
            const template = `
                <div class="dynamic-item" data-section="education">
                    <div class="dynamic-item-header">
                        <div class="dynamic-item-title">Education #${educationCount + 1}</div>
                        <button type="button" class="btn-remove" onclick="removeItem(this)">Remove</button>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Degree</label>
                                <input type="text" class="form-control" name="education[${educationCount}][degree]" placeholder="Bachelor of Science in Computer Science">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Institution</label>
                                <input type="text" class="form-control" name="education[${educationCount}][institution]" placeholder="University of Technology">
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Date Range</label>
                                <input type="text" class="form-control" name="education[${educationCount}][date]" placeholder="2018 - 2022">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Location</label>
                                <input type="text" class="form-control" name="education[${educationCount}][location]" placeholder="Boston, MA">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">GPA (Optional)</label>
                                <input type="text" class="form-control" name="education[${educationCount}][gpa]" placeholder="3.8/4.0">
                            </div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Additional Details</label>
                        <textarea class="form-control" name="education[${educationCount}][details]" placeholder="Relevant coursework, honors, achievements..."></textarea>
                    </div>
                </div>
            `;
            
            const addButton = container.querySelector('.btn-add');
            addButton.insertAdjacentHTML('beforebegin', template);
            educationCount++;
        }

        function addExperience() {
            const container = document.getElementById('experience-section');
            const template = `
                <div class="dynamic-item" data-section="experience">
                    <div class="dynamic-item-header">
                        <div class="dynamic-item-title">Experience #${experienceCount + 1}</div>
                        <button type="button" class="btn-remove" onclick="removeItem(this)">Remove</button>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Job Title</label>
                                <input type="text" class="form-control" name="experience[${experienceCount}][title]" placeholder="Senior Software Engineer">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Company</label>
                                <input type="text" class="form-control" name="experience[${experienceCount}][company]" placeholder="Tech Corp Inc.">
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Date Range</label>
                                <input type="text" class="form-control" name="experience[${experienceCount}][date]" placeholder="Jan 2022 - Present">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Location</label>
                                <input type="text" class="form-control" name="experience[${experienceCount}][location]" placeholder="San Francisco, CA">
                            </div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Description (One per line)</label>
                        <textarea class="form-control textarea-auto" name="experience[${experienceCount}][description]" placeholder="• Led a team of 5 developers in building scalable web applications&#10;• Improved system performance by 40% through optimization&#10;• Mentored junior developers and conducted code reviews"></textarea>
                    </div>
                </div>
            `;
            
            const addButton = container.querySelector('.btn-add');
            addButton.insertAdjacentHTML('beforebegin', template);
            experienceCount++;
        }

        function addProject() {
            const container = document.getElementById('projects-section');
            const template = `
                <div class="dynamic-item" data-section="projects">
                    <div class="dynamic-item-header">
                        <div class="dynamic-item-title">Project #${projectCount + 1}</div>
                        <button type="button" class="btn-remove" onclick="removeItem(this)">Remove</button>
                    </div>
                    <div class="row">
                        <div class="col-md-8">
                            <div class="form-group">
                                <label class="form-label">Project Title</label>
                                <input type="text" class="form-control" name="projects[${projectCount}][title]" placeholder="E-Commerce Platform">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Date/Duration</label>
                                <input type="text" class="form-control" name="projects[${projectCount}][date]" placeholder="2023">
                            </div>

                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Description</label>
                        <textarea class="form-control" name="projects[${projectCount}][description]" placeholder="Built a full-stack e-commerce platform with user authentication, payment processing, and admin dashboard..."></textarea>
                    </div>
                    <div class="row">
                        <div class="col-md-8">
                            <div class="form-group">
                                <label class="form-label">Technologies Used</label>
                                <input type="text" class="form-control" name="projects[${projectCount}][technologies]" placeholder="React, Node.js, MongoDB, Stripe API">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Project Link</label>
                                <input type="url" class="form-control" name="projects[${projectCount}][link]" placeholder="https://github.com/user/project">
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            const addButton = container.querySelector('.btn-add');
            addButton.insertAdjacentHTML('beforebegin', template);
            projectCount++;
        }

        function addCustomField() {
            const container = document.getElementById('custom-fields-container');
            const template = `
                <div class="custom-field">
                    <div class="custom-field-header">
                        <div class="form-group" style="margin-bottom: 0; flex-grow: 1;">
                            <input type="text" class="form-control" name="custom[${customFieldCount}][title]" placeholder="Section Title (e.g., Certifications, Languages, Awards)">
                        </div>
                        <button type="button" class="btn-remove" onclick="removeCustomField(this)" style="margin-left: 12px;">Remove</button>
                    </div>
                    <div class="form-group">
                        <textarea class="form-control textarea-auto" name="custom[${customFieldCount}][content]" placeholder="Add the content for this section...&#10;&#10;For lists, separate items with new lines:&#10;• Certification 1&#10;• Certification 2&#10;• Certification 3"></textarea>
                    </div>
                </div>
            `;
            
            container.insertAdjacentHTML('beforeend', template);
            customFieldCount++;
        }

        function removeItem(button) {
            const item = button.closest('.dynamic-item');
            item.remove();
        }

        function removeCustomField(button) {
            const field = button.closest('.custom-field');
            field.remove();
        }

        // Form submission
        document.getElementById('cvForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitButton = document.querySelector('.btn-generate');
            const spinner = document.querySelector('.loading-spinner');
            const icon = submitButton.querySelector('.fas');
            
            // Show loading state
            submitButton.disabled = true;
            spinner.style.display = 'block';
            icon.style.display = 'none';
            submitButton.innerHTML = submitButton.innerHTML.replace('Generate LaTeX Resume', 'Processing...');
            
            // Collect form data
            const formData = new FormData(this);
            const data = {};
            
            // Convert FormData to nested object
            for (let [key, value] of formData.entries()) {
                if (key.includes('[') && key.includes(']')) {
                    // Handle nested arrays like education[0][degree]
                    const match = key.match(/(\w+)\[(\d+)\]\[(\w+)\]/);
                    if (match) {
                        const [, section, index, field] = match;
                        if (!data[section]) data[section] = [];
                        if (!data[section][index]) data[section][index] = {};
                        data[section][index][field] = value;
                    } else {
                        // Handle simple nested objects like skills[languages]
                        const match2 = key.match(/(\w+)\[(\w+)\]/);
                        if (match2) {
                            const [, section, field] = match2;
                            if (!data[section]) data[section] = {};
                            data[section][field] = value;
                        }
                    }
                } else {
                    data[key] = value;
                }
            }
            
            // Handle custom fields
            if (data.custom) {
                const customSections = [];
                Object.values(data.custom).forEach(custom => {
                    if (custom.title && custom.content) {
                        customSections.push({
                            title: custom.title,
                            content: custom.content
                        });
                    }
                });
                data.custom = customSections;
            }
            
            // Clean up empty arrays and objects
            Object.keys(data).forEach(key => {
                if (Array.isArray(data[key])) {
                    data[key] = data[key].filter(item => 
                        item && Object.values(item).some(val => val && val.trim())
                    );
                }
            });
            
            console.log('Form data:', data);
            
            // Send to backend
            fetch('/api/create-cv', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Redirect to result page
                    window.location.href = `/result?latex_file=${result.latex_file}&pdf_file=${result.pdf_file}`;
                } else {
                    alert('Error: ' + result.error);
                    // Reset button state
                    submitButton.disabled = false;
                    spinner.style.display = 'none';
                    icon.style.display = 'inline-block';
                    submitButton.innerHTML = submitButton.innerHTML.replace('Processing...', 'Generate LaTeX Resume');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while processing your CV. Please try again.');
                // Reset button state
                submitButton.disabled = false;
                spinner.style.display = 'none';
                icon.style.display = 'inline-block';
                submitButton.innerHTML = submitButton.innerHTML.replace('Processing...', 'Generate LaTeX Resume');
            });
        });

        // Enhanced animations on scroll
        document.addEventListener('DOMContentLoaded', function() {
            // Add smooth entrance animations
            const elements = document.querySelectorAll('.form-container, .page-header');
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, { threshold: 0.1 });

            elements.forEach(el => {
                observer.observe(el);
            });

            // Add focus animations for form elements
            const formElements = document.querySelectorAll('.form-control, .form-select');
            formElements.forEach(element => {
                element.addEventListener('focus', function() {
                    this.style.transform = 'scale(1.02)';
                });
                
                element.addEventListener('blur', function() {
                    this.style.transform = 'scale(1)';
                });
            });
        });
