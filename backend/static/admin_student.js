document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".student-form");
  if (!form) return;

  // --- Existing validation on submit ---
  form.addEventListener("submit", (e) => {
    const studentId = document.getElementById("student_id");
    const studentName = document.getElementById("student_name");
    const parentEmail = document.getElementById("parent_email");
    const guardianEmail = document.getElementById("guardian_email");

    let valid = true;

    if (studentId.value.trim() === "") {
      studentId.setCustomValidity("Student ID is required.");
      valid = false;
    } else {
      studentId.setCustomValidity("");
    }

    if (studentName.value.trim() === "") {
      studentName.setCustomValidity("Student name is required.");
      valid = false;
    } else {
      studentName.setCustomValidity("");
    }

    if (parentEmail.value.trim() !== "" && !/^[^@]+@[^@]+\.[^@]+$/.test(parentEmail.value)) {
      parentEmail.setCustomValidity("Enter a valid parent email.");
      valid = false;
    } else {
      parentEmail.setCustomValidity("");
    }

    if (guardianEmail.value.trim() !== "" && !/^[^@]+@[^@]+\.[^@]+$/.test(guardianEmail.value)) {
      guardianEmail.setCustomValidity("Enter a valid guardian email.");
      valid = false;
    } else {
      guardianEmail.setCustomValidity("");
    }

    // Additional check for student contact (if you want to enforce 10 digits on submit)
    const studentContact = document.getElementById("student_contact");
    if (studentContact && studentContact.value.trim() !== "" && !/^\d{10}$/.test(studentContact.value)) {
      studentContact.setCustomValidity("Student contact must be exactly 10 digits.");
      valid = false;
    } else if (studentContact) {
      studentContact.setCustomValidity("");
    }

    if (!valid) {
      e.preventDefault();
      form.reportValidity();
    }
  });

  // --- New: Live digit restriction for contact fields ---
  document.querySelectorAll('input[type="tel"]').forEach(input => {
    input.addEventListener('input', function(e) {
      this.value = this.value.replace(/\D/g, '').slice(0, 10);
    });
  });

  // --- New: Bootstrap validation styling (if you're using Bootstrap) ---
  // This enables the was-validated class on form submit
  form.addEventListener('submit', function(event) {
    if (!form.checkValidity()) {
      event.preventDefault();
      event.stopPropagation();
    }
    form.classList.add('was-validated');
  }, false);
});