// Run before page paint; first-time visitors meet NutriAI before account forms.
(() => {
    try {
        const page = location.pathname.split('/').pop() || 'index.html';
        if (!localStorage.getItem('nutri_token') && localStorage.getItem('nutri_intro_completed_v1') !== 'true' && ['index.html', 'login.html', 'register.html'].includes(page)) {
            location.replace('welcome.html');
        }
    } catch (_) { /* Restricted storage must not trap visitors in a redirect loop. */ }
})();
