// admin_dashboard.js
// Modern, robust client-side behavior for admin_dashboard.html
// Unified with student_dashboard.js architecture

(function () {
  "use strict";

  /* -------------------------
     Utility helpers
  -------------------------*/
  function qs(selector, root = document) {
    return root.querySelector(selector);
  }
  function qsa(selector, root = document) {
    return Array.from(root.querySelectorAll(selector));
  }

  /* -------------------------
     Panel switching
     - Hides all .panel elements and shows the one with id=panelId
  -------------------------*/
  function showPanel(panelId) {
    try {
      const panels = qsa(".panel");
      panels.forEach((p) => {
        p.classList.remove("active");
        p.classList.add("hidden");
        p.style.display = "none";
      });

      const target = document.getElementById(panelId);
      if (target) {
        target.classList.remove("hidden");
        target.classList.add("active");
        target.style.display = "block";

        // update URL hash without scrolling
        if (window.history && typeof window.history.replaceState === 'function') {
          window.history.replaceState(null, "", "#" + panelId);
        } else {
          window.location.hash = panelId;
        }
      }
      setActiveLink(panelId);
    } catch (err) {
      console.error("Error in showPanel:", err);
    }
  }

  /* -------------------------
     Active link highlighting
  -------------------------*/
  function setActiveLink(panelId) {
    const links = qsa(".sidebar nav a");
    links.forEach((a) => {
      const href = a.getAttribute("href") || "";
      const onclick = a.getAttribute("onclick") || "";
      const targetId = href.startsWith("#") ? href.slice(1) : "";

      if (targetId === panelId || onclick.indexOf(panelId) !== -1) {
        a.classList.add("active");
      } else {
        a.classList.remove("active");
      }
    });
  }

  /* -------------------------
     Initialization on DOMContentLoaded
  -------------------------*/
  document.addEventListener("DOMContentLoaded", function () {
    // Show panel based on hash or default to add-student
    const initial = (location.hash && location.hash.slice(1)) || "add-student";
    showPanel(initial);

    // Global listeners for specialized components
    initStudentSearch();
    initAttendanceQuickToggle();
  });

  function initStudentSearch() {
    const searchInput = document.getElementById('studentSearch');
    if (searchInput) {
      searchInput.addEventListener('keyup', function () {
        const filter = this.value.toLowerCase();
        qsa('#studentTable tbody tr').forEach(row => {
          const id = row.cells[0].textContent.toLowerCase();
          const name = row.cells[1].textContent.toLowerCase();
          row.style.display = (id.includes(filter) || name.includes(filter)) ? '' : 'none';
        });
      });
    }
  }

  function initAttendanceQuickToggle() {
    const attendanceRows = qsa("#attendance tbody tr");
    attendanceRows.forEach(row => {
      const radios = qsa("input[type='radio']", row);
      radios.forEach(radio => {
        radio.addEventListener("change", () => {
          row.style.backgroundColor = radio.value === "Present" ? "#e8f8e8" : "#fbeaea";
        });
      });
    });
  }

  /* -------------------------
     Expose showPanel for inline onclick handlers
  -------------------------*/
  window.showPanel = showPanel;
})();