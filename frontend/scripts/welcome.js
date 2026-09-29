(() => {
    'use strict';
    const key = 'nutri_intro_completed_v1';
    const slides = [
        ['YOUR EVERYDAY NUTRITION COMPANION', 'Good food.', 'Better understanding.', 'Meet NutriAI. Get to know your meals, keep a food journal, and build a more mindful relationship with what’s on your plate.', 'A fresh start, one meal at a time.'],
        ['LESS GUESSWORK, MORE AWARENESS', 'Meet your meal.', 'Discover what’s inside.', 'Take a photo or type a food to explore estimated calories and nutrients. Check the food and portion before adding it to your journal.', 'Your portion matters. You’re in control.'],
        ['SMALL STEPS ADD UP', 'Find your rhythm.', 'See your progress.', 'Bring your meals, daily nutrition totals, and weight history together. Notice patterns and make room for habits that work for you.', 'Your journey, at your own pace.']
    ];
    let step = 0;
    const $ = id => document.getElementById(id);
    function render(focus = true) {
        const slide = slides[step];
        $('introEyebrow').textContent = slide[0];
        $('introTitle').replaceChildren(document.createTextNode(slide[1]), document.createElement('br'));
        const emphasis = document.createElement('em'); emphasis.textContent = slide[2]; $('introTitle').append(emphasis);
        $('introDescription').textContent = slide[3];
        $('introFeature').querySelector('span').textContent = `0${step + 1}`;
        $('introFeature').querySelector('p').textContent = slide[4];
        $('stepCount').textContent = `0${step + 1} / 03`;
        document.querySelectorAll('.step-dot').forEach((dot, i) => dot.classList.toggle('active', i === step));
        $('backIntro').hidden = step === 0;
        $('nextIntro').textContent = step === 2 ? 'Let’s get started →' : 'Next →';
        $('introProgress').hidden = false; $('introControls').hidden = false;
        $('accountChoices').hidden = true; $('skipIntro').hidden = false;
        if (focus) $('introTitle').focus();
    }
    function finish() {
        try { localStorage.setItem(key, 'true'); } catch (_) { /* Navigation still works without storage. */ }
        $('introEyebrow').textContent = 'WELCOME TO YOUR NEXT CHAPTER';
        $('introTitle').textContent = 'Make yourself at home.';
        $('introDescription').textContent = 'Create your NutriAI account to start your food journal, or log in to pick up where you left off.';
        $('introFeature').querySelector('span').textContent = '✦';
        $('introFeature').querySelector('p').textContent = 'A little awareness with every bite.';
        $('introProgress').hidden = true; $('introControls').hidden = true; $('skipIntro').hidden = true;
        $('accountChoices').hidden = false; $('introTitle').focus();
    }
    $('nextIntro').addEventListener('click', () => step < 2 ? (step++, render()) : finish());
    $('backIntro').addEventListener('click', () => { step = Math.max(0, step - 1); render(); });
    $('skipIntro').addEventListener('click', finish);
    $('replayIntro').addEventListener('click', () => { step = 0; render(); });
    try { if (localStorage.getItem(key) === 'true' && !new URLSearchParams(location.search).has('replay')) finish(); } catch (_) {}
})();
