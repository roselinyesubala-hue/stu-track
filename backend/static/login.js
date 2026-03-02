document.addEventListener("DOMContentLoaded", () => {
  const togglePassword = document.getElementById("togglePassword");
  const passwordField = document.getElementById("password");
  const usernameField = document.getElementById("username");
  const form = document.querySelector("form");

  // Show/hide password toggle
  togglePassword.addEventListener("click", () => {
    const type = passwordField.type === "password" ? "text" : "password";
    passwordField.type = type;
    togglePassword.textContent = type === "password" ? "👁️" : "🚫";
  });

  // Form validation
  form.addEventListener("submit", (e) => {
    let valid = true;

    if (usernameField.value.trim() === "") {
      usernameField.setCustomValidity("Username is required.");
      valid = false;
    } else {
      usernameField.setCustomValidity("");
    }

    if (passwordField.value.length < 6) {
      passwordField.setCustomValidity("Password must be at least 6 characters.");
      valid = false;
    } else {
      passwordField.setCustomValidity("");
    }

    if (!valid) {
      e.preventDefault();
      form.reportValidity();
    }
  });
});