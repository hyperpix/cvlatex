let currentDeleteId = null;

document.addEventListener("DOMContentLoaded", function () {
  loadCVs();
});

async function loadCVs() {
  try {
    const response = await fetch("/api/cvs");
    const data = await response.json();

    if (data.success) {
      displayCVs(data.cvs);
    } else {
      showError("Failed to load CVs: " + data.error);
    }
  } catch (error) {
    showError("Error loading CVs: " + error.message);
  }
}

function displayCVs(cvs) {
  const loading = document.getElementById("loading");
  const container = document.getElementById("cvs-container");
  const emptyState = document.getElementById("empty-state");
  const grid = document.getElementById("cvs-grid");

  loading.classList.add("hidden");

  if (cvs.length === 0) {
    emptyState.classList.remove("hidden");
    return;
  }

  container.classList.remove("hidden");
  grid.innerHTML = "";

  cvs.forEach((cv) => {
    const cvCard = createCVCard(cv);
    grid.appendChild(cvCard);
  });
}

function createCVCard(cv) {
  const card = document.createElement("div");
  card.className = "card cv-card rounded-xl shadow-lg p-6";

  card.innerHTML = `
                <div class="flex justify-between items-start mb-4">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-800 mb-1">${escapeHtml(
                          cv.name
                        )}</h3>
                        <p class="text-sm text-gray-600 mb-2">${escapeHtml(
                          cv.email
                        )}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="editCV('${cv.id}')" 
                                class="text-blue-500 hover:text-blue-700 transition-colors"
                                title="Edit CV">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteCV('${cv.id}')" 
                                class="text-red-500 hover:text-red-700 transition-colors"
                                title="Delete CV">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
                
                <div class="text-xs text-gray-500 mb-4">
                    <div class="flex justify-between">
                        <span>Created: ${formatDate(cv.created_at)}</span>
                        <span>Updated: ${formatDate(cv.updated_at)}</span>
                    </div>
                </div>
                
                <div class="flex space-x-2">
                    <button onclick="editCV('${cv.id}')" 
                            class="flex-1 btn-primary text-white px-4 py-2 rounded-lg text-sm">
                        <i class="fas fa-edit mr-2"></i>Edit
                    </button>
                    <a href="/download/resume_${cv.id}.pdf" 
                       class="flex-1 btn-secondary text-white px-4 py-2 rounded-lg text-sm text-center"
                       target="_blank">
                        <i class="fas fa-download mr-2"></i>PDF
                    </a>
                    <a href="/download/resume_${cv.id}.tex" 
                       class="flex-1 bg-gray-600 text-white px-4 py-2 rounded-lg text-sm text-center hover:bg-gray-700"
                       target="_blank">
                        <i class="fas fa-code mr-2"></i>LaTeX
                    </a>
                </div>
            `;

  return card;
}

function editCV(cvId) {
  window.location.href = `/edit-cv/${cvId}`;
}

function deleteCV(cvId) {
  currentDeleteId = cvId;
  document.getElementById("deleteModal").classList.remove("hidden");
  document.getElementById("deleteModal").classList.add("flex");
}

document.getElementById("cancelDelete").addEventListener("click", function () {
  document.getElementById("deleteModal").classList.add("hidden");
  document.getElementById("deleteModal").classList.remove("flex");
  currentDeleteId = null;
});

document
  .getElementById("confirmDelete")
  .addEventListener("click", async function () {
    if (!currentDeleteId) return;

    try {
      const response = await fetch(`/api/cv/${currentDeleteId}`, {
        method: "DELETE"
      });
      const data = await response.json();

      if (data.success) {
        document.getElementById("deleteModal").classList.add("hidden");
        document.getElementById("deleteModal").classList.remove("flex");

        await loadCVs();

        showSuccess("CV deleted successfully");
      } else {
        showError("Failed to delete CV: " + data.error);
      }
    } catch (error) {
      showError("Error deleting CV: " + error.message);
    }

    currentDeleteId = null;
  });

function formatDate(dateString) {
  if (!dateString) return "Unknown";
  const date = new Date(dateString);
  return (
    date.toLocaleDateString() +
    " " +
    date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  );
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function showError(message) {
  alert("Error: " + message);
}

function showSuccess(message) {
  alert("Success: " + message);
}
