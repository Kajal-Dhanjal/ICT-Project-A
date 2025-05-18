/**
 * Forgot Password page JavaScript for ElderSafe Connect
 * 
 * Handles the forgot password form submission and displays notifications.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS
    if (typeof AOS !== 'undefined') {
        AOS.init({ once: true });
    }
    
    // Handle the form submission
    const forgotPasswordForm = document.getElementById('forgot-password-form');
    if (forgotPasswordForm) {
        forgotPasswordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const emailInput = document.getElementById('email');
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                // Always show success message for security purposes
                // This way an attacker can't determine if an email exists in the system
                showSuccessNotification('If your email is registered, you\'ll receive a password reset link.', 6000);
                
                // Clear the form
                emailInput.value = '';
                
                return response.json().catch(() => {
                    // If not JSON, we still continue with default message
                    return { success: true };
                });
            })
            .then(data => {
                // We've already shown the standard message above
                // No need to do anything here
            })
            .catch(error => {
                console.error('Error:', error);
                // Even on error, we don't tell user - security best practice
            });
        });
    }
});