<!-- 
Template snippet untuk validasi file size di client-side.
Tambahkan ke template upload dokumen (superadmin/dokumen.html atau admin/dokumen.html)

Nama file ini bisa disimpan di static/js/upload-validation.js
Kemudian include di template:
<script src="{{ url_for('static', filename='js/upload-validation.js') }}"></script>
-->

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_FILE_SIZE_MB = 10;

document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file-input');
    const submitButton = document.getElementById('submit-upload');
    const errorMessage = document.getElementById('file-error');

    if (!fileInput) return;

    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        
        // Clear previous error message
        if (errorMessage) {
            errorMessage.textContent = '';
            errorMessage.style.display = 'none';
        }

        if (!file) {
            return;
        }

        // Cek ukuran file
        if (file.size > MAX_FILE_SIZE) {
            const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
            const errorText = `File terlalu besar: ${fileSizeMB}MB (maksimal ${MAX_FILE_SIZE_MB}MB)`;
            
            if (errorMessage) {
                errorMessage.textContent = errorText;
                errorMessage.style.display = 'block';
                errorMessage.classList.add('alert', 'alert-danger');
            } else {
                // Fallback: alert jika element belum ada
                alert(errorText);
            }
            
            // Disable submit button
            if (submitButton) {
                submitButton.disabled = true;
            }
            
            return;
        }

        // Enable submit button jika semua validasi pass
        if (submitButton) {
            submitButton.disabled = false;
        }
    });
});
