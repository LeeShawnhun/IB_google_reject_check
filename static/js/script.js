document.addEventListener('DOMContentLoaded', (event) => {
    const form = document.querySelector('form');
    const fileInput = document.querySelector('input[type="file"]');

    form.addEventListener('submit', (e) => {
        if (fileInput.files.length === 0) {
            e.preventDefault();
            alert('Please select at least one file.');
        }
    });
});