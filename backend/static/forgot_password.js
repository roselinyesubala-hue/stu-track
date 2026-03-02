document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    const identifierInput = document.getElementById("identifier");

  form.addEventListener("submit", (e) => {
        let valid = true;

        // Basic validation
        if (identifierInput.value.trim() === "") {
            identifierInput.setCustomValidity("Please enter your username or email.");
            valid = false;
        } else {
            identifierInput.setCustomValidity("");
        }

        // Prevent submission if invalid
        if (!valid) {
            e.preventDefault();
            form.reportValidity();
        }
    });
    identifierInput.addEventListener("input", () => {
        if (identifierInput.value.trim() !== "") {
            identifierInput.setCustomValidity("");
        }
    });
});