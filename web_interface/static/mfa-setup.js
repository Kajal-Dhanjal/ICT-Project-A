/**
 * MFA Setup page JavaScript for ElderSafe Connect
 * 
 * Handles the MFA setup process and displays notifications.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS
    if (typeof AOS !== 'undefined') {
        AOS.init({ once: true });
    }
    
    // Show info notification with instructions
    showInfoNotification('Set up your authenticator app using the QR code or manual entry code', 8000);
    
    // Handle continue button click
    const continueBtn = document.getElementById('continue-btn');
    if (continueBtn) {
        continueBtn.addEventListener('click', function(e) {
            // Show loading message
            showSuccessNotification('MFA setup complete! Redirecting to verification...', 2000);
            
            // Don't prevent default - allow normal navigation to /mfa page
        });
    }
    
    // Copy code to clipboard functionality
    const secretCode = document.querySelector('.secret-code');
    if (secretCode) {
        secretCode.addEventListener('click', function() {
            // Create a temporary element to copy the text
            const tempElement = document.createElement('textarea');
            tempElement.value = this.textContent;
            document.body.appendChild(tempElement);
            tempElement.select();
            
            try {
                // Copy the text to clipboard
                document.execCommand('copy');
                showSuccessNotification('Secret code copied to clipboard', 3000);
            } catch (err) {
                showErrorNotification('Failed to copy code. Please select and copy manually.');
            }
            
            // Remove the temporary element
            document.body.removeChild(tempElement);
        });
        
        // Add title attribute to hint about clicking to copy
        secretCode.title = 'Click to copy to clipboard';
        
        // Add pointer cursor to indicate it's clickable
        secretCode.style.cursor = 'pointer';
    }
});