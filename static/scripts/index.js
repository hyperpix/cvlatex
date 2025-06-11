const uploadArea = document.getElementById("uploadArea");
const fileInput = document.getElementById("fileInput");
const progressSection = document.getElementById("progressSection");
const resultsSection = document.getElementById("resultsSection");
const alertArea = document.getElementById("alertArea");
const uploadSection = document.querySelector(".upload-section");

uploadArea.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadArea.classList.add("dragover");
});

uploadArea.addEventListener("dragleave", () => {
  uploadArea.classList.remove("dragover");
});

uploadArea.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadArea.classList.remove("dragover");
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
});

uploadArea.addEventListener("click", () => {
  fileInput.click();
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length > 0) {
    handleFile(e.target.files[0]);
  }
});

function showAlert(message, type = "danger") {
  const alertHtml = `
                <div class="alert alert-${type} alert-custom alert-dismissible fade show" role="alert">
                    <i class="fas fa-${
                      type === "success" ? "check-circle" : "exclamation-circle"
                    } me-2"></i>
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
  alertArea.innerHTML = alertHtml;
}

function handleFile(file) {
  const allowedTypes = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  ];
  if (!allowedTypes.includes(file.type)) {
    showAlert("Please upload a PDF or DOCX file only.");
    return;
  }

  if (file.size > 16 * 1024 * 1024) {
    showAlert("File size must be less than 16MB.");
    return;
  }

  const fileInfo = `
                <div class="file-info">
                    <h6><i class="fas fa-file me-2"></i>${file.name}</h6>
                    <small class="text-muted">Size: ${(
                      file.size /
                      1024 /
                      1024
                    ).toFixed(2)} MB</small>
                </div>
            `;

  uploadSection.style.display = "none";
  progressSection.style.display = "block";
  alertArea.innerHTML = fileInfo;

  uploadFile(file);
}

function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  fetch("/upload", {
    method: "POST",
    body: formData
  })
    .then((response) => response.json())
    .then((data) => {
      progressSection.style.display = "none";

      if (data.success) {
        displayResults(data);
        resultsSection.style.display = "block";
        showAlert("CV successfully converted to LaTeX!", "success");
      } else {
        uploadSection.style.display = "block";
        showAlert(
          data.error || "An error occurred while processing your file."
        );
      }
    })
    .catch((error) => {
      progressSection.style.display = "none";
      uploadSection.style.display = "block";
      showAlert("Network error. Please try again.");
      console.error("Error:", error);
    });
}

function displayResults(data) {
  const parsedData = data.parsed_data;
  const latexContent = data.latex_content;

  const parsedDataHtml = `
                <div class="mb-3">
                    <h6><i class="fas fa-user me-2"></i>Personal Information</h6>
                    <p><strong>Name:</strong> ${
                      parsedData.name || "Not found"
                    }</p>
                    <p><strong>Email:</strong> ${
                      parsedData.email || "Not found"
                    }</p>
                    <p><strong>Phone:</strong> ${
                      parsedData.phone || "Not found"
                    }</p>
                    <p><strong>LinkedIn:</strong> ${
                      parsedData.linkedin || "Not found"
                    }</p>
                    <p><strong>GitHub:</strong> ${
                      parsedData.github || "Not found"
                    }</p>
                </div>
                
                <div class="mb-3">
                    <h6><i class="fas fa-graduation-cap me-2"></i>Education</h6>
                    <p>${parsedData.education.length} entries found</p>
                </div>
                
                <div class="mb-3">
                    <h6><i class="fas fa-briefcase me-2"></i>Experience</h6>
                    <p>${parsedData.experience.length} entries found</p>
                </div>
                
                <div class="mb-3">
                    <h6><i class="fas fa-project-diagram me-2"></i>Projects</h6>
                    <p>${parsedData.projects.length} entries found</p>
                </div>
                
                <div class="mb-3">
                    <h6><i class="fas fa-code me-2"></i>Skills</h6>
                    <p><strong>Languages:</strong> ${
                      parsedData.skills.languages.length
                    } found</p>
                    <p><strong>Frameworks:</strong> ${
                      parsedData.skills.frameworks.length
                    } found</p>
                    <p><strong>Tools:</strong> ${
                      parsedData.skills.tools.length
                    } found</p>
                </div>
            `;

  document.getElementById("parsedData").innerHTML = parsedDataHtml;

  const truncatedLatex =
    latexContent.length > 2000
      ? latexContent.substring(0, 2000) + "\n\n... (truncated for preview)"
      : latexContent;

  document.getElementById(
    "latexPreview"
  ).innerHTML = `<pre><code class="language-latex">${escapeHtml(
    truncatedLatex
  )}</code></pre>`;

  if (window.Prism) {
    Prism.highlightAll();
  }

  document.getElementById("downloadBtn").onclick = () => {
    window.location.href = data.download_url;
  };
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

document.addEventListener("DOMContentLoaded", function () {
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});
