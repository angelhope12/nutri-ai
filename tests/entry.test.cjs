const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../frontend/scripts/entry.js'), 'utf8');
function destination(page, storage = {}, blocked = false) {
  let redirect;
  vm.runInNewContext(source, {
    location: {pathname: page, replace: value => { redirect = value; }},
    localStorage: {getItem: key => { if (blocked) throw new Error('Storage disabled'); return storage[key] || null; }}
  });
  return redirect;
}
test('first visit enters welcome from home and account routes', () => {
  for (const page of ['/', '/index.html', '/login.html', '/register.html']) assert.equal(destination(page), 'welcome.html');
});
test('completed introduction allows login without another welcome', () => {
  assert.equal(destination('/login.html', {nutri_intro_completed_v1: 'true'}), undefined);
});
test('signed-in visitors keep their dashboard', () => {
  assert.equal(destination('/', {nutri_token: 'test-session'}), undefined);
});
test('recovery and profile routes are not interrupted by the entry gate', () => {
  for (const page of ['/forgot-password.html', '/onboarding.html', '/profile.html']) assert.equal(destination(page), undefined);
});
test('blocked browser storage does not create a redirect loop', () => {
  assert.equal(destination('/login.html', {}, true), undefined);
});
