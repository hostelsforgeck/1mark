// static/js/scripts.js

// Example: Fade out flash messages after 3 seconds
window.addEventListener('load', () => {
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            new bootstrap.Alert(alert).close();
        });
    }, 3000);
});
