      let cvId = "{{ cv_id }}";
      let educationCount = 0;
      let experienceCount = 0;
      let projectCount = 0;
      let customCount = 0;

      document.addEventListener("DOMContentLoaded", function () {
        loadCVData();
      });

      async function loadCVData() {
        try {
          const response = await fetch(`/api/cv/${cvId}`);
          const data = await response.json();

          if (data.success) {
            populateForm(data.cv_data.data);
            document.getElementById("loadingState").style.display = "none";
            document.getElementById("cvForm").style.display = "block";
          } else {
            showError("Failed to load CV data: " + data.error);
          }
        } catch (error) {
          showError("Error loading CV data: " + error.message);
        }
      }

      function populateForm(cvData) {
        document.getElementById("name").value = cvData.name || "";
        document.getElementById("email").value = cvData.email || "";
        document.getElementById("phone").value = cvData.phone || "";
        document.getElementById("address").value = cvData.address || "";
        document.getElementById("linkedin").value = cvData.linkedin || "";
        document.getElementById("github").value = cvData.github || "";
        document.getElementById("website").value = cvData.website || "";
        document.getElementById("summary").value = cvData.summary || "";

        if (cvData.education && cvData.education.length > 0) {
          cvData.education.forEach((edu) => addEducation(edu));
        } else {
          addEducation();
        }

        if (cvData.experience && cvData.experience.length > 0) {
          cvData.experience.forEach((exp) => addExperience(exp));
        } else {
          addExperience();
        }

        if (cvData.projects && cvData.projects.length > 0) {
          cvData.projects.forEach((proj) => addProject(proj));
        }

        if (cvData.skills) {
          const skills = cvData.skills;
          document.getElementById("languages").value = skills.languages
            ? skills.languages.join(", ")
            : "";
          document.getElementById("frameworks").value = skills.frameworks
            ? skills.frameworks.join(", ")
            : "";
          document.getElementById("tools").value = skills.tools
            ? skills.tools.join(", ")
            : "";
          document.getElementById("databases").value = skills.databases
            ? skills.databases.join(", ")
            : "";
          document.getElementById("other").value = skills.other
            ? skills.other.join(", ")
            : "";
        }

        if (cvData.custom_sections && cvData.custom_sections.length > 0) {
          cvData.custom_sections.forEach((custom) => addCustomSection(custom));
        }
      }

      function addEducation(data = {}) {
        educationCount++;
        const container = document.getElementById("educationContainer");
        const educationDiv = document.createElement("div");
        educationDiv.className = "dynamic-section";
        educationDiv.id = `education_${educationCount}`;

        educationDiv.innerHTML = `
                <div class="dynamic-header">
                    <h6 class="mb-0">Education #${educationCount}</h6>
                    <button type="button" class="remove-button" onclick="removeEducation(${educationCount})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="dynamic-content">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Degree/Program</label>
                                <input type="text" class="form-control" name="education_degree_${educationCount}" 
                                       value="${
                                         data.degree || ""
                                       }" placeholder="Bachelor of Science in Computer Science">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Institution</label>
                                <input type="text" class="form-control" name="education_institution_${educationCount}" 
                                       value="${
                                         data.institution || ""
                                       }" placeholder="University Name">
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Date Range</label>
                                <input type="text" class="form-control" name="education_date_${educationCount}" 
                                       value="${
                                         data.date || ""
                                       }" placeholder="Sep 2018 - May 2022">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Location</label>
                                <input type="text" class="form-control" name="education_location_${educationCount}" 
                                       value="${
                                         data.location || ""
                                       }" placeholder="City, State">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">GPA (Optional)</label>
                                <input type="text" class="form-control" name="education_gpa_${educationCount}" 
                                       value="${
                                         data.gpa || ""
                                       }" placeholder="3.8/4.0">
                            </div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Additional Details</label>
                        <textarea class="form-control" name="education_details_${educationCount}" rows="2" 
                                  placeholder="Relevant coursework, honors, activities...">${
                                    data.details || ""
                                  }</textarea>
                    </div>
                </div>
            `;

        container.appendChild(educationDiv);
      }

      function removeEducation(id) {
        const element = document.getElementById(`education_${id}`);
        if (element) {
          element.remove();
        }
      }

      // Experience functions
      function addExperience(data = {}) {
        experienceCount++;
        const container = document.getElementById("experienceContainer");
        const experienceDiv = document.createElement("div");
        experienceDiv.className = "dynamic-section";
        experienceDiv.id = `experience_${experienceCount}`;

        const description = data.description ? data.description.join("\n") : "";

        experienceDiv.innerHTML = `
                <div class="dynamic-header">
                    <h6 class="mb-0">Experience #${experienceCount}</h6>
                    <button type="button" class="remove-button" onclick="removeExperience(${experienceCount})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="dynamic-content">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Job Title</label>
                                <input type="text" class="form-control" name="experience_title_${experienceCount}" 
                                       value="${
                                         data.title || ""
                                       }" placeholder="Software Engineer">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Company</label>
                                <input type="text" class="form-control" name="experience_company_${experienceCount}" 
                                       value="${
                                         data.company || ""
                                       }" placeholder="Company Name">
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Date Range</label>
                                <input type="text" class="form-control" name="experience_date_${experienceCount}" 
                                       value="${
                                         data.date || ""
                                       }" placeholder="Jan 2022 - Present">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Location</label>
                                <input type="text" class="form-control" name="experience_location_${experienceCount}" 
                                       value="${
                                         data.location || ""
                                       }" placeholder="City, State">
                            </div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Job Description & Achievements</label>
                        <textarea class="form-control" name="experience_description_${experienceCount}" rows="4" 
                                  placeholder="• Developed and maintained web applications using React and Node.js&#10;• Collaborated with cross-functional teams to deliver high-quality software&#10;• Improved application performance by 30% through code optimization">${description}</textarea>
                        <small class="text-muted">Use bullet points (•) or separate lines for each responsibility/achievement</small>
                    </div>
                </div>
            `;

        container.appendChild(experienceDiv);
      }

      function removeExperience(id) {
        const element = document.getElementById(`experience_${id}`);
        if (element) {
          element.remove();
        }
      }

      // Project functions
      function addProject(data = {}) {
        projectCount++;
        const container = document.getElementById("projectsContainer");
        const projectDiv = document.createElement("div");
        projectDiv.className = "dynamic-section";
        projectDiv.id = `project_${projectCount}`;

        projectDiv.innerHTML = `
                <div class="dynamic-header">
                    <h6 class="mb-0">Project #${projectCount}</h6>
                    <button type="button" class="remove-button" onclick="removeProject(${projectCount})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="dynamic-content">
                    <div class="row">
                        <div class="col-md-8">
                            <div class="form-group">
                                <label class="form-label">Project Name</label>
                                <input type="text" class="form-control" name="project_title_${projectCount}" 
                                       value="${
                                         data.title || ""
                                       }" placeholder="E-commerce Web Application">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Date</label>
                                <input type="text" class="form-control" name="project_date_${projectCount}" 
                                       value="${
                                         data.date || ""
                                       }" placeholder="2023">
                            </div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Description</label>
                        <textarea class="form-control" name="project_description_${projectCount}" rows="3" 
                                  placeholder="Brief description of the project, your role, and key achievements...">${
                                    data.description || ""
                                  }</textarea>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Technologies Used</label>
                                <input type="text" class="form-control" name="project_technologies_${projectCount}" 
                                       value="${
                                         data.technologies || ""
                                       }" placeholder="React, Node.js, MongoDB">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Project Link (Optional)</label>
                                <input type="url" class="form-control" name="project_link_${projectCount}" 
                                       value="${
                                         data.link || ""
                                       }" placeholder="https://github.com/username/project">
                            </div>
                        </div>
                    </div>
                </div>
            `;

        container.appendChild(projectDiv);
      }

      function removeProject(id) {
        const element = document.getElementById(`project_${id}`);
        if (element) {
          element.remove();
        }
      }

      // Custom section functions
      function addCustomSection(data = {}) {
        customCount++;
        const container = document.getElementById("customContainer");
        const customDiv = document.createElement("div");
        customDiv.className = "dynamic-section";
        customDiv.id = `custom_${customCount}`;

        customDiv.innerHTML = `
                <div class="dynamic-header">
                    <h6 class="mb-0">Custom Section #${customCount}</h6>
                    <button type="button" class="remove-button" onclick="removeCustomSection(${customCount})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="dynamic-content">
                    <div class="form-group">
                        <label class="form-label">Section Title</label>
                        <input type="text" class="form-control" name="custom_title_${customCount}" 
                               value="${
                                 data.title || ""
                               }" placeholder="Certifications, Awards, Publications, etc.">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Content</label>
                        <textarea class="form-control" name="custom_content_${customCount}" rows="4" 
                                  placeholder="List your certifications, awards, publications, or other relevant information...">${
                                    data.content || ""
                                  }</textarea>
                    </div>
                </div>
            `;

        container.appendChild(customDiv);
      }

      function removeCustomSection(id) {
        const element = document.getElementById(`custom_${id}`);
        if (element) {
          element.remove();
        }
      }

      // Form submission
      document
        .getElementById("editCvForm")
        .addEventListener("submit", async function (e) {
          e.preventDefault();

          const updateButton = document.getElementById("updateButton");
          const originalText = updateButton.innerHTML;

          updateButton.innerHTML =
            '<span class="spinner"></span> Updating CV...';
          updateButton.disabled = true;

          try {
            const formData = collectFormData();

            const response = await fetch(`/api/cv/${cvId}`, {
              method: "PUT",
              headers: {
                "Content-Type": "application/json"
              },
              body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
              showSuccess("CV updated successfully!");

              setTimeout(() => {
                const url = `/result?latex_file=${data.latex_file}&pdf_file=${
                  data.pdf_file || ""
                }&cv_id=${cvId}`;
                window.location.href = url;
              }, 1500);
            } else {
              showError("Failed to update CV: " + data.error);
            }
          } catch (error) {
            showError("Error updating CV: " + error.message);
          } finally {
            updateButton.innerHTML = originalText;
            updateButton.disabled = false;
          }
        });

      function collectFormData() {
        const formData = {
          name: document.getElementById("name").value,
          email: document.getElementById("email").value,
          phone: document.getElementById("phone").value,
          address: document.getElementById("address").value,
          linkedin: document.getElementById("linkedin").value,
          github: document.getElementById("github").value,
          website: document.getElementById("website").value,
          summary: document.getElementById("summary").value,
          education: [],
          experience: [],
          projects: [],
          skills: {
            languages: document.getElementById("languages").value,
            frameworks: document.getElementById("frameworks").value,
            tools: document.getElementById("tools").value,
            databases: document.getElementById("databases").value,
            other: document.getElementById("other").value
          },
          custom: []
        };

        // Collect education data
        for (let i = 1; i <= educationCount; i++) {
          const degreeEl = document.querySelector(
            `[name="education_degree_${i}"]`
          );
          if (degreeEl && degreeEl.closest(".dynamic-section")) {
            const education = {
              degree: degreeEl.value,
              institution: document.querySelector(
                `[name="education_institution_${i}"]`
              ).value,
              date: document.querySelector(`[name="education_date_${i}"]`)
                .value,
              location: document.querySelector(
                `[name="education_location_${i}"]`
              ).value,
              gpa: document.querySelector(`[name="education_gpa_${i}"]`).value,
              details: document.querySelector(`[name="education_details_${i}"]`)
                .value
            };
            if (education.degree || education.institution) {
              formData.education.push(education);
            }
          }
        }

        // Collect experience data
        for (let i = 1; i <= experienceCount; i++) {
          const titleEl = document.querySelector(
            `[name="experience_title_${i}"]`
          );
          if (titleEl && titleEl.closest(".dynamic-section")) {
            const experience = {
              title: titleEl.value,
              company: document.querySelector(
                `[name="experience_company_${i}"]`
              ).value,
              date: document.querySelector(`[name="experience_date_${i}"]`)
                .value,
              location: document.querySelector(
                `[name="experience_location_${i}"]`
              ).value,
              description: document.querySelector(
                `[name="experience_description_${i}"]`
              ).value
            };
            if (experience.title || experience.company) {
              formData.experience.push(experience);
            }
          }
        }

        // Collect project data
        for (let i = 1; i <= projectCount; i++) {
          const titleEl = document.querySelector(`[name="project_title_${i}"]`);
          if (titleEl && titleEl.closest(".dynamic-section")) {
            const project = {
              title: titleEl.value,
              description: document.querySelector(
                `[name="project_description_${i}"]`
              ).value,
              technologies: document.querySelector(
                `[name="project_technologies_${i}"]`
              ).value,
              date: document.querySelector(`[name="project_date_${i}"]`).value,
              link: document.querySelector(`[name="project_link_${i}"]`).value
            };
            if (project.title) {
              formData.projects.push(project);
            }
          }
        }

        // Collect custom section data
        for (let i = 1; i <= customCount; i++) {
          const titleEl = document.querySelector(`[name="custom_title_${i}"]`);
          if (titleEl && titleEl.closest(".dynamic-section")) {
            const custom = {
              title: titleEl.value,
              content: document.querySelector(`[name="custom_content_${i}"]`)
                .value
            };
            if (custom.title && custom.content) {
              formData.custom.push(custom);
            }
          }
        }

        return formData;
      }

      function showError(message) {
        showStatus(message, "error");
      }

      function showSuccess(message) {
        showStatus(message, "success");
      }

      function showWarning(message) {
        showStatus(message, "warning");
      }

      function showStatus(message, type) {
        const container = document.getElementById("statusContainer");
        const statusDiv = document.createElement("div");
        statusDiv.className = `status-message status-${type}`;
        statusDiv.innerHTML = `
                <i class="fas fa-${
                  type === "error"
                    ? "exclamation-circle"
                    : type === "success"
                    ? "check-circle"
                    : "exclamation-triangle"
                } me-2"></i>
                ${message}
            `;

        container.innerHTML = "";
        container.appendChild(statusDiv);
        statusDiv.style.display = "block";

        if (type === "success") {
          setTimeout(() => {
            statusDiv.style.display = "none";
          }, 5000);
        }

        window.scrollTo({ top: 0, behavior: "smooth" });
      }