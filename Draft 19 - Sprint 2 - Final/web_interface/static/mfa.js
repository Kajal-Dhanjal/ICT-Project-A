/**
 * MFA Verification page JavaScript for ElderSafe Connect
 * 
 * Handles the MFA form submission and displays notifications for errors.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS
    if (typeof AOS !== 'undefined') {
        AOS.init({ once: true });
    }
    
    // Handle MFA form submission
    const mfaForm = document.getElementById('mfa-form');
    if (mfaForm) {
        mfaForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const otpInput = document.getElementById('otp');
            
            // Basic validation
            if (!otpInput.value.trim()) {
                showErrorNotification('Please enter the OTP code from your authenticator app.');
                otpInput.focus();
                return;
            }
            
            fetch('/mfa/validate', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (response.redirected) {
                    // Success - follow the redirect
                    window.location.href = response.url;
                    return null;
                }
                return response.text();
            })
            .then(html => {
                if (html) {
                    // Extract error message from the response HTML
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const errorMsg = doc.querySelector('.error-msg');
                    
                    if (errorMsg) {
                        showErrorNotification(errorMsg.textContent);
                    } else {
                        showErrorNotification('Invalid OTP code. Please try again.');
                    }
                    
                    // Clear and focus the OTP field
                    otpInput.value = '';
                    otpInput.focus();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showErrorNotification('An unexpected error occurred. Please try again.');
                
                // Clear the OTP field
                otpInput.value = '';
                otpInput.focus();
            });
        });
    }
    
    // Show OTP section by default
    const showOTPBtn = document.getElementById('show-otp-btn');
    if (showOTPBtn) {
        showOTPBtn.classList.add('active');
        document.getElementById('mfa-section').style.display = 'block';
    }
});