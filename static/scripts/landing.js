document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute("href"));
      if (target) {
        target.scrollIntoView({
          behavior: "smooth",
          block: "start"
        });
      }
    });
  });

  const navbar = document.querySelector(".navbar");
  let lastScrollY = window.scrollY;

  window.addEventListener("scroll", function () {
    const currentScrollY = window.scrollY;

    if (currentScrollY > 100) {
      navbar.classList.add("scrolled");
    } else {
      navbar.classList.remove("scrolled");
    }

    if (currentScrollY > lastScrollY && currentScrollY > 300) {
      navbar.style.opacity = "0";
      navbar.style.transform = "translateX(-50%) translateY(-100%)";
    } else {
      navbar.style.opacity = "1";
      navbar.style.transform = "translateX(-50%) translateY(0)";
    }

    lastScrollY = currentScrollY;
  });

  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px"
  };

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1";
        entry.target.style.transform = "translateY(0)";
      }
    });
  }, observerOptions);

  document.querySelectorAll(".feature-card, .step-card").forEach((el) => {
    el.style.opacity = "0";
    el.style.transform = "translateY(30px)";
    el.style.transition = "all 0.6s ease";
    observer.observe(el);
  });

  const track = document.getElementById("marquee-track");
  const viewport = track.parentElement;
  let animId,
    setWidth,
    duration = 0;

  function setupMarquee() {
    while (track.children.length > 8) track.removeChild(track.lastChild);
    for (let i = 0; i < 8; i++) {
      track.appendChild(track.children[i].cloneNode(true));
    }

    setWidth = 0;
    for (let i = 0; i < 8; i++) {
      setWidth += track.children[i].offsetWidth + 35;
    }
    track.style.minWidth = setWidth * 2 + "px";
    duration = setWidth / 80;
    startMarquee();
  }

  function startMarquee() {
    let start = null;
    let paused = false;
    let lastProgress = 0;
    function step(ts) {
      if (!start) start = ts;
      if (paused) {
        start = ts - lastProgress * duration * 1000;
      }
      let progress = (ts - start) / 1000 / duration;
      lastProgress = progress;
      if (progress > 1) {
        start = ts;
        progress = 0;
      }
      track.style.transform = `translateX(${-setWidth * progress}px)`;
      animId = requestAnimationFrame(step);
    }
    viewport.addEventListener("mouseenter", () => {
      paused = true;
    });
    viewport.addEventListener("mouseleave", () => {
      paused = false;
    });
    cancelAnimationFrame(animId);
    animId = requestAnimationFrame(step);
  }

  setTimeout(setupMarquee, 300);
  window.addEventListener("resize", () => setTimeout(setupMarquee, 300));

  const getStartedBtn = document.getElementById("hero-get-started");
  const modalOverlay = document.getElementById("hero-modal-overlay");
  const modalClose = document.getElementById("hero-modal-close");
  getStartedBtn.addEventListener("click", () => {
    modalOverlay.style.display = "flex";
    setTimeout(() => {
      modalOverlay.style.opacity = 1;
    }, 10);
  });
  modalClose.addEventListener("click", () => {
    modalOverlay.style.opacity = 0;
    setTimeout(() => {
      modalOverlay.style.display = "none";
    }, 200);
  });
  modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) {
      modalOverlay.style.opacity = 0;
      setTimeout(() => {
        modalOverlay.style.display = "none";
      }, 200);
    }
  });

  (function () {
    if (window.innerWidth < 600) return;
    let dragTarget = null,
      offsetX = 0,
      offsetY = 0,
      startX = 0,
      startY = 0;
    document.querySelectorAll(".cv-paper").forEach((paper) => {
      paper.addEventListener("mousedown", function (e) {
        if (e.target.isContentEditable) return;
        dragTarget = paper;
        dragTarget.classList.add("dragging");
        startX = e.clientX;
        startY = e.clientY;
        const rect = paper.getBoundingClientRect();
        offsetX = startX - rect.left;
        offsetY = startY - rect.top;
        document.body.style.userSelect = "none";
      });
    });
    document.addEventListener("mousemove", function (e) {
      if (!dragTarget) return;
      let x = e.clientX - offsetX;
      let y = e.clientY - offsetY;
      dragTarget.style.left = "";
      dragTarget.style.right = "";
      dragTarget.style.top = "";
      dragTarget.style.bottom = "";
      dragTarget.style.transform = "none";
      dragTarget.style.position = "fixed";
      dragTarget.style.zIndex = 1000;
      dragTarget.style.left = x + "px";
      dragTarget.style.top = y + "px";
    });
    document.addEventListener("mouseup", function () {
      if (dragTarget) {
        dragTarget.classList.remove("dragging");
        dragTarget.style.position = "absolute";
        dragTarget.style.zIndex = "";
        dragTarget = null;
        document.body.style.userSelect = "";
      }
    });
  })();
});
