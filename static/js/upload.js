// Global variables
let selectedFiles = [];
let allDocuments = [];  
let currentFilter = 'all';  

// Initialize upload functionality
document.addEventListener('DOMContentLoaded', () => {
    initUploadBox();
    loadDocuments();
});

// Initialize drag and drop
function initUploadBox() {
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    
    // Click to select files
    uploadBox.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
    
    // Drag and drop events
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('dragover');
    });
    
    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('dragover');
    });
    
    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
}

// Handle selected files
function handleFiles(files) {
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg', 'image/gif'];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    for (let file of files) {
        // Validate file type
        if (!allowedTypes.includes(file.type)) {
            showNotification(`${file.name}: File type not supported`, 'error');
            continue;
        }
        
        // Validate file size
        if (file.size > maxSize) {
            showNotification(`${file.name}: File too large (max 10MB)`, 'error');
            continue;
        }
        
        // Check if file already selected
        if (selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
            showNotification(`${file.name}: Already selected`, 'warning');
            continue;
        }
        
        selectedFiles.push(file);
    }
    
    displaySelectedFiles();
}

// Display selected files
function displaySelectedFiles() {
    const selectedFilesDiv = document.getElementById('selectedFiles');
    const filesList = document.getElementById('filesList');
    
    if (selectedFiles.length === 0) {
        selectedFilesDiv.style.display = 'none';
        return;
    }
    
    selectedFilesDiv.style.display = 'block';
    
    filesList.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <div class="file-icon">${getFileIcon(file.type)}</div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-details">
                    ${(file.size / (1024 * 1024)).toFixed(2)} MB
                </div>
            </div>
            <button class="file-remove" onclick="removeFile(${index})">
                Remove
            </button>
        </div>
    `).join('');
}

// Get file icon based on type
function getFileIcon(type) {
    if (type === 'application/pdf') return '📄';
    if (type.startsWith('image/')) return '🖼️';
    return '📁';
}

// Remove file from selection
function removeFile(index) {
    selectedFiles.splice(index, 1);
    displaySelectedFiles();
}

// Clear all selected files
function clearSelection() {
    selectedFiles = [];
    displaySelectedFiles();
    document.getElementById('fileInput').value = '';
    showNotification('Selection cleared', 'info');
}

// Upload files
async function uploadFiles() {
    if (selectedFiles.length === 0) {
        showNotification('Please select files to upload', 'warning');
        return;
    }
    
    const progressDiv = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressPercent = document.getElementById('progressPercent');
    const progressText = document.getElementById('progressText');
    
    progressDiv.style.display = 'block';
    
    let uploadedCount = 0;
    let failedCount = 0;
    
    for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            progressText.textContent = `Uploading ${file.name}...`;
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                uploadedCount++;
                showNotification(`✓ ${file.name} uploaded successfully`, 'success');
            } else {
                failedCount++;
                showNotification(`✗ ${file.name}: ${data.error}`, 'error');
            }
            
        } catch (error) {
            failedCount++;
            showNotification(`✗ ${file.name}: Upload failed`, 'error');
            console.error('Upload error:', error);
        }
        
        // Update progress
        const progress = ((i + 1) / selectedFiles.length) * 100;
        progressFill.style.width = progress + '%';
        progressPercent.textContent = Math.round(progress) + '%';
    }
    
    // Upload complete
    progressText.textContent = 'Upload Complete!';
    
    setTimeout(() => {
        progressDiv.style.display = 'none';
        progressFill.style.width = '0%';
        clearSelection();
        loadDocuments();
        
        if (uploadedCount > 0) {
            showNotification(`✅ ${uploadedCount} file(s) uploaded successfully`, 'success');
        }
        if (failedCount > 0) {
            showNotification(`⚠️ ${failedCount} file(s) failed to upload`, 'error');
        }
    }, 2000);
}

// Load uploaded documents
async function loadDocuments() {
    const grid = document.getElementById('documentsGrid');
    grid.innerHTML = '<p class="loading">Loading documents...</p>';
    
    try {
        const response = await fetch('/api/documents');
        const documents = await response.json();
        
        // Store documents globally for filtering
        allDocuments = documents;
        
        // Update stats
        updateUploadStats(documents);
        
        // Display documents with current filter
        displayDocuments(filterDocumentsByType(documents, currentFilter));
        
        console.log('✅ Documents loaded successfully');
        
    } catch (error) {
        console.error('❌ Error loading documents:', error);
        grid.innerHTML = '<div class="error"><p>⚠️ Error loading documents</p></div>';
    }
}

// Filter documents by type
function filterDocuments(type) {
    currentFilter = type;
    
    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-filter') === type) {
            btn.classList.add('active');
        }
    });
    
    // Filter and display
    const filtered = filterDocumentsByType(allDocuments, type);
    displayDocuments(filtered);
}

// Filter helper function
function filterDocumentsByType(documents, type) {
    if (type === 'all') return documents;
    return documents.filter(doc => doc.file_type === type);
}

// Display documents in grid
function displayDocuments(documents) {
    const grid = document.getElementById('documentsGrid');
    
    if (documents.length === 0) {
        const filterText = currentFilter === 'all' ? '' : ` ${currentFilter}`;
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <p>No${filterText} documents found</p>
                <p>${currentFilter === 'all' ? 'Upload your first document to get started!' : 'Try a different filter or upload more documents'}</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = documents.map(doc => `
        <div class="document-card">
            <div class="document-header">
                <div class="document-type">${getDocumentIcon(doc.file_type)}</div>
                <span class="document-badge ${doc.processed ? 'processed' : 'pending'}">
                    ${doc.processed ? 'Processed' : 'Pending'}
                </span>
            </div>
            <div class="document-body">
                <h4 title="${doc.original_filename}">${doc.original_filename}</h4>
                <p class="document-meta">📅 ${formatDate(doc.upload_date)}</p>
                <p class="document-meta">📁 ${doc.file_type}</p>
            </div>
            <div class="document-actions">
                <button class="btn-small btn-view" onclick="viewDocument(${doc.id})">
                    👁️ View
                </button>
                ${!doc.processed ? `
                    <button class="btn-small btn-process" onclick="processDocument(${doc.id})">
                        ⚙️ Process
                    </button>
                ` : `
                    <button class="btn-small btn-details" onclick="showDocumentDetails(${doc.id})">
                        📊 Details
                    </button>
                `}
                <button class="btn-small btn-delete" onclick="deleteDocument(${doc.id}, '${doc.original_filename}')">
                    🗑️ Delete
                </button>
            </div>
        </div>
    `).join('');
}

// Update upload statistics
function updateUploadStats(documents) {
    const totalDocs = documents.length;
    const processedDocs = documents.filter(doc => doc.processed).length;
    const pendingDocs = totalDocs - processedDocs;
    
    // Update stats display
    const totalDocsEl = document.getElementById('totalDocs');
    const processedDocsEl = document.getElementById('processedDocs');
    const pendingDocsEl = document.getElementById('pendingDocs');
    
    if (totalDocsEl) totalDocsEl.textContent = totalDocs;
    if (processedDocsEl) processedDocsEl.textContent = processedDocs;
    if (pendingDocsEl) pendingDocsEl.textContent = pendingDocs;
}

// Get document icon
function getDocumentIcon(type) {
    const icons = {
        'invoice': '🧾',
        'receipt': '🧾',
        'statement': '📊',
        'other': '📄'
    };
    return icons[type] || '📄';
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// View document
async function viewDocument(docId) {
    const modal = document.getElementById('previewModal');
    const previewTitle = document.getElementById('previewTitle');
    const previewContent = document.getElementById('previewContent');
    
    // Show modal
    modal.style.display = 'flex';
    previewContent.innerHTML = '<p class="loading">Loading preview...</p>';
    
    try {
        const response = await fetch(`/api/documents/${docId}`);
        const doc = await response.json();
        
        if (!doc) {
            previewContent.innerHTML = '<p class="error">Document not found</p>';
            return;
        }
        
        previewTitle.textContent = doc.original_filename;
        
        // Check if it's an image
        const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp'];
        const ext = doc.filename.split('.').pop().toLowerCase();
        
        if (imageExtensions.includes(ext)) {
            previewContent.innerHTML = `
                <img src="/uploads/${doc.filename}" alt="${doc.original_filename}">
                <div class="preview-info">
                    <p><strong>Type:</strong> ${doc.file_type}</p>
                    <p><strong>Uploaded:</strong> ${formatDate(doc.upload_date)}</p>
                    <p><strong>Status:</strong> ${doc.processed ? 'Processed' : 'Pending Processing'}</p>
                </div>
            `;
        } else if (ext === 'pdf') {
            previewContent.innerHTML = `
                <div class="preview-info">
                    <p><strong>📄 PDF Document</strong></p>
                    <p><strong>Filename:</strong> ${doc.original_filename}</p>
                    <p><strong>Type:</strong> ${doc.file_type}</p>
                    <p><strong>Uploaded:</strong> ${formatDate(doc.upload_date)}</p>
                    <p><strong>Status:</strong> ${doc.processed ? 'Processed ✓' : 'Pending Processing'}</p>
                    <p style="margin-top: 1rem; color: #6B7280;">PDF preview will be available in the next phase.</p>
                    <a href="/uploads/${doc.filename}" target="_blank" class="btn-primary" style="margin-top: 1rem; display: inline-block;">
                        Open PDF in New Tab
                    </a>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error loading preview:', error);
        previewContent.innerHTML = '<p class="error">⚠️ Error loading preview</p>';
    }
}

// Close preview modal
function closePreview() {
    const modal = document.getElementById('previewModal');
    modal.style.display = 'none';
}

// Close modal on ESC key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closePreview();
    }
});

// Delete document
async function deleteDocument(docId, filename) {
    if (!confirm(`Delete "${filename}"?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/documents/${docId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`✓ ${filename} deleted successfully`, 'success');
            loadDocuments();
        } else {
            showNotification(`✗ Error: ${data.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('✗ Error deleting document', 'error');
    }
}

// ============= DAY 4: PROCESSING FUNCTIONS =============

// Process a single document
async function processDocument(docId) {
    if (!confirm('Process this document? This will extract data and create transactions.')) {
        return;
    }
    
    showNotification('Processing document...', 'info');
    
    try {
        const response = await fetch(`/api/process-document/${docId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Document processed successfully!', 'success');
            loadDocuments();
            
            // Optionally show extracted data
            setTimeout(() => {
                showDocumentDetails(docId);
            }, 1000);
        } else {
            showNotification(`❌ ${data.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Processing error:', error);
        showNotification('❌ Error processing document', 'error');
    }
}

// Process all unprocessed documents
async function processAllDocuments() {
    const unprocessedCount = allDocuments.filter(doc => !doc.processed).length;
    
    if (unprocessedCount === 0) {
        showNotification('No documents to process', 'info');
        return;
    }
    
    if (!confirm(`Process ${unprocessedCount} unprocessed document(s)? This may take a few minutes.`)) {
        return;
    }
    
    showNotification('Processing all documents...', 'info');
    
    try {
        const response = await fetch('/api/process-all-documents', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(
                `✅ Processed ${data.processed_count} documents successfully!`,
                'success'
            );
            
            if (data.failed_count > 0) {
                showNotification(
                    `⚠️ ${data.failed_count} documents failed to process`,
                    'warning'
                );
                console.log('Failed documents:', data.errors);
            }
            
            loadDocuments();
        } else {
            showNotification(`❌ ${data.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Processing error:', error);
        showNotification('❌ Error processing documents', 'error');
    }
}

// Show document details with extracted data
async function showDocumentDetails(docId) {
    const modal = document.getElementById('previewModal');
    const previewTitle = document.getElementById('previewTitle');
    const previewContent = document.getElementById('previewContent');
    
    modal.style.display = 'flex';
    previewContent.innerHTML = '<p class="loading">Loading details...</p>';
    
    try {
        const response = await fetch(`/api/document-details/${docId}`);
        const data = await response.json();
        
        if (!data.document) {
            previewContent.innerHTML = '<p class="error">Document not found</p>';
            return;
        }
        
        previewTitle.textContent = `${data.document.original_filename} - Details`;
        
        let html = `
            <div class="document-details">
                <div class="detail-section">
                    <h4>📄 Document Information</h4>
                    <p><strong>Type:</strong> ${data.document.file_type}</p>
                    <p><strong>Uploaded:</strong> ${formatDate(data.document.upload_date)}</p>
                    <p><strong>Status:</strong> ${data.document.processed ? '✅ Processed' : '⏳ Pending'}</p>
                </div>
        `;
        
        if (data.raw_text) {
            html += `
                <div class="detail-section">
                    <h4>📝 Extracted Text (Preview)</h4>
                    <div class="extracted-text">
                        ${data.raw_text}...
                    </div>
                </div>
            `;
        }
        
        if (data.transactions && data.transactions.length > 0) {
            html += `
                <div class="detail-section">
                    <h4>💰 Extracted Transactions (${data.transaction_count})</h4>
                    <table class="details-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Vendor</th>
                                <th>Amount</th>
                                <th>Category</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.transactions.map(t => `
                                <tr>
                                    <td>${t.date || 'N/A'}</td>
                                    <td>${t.vendor || 'Unknown'}</td>
                                    <td>₹${t.amount.toLocaleString('en-IN')}</td>
                                    <td><span class="badge">${t.category}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } else if (data.document.processed) {
            html += `
                <div class="detail-section">
                    <p class="no-data">⚠️ Document processed but no transactions extracted</p>
                </div>
            `;
        } else {
            html += `
                <div class="detail-section">
                    <p class="no-data">⏳ Document not yet processed</p>
                    <button class="btn-primary" onclick="closePreview(); processDocument(${docId});">
                        ⚙️ Process Now
                    </button>
                </div>
            `;
        }
        
        html += `</div>`;
        
        previewContent.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading details:', error);
        previewContent.innerHTML = '<p class="error">⚠️ Error loading details</p>';
    }
}