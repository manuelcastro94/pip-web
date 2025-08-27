// Main application logic
class CEPIPApp {
    constructor() {
        this.tables = [];
        this.currentData = [];
        this.currentColumns = [];
        this.settings = {};
        
        this.init();
    }

    async init() {
        console.log('Initializing CEPIP Web App...');
        
        // Wait for authentication to be ready
        await this.waitForAuth();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadDashboard();
    }

    async waitForAuth() {
        return new Promise((resolve) => {
            const checkAuth = () => {
                if (window.authManager && window.authManager.isAuthenticated()) {
                    console.log('Auth is ready');
                    resolve();
                } else if (window.authManager && !window.authManager.token) {
                    // No token, but authManager is ready - continue without auth
                    console.log('No authentication found, continuing...');
                    resolve();
                } else {
                    // Still waiting for authManager to initialize
                    setTimeout(checkAuth, 100);
                }
            };
            checkAuth();
        });
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const sectionId = e.target.getAttribute('href').substring(1);
                this.navigateToSection(sectionId);
            });
        });

        // Data controls
        const addRecordBtn = document.getElementById('add-record');
        if (addRecordBtn) {
            addRecordBtn.addEventListener('click', () => this.showAddRecordModal());
        }

        const refreshBtn = document.getElementById('refresh-data');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadDataSection());
        }

        // Modal controls
        const modalClose = document.getElementById('modal-close');
        const modalCancel = document.getElementById('modal-cancel');
        const modalSave = document.getElementById('modal-save');
        
        if (modalClose) modalClose.addEventListener('click', () => ui.hideModal());
        if (modalCancel) modalCancel.addEventListener('click', () => ui.hideModal());
        
        // Add click listener to save button for debugging
        if (modalSave) {
            modalSave.addEventListener('click', (e) => {
                console.log('Save button clicked! Button type:', e.target.type);
                
                // Check if form exists and is valid
                const form = document.getElementById('record-form');
                console.log('Form found:', !!form);
                
                if (form) {
                    console.log('Form has submit event listeners:', form.onsubmit);
                    console.log('Form action:', form.action);
                    console.log('Form method:', form.method);
                    console.log('Button form attribute:', e.target.getAttribute('form'));
                    
                    // Try to manually trigger form submit
                    console.log('Manually triggering form submit...');
                    const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
                    const result = form.dispatchEvent(submitEvent);
                    console.log('Submit event dispatched, result:', result);
                }
            });
        }

        // Modal form submission - only for generic data section
        const recordForm = document.getElementById('record-form');
        console.log('Setting up form listener, form found:', !!recordForm);
        
        if (recordForm) {
            recordForm.addEventListener('submit', (e) => {
                console.log('Form submit event triggered!');
                
                // Only handle form submission if we're in the generic data section
                // Let specific managers (empresas, personas, etc.) handle their own forms
                const currentSection = document.querySelector('.section.active')?.id;
                console.log('Current section:', currentSection);
                console.log('ui.onModalSave available:', !!ui.onModalSave);
                
                if (currentSection === 'data') {
                    console.log('Handling as generic data section');
                    e.preventDefault();
                    this.handleFormSubmit(e.target);
                } else if (ui.onModalSave) {
                    // Let the specific section managers handle the form
                    console.log('Handling with section-specific callback');
                    e.preventDefault();
                    const data = ui.getFormData(e.target);
                    console.log('Form data:', data);
                    ui.onModalSave(data);
                } else {
                    console.log('No handler found, preventing default');
                    e.preventDefault();
                }
            });
        }

        // Report generation
        const generateReportBtn = document.getElementById('generate-report');
        if (generateReportBtn) {
            generateReportBtn.addEventListener('click', () => this.generateReport());
        }

        // Settings form
        const settingsForm = document.getElementById('settings-form');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSettings();
            });
        }

        // Click outside modal to close
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('record-modal');
            if (e.target === modal) {
                ui.hideModal();
            }
        });
    }

    async navigateToSection(sectionId) {
        ui.showSection(sectionId);
        
        switch (sectionId) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'empresas':
                await this.loadEmpresasSection();
                break;
            case 'personas':
                await this.loadPersonasSection();
                break;
            case 'consorcistas':
                await this.loadConsorcistaSection();
                break;
            case 'parcelas':
                await this.loadParcelasSection();
                break;
            case 'data':
                await this.loadDataSection();
                break;
            case 'reports':
                await this.loadReportsSection();
                break;
            case 'settings':
                await this.loadSettingsSection();
                break;
        }
    }

    async loadDashboard() {
        console.log('Loading dashboard...');
        
        const totalRecordsEl = document.getElementById('total-records');
        const lastUpdateEl = document.getElementById('last-update');
        
        if (!totalRecordsEl || !lastUpdateEl) return;
        
        try {
            // Show loading state
            totalRecordsEl.textContent = '...';
            lastUpdateEl.textContent = '...';
            
            // Try to load stats from API
            try {
                const stats = await api.getStats();
                totalRecordsEl.textContent = stats.totalRecords || '0';
                lastUpdateEl.textContent = stats.lastUpdate || 'N/A';
            } catch (error) {
                // Fallback to mock data if API is not available
                console.warn('API not available, using mock data');
                totalRecordsEl.textContent = '0';
                lastUpdateEl.textContent = 'API no disponible';
            }
            
        } catch (error) {
            console.error('Error loading dashboard:', error);
            ui.showError(document.getElementById('dashboard'), error.message);
        }
    }

    async loadEmpresasSection() {
        console.log('Loading empresas section...');
        
        try {
            // Load empresas data using the empresas manager
            if (window.empresasManager) {
                await window.empresasManager.loadEmpresas();
            }
        } catch (error) {
            console.error('Error loading empresas section:', error);
        }
    }

    async loadPersonasSection() {
        console.log('Loading personas section...');
        
        try {
            // Load personas data using the personas manager
            if (window.personasManager) {
                await window.personasManager.loadPersonas();
            }
        } catch (error) {
            console.error('Error loading personas section:', error);
        }
    }

    async loadConsorcistaSection() {
        console.log('Loading consorcistas section...');
        
        try {
            // Load consorcistas data using the consorcistas manager
            if (window.consorcistaManager) {
                await window.consorcistaManager.loadConsorcistas();
            }
        } catch (error) {
            console.error('Error loading consorcistas section:', error);
        }
    }

    async loadParcelasSection() {
        console.log('Loading parcelas section...');
        
        try {
            // Load parcelas data using the parcelas manager
            if (window.parcelasManager) {
                await window.parcelasManager.loadParcelas();
            }
        } catch (error) {
            console.error('Error loading parcelas section:', error);
        }
    }

    async loadDataSection() {
        console.log('Loading data section...');
        
        const tableBody = document.getElementById('table-body');
        if (!tableBody) return;
        
        ui.showLoading(tableBody);
        
        try {
            // Try to load data from API
            try {
                const response = await api.getRecords(ui.currentTable, ui.currentPage, ui.recordsPerPage);
                this.currentData = response.data || [];
                this.currentColumns = response.columns || this.getDefaultColumns();
                
                this.renderDataTable();
            } catch (error) {
                // Fallback to mock data if API is not available
                console.warn('API not available, using mock data');
                this.loadMockData();
            }
            
        } catch (error) {
            console.error('Error loading data:', error);
            ui.showError(tableBody, error.message);
        }
    }

    loadMockData() {
        // Mock data for testing when API is not available
        this.currentData = [
            { id: 1, nombre: 'Ejemplo 1', fecha: '2024-01-15', estado: 'Activo' },
            { id: 2, nombre: 'Ejemplo 2', fecha: '2024-01-16', estado: 'Inactivo' },
            { id: 3, nombre: 'Ejemplo 3', fecha: '2024-01-17', estado: 'Activo' }
        ];
        
        this.currentColumns = [
            { name: 'id', label: 'ID', type: 'number' },
            { name: 'nombre', label: 'Nombre', type: 'text' },
            { name: 'fecha', label: 'Fecha', type: 'date' },
            { name: 'estado', label: 'Estado', type: 'text' }
        ];
        
        this.renderDataTable();
    }

    getDefaultColumns() {
        return [
            { name: 'id', label: 'ID', type: 'number' },
            { name: 'nombre', label: 'Nombre', type: 'text' },
            { name: 'fecha', label: 'Fecha', type: 'date' }
        ];
    }

    renderDataTable() {
        const tableContainer = document.querySelector('.table-container');
        if (!tableContainer) return;
        
        const tableHTML = ui.generateTable(this.currentData, this.currentColumns);
        tableContainer.innerHTML = tableHTML;
    }

    showAddRecordModal() {
        const formFields = this.currentColumns
            .filter(col => col.name !== 'id') // Don't include ID in add form
            .map(col => ({
                name: col.name,
                label: col.label,
                type: this.getFormFieldType(col.type),
                required: col.required || false
            }));
        
        const formHTML = ui.generateForm(formFields);
        ui.showModal('Agregar Registro', formHTML, (data) => this.createRecord(data));
    }

    async editRecord(id) {
        try {
            let recordData;
            
            // Try to get record from API
            try {
                recordData = await api.getRecord(ui.currentTable, id);
            } catch (error) {
                // Fallback to finding in current data
                recordData = this.currentData.find(record => record.id == id);
                if (!recordData) {
                    ui.showToast('Registro no encontrado', 'error');
                    return;
                }
            }
            
            const formFields = this.currentColumns
                .filter(col => col.name !== 'id')
                .map(col => ({
                    name: col.name,
                    label: col.label,
                    type: this.getFormFieldType(col.type),
                    required: col.required || false
                }));
            
            const formHTML = ui.generateForm(formFields, recordData);
            ui.showModal('Editar Registro', formHTML, (data) => this.updateRecord(id, data));
            
        } catch (error) {
            console.error('Error loading record for edit:', error);
            ui.showToast('Error al cargar el registro', 'error');
        }
    }

    async deleteRecord(id) {
        if (!confirm('¿Estás seguro de que quieres eliminar este registro?')) {
            return;
        }
        
        try {
            await api.deleteRecord(ui.currentTable, id);
            ui.showToast('Registro eliminado correctamente', 'success');
            await this.loadDataSection(); // Reload data
        } catch (error) {
            console.error('Error deleting record:', error);
            ui.showToast('Error al eliminar el registro', 'error');
        }
    }

    getFormFieldType(columnType) {
        const typeMap = {
            'number': 'number',
            'date': 'date',
            'datetime': 'datetime-local',
            'boolean': 'checkbox',
            'text': 'text',
            'longtext': 'textarea'
        };
        
        return typeMap[columnType] || 'text';
    }

    async handleFormSubmit(form) {
        const data = ui.getFormData(form);
        
        if (ui.onModalSave) {
            await ui.onModalSave(data);
        }
    }

    async createRecord(data) {
        try {
            await api.createRecord(ui.currentTable, data);
            ui.showToast('Registro creado correctamente', 'success');
            ui.hideModal();
            await this.loadDataSection(); // Reload data
        } catch (error) {
            console.error('Error creating record:', error);
            ui.showToast('Error al crear el registro', 'error');
        }
    }

    async updateRecord(id, data) {
        try {
            await api.updateRecord(ui.currentTable, id, data);
            ui.showToast('Registro actualizado correctamente', 'success');
            ui.hideModal();
            await this.loadDataSection(); // Reload data
        } catch (error) {
            console.error('Error updating record:', error);
            ui.showToast('Error al actualizar el registro', 'error');
        }
    }

    async loadReportsSection() {
        console.log('Loading reports section...');
        // Report functionality will be implemented based on the specific needs
        // after we understand the Access database structure
    }

    async generateReport() {
        const reportType = document.getElementById('report-type').value;
        const reportOutput = document.getElementById('report-output');
        
        if (!reportType) {
            ui.showToast('Selecciona un tipo de reporte', 'warning');
            return;
        }
        
        ui.showLoading(reportOutput);
        
        try {
            const report = await api.generateReport(reportType);
            reportOutput.innerHTML = `
                <h3>Reporte: ${reportType}</h3>
                <pre>${JSON.stringify(report, null, 2)}</pre>
            `;
        } catch (error) {
            console.error('Error generating report:', error);
            reportOutput.innerHTML = `
                <p>Error al generar el reporte. El servidor backend no está disponible.</p>
                <p>Implementar la generación de reportes una vez que la migración esté completa.</p>
            `;
        }
    }

    async loadSettingsSection() {
        console.log('Loading settings section...');
        
        try {
            const settings = await api.getSettings();
            this.settings = settings;
            
            // Update form values
            document.getElementById('app-name').value = settings.appName || 'CEPIP';
            document.getElementById('records-per-page').value = settings.recordsPerPage || 20;
            
        } catch (error) {
            console.warn('Could not load settings from API:', error);
            // Use default settings
            this.settings = {
                appName: 'CEPIP',
                recordsPerPage: 20
            };
        }
    }

    async saveSettings() {
        const formData = ui.getFormData(document.getElementById('settings-form'));
        
        try {
            await api.updateSettings(formData);
            this.settings = { ...this.settings, ...formData };
            ui.recordsPerPage = parseInt(formData.recordsPerPage);
            ui.showToast('Configuración guardada correctamente', 'success');
        } catch (error) {
            console.error('Error saving settings:', error);
            ui.showToast('Error al guardar la configuración', 'error');
        }
    }

    // Pagination handler
    async changePage(page) {
        ui.currentPage = page;
        await this.loadDataSection();
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new CEPIPApp();
});