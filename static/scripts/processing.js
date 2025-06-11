document.addEventListener("DOMContentLoaded", function () {
  let currentStep = 1;
  let processingTime = 0;
  let accuracy = 85;

  const steps = [
    { duration: 2000, name: "File Upload" },
    { duration: 8000, name: "AI Extraction" },
    { duration: 5000, name: "LaTeX Generation" },
    { duration: 3000, name: "PDF Compilation" }
  ];

  const timeInterval = setInterval(() => {
    processingTime++;
    document.getElementById("processingTime").textContent =
      processingTime + "s";

    if (accuracy < 97 && Math.random() > 0.7) {
      accuracy += 1;
      document.getElementById("accuracy").textContent = accuracy + "%";
    }
  }, 1000);

  const totalDuration = steps.reduce((sum, step) => sum + step.duration, 0);
  let elapsedTime = 0;

  const progressInterval = setInterval(() => {
    elapsedTime += 100;
    const progress = Math.min((elapsedTime / totalDuration) * 100, 100);
    document.getElementById("overallProgress").style.width = progress + "%";

    if (progress >= 100) {
      clearInterval(progressInterval);
    }
  }, 100);

  function processStep(stepIndex) {
    if (stepIndex >= steps.length) {
      clearInterval(timeInterval);
      setTimeout(() => {
        window.location.href =
          "/result?pdf=%2Fpreview%2Fresume.pdf&latex=%2Fdownload%2Fresume.tex&pdf_download=%2Fdownload%2Fresume.pdf";
      }, 1000);
      return;
    }

    const step = steps[stepIndex];
    const stepElement = document.getElementById(`step${stepIndex + 1}`);

    stepElement.classList.add("active");

    const timeElement = stepElement.querySelector(".step-time");
    let stepTime = 0;
    const stepTimeInterval = setInterval(() => {
      stepTime += 0.1;
      timeElement.textContent = `Processing... ${stepTime.toFixed(1)}s`;
    }, 100);

    setTimeout(() => {
      clearInterval(stepTimeInterval);

      stepElement.classList.remove("active");
      stepElement.classList.add("completed");
      stepElement.querySelector(".step-icon i").className = "fas fa-check";
      timeElement.textContent = `Completed in ${(step.duration / 1000).toFixed(
        1
      )}s`;

      setTimeout(() => {
        processStep(stepIndex + 1);
      }, 500);
    }, step.duration);
  }

  setTimeout(() => {
    processStep(1);
  }, 1000);

  let sectionsFound = 3;
  const sectionsInterval = setInterval(() => {
    if (sectionsFound < 7 && Math.random() > 0.6) {
      sectionsFound++;
      document.getElementById("sectionsFound").textContent =
        sectionsFound + "/8";
    }

    if (sectionsFound >= 7) {
      clearInterval(sectionsInterval);
    }
  }, 2000);

  document.querySelectorAll(".stat-card").forEach((card) => {
    card.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-6px) scale(1.02)";
    });

    card.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0) scale(1)";
    });
  });
});
