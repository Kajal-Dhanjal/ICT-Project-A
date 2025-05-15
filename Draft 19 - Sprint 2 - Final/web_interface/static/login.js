/**
 * Login page JavaScript for ElderSafe Connect
 * 
 * Handles the login form submission and displays notifications for errors.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS
    if (typeof AOS !== 'undefined') {
        AOS.init({ once: true });
    }

    // Handle form submission with fetch API
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('/login', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) {
                    // Show error notification for invalid login
                    showErrorNotification('Invalid credentials. Please try again.', 5000);
                    throw new Error('Login failed');
                }
                return response.text();
            })
            .then(data => {
                // Successful login - redirect based on the response
                window.location.href = data.includes('/mfa/setup') ? '/mfa/setup' : '/mfa';
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }
});