/* Canonical API values stay in centimetres and kilograms. */
(function (root) {
    const units = {
        height(value, unit, inches = 0) {
            const n = Number(value), i = Number(inches);
            if (!Number.isFinite(n) || n <= 0) return NaN;
            if (unit === 'ft') return Number.isFinite(i) && i >= 0 && i < 12 && Number.isInteger(n) ? (n * 12 + i) * 2.54 : NaN;
            return unit === 'm' ? n * 100 : n;
        },
        weight(value, unit) {
            const n = Number(value);
            return Number.isFinite(n) && n > 0 ? n * (unit === 'lb' ? 0.45359237 : 1) : NaN;
        }
    };
    if (typeof module !== 'undefined') module.exports = units;
    if (!root.document) return;
    root.setupMeasurements = function () {
        const fields = [];
        for (const [id, title, kind] of [['height_cm', 'Height', 'height'], ['weight_kg', 'Current weight', 'weight'], ['target_weight_kg', 'Target weight', 'weight']]) {
            const canonical = document.getElementById(id);
            if (!canonical || document.getElementById(id + '_display')) continue;
            const label = canonical.previousElementSibling;
            if (label?.tagName === 'LABEL') { label.textContent = title; label.htmlFor = id + '_display'; }
            canonical.type = 'hidden'; canonical.required = false;
            const group = document.createElement('div'); group.className = 'measurement-control';
            const options = kind === 'height' ? '<option value="cm">cm</option><option value="ft">ft + in</option><option value="m">metres</option>' : '<option value="kg">kg</option><option value="lb">lb</option>';
            group.innerHTML = `<div class="measurement-row"><input id="${id}_display" type="number" min="0.01" step="any" required class="form-control" aria-label="${title}"><select id="${id}_unit" class="form-select" aria-label="${title} unit">${options}</select></div>${kind === 'height' ? `<label class="inches-field" hidden>Inches<input type="number" min="0" max="11.99" step="any" value="0" class="form-control" aria-label="Additional inches"></label>` : ''}<small class="measurement-equivalent" aria-live="polite"></small>`;
            canonical.after(group);
            const input = group.querySelector('input'), select = group.querySelector('select'), inches = group.querySelector('.inches-field input');
            let oldUnit = select.value;
            const sync = () => {
                const val = kind === 'height' ? units.height(input.value, select.value, inches?.value || 0) : units.weight(input.value, select.value);
                input.setCustomValidity(Number.isFinite(val) ? '' : 'Enter a positive measurement. For feet, use whole feet and 0–11.99 inches.');
                canonical.value = Number.isFinite(val) ? String(val) : '';
                group.querySelector('small').textContent = Number.isFinite(val) ? `${val.toFixed(1)} ${kind === 'height' ? 'cm' : 'kg'} · saved measurement` : '';
                canonical.dispatchEvent(new Event('change', { bubbles: true }));
                return Number.isFinite(val);
            };
            const refresh = () => {
                const val = Number(canonical.value);
                if (!(val > 0)) return;
                if (select.value === 'ft') {
                    const total = Math.round(val / 2.54 * 100) / 100;
                    input.value = Math.floor(total / 12); inches.value = (total % 12).toFixed(2);
                } else input.value = (val / (select.value === 'm' ? 100 : select.value === 'lb' ? 0.45359237 : 1)).toFixed(2);
                input.setCustomValidity('');
                group.querySelector('small').textContent = `${val.toFixed(1)} ${kind === 'height' ? 'cm' : 'kg'} · saved measurement`;
            };
            select.addEventListener('change', () => {
                // Convert the previously entered value before changing presentation.
                const val = kind === 'height' ? units.height(input.value, oldUnit, inches?.value || 0) : units.weight(input.value, oldUnit);
                if (Number.isFinite(val)) canonical.value = val;
                if (inches) { inches.parentElement.hidden = select.value !== 'ft'; inches.required = select.value === 'ft'; }
                input.step = select.value === 'ft' ? '1' : 'any';
                oldUnit = select.value; refresh();
            });
            input.addEventListener('input', sync); inches?.addEventListener('input', sync);
            fields.push({ sync, refresh }); refresh();
        }
        root.syncMeasurements = () => fields.map(f => f.sync()).every(Boolean);
        root.refreshMeasurements = () => fields.forEach(f => f.refresh());
    };
})(typeof window !== 'undefined' ? window : globalThis);
