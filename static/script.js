// ======= HELPER MESSAGE DISPLAY =======
function showMessage(form, message, type = "success") {
  let msgBox = form.querySelector(".form-message");
  if (!msgBox) {
    msgBox = document.createElement("p");
    msgBox.className = "form-message";
    form.appendChild(msgBox);
  }
  msgBox.textContent = message;
  msgBox.style.color = type === "success" ? "#2ecc71" : "#e74c3c";
  msgBox.style.marginTop = "10px";
  msgBox.style.fontWeight = "500";
}

// ======= VALIDATION RULES =======
const nameRegex = /^[A-Za-z\s]{3,}$/;
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const phoneRegex = /^\d{10}$/;

// ======= INLINE ERROR HANDLERS =======
function showInlineError(input, message) {
  let existing = input.parentElement.querySelector(".error-msg");
  if (existing) existing.remove();

  const msg = document.createElement("span");
  msg.className = "error-msg";
  msg.textContent = message;
  input.classList.add("error");
  input.parentElement.appendChild(msg);
}

function clearInlineError(input) {
  input.classList.remove("error");
  const existing = input.parentElement.querySelector(".error-msg");
  if (existing) existing.remove();
}

// ======= VALIDATE FIELD FUNCTION =======
function validateField(input) {
  const value = input.value.trim();
  let valid = true;
  let msg = "";

  switch (input.id) {
    case "name":
      if (!nameRegex.test(value)) {
        valid = false;
        msg = "Full name should be at least 3 letters.";
      }
      break;

    case "email":
    case "loginEmail":
      if (!emailRegex.test(value)) {
        valid = false;
        msg = "Enter a valid email (e.g. abc@example.com)";
      }
      break;

    case "password":
    case "loginPassword":
      if (value.length < 6) {
        valid = false;
        msg = "Password must be at least 6 characters.";
      }
      break;

    case "phone":
      if (value && !phoneRegex.test(value)) {
        valid = false;
        msg = "Phone must be exactly 10 digits.";
      }
      break;

    case "dob":
      // DOB is optional, no validation needed
      break;
  }

  if (!valid) showInlineError(input, msg);
  else clearInlineError(input);

  return valid;
}

// ======= REAL-TIME VALIDATION =======
const registerFormInputs = document.querySelectorAll("#registerForm input");
if (registerFormInputs.length > 0) {
  registerFormInputs.forEach((input) => {
    input.addEventListener("input", () => validateField(input));
  });
}

// ======= REGISTER FORM =======
const registerForm = document.getElementById("registerForm");
if (registerForm) {
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const date = document.getElementById("dob").value;

    const inputs = registerForm.querySelectorAll("input");
    let allValid = true;
    inputs.forEach((inp) => {
      if (!validateField(inp)) allValid = false;
    });

    if (!allValid) {
      showMessage(registerForm, "Please fix errors before submitting.", "error");
      return;
    }

    try {
      const res = await fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password, phone, date }),
      });

      let data;
      try {
        const text = await res.text();
        data = JSON.parse(text);
      } catch {
        showMessage(registerForm, "Server error. Try again later.", "error");
        return;
      }

      if (res.ok) {
        // ✅ Redirect to dashboard after successful registration (user is auto-logged in)
        showMessage(registerForm, "Registration successful! Redirecting to dashboard...", "success");
        setTimeout(() => {
          window.location.href = "/dashboard";
        }, 1000);
      } else {
        // ❌ Show backend error inline if specific
        if (data.error?.includes("email")) {
          showInlineError(document.getElementById("email"), data.error);
        } else {
          showMessage(registerForm, data.error || "Registration failed", "error");
        }
      }
    } catch (err) {
      showMessage(registerForm, "Something went wrong. Try again.", "error");
      console.error(err);
    }
  });
}

// ======= LOGIN FORM =======
const loginForm = document.getElementById("loginForm");
if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const emailInput = document.getElementById("loginEmail");
    const passwordInput = document.getElementById("loginPassword");

    if (!emailInput || !passwordInput) {
      console.error("Login form inputs not found!");
      return;
    }

    // Validate fields
    const validEmail = validateField(emailInput);
    const validPass = validateField(passwordInput);
    if (!validEmail || !validPass) return;

    try {
      const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: emailInput.value.trim(),
          password: passwordInput.value.trim(),
        }),
      });

      let data;
      try {
        const text = await res.text();
        data = JSON.parse(text);
      } catch {
        showMessage(loginForm, "Server error. Try again later.", "error");
        return;
      }

      if (res.ok) {
        // ✅ Redirect after success
        window.location.href = "/dashboard";
      } else {
        // ❌ Show inline error message depending on backend response
        if (data.error?.includes("User") || data.error?.includes("email")){
          showInlineError(emailInput, data.error);
        } else if (data.error?.includes("password")) {
          showInlineError(passwordInput, data.error);
        } else {
          showMessage(loginForm, data.error || "Invalid credentials", "error");
        }
      }
    } catch (err) {
      console.error(err);
      showMessage(loginForm, "Something went wrong. Try again.", "error");
    }
  });
}
