// UI utilities and components
class UIManager {
    constructor() {
        this.currentSection = 'dashboard';
        this.currentTable = 'ente';
        this.currentPage = 1;
        this.recordsPerPage = 20;
    }

    // Show loading state
    showLoading(element) {
        element.innerHTML = '<div class="loading">Cargando...</div>';
    }

    // Show error message
    showError(element, message) {
        element.innerHTML = `
            <div class="error">
                <p>Error: ${message}</p>
                <button class="btn btn-secondary" onclick="location.reload()">Reintentar</button>
            </div>
        `;
    }

    // Show success message
    showSuccess(message) {
        this.showToast(message, 'success');
    }

    // Show toast notification
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">&times;</button>
        `;
        
        // Add toast styles if not already added
        if (!document.querySelector('#toast-styles')) {
            const styles = document.createElement('style');
            styles.id = 'toast-styles';
            styles.innerHTML = `
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #333;
                    color: white;
                    padding: 1rem 1.5rem;
                    border-radius: 4px;
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    animation: slideIn 0.3s ease;
                }
                .toast-success { background: #27ae60; }
                .toast-error { background: #e74c3c; }
                .toast-warning { background: #f39c12; }
                .toast button {
                    background: none;
                    border: none;
                    color: inherit;
                    cursor: pointer;
                    font-size: 1.2rem;
                }
                @keyframes slideIn {
                    from { transform: translateX(100%); }
                    to { transform: translateX(0); }
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.appendChild(toast);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 3000);
    }

    // Switch between sections
    showSection(sectionId) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Remove active class from nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Show target section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        // Add active class to corresponding nav link
        const navLink = document.querySelector(`[href="#${sectionId}"]`);
        if (navLink) {
            navLink.classList.add('active');
        }
        
        this.currentSection = sectionId;
    }

    // Generate table HTML
    generateTable(data, columns) {
        if (!data || data.length === 0) {
            return '<p>No hay datos para mostrar</p>';
        }

        let html = '<table class="data-table"><thead><tr>';
        
        // Generate headers
        columns.forEach(col => {
            html += `<th>${col.label || col.name}</th>`;
        });
        html += '<th>Acciones</th></tr></thead><tbody>';
        
        // Generate rows
        data.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                const value = row[col.name] || '-';
                html += `<td>${this.formatCellValue(value, col.type)}</td>`;
            });
            const recordId = row.enteid || row.personaid || row.consorcistaid || row.parcelaid || row.sectorid || row.id;
            html += `
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="app.editRecord('${recordId}')">Editar</button>
                    <button class="btn btn-danger btn-sm" onclick="app.deleteRecord('${recordId}')">Eliminar</button>
                </td>
            `;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }

    // Format cell values based on type
    formatCellValue(value, type) {
        if (value === null || value === undefined) return '-';
        
        switch (type) {
            case 'date':
                return new Date(value).toLocaleDateString('es-ES');
            case 'datetime':
                return new Date(value).toLocaleString('es-ES');
            case 'currency':
                return new Intl.NumberFormat('es-ES', { 
                    style: 'currency', 
                    currency: 'EUR' 
                }).format(value);
            case 'number':
                return new Intl.NumberFormat('es-ES').format(value);
            default:
                return String(value);
        }
    }

    // Generate form HTML
    generateForm(fields, data = {}) {
        let html = '';
        
        fields.forEach(field => {
            const value = data[field.name] || '';
            
            html += `<div class="form-group">`;
            html += `<label for="${field.name}">${field.label || field.name}</label>`;
            
            switch (field.type) {
                case 'textarea':
                    html += `<textarea id="${field.name}" name="${field.name}" class="form-control" ${field.required ? 'required' : ''}>${value}</textarea>`;
                    break;
                case 'select':
                    html += `<select id="${field.name}" name="${field.name}" class="form-control" ${field.required ? 'required' : ''}>`;
                    html += `<option value="">Seleccionar...</option>`;
                    if (field.options) {
                        field.options.forEach(option => {
                            const selected = option.value === value ? 'selected' : '';
                            html += `<option value="${option.value}" ${selected}>${option.label}</option>`;
                        });
                    }
                    html += `</select>`;
                    break;
                case 'checkbox':
                    const checked = value ? 'checked' : '';
                    html += `<input type="checkbox" id="${field.name}" name="${field.name}" ${checked}> ${field.label}`;
                    break;
                default:
                    html += `<input type="${field.type || 'text'}" id="${field.name}" name="${field.name}" value="${value}" class="form-control" ${field.required ? 'required' : ''}>`;
            }
            
            html += `</div>`;
        });
        
        return html;
    }

    // Show modal
    showModal(title, content, onSave) {
        console.log('showModal called with:', { title, hasContent: !!content, hasCallback: !!onSave });
        
        const modal = document.getElementById('record-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = modal.querySelector('.modal-body');
        const form = document.getElementById('record-form');
        
        console.log('Modal elements found:', { modal: !!modal, modalTitle: !!modalTitle, modalBody: !!modalBody, form: !!form });
        
        modalTitle.textContent = title;
        
        // Insert content inside the existing form instead of replacing the entire modal body
        if (form) {
            form.innerHTML = content;
        } else {
            // Fallback: if form doesn't exist, create one with the content
            modalBody.innerHTML = `<form id="record-form">${content}</form>`;
        }
        
        modal.classList.add('active');
        
        // Store callback for save button
        this.onModalSave = onSave;
        console.log('onModalSave stored:', !!this.onModalSave);
    }

    // Hide modal
    hideModal() {
        const modal = document.getElementById('record-modal');
        modal.classList.remove('active');
        this.onModalSave = null;
    }

    // Get form data as object
    getFormData(formElement) {
        const formData = new FormData(formElement);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            // Handle checkboxes
            const checkbox = formElement.querySelector(`input[name="${key}"][type="checkbox"]`);
            if (checkbox) {
                data[key] = checkbox.checked;
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }

    // Generate pagination
    generatePagination(currentPage, totalPages, onPageChange) {
        if (totalPages <= 1) return '';
        
        let html = '<div class="pagination">';
        
        // Previous button
        if (currentPage > 1) {
            html += `<button class="btn btn-secondary" onclick="${onPageChange}(${currentPage - 1})">« Anterior</button>`;
        }
        
        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const active = i === currentPage ? 'btn-primary' : 'btn-secondary';
            html += `<button class="btn ${active}" onclick="${onPageChange}(${i})">${i}</button>`;
        }
        
        // Next button
        if (currentPage < totalPages) {
            html += `<button class="btn btn-secondary" onclick="${onPageChange}(${currentPage + 1})">Siguiente »</button>`;
        }
        
        html += '</div>';
        
        // Add pagination styles if not already added
        if (!document.querySelector('#pagination-styles')) {
            const styles = document.createElement('style');
            styles.id = 'pagination-styles';
            styles.innerHTML = `
                .pagination {
                    display: flex;
                    justify-content: center;
                    gap: 0.5rem;
                    margin: 2rem 0;
                }
                .pagination .btn {
                    padding: 0.5rem 1rem;
                }
            `;
            document.head.appendChild(styles);
        }
        
        return html;
    }
}

// Global UI manager instance
const ui = new UIManager();