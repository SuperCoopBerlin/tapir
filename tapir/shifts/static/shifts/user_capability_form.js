document.addEventListener('DOMContentLoaded', function() {
    const unlimitedCheckbox = document.getElementById('id_unlimited');

    if (!unlimitedCheckbox) return;

    const startDateField = getFormField('id_start_date');
    const endDateField = getFormField('id_end_date');

    if (!startDateField || !endDateField) return;

    function getFormField(fieldId) {
        const field = document.getElementById(fieldId);
        if (!field) return null;
        return field.closest('.form-group')
            || field.closest('.form-row')
            || field.parentElement;
    }

    function toggleFields() {
        const isUnlimited = unlimitedCheckbox.checked;
        startDateField.style.display = isUnlimited ? 'none' : 'block';
        endDateField.style.display = isUnlimited ? 'none' : 'block';
    }

    unlimitedCheckbox.addEventListener('change', toggleFields);

    toggleFields();
});
