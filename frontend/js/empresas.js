// Empresas management functionality
class EmpresasManager {
    constructor() {
        this.currentPage = 1;
        this.recordsPerPage = 20;
        this.currentFilters = {};
        this.empresas = [];
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-empresas');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadEmpresas());
        }

        // Search input
        const searchInput = document.getElementById('search-empresa');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.currentFilters.search = e.target.value;
                this.applyFilters();
            });
        }

        // Filter selects
        const filterSocio = document.getElementById('filter-socio');
        if (filterSocio) {
            filterSocio.addEventListener('change', (e) => {
                this.currentFilters.es_socio = e.target.value;
                this.applyFilters();
            });
        }

        const filterConsorcista = document.getElementById('filter-consorcista');
        if (filterConsorcista) {
            filterConsorcista.addEventListener('change', (e) => {
                this.currentFilters.esconsorcista = e.target.value;
                this.applyFilters();
            });
        }

        // Clear filters
        const clearFiltersBtn = document.getElementById('clear-empresas-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        }

        // Add empresa button
        const addEmpresaBtn = document.getElementById('add-empresa');
        if (addEmpresaBtn) {
            addEmpresaBtn.addEventListener('click', () => this.showAddEmpresaModal());
        }

        // Export button
        const exportBtn = document.getElementById('export-empresas');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportEmpresas());
        }
    }

    async loadEmpresas() {
        console.log('Loading empresas...');
        
        const tableBody = document.getElementById('empresas-table-body');
        if (!tableBody) {
            console.error('Table body not found!');
            return;
        }
        
        ui.showLoading(tableBody);
        
        try {
            console.log('Calling API...');
            // Load empresas data from API
            const response = await api.getRecords('ente', this.currentPage, this.recordsPerPage);
            console.log('API response:', response);
            this.empresas = response.data || [];
            console.log('Empresas loaded:', this.empresas.length);
            
            // Load statistics
            console.log('Loading statistics...');
            await this.loadStatistics();
            
            // Render table
            console.log('Rendering table...');
            this.renderEmpresasTable();
            
            // Render pagination
            this.renderPagination(response.pagination);
            
        } catch (error) {
            console.error('Error loading empresas:', error);
            ui.showError(tableBody, 'Error al cargar las empresas');
        }
    }

    async loadStatistics() {
        try {
            const totalEmpresas = this.empresas.length;
            const socios = this.empresas.filter(e => e.es_socio).length;
            const consorcistas = this.empresas.filter(e => e.esconsorcista).length;
            
            // Count unique sectors
            const sectores = new Set(this.empresas.map(e => e.sector_nombre).filter(Boolean)).size;

            // Update statistics display
            document.getElementById('total-empresas').textContent = totalEmpresas;
            document.getElementById('empresas-socios').textContent = socios;
            document.getElementById('empresas-consorcistas').textContent = consorcistas;
            document.getElementById('total-sectores').textContent = sectores;

        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    renderEmpresasTable() {
        const tableBody = document.getElementById('empresas-table-body');
        if (!tableBody) return;

        if (!this.empresas || this.empresas.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="10">No hay empresas para mostrar</td></tr>';
            return;
        }

        let html = '';
        this.empresas.forEach(empresa => {
            html += `
                <tr>
                    <td>${empresa.enteid}</td>
                    <td><strong>${empresa.razonsocial || '-'}</strong></td>
                    <td>${this.formatCUIT(empresa.cuit)}</td>
                    <td>${empresa.nro_socio_cepip || '-'}</td>
                    <td>${empresa.sector_nombre || '-'}</td>
                    <td>${empresa.rubro_nombre || '-'}</td>
                    <td>${this.formatBoolean(empresa.es_socio)}</td>
                    <td>${this.formatBoolean(empresa.esconsorcista)}</td>
                    <td>${this.formatWeb(empresa.web)}</td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="empresasManager.editEmpresa(${empresa.enteid})">
                            Editar
                        </button>
                        <button class="btn btn-info btn-sm" onclick="empresasManager.viewDetails(${empresa.enteid})">
                            Detalles
                        </button>
                    </td>
                </tr>
            `;
        });

        tableBody.innerHTML = html;
    }

    formatCUIT(cuit) {
        if (!cuit) return '-';
        const cuitStr = cuit.toString();
        if (cuitStr.length === 11) {
            return `${cuitStr.substr(0, 2)}-${cuitStr.substr(2, 8)}-${cuitStr.substr(10, 1)}`;
        }
        return cuitStr;
    }

    formatBoolean(value) {
        if (value === true || value === 'true' || value === 1) {
            return '<span class="badge badge-success">Sí</span>';
        } else if (value === false || value === 'false' || value === 0) {
            return '<span class="badge badge-secondary">No</span>';
        }
        return '<span class="badge badge-light">-</span>';
    }

    formatWeb(web) {
        if (!web) return '-';
        if (web.startsWith('http')) {
            return `<a href="${web}" target="_blank" class="web-link">${web}</a>`;
        }
        return `<a href="http://${web}" target="_blank" class="web-link">${web}</a>`;
    }

    renderPagination(pagination) {
        const paginationContainer = document.getElementById('empresas-pagination');
        if (!paginationContainer || !pagination) return;

        const totalPages = pagination.pages || 1;
        
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let html = '<div class="pagination">';
        
        // Previous button
        if (this.currentPage > 1) {
            html += `<button class="btn btn-secondary" onclick="empresasManager.changePage(${this.currentPage - 1})">« Anterior</button>`;
        }
        
        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const active = i === this.currentPage ? 'btn-primary' : 'btn-secondary';
            html += `<button class="btn ${active}" onclick="empresasManager.changePage(${i})">${i}</button>`;
        }
        
        // Next button
        if (this.currentPage < totalPages) {
            html += `<button class="btn btn-secondary" onclick="empresasManager.changePage(${this.currentPage + 1})">Siguiente »</button>`;
        }
        
        html += '</div>';
        paginationContainer.innerHTML = html;
    }

    async changePage(page) {
        this.currentPage = page;
        await this.loadEmpresas();
    }

    applyFilters() {
        console.log('Applying filters:', this.currentFilters);
        // For now, just reload data - in production would filter on server
        this.loadEmpresas();
    }

    clearFilters() {
        this.currentFilters = {};
        document.getElementById('search-empresa').value = '';
        document.getElementById('filter-socio').value = '';
        document.getElementById('filter-consorcista').value = '';
        this.loadEmpresas();
    }

    showAddEmpresaModal() {
        const formFields = [
            { name: 'razonsocial', label: 'Razón Social', type: 'text', required: true },
            { name: 'cuit', label: 'CUIT', type: 'text' },
            { name: 'nro_socio_cepip', label: 'N° Socio CEPIP', type: 'number' },
            { name: 'web', label: 'Sitio Web', type: 'url' },
            { name: 'es_socio', label: 'Es Socio CEPIP', type: 'checkbox' },
            { name: 'esconsorcista', label: 'Es Consorcista', type: 'checkbox' },
            { name: 'observaciones', label: 'Observaciones', type: 'textarea' }
        ];

        const formHTML = ui.generateForm(formFields);
        ui.showModal('Agregar Empresa', formHTML, (data) => this.createEmpresa(data));
    }

    async editEmpresa(id) {
        try {
            const empresa = this.empresas.find(e => e.enteid === id);
            if (!empresa) {
                ui.showToast('Empresa no encontrada', 'error');
                return;
            }

            const formFields = [
                { name: 'razonsocial', label: 'Razón Social', type: 'text', required: true },
                { name: 'cuit', label: 'CUIT', type: 'text' },
                { name: 'nro_socio_cepip', label: 'N° Socio CEPIP', type: 'number' },
                { name: 'web', label: 'Sitio Web', type: 'url' },
                { name: 'es_socio', label: 'Es Socio CEPIP', type: 'checkbox' },
                { name: 'esconsorcista', label: 'Es Consorcista', type: 'checkbox' },
                { name: 'observaciones', label: 'Observaciones', type: 'textarea' }
            ];

            const formHTML = ui.generateForm(formFields, empresa);
            ui.showModal('Editar Empresa', formHTML, (data) => this.updateEmpresa(id, data));

        } catch (error) {
            console.error('Error editing empresa:', error);
            ui.showToast('Error al cargar la empresa', 'error');
        }
    }

    async viewDetails(id) {
        const empresa = this.empresas.find(e => e.enteid === id);
        if (!empresa) {
            ui.showToast('Empresa no encontrada', 'error');
            return;
        }

        // Show modal with loading
        const loadingHTML = `
            <div class="empresa-details">
                <h4>Detalles de ${empresa.razonsocial}</h4>
                <div class="details-grid">
                    <div><strong>ID:</strong> ${empresa.enteid}</div>
                    <div><strong>Razón Social:</strong> ${empresa.razonsocial || '-'}</div>
                    <div><strong>CUIT:</strong> ${this.formatCUIT(empresa.cuit)}</div>
                    <div><strong>N° Socio CEPIP:</strong> ${empresa.nro_socio_cepip || '-'}</div>
                    <div><strong>Sector:</strong> ${empresa.sector_nombre || '-'}</div>
                    <div><strong>Rubro:</strong> ${empresa.rubro_nombre || '-'}</div>
                    <div><strong>Sitio Web:</strong> ${empresa.web || '-'}</div>
                    <div><strong>Es Socio:</strong> ${empresa.es_socio ? 'Sí' : 'No'}</div>
                    <div><strong>Es Consorcista:</strong> ${empresa.esconsorcista ? 'Sí' : 'No'}</div>
                    <div><strong>Observaciones:</strong> ${empresa.observaciones || '-'}</div>
                    <div><strong>Consorcista ID:</strong> ${empresa.consorcistaid || '-'}</div>
                    <div><strong>Fecha de Carga:</strong> ${empresa.fecha_de_carga || '-'}</div>
                </div>
                
                <div class="mt-4">
                    <h5>📍 Direcciones</h5>
                    <div id="empresa-direcciones">Cargando direcciones...</div>
                </div>
                
                <div class="mt-4">
                    <h5>🏢 Cámaras Empresariales</h5>
                    <div id="empresa-camaras">Cargando cámaras...</div>
                </div>
                
                <div class="mt-4">
                    <h5>👥 Sindicatos</h5>
                    <div id="empresa-sindicatos">Cargando sindicatos...</div>
                </div>
            </div>
        `;

        ui.showModal('Detalles de Empresa', loadingHTML);
        
        // Load additional data
        await this.loadEmpresaRelations(id);
    }

    async loadEmpresaRelations(ente_id) {
        try {
            // Load direcciones, camaras, and sindicatos in parallel
            const [direccionesRes, camarasRes, sindicatosRes] = await Promise.all([
                fetch(`/api/records/ente/${ente_id}/direcciones`),
                fetch(`/api/records/ente/${ente_id}/camaras`),
                fetch(`/api/records/ente/${ente_id}/sindicatos`)
            ]);

            // Update direcciones
            if (direccionesRes.ok) {
                const direccionesData = await direccionesRes.json();
                const direccionesContainer = document.getElementById('empresa-direcciones');
                if (direccionesContainer) {
                    if (direccionesData.direcciones && direccionesData.direcciones.length > 0) {
                        direccionesContainer.innerHTML = direccionesData.direcciones.map(dir => 
                            `<div class="relation-item">📍 ${dir.calle} ${dir.altura}</div>`
                        ).join('');
                    } else {
                        direccionesContainer.innerHTML = '<div class="text-muted">Sin direcciones registradas</div>';
                    }
                }
            }

            // Update camaras
            if (camarasRes.ok) {
                const camarasData = await camarasRes.json();
                const camarasContainer = document.getElementById('empresa-camaras');
                if (camarasContainer) {
                    if (camarasData.camaras && camarasData.camaras.length > 0) {
                        camarasContainer.innerHTML = camarasData.camaras.map(camara => 
                            `<div class="relation-item">🏢 ${camara.camara}</div>`
                        ).join('');
                    } else {
                        camarasContainer.innerHTML = '<div class="text-muted">Sin cámaras asociadas</div>';
                    }
                }
            }

            // Update sindicatos
            if (sindicatosRes.ok) {
                const sindicatosData = await sindicatosRes.json();
                const sindicatosContainer = document.getElementById('empresa-sindicatos');
                if (sindicatosContainer) {
                    if (sindicatosData.sindicatos && sindicatosData.sindicatos.length > 0) {
                        sindicatosContainer.innerHTML = sindicatosData.sindicatos.map(sindicato => 
                            `<div class="relation-item">👥 ${sindicato.siglas} - ${sindicato.sindicato}</div>`
                        ).join('');
                    } else {
                        sindicatosContainer.innerHTML = '<div class="text-muted">Sin sindicatos asociados</div>';
                    }
                }
            }

        } catch (error) {
            console.error('Error loading empresa relations:', error);
        }
    }

    async createEmpresa(data) {
        try {
            await api.createRecord('ente', data);
            ui.showToast('Empresa creada correctamente', 'success');
            ui.hideModal();
            await this.loadEmpresas();
        } catch (error) {
            console.error('Error creating empresa:', error);
            ui.showToast('Error al crear la empresa', 'error');
        }
    }

    async updateEmpresa(id, data) {
        try {
            await api.updateRecord('ente', id, data);
            ui.showToast('Empresa actualizada correctamente', 'success');
            ui.hideModal();
            await this.loadEmpresas();
        } catch (error) {
            console.error('Error updating empresa:', error);
            ui.showToast('Error al actualizar la empresa', 'error');
        }
    }

    exportEmpresas() {
        if (!this.empresas || this.empresas.length === 0) {
            ui.showToast('No hay datos para exportar', 'warning');
            return;
        }

        // Create CSV content
        const headers = ['ID', 'Razón Social', 'CUIT', 'N° Socio', 'Sector', 'Rubro', 'Es Socio', 'Consorcista', 'Web'];
        const csvContent = [
            headers.join(','),
            ...this.empresas.map(e => [
                e.enteid,
                `"${e.razonsocial || ''}"`,
                `"${this.formatCUIT(e.cuit)}"`,
                e.nro_socio_cepip || '',
                `"${e.sector_nombre || ''}"`,
                `"${e.rubro_nombre || ''}"`,
                e.es_socio ? 'Sí' : 'No',
                e.esconsorcista ? 'Sí' : 'No',
                `"${e.web || ''}"`
            ].join(','))
        ].join('\n');

        // Download CSV
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `empresas_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        ui.showToast('Empresas exportadas correctamente', 'success');
    }
}

// Initialize empresas manager
window.empresasManager = new EmpresasManager();