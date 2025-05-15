// This file implements client-side password validation
// Using HIBP (Have I Been Pwned) API for checking password breaches

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

    return violations;
}

// This function checks if a password has been involved in known data breaches
// Uses the k-anonymity model of the HIBP API for secure checking
async function checkPwnedPassword(password) {
    try {
        // Generate SHA-1 hash of the password
        const encoder = new TextEncoder();
        const data = encoder.encode(password);
        const hashBuffer = await crypto.subtle.digest('SHA-1', data);
        
        // Convert hash to uppercase hex string
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
        
        // Get the first 5 characters (prefix) to send to the API
        const prefix = hashHex.substring(0, 5);
        const suffix = hashHex.substring(5);
        
        // Make request to HIBP API
        const response = await fetch(`https://api.pwnedpasswords.com/range/${prefix}`);
        
        if (!response.ok) {
            console.error('Error checking password against HIBP');
            return false; // Assume not pwned if service is unavailable
        }
        
        // Check if the suffix exists in the response
        const text = await response.text();
        const lines = text.split('\n');
        
        for (const line of lines) {
            const [hashSuffix, count] = line.split(':');
            if (hashSuffix.trim() === suffix) {
                return true; // Password has been pwned
            }
        }
        
        return false; // Password has not been pwned
        
    } catch (error) {
        console.error('Error during password check:', error);
        return false; // Assume not pwned if there's an error
    }
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
    tooltip.style.maxWidth = "300px";
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
            setTimeout(() => {
                tooltip.style.display = "none";
            }, 300);
        });
    });
});

// Form submission validation
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("form").forEach((form) => {
        form.addEventListener("submit", async (e) => {
            const passwordInput = form.querySelector('input[type="password"]');
            if (!passwordInput) return;

            const password = passwordInput.value;
            const violations = validatePassword(password);

            // Optional async HIBP check
            if (violations.length === 0) {
                const isPwned = await checkPwnedPassword(password);
                if (isPwned) {
                    violations.push("Password has been found in a known data breach.");
                }
            }

            if (violations.length > 0) {
                e.preventDefault(); // 🔐 Block form submission
                
                // Create a formatted error message
                const errorMessage = document.createElement('div');
                errorMessage.className = 'error-message';
                errorMessage.style.display = 'block';
                errorMessage.style.marginTop = '10px';
                
                const title = document.createElement('strong');
                title.textContent = 'Please fix the following issues:';
                errorMessage.appendChild(title);
                
                const list = document.createElement('ul');
                list.style.marginLeft = '20px';
                list.style.marginTop = '5px';
                
                violations.forEach(violation => {
                    const item = document.createElement('li');
                    item.textContent = violation;
                    list.appendChild(item);
                });
                
                errorMessage.appendChild(list);
                
                // Remove any existing error messages
                const existingError = form.querySelector('.error-message');
                if (existingError) {
                    existingError.remove();
                }
                
                // Insert the error message before the submit button
                const submitButton = form.querySelector('button[type="submit"], input[type="submit"], .submit-btn, .register-btn');
                if (submitButton) {
                    submitButton.parentNode.insertBefore(errorMessage, submitButton);
                } else {
                    form.appendChild(errorMessage);
                }
                
                // Focus back on the password field
                passwordInput.focus();
            }
        });
    });
});