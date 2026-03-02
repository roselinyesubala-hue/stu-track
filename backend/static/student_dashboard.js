// student_dashboard.js
// Complete client-side behavior for student_dashboard.html
// - Panel switching
// - Sidebar mobile toggle
// - Active link highlighting
// - Lightweight dynamic loaders (notices, attendance) if API endpoints exist
// - Safe DOM-ready initialization

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
    const panels = qsa(".panel");
    panels.forEach((p) => p.classList.add("hidden"));

    const target = document.getElementById(panelId);
    if (target) {
      target.classList.remove("hidden");
      // update URL hash without scrolling
      if (history && history.replaceState) {
        history.replaceState(null, "", "#" + panelId);
      } else {
        location.hash = panelId;
      }
    }
    setActiveLink(panelId);
  }

  /* -------------------------
     Active link highlighting
  -------------------------*/
  function setActiveLink(panelId) {
    const links = qsa(".sidebar-nav a");
    links.forEach((a) => {
      // links use onclick handlers with return false; or href="#id"
      const href = a.getAttribute("href") || "";
      const targetId = href.startsWith("#") ? href.slice(1) : a.dataset.target;
      if (targetId === panelId) {
        a.classList.add("active");
      } else {
        a.classList.remove("active");
      }
    });
  }

  /* -------------------------
     Sidebar mobile toggle
  -------------------------*/
  function initSidebarToggle() {
    // create a small toggle button for narrow screens
    const toggle = document.createElement("button");
    toggle.className = "sidebar-toggle";
    toggle.type = "button";
    toggle.innerText = "☰";
    toggle.setAttribute("aria-label", "Toggle navigation");
    document.body.insertBefore(toggle, document.body.firstChild);

    const sidebar = qs(".sidebar");
    toggle.addEventListener("click", function () {
      if (!sidebar) return;
      sidebar.classList.toggle("collapsed");
    });

    // close sidebar when clicking outside on small screens
    document.addEventListener("click", (e) => {
      if (!sidebar) return;
      if (window.innerWidth > 900) return; // only for small screens
      if (sidebar.contains(e.target) || toggle.contains(e.target)) return;
      sidebar.classList.add("collapsed");
    });
  }

  /* -------------------------
     Attach sidebar link handlers
     - Links in HTML call showPanel via onclick; this ensures keyboard accessibility too
  -------------------------*/
  function initSidebarLinks() {
    const links = qsa(".sidebar-nav a");
    links.forEach((a) => {
      // If link already has inline onclick, keep it; still attach for keyboard
      a.addEventListener("click", function (ev) {
        const href = a.getAttribute("href") || "";
        const panelId = href.startsWith("#") ? href.slice(1) : a.dataset.target;
        if (panelId) {
          ev.preventDefault();
          showPanel(panelId);
        }
      });
    });
  }

  /* -------------------------
     Lightweight dynamic loaders (optional)
     - These try to fetch JSON from endpoints if available.
     - They fail silently (console.warn) if endpoints don't exist.
  -------------------------*/
  function loadNotices() {
    const container = qs("#notice .notice-cards");
    if (!container) return;
    fetch("/student/api/notices")
      .then((r) => {
        if (!r.ok) throw new Error("No notices API");
        return r.json();
      })
      .then((data) => {
        if (!Array.isArray(data)) return;
        container.innerHTML = data.length
          ? data
            .map(
              (n) =>
                `<div class="notice-card">
                    <div class="notice-header">
                      <h3 class="notice-title">${escapeHtml(n.title)}</h3>
                    </div>
                    <div class="notice-body">
                      ${escapeHtml(n.description || n.content || "")}
                    </div>
                    <div class="notice-footer">
                      <span class="notice-date">Posted on: ${escapeHtml(n.posted_on || "")}</span>
                    </div>
                  </div>`
            )
            .join("")
          : "<p>No notices available</p>";
      })
      .catch((err) => {
        // not critical; keep server-rendered content if present
        console.warn("loadNotices:", err.message);
      });
  }

  function loadAttendance() {
    const tableBody = qs("#attendance tbody");
    if (!tableBody) return;
    fetch("/student/api/attendance")
      .then((r) => {
        if (!r.ok) throw new Error("No attendance API");
        return r.json();
      })
      .then((data) => {
        if (!Array.isArray(data)) return;
        tableBody.innerHTML = data.length
          ? data
            .map(
              (rec) => {
                const badgeClass = rec.status === 'Present' ? 'bg-success' : 'bg-danger';
                return `<tr>
                  <td>${escapeHtml(rec.date)}</td>
                  <td>${escapeHtml(rec.time)}</td>
                  <td><span class="badge ${badgeClass}">${escapeHtml(rec.status)}</span></td>
                </tr>`;
              }
            )
            .join("")
          : `<tr><td colspan="3">No attendance records found</td></tr>`;
      })
      .catch((err) => {
        console.warn("loadAttendance:", err.message);
      });
  }

  /* -------------------------
     Small helper: escape HTML for inserted strings
  -------------------------*/
  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  /* -------------------------
     Form enhancement (optional)
     - Prevent double submits and show a simple disabled state
  -------------------------*/
  function initForms() {
    const forms = qsa(".form");
    forms.forEach((form) => {
      form.addEventListener("submit", function (ev) {
        const btn = form.querySelector("button[type='submit']");
        if (btn) {
          btn.disabled = true;
          btn.classList.add("disabled");
          // allow normal submit to proceed; re-enable on page navigation/failure handled server-side
        }
      });
    });
  }

  /* -------------------------
     Initialization on DOMContentLoaded
  -------------------------*/
  document.addEventListener("DOMContentLoaded", function () {
    initSidebarToggle();
    initSidebarLinks();
    initForms();

    // Show panel based on hash or default to profile
    const initial = (location.hash && location.hash.slice(1)) || "profile";
    showPanel(initial);

    // Try to load dynamic content (non-blocking)
    loadNotices();
    loadAttendance();
  });

  /* -------------------------
     Expose showPanel for inline onclick handlers (if used)
  -------------------------*/
  window.showPanel = showPanel;
})();

// Student attendance date filter
document.addEventListener('DOMContentLoaded', function () {
  const searchInput = document.getElementById('studentAttendanceSearch');
  if (searchInput) {
    searchInput.addEventListener('keyup', function () {
      const filter = this.value.toLowerCase();
      const rows = document.querySelectorAll('#studentAttendanceTable tbody tr');
      rows.forEach(row => {
        if (row.cells.length >= 1) {
          const date = row.cells[0].textContent.toLowerCase();
          row.style.display = date.includes(filter) ? '' : 'none';
        }
      });
    });
  }
});