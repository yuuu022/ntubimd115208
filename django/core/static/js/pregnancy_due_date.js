/**
 * EDD from LMP (first day of last menstrual period).
 * Uses Naegele's rule (month −3, day +7, year +1), equivalent to LMP + 280 days.
 */
(function () {
    function parseLocalDate(ymd) {
        const parts = ymd.split('-').map(Number);
        if (parts.length !== 3 || parts.some(Number.isNaN)) {
            return null;
        }
        return new Date(parts[0], parts[1] - 1, parts[2]);
    }

    function formatLocalDate(date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    function dueDateFromLMP(ymd) {
        const lmp = parseLocalDate(ymd);
        if (!lmp) {
            return '';
        }
        const due = new Date(lmp);
        due.setFullYear(due.getFullYear() + 1);
        due.setMonth(due.getMonth() - 3);
        due.setDate(due.getDate() + 7);
        return formatLocalDate(due);
    }

    function bindDueDateAutoCalc(menstruationInput, expecteddateInput) {
        if (!menstruationInput || !expecteddateInput) {
            return;
        }

        function syncExpectedDate() {
            const lmp = menstruationInput.value;
            if (!lmp) {
                return;
            }
            const calculated = dueDateFromLMP(lmp);
            if (calculated) {
                expecteddateInput.value = calculated;
            }
        }

        menstruationInput.addEventListener('input', syncExpectedDate);
        menstruationInput.addEventListener('change', syncExpectedDate);
    }

    window.PregnancyDueDate = { dueDateFromLMP, bindDueDateAutoCalc };
})();
