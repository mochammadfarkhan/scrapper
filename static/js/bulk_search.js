// Bulk Search JavaScript Functionality
let progressInterval;
let logEventSource;
let isCompleted = false;
let logsVisible = false;
let rowCounter = 0;

// Initialize page when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    console.log('Bulk search page loaded, initializing...');

    // Add initial row
    addTableRow();

    // Check if scraping is already running on page load
    checkInitialScrapingStatus();
});

// Table Management Functions
function addTableRow() {
    rowCounter++;
    const tableBody = document.getElementById('searchTableBody');
    const newRow = document.createElement('tr');
    newRow.id = `row-${rowCounter}`;

    newRow.innerHTML = `
        <td>
            <input type="text" class="form-control" name="keyword[]" placeholder="e.g., cats, dogs, cars" required>
            <div class="invalid-feedback">Please enter a keyword</div>
        </td>
        <td>
            <input type="text" class="form-control" name="className[]" placeholder="e.g., animals, vehicles" required>
            <div class="invalid-feedback">Please enter a class name</div>
        </td>
        <td>
            <input type="text" class="form-control" name="destinationFolder[]" placeholder="Optional: custom folder path">
            <div class="form-text small">Leave empty to use global setting</div>
        </td>
        <td class="text-center">
            <button type="button" class="btn btn-outline-danger btn-sm delete-row-btn" onclick="deleteTableRow('row-${rowCounter}')">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;

    tableBody.appendChild(newRow);
    console.log(`Added row ${rowCounter}`);

    // Focus on the keyword input of the new row
    const keywordInput = newRow.querySelector('input[name="keyword[]"]');
    if (keywordInput) {
        keywordInput.focus();
    }
}

function deleteTableRow(rowId) {
    const tableBody = document.getElementById('searchTableBody');
    const rowToDelete = document.getElementById(rowId);

    // Prevent deleting the last row
    if (tableBody.children.length <= 1) {
        alert('You must have at least one search entry.');
        return;
    }

    if (rowToDelete) {
        rowToDelete.remove();
        console.log(`Deleted row ${rowId}`);
    }
}

// Form Validation and Data Collection
function validateBulkSearchForm() {
    const tableBody = document.getElementById('searchTableBody');
    const rows = tableBody.querySelectorAll('tr');
    const imagesPerClass = document.getElementById('images_per_class').value;

    // Clear previous validation
    clearValidationErrors();

    let isValid = true;
    let validEntries = 0;

    // Validate each row
    rows.forEach((row, index) => {
        const keywordInput = row.querySelector('input[name="keyword[]"]');
        const classNameInput = row.querySelector('input[name="className[]"]');
        const destinationFolderInput = row.querySelector('input[name="destinationFolder[]"]');

        const keyword = keywordInput.value.trim();
        const className = classNameInput.value.trim();
        const destinationFolder = destinationFolderInput.value.trim();

        if (keyword && className) {
            validEntries++;
            // Clear any previous validation errors for valid rows
            keywordInput.classList.remove('is-invalid');
            classNameInput.classList.remove('is-invalid');
            destinationFolderInput.classList.remove('is-invalid');
        } else {
            // Show validation errors for incomplete rows
            if (!keyword) {
                keywordInput.classList.add('is-invalid');
                isValid = false;
            }
            if (!className) {
                classNameInput.classList.add('is-invalid');
                isValid = false;
            }
        }

        // Validate destination folder format if provided
        if (destinationFolder && !/^[a-zA-Z0-9_\-\s\/\\]*$/.test(destinationFolder)) {
            destinationFolderInput.classList.add('is-invalid');
            isValid = false;
        }
    });

    // Validate images per class
    const imagesPerClassNum = parseInt(imagesPerClass);
    if (!imagesPerClass || imagesPerClassNum < 1 || imagesPerClassNum > 500) {
        showValidationError('images_per_class', 'Please enter a number between 1 and 500');
        isValid = false;
    }

    // Check if we have at least one valid entry
    if (validEntries === 0) {
        alert('Please add at least one complete keyword/class name pair.');
        isValid = false;
    }

    return isValid;
}

function collectBulkSearchData() {
    const tableBody = document.getElementById('searchTableBody');
    const rows = tableBody.querySelectorAll('tr');
    const searchEntries = [];

    rows.forEach(row => {
        const keyword = row.querySelector('input[name="keyword[]"]').value.trim();
        const className = row.querySelector('input[name="className[]"]').value.trim();
        const destinationFolder = row.querySelector('input[name="destinationFolder[]"]').value.trim();

        if (keyword && className) {
            searchEntries.push({
                keyword: keyword,
                className: className,
                destinationFolder: destinationFolder || null // null if empty, will use global setting
            });
        }
    });

    return {
        search_entries: searchEntries,
        images_per_class: parseInt(document.getElementById('images_per_class').value),
        destination_folder: document.getElementById('destination_folder').value.trim()
    };
}

// Main Bulk Search Function
function startBulkSearch() {
    console.log('Start bulk search button clicked');

    // Validate form inputs
    if (!validateBulkSearchForm()) {
        console.log('Bulk search validation failed');
        return;
    }

    console.log('Bulk search validation passed');

    // Get button and update UI
    const startBtn = document.getElementById('startBulkSearchBtn');
    if (startBtn) {
        startBtn.disabled = true;
        startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Starting Bulk Search...';
    }

    // Collect form data
    const formData = collectBulkSearchData();
    console.log('Bulk search data collected:', formData);

    // Send AJAX request
    sendBulkSearchRequest(formData);
}

function sendBulkSearchRequest(formData) {
    console.log('Sending bulk search request...');

    fetch('/perform-bulk-search', {
        method: 'POST',
        body: JSON.stringify(formData),
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            console.log('Response received:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('JSON response:', data);
            handleBulkSearchResponse(data);
        })
        .catch(error => {
            console.error('Request failed:', error);
            handleBulkSearchError(error.message);
        });
}

function handleBulkSearchResponse(data) {
    if (data.status === 'success') {
        console.log('Bulk search started successfully');
        showProgressSection();
        startProgressMonitoring();
    } else {
        // Check if error is because scraping is already running
        if (data.message && data.message.includes('already in progress')) {
            console.log('Scraping already in progress, showing progress section');
            showProgressSection();
            startProgressMonitoring();
        } else {
            console.log('Bulk search failed:', data.message);
            handleBulkSearchError(data.message || 'Unknown error occurred');
        }
    }
}

function handleBulkSearchError(errorMessage) {
    alert('Error: ' + errorMessage);
    resetStartButton();
}

function resetStartButton() {
    const startBtn = document.getElementById('startBulkSearchBtn');
    if (startBtn) {
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="fas fa-rocket me-2"></i>Start Bulk Search';
    }
}

// Validation Helper Functions
function showValidationError(fieldId, message) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.classList.add('is-invalid');

        // Find or create error message element
        let errorElement = field.parentNode.querySelector('.invalid-feedback');
        if (errorElement) {
            errorElement.textContent = message;
        }
    }
}

function clearValidationErrors() {
    // Clear table validation errors
    const tableInputs = document.querySelectorAll('#searchTable input');
    tableInputs.forEach(input => {
        input.classList.remove('is-invalid');
    });

    // Clear other field validation errors
    const imagesPerClassField = document.getElementById('images_per_class');
    if (imagesPerClassField) {
        imagesPerClassField.classList.remove('is-invalid');
    }
}

// Progress Monitoring Functions (reused from index.html)
function checkInitialScrapingStatus() {
    fetch('/api/scraping_status')
        .then(response => response.json())
        .then(data => {
            if (data.is_running) {
                console.log('Scraping already in progress, showing progress section');
                showProgressSection();
                startProgressMonitoring();
            }
        })
        .catch(error => {
            console.log('Could not check initial scraping status:', error);
        });
}

function showProgressSection() {
    console.log('showProgressSection() called');
    const formSection = document.getElementById('formSection');
    const progressSection = document.getElementById('progressSection');

    if (formSection && progressSection) {
        console.log('Hiding form section and showing progress section');
        formSection.style.display = 'none';
        progressSection.style.display = 'block';
    }
}

function resetToForm() {
    console.log('Resetting to form view');

    // Reset form inputs
    const tableBody = document.getElementById('searchTableBody');
    tableBody.innerHTML = '';
    rowCounter = 0;
    addTableRow(); // Add one initial row

    document.getElementById('images_per_class').value = '100';
    document.getElementById('destination_folder').value = '';

    // Clear validation errors
    clearValidationErrors();

    // Reset start button
    resetStartButton();

    // Reset progress variables
    isCompleted = false;
    logsVisible = false;

    // Close log stream if open
    if (logEventSource) {
        logEventSource.close();
        logEventSource = null;
    }

    // Clear progress interval
    if (progressInterval) {
        clearInterval(progressInterval);
    }

    // Reset progress display
    resetProgressDisplay();

    // Show form section and hide progress
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('formSection').style.display = 'block';
}

function resetProgressDisplay() {
    // Reset progress bar
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    if (progressBar && progressText) {
        progressBar.style.width = '0%';
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
        progressText.textContent = 'Initializing...';
    }

    // Reset status message
    const statusMessage = document.getElementById('statusMessage');
    const statusText = document.getElementById('statusText');
    if (statusMessage && statusText) {
        statusMessage.className = 'alert alert-info';
        statusText.textContent = 'Preparing to start bulk scraping...';
    }

    // Reset spinner
    const loadingSpinner = document.getElementById('loadingSpinner');
    if (loadingSpinner) {
        loadingSpinner.style.display = 'block';
    }

    // Hide completion actions
    const completionActions = document.getElementById('completionActions');
    if (completionActions) {
        completionActions.style.display = 'none';
    }

    // Reset logs
    const logDisplay = document.getElementById('logDisplay');
    if (logDisplay) {
        logDisplay.innerHTML = '<div class="text-muted text-center p-3"><i class="fas fa-clock me-2"></i>Waiting for logs...</div>';
    }

    // Reset log buttons
    const toggleLogs = document.getElementById('toggleLogs');
    const downloadLogs = document.getElementById('downloadLogs');
    const clearLogsBtn = document.getElementById('clearLogs');

    if (toggleLogs) {
        toggleLogs.innerHTML = '<i class="fas fa-eye me-1"></i>Show Details';
    }
    if (downloadLogs) {
        downloadLogs.disabled = true;
    }
    if (clearLogsBtn) {
        clearLogsBtn.disabled = true;
    }

    // Hide logs container
    const logsContainer = document.getElementById('logsContainer');
    if (logsContainer) {
        logsContainer.style.display = 'none';
    }
    logsVisible = false;
}

// Progress Monitoring Functions (from index.html)
function startProgressMonitoring() {
    console.log('Starting progress monitoring...');

    // Start polling for progress updates
    progressInterval = setInterval(updateProgress, 1000);

    // Start log streaming
    startLogStreaming();
}

function updateProgress() {
    fetch('/api/scraping_status')
        .then(response => response.json())
        .then(data => {
            updateProgressDisplay(data);

            if (!data.is_running && !isCompleted) {
                console.log('Scraping completed, stopping progress monitoring');
                stopProgressMonitoring();
                showCompletionActions();
                isCompleted = true;
            }
        })
        .catch(error => {
            console.error('Error fetching progress:', error);
        });
}

function updateProgressDisplay(data) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const statusMessage = document.getElementById('statusMessage');
    const statusText = document.getElementById('statusText');

    if (progressText && data.progress) {
        progressText.textContent = data.progress;
    }

    if (statusText && data.progress) {
        statusText.textContent = data.progress;
    }

    // Update progress bar based on status
    if (progressBar) {
        if (data.is_running) {
            progressBar.style.width = '100%';
            progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-info';
        } else if (isCompleted) {
            progressBar.style.width = '100%';
            progressBar.className = 'progress-bar bg-success';
            if (progressText) {
                progressText.textContent = 'Completed!';
            }
        }
    }

    // Update status message styling
    if (statusMessage) {
        if (data.is_running) {
            statusMessage.className = 'alert alert-info';
        } else if (isCompleted) {
            statusMessage.className = 'alert alert-success';
        }
    }
}

function stopProgressMonitoring() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }

    if (logEventSource) {
        logEventSource.close();
        logEventSource = null;
    }

    // Hide spinner
    const loadingSpinner = document.getElementById('loadingSpinner');
    if (loadingSpinner) {
        loadingSpinner.style.display = 'none';
    }
}

function showCompletionActions() {
    const completionActions = document.getElementById('completionActions');
    if (completionActions) {
        completionActions.style.display = 'block';
    }
}

// Log Management Functions
function startLogStreaming() {
    if (logEventSource) {
        logEventSource.close();
    }

    console.log('Starting log streaming...');
    logEventSource = new EventSource('/api/scraping_logs/stream');

    logEventSource.onmessage = function (event) {
        try {
            const data = JSON.parse(event.data);
            handleLogEvent(data);
        } catch (error) {
            console.error('Error parsing log event:', error);
        }
    };

    logEventSource.onerror = function (event) {
        console.error('Log stream error:', event);
    };

    logEventSource.onopen = function (event) {
        console.log('Log stream connected');
        enableLogButtons();
    };
}

function handleLogEvent(data) {
    if (data.type === 'log') {
        appendLogEntry(data);
    } else if (data.type === 'complete') {
        console.log('Log streaming completed');
    } else if (data.type === 'error') {
        console.error('Log streaming error:', data.message);
    }
}

function appendLogEntry(logData) {
    const logDisplay = document.getElementById('logDisplay');
    if (!logDisplay) return;

    // Create log entry element
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${logData.level.toLowerCase()}`;
    logEntry.innerHTML = logData.formatted;

    // Remove "waiting for logs" message if it exists
    const waitingMessage = logDisplay.querySelector('.text-muted');
    if (waitingMessage) {
        waitingMessage.remove();
    }

    // Append new log entry
    logDisplay.appendChild(logEntry);

    // Auto-scroll to bottom
    logDisplay.scrollTop = logDisplay.scrollHeight;
}

function enableLogButtons() {
    const downloadLogs = document.getElementById('downloadLogs');
    const clearLogsBtn = document.getElementById('clearLogs');

    if (downloadLogs) {
        downloadLogs.disabled = false;
    }
    if (clearLogsBtn) {
        clearLogsBtn.disabled = false;
    }
}

function toggleLogDisplay() {
    const logsContainer = document.getElementById('logsContainer');
    const toggleBtn = document.getElementById('toggleLogs');

    if (!logsContainer || !toggleBtn) return;

    logsVisible = !logsVisible;

    if (logsVisible) {
        logsContainer.style.display = 'block';
        toggleBtn.innerHTML = '<i class="fas fa-eye-slash me-1"></i>Hide Details';
    } else {
        logsContainer.style.display = 'none';
        toggleBtn.innerHTML = '<i class="fas fa-eye me-1"></i>Show Details';
    }
}

function downloadLogs() {
    window.open('/api/scraping_logs/download', '_blank');
}

function clearLogs() {
    if (confirm('Are you sure you want to clear all logs?')) {
        fetch('/api/scraping_logs/clear', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const logDisplay = document.getElementById('logDisplay');
                    if (logDisplay) {
                        logDisplay.innerHTML = '<div class="text-muted text-center p-3"><i class="fas fa-clock me-2"></i>Logs cleared</div>';
                    }
                }
            })
            .catch(error => {
                console.error('Error clearing logs:', error);
            });
    }
}
