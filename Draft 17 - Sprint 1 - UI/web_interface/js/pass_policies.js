function validatePassword(password) {
    const violations = [];

    // Enforce password policy
    if (password.length < 8) {
        violations.push("Minimum 8 characters required");
    }
    if (!/[A-Z]/.test(password)) {
        violations.push("At least 1 uppercase letter required");
    }
    if (!/[a-z]/.test(password)) {
        violations.push("At least 1 lowercase letter required");
    }
    if (!/[0-9]/.test(password)) {
        violations.push("At least 1 digit required");
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        violations.push("At least 1 special character required");
    }

    // Only check against HIBP if no policy violations
    if (violations.length === 0 && checkPwnedPassword(password)) {
        violations.push("Password has been found in a known data breach.");
    }

    return violations;
}

document.addEventListener("DOMContentLoaded", () => {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    const tooltip = document.createElement("div");
    tooltip.style.position = "absolute";
    tooltip.style.backgroundColor = "#f8d7da";
    tooltip.style.color = "#721c24";
    tooltip.style.border = "1px solid #f5c6cb";
    tooltip.style.padding = "10px";
    tooltip.style.borderRadius = "5px";
    tooltip.style.display = "none";
    tooltip.style.zIndex = "1000";
    document.body.appendChild(tooltip);

    passwordInputs.forEach((passwordInput) => {
        passwordInput.addEventListener("input", (event) => {
            const password = event.target.value;
            const violations = validatePassword(password);

            if (violations.length > 0) {
                tooltip.innerHTML = violations.join("<br>");
                const rect = passwordInput.getBoundingClientRect();
                tooltip.style.left = `${rect.left + window.scrollX}px`;
                tooltip.style.top = `${rect.bottom + window.scrollY + 5}px`;
                tooltip.style.display = "block";
            } else {
                tooltip.style.display = "none";
            }
        });

        passwordInput.addEventListener("blur", () => {
            tooltip.style.display = "none";
        });
    });
});

document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", async (e) => {
        const passwordInput = form.querySelector('input[type="password"]');
        if (!passwordInput) return;

        const password = passwordInput.value;
        const violations = validatePassword(password);

        // Optional async HIBP check
        if (violations.length === 0 && await checkPwnedPassword(password)) {
            violations.push("Password has been found in a known data breach.");
        }

        if (violations.length > 0) {
            e.preventDefault(); // 🔐 Block form submission
            alert("Please fix the following:\n\n" + violations.join("\n"));
        }
    });
});
