// Consorcistas management functionality
class ConsorcistaManager {
    constructor() {
        this.currentPage = 1;
        this.recordsPerPage = 20;
        this.currentFilters = {};
        this.consorcistas = [];
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-consorcistas');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadConsorcistas());
        }

        // Search input with debounce
        const searchInput = document.getElementById('search-consorcista');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.currentFilters.search = e.target.value;
                    this.currentPage = 1; // Reset to first page when searching
                    this.applyFilters();
                }, 300); // Wait 300ms before searching
            });
        }

        // Clear filters
        const clearFiltersBtn = document.getElementById('clear-consorcistas-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        }

        // Add consorcista button
        const addConsorcistaBtn = document.getElementById('add-consorcista');
        if (addConsorcistaBtn) {
            addConsorcistaBtn.addEventListener('click', () => this.showAddConsorcistaModal());
        }

        // Export button
        const exportBtn = document.getElementById('export-consorcistas');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportConsorcistas());
        }
    }

    async loadConsorcistas() {
        console.log('Loading consorcistas...');
        
        const tableBody = document.getElementById('consorcistas-table-body');
        if (!tableBody) return;
        
        ui.showLoading(tableBody);
        
        try {
            // Load consorcistas data from API
            const response = await api.getRecords('consorcista', this.currentPage, this.recordsPerPage);
            this.consorcistas = response.data || [];
            
            // Load statistics
            await this.loadStatistics();
            
            // Render table
            this.renderConsorcistaTable();
            
            // Render pagination
            this.renderPagination(response.pagination);
            
        } catch (error) {
            console.error('Error loading consorcistas:', error);
            ui.showError(tableBody, 'Error al cargar los consorcistas');
        }
    }

    async loadStatistics() {
        try {
            const totalConsorcistas = this.consorcistas.length;
            const totalParcelas = this.consorcistas.reduce((sum, c) => sum + (parseInt(c.parcelas_count) || 0), 0);
            const totalEmpresas = this.consorcistas.reduce((sum, c) => sum + (parseInt(c.empresas_count) || 0), 0);
            const tipos = new Set(this.consorcistas.map(c => c.tipo_nombre).filter(Boolean)).size;

            // Update statistics display
            document.getElementById('total-consorcistas').textContent = totalConsorcistas;
            document.getElementById('parcelas-consorcistas').textContent = totalParcelas;
            document.getElementById('empresas-consorcistas').textContent = totalEmpresas;
            document.getElementById('tipos-consorcistas').textContent = tipos;

        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    renderConsorcistaTable() {
        const tableBody = document.getElementById('consorcistas-table-body');
        if (!tableBody) return;

        if (!this.consorcistas || this.consorcistas.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="8">No hay consorcistas para mostrar</td></tr>';
            return;
        }

        let html = '';
        this.consorcistas.forEach(consorcista => {
            html += `
                <tr>
                    <td>${consorcista.consorcistaid}</td>
                    <td><strong>${consorcista.nombre || '-'}</strong></td>
                    <td>${consorcista.nro_consorcista || '-'}</td>
                    <td>${consorcista.tipo_nombre || '-'}</td>
                    <td>
                        <span class="badge ${(consorcista.parcelas_count || 0) > 0 ? 'badge-success' : 'badge-secondary'}">
                            ${consorcista.parcelas_count || 0}
                        </span>
                    </td>
                    <td>
                        <span class="badge ${(consorcista.empresas_count || 0) > 0 ? 'badge-success' : 'badge-secondary'}">
                            ${consorcista.empresas_count || 0}
                        </span>
                    </td>
                    <td>${this.formatDate(consorcista.fecha_de_carga)}</td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="consorcistaManager.editConsorcista(${consorcista.consorcistaid})">
                            Editar
                        </button>
                        <button class="btn btn-info btn-sm" onclick="consorcistaManager.viewDetails(${consorcista.consorcistaid})">
                            Detalles
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="consorcistaManager.manageParcelas(${consorcista.consorcistaid})">
                            Parcelas
                        </button>
                        <button class="btn btn-success btn-sm" onclick="consorcistaManager.viewRelations(${consorcista.consorcistaid})">
                            Relaciones
                        </button>
                    </td>
                </tr>
            `;
        });

        tableBody.innerHTML = html;
    }

    formatDate(dateStr) {
        if (!dateStr) return '-';
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('es-ES');
        } catch {
            return dateStr;
        }
    }

    renderPagination(pagination) {
        const paginationContainer = document.getElementById('consorcistas-pagination');
        if (!paginationContainer || !pagination) return;

        const totalPages = pagination.pages || 1;
        const currentPage = pagination.page || 1;
        const total = pagination.total || 0;
        
        // Show pagination info
        const startRecord = ((currentPage - 1) * this.recordsPerPage) + 1;
        const endRecord = Math.min(currentPage * this.recordsPerPage, total);
        
        let html = `
            <div class="pagination-info">
                Mostrando ${startRecord}-${endRecord} de ${total} consorcistas
            </div>
        `;

        if (totalPages <= 1) {
            paginationContainer.innerHTML = html;
            return;
        }

        html += '<div class="pagination">';
        
        // First page
        if (currentPage > 1) {
            html += `<button class="btn btn-secondary" onclick="consorcistaManager.changePage(1)">« Primero</button>`;
        }
        
        // Previous button
        if (currentPage > 1) {
            html += `<button class="btn btn-secondary" onclick="consorcistaManager.changePage(${currentPage - 1})">‹ Anterior</button>`;
        }
        
        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const active = i === currentPage ? 'btn-primary' : 'btn-secondary';
            html += `<button class="btn ${active}" onclick="consorcistaManager.changePage(${i})">${i}</button>`;
        }
        
        // Next button
        if (currentPage < totalPages) {
            html += `<button class="btn btn-secondary" onclick="consorcistaManager.changePage(${currentPage + 1})">Siguiente ›</button>`;
        }
        
        // Last page
        if (currentPage < totalPages) {
            html += `<button class="btn btn-secondary" onclick="consorcistaManager.changePage(${totalPages})">Último »</button>`;
        }
        
        html += '</div>';
        paginationContainer.innerHTML = html;
    }

    async changePage(page) {
        this.currentPage = page;
        await this.loadConsorcistas();
        
        // Scroll to top of table
        const tableContainer = document.querySelector('#consorcistas .table-container');
        if (tableContainer) {
            tableContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    applyFilters() {
        console.log('Applying filters:', this.currentFilters);
        this.currentPage = 1; // Reset to first page when filtering
        this.loadConsorcistas();
    }

    clearFilters() {
        this.currentFilters = {};
        document.getElementById('search-consorcista').value = '';
        this.currentPage = 1;
        this.loadConsorcistas();
    }

    showAddConsorcistaModal() {
        const formFields = [
            { name: 'nombre', label: 'Nombre', type: 'text', required: true },
            { name: 'nro_consorcista', label: 'N° Consorcista', type: 'number', required: true }
        ];

        const formHTML = ui.generateForm(formFields);
        ui.showModal('Agregar Consorcista', formHTML, (data) => this.createConsorcista(data));
    }

    async editConsorcista(id) {
        try {
            const consorcista = this.consorcistas.find(c => c.consorcistaid === id);
            if (!consorcista) {
                ui.showToast('Consorcista no encontrado', 'error');
                return;
            }

            const formFields = [
                { name: 'nombre', label: 'Nombre', type: 'text', required: true },
                { name: 'nro_consorcista', label: 'N° Consorcista', type: 'number', required: true }
            ];

            const formHTML = ui.generateForm(formFields, consorcista);
            ui.showModal('Editar Consorcista', formHTML, (data) => this.updateConsorcista(id, data));

        } catch (error) {
            console.error('Error editing consorcista:', error);
            ui.showToast('Error al cargar el consorcista', 'error');
        }
    }

    viewDetails(id) {
        const consorcista = this.consorcistas.find(c => c.consorcistaid === id);
        if (!consorcista) {
            ui.showToast('Consorcista no encontrado', 'error');
            return;
        }

        const detailsHTML = `
            <div class="consorcista-details">
                <h4>Detalles del Consorcista</h4>
                <div class="details-grid">
                    <div><strong>ID:</strong> ${consorcista.consorcistaid}</div>
                    <div><strong>Nombre:</strong> ${consorcista.nombre || '-'}</div>
                    <div><strong>N° Consorcista:</strong> ${consorcista.nro_consorcista || '-'}</div>
                    <div><strong>Tipo:</strong> ${consorcista.tipo_nombre || '-'}</div>
                    <div><strong>Parcelas Asociadas:</strong> ${consorcista.parcelas_count || 0}</div>
                    <div><strong>Empresas Vinculadas:</strong> ${consorcista.empresas_count || 0}</div>
                    <div><strong>Fecha de Carga:</strong> ${this.formatDate(consorcista.fecha_de_carga)}</div>
                </div>
                
                <div class="action-buttons" style="margin-top: 1rem;">
                    <button class="btn btn-info" onclick="consorcistaManager.viewRelations(${consorcista.consorcistaid})">
                        Ver Parcelas y Empresas
                    </button>
                </div>
            </div>
        `;

        ui.showModal('Detalles del Consorcista', detailsHTML);
    }

    async viewRelations(id) {
        const consorcista = this.consorcistas.find(c => c.consorcistaid === id);
        if (!consorcista) {
            ui.showToast('Consorcista no encontrado', 'error');
            return;
        }

        // This would ideally make additional API calls to get related data
        const relationsHTML = `
            <div class="consorcista-relations">
                <h4>Relaciones de ${consorcista.nombre}</h4>
                
                <div class="relations-summary">
                    <div class="relation-card">
                        <h5>📍 Parcelas Asociadas</h5>
                        <p class="relation-count">${consorcista.parcelas_count || 0} parcelas</p>
                        <small>Parcelas bajo la administración de este consorcista</small>
                    </div>
                    
                    <div class="relation-card">
                        <h5>🏢 Empresas Vinculadas</h5>
                        <p class="relation-count">${consorcista.empresas_count || 0} empresas</p>
                        <small>Empresas que forman parte del consorcio</small>
                    </div>
                </div>
                
                <div class="note">
                    <strong>Nota:</strong> Para ver el detalle completo de parcelas y empresas, 
                    navega a las secciones correspondientes y filtra por este consorcista.
                </div>
            </div>
        `;

        ui.showModal('Relaciones del Consorcista', relationsHTML);
    }

    async createConsorcista(data) {
        try {
            await api.createRecord('consorcista', data);
            ui.showToast('Consorcista creado correctamente', 'success');
            ui.hideModal();
            await this.loadConsorcistas();
        } catch (error) {
            console.error('Error creating consorcista:', error);
            ui.showToast('Error al crear el consorcista', 'error');
        }
    }

    async updateConsorcista(id, data) {
        try {
            await api.updateRecord('consorcista', id, data);
            ui.showToast('Consorcista actualizado correctamente', 'success');
            ui.hideModal();
            await this.loadConsorcistas();
        } catch (error) {
            console.error('Error updating consorcista:', error);
            ui.showToast('Error al actualizar el consorcista', 'error');
        }
    }

    exportConsorcistas() {
        if (!this.consorcistas || this.consorcistas.length === 0) {
            ui.showToast('No hay datos para exportar', 'warning');
            return;
        }

        // Create CSV content
        const headers = ['ID', 'Nombre', 'N° Consorcista', 'Tipo', 'Parcelas', 'Empresas', 'Fecha Carga'];
        const csvContent = [
            headers.join(','),
            ...this.consorcistas.map(c => [
                c.consorcistaid,
                `"${c.nombre || ''}"`,
                c.nro_consorcista || '',
                `"${c.tipo_nombre || ''}"`,
                c.parcelas_count || 0,
                c.empresas_count || 0,
                `"${this.formatDate(c.fecha_de_carga)}"`
            ].join(','))
        ].join('\n');

        // Download CSV
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `consorcistas_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        ui.showToast('Consorcistas exportados correctamente', 'success');
    }

    async manageParcelas(consorcistaId) {
        try {
            const consorcista = this.consorcistas.find(c => c.consorcistaid === consorcistaId);
            if (!consorcista) {
                ui.showToast('Consorcista no encontrado', 'error');
                return;
            }

            // Load parcelas assigned to this consorcista
            const response = await fetch(`/api/records/consorcista/${consorcistaId}/parcelas`);
            if (!response.ok) {
                throw new Error('Error al cargar las parcelas');
            }

            const data = await response.json();
            const parcelas = data.parcelas || [];

            let parcelasTableHTML = '';
            if (parcelas.length === 0) {
                parcelasTableHTML = '<tr><td colspan="8">No hay parcelas asignadas</td></tr>';
            } else {
                parcelasTableHTML = parcelas.map(p => `
                    <tr>
                        <td>${p.id}</td>
                        <td><strong>${p.parcela || '-'}</strong></td>
                        <td>${p.calle || '-'}</td>
                        <td>${p.numero || '-'}</td>
                        <td>${p.superficie_has || '-'}</td>
                        <td>${p.tieneplanta ? 'Sí' : 'No'}</td>
                        <td>${p.alquilada ? 'Sí' : 'No'}</td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="consorcistaManager.unassignParcela(${p.id}, ${consorcistaId})">
                                Desasignar
                            </button>
                        </td>
                    </tr>
                `).join('');
            }

            const manageHTML = `
                <div class="consorcista-parcelas-manager">
                    <h4>Parcelas de ${consorcista.nombre}</h4>
                    <p><strong>Total de parcelas:</strong> ${parcelas.length}</p>
                    
                    <div class="table-container" style="max-height: 400px; overflow-y: auto;">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Parcela</th>
                                    <th>Calle</th>
                                    <th>Número</th>
                                    <th>Superficie</th>
                                    <th>Planta</th>
                                    <th>Alquilada</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${parcelasTableHTML}
                            </tbody>
                        </table>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <button class="btn btn-primary" onclick="consorcistaManager.showAssignParcelaModal(${consorcistaId})">
                            Asignar Nueva Parcela
                        </button>
                    </div>
                </div>
            `;

            ui.showModal('Gestionar Parcelas', manageHTML);

        } catch (error) {
            console.error('Error managing parcelas:', error);
            ui.showToast('Error al cargar las parcelas', 'error');
        }
    }

    async showAssignParcelaModal(consorcistaId) {
        try {
            // Load all parcelas that don't have a consorcista assigned
            const response = await fetch('/api/records/parcela?page=1&limit=1000');
            if (!response.ok) {
                throw new Error('Error al cargar las parcelas');
            }

            const data = await response.json();
            const availableParcelas = (data.data || []).filter(p => !p.consorcistaid);

            if (availableParcelas.length === 0) {
                ui.showToast('No hay parcelas disponibles para asignar', 'warning');
                return;
            }

            const parcelasOptions = availableParcelas.map(p => 
                `<option value="${p.parcelaid}">${p.parcela || 'N/A'} - ${p.calle || ''} ${p.numero || ''}</option>`
            ).join('');

            const assignHTML = `
                <div class="assign-parcela-form">
                    <h4>Asignar Parcela</h4>
                    <form id="assign-parcela-form">
                        <div class="form-group">
                            <label for="parcela-select">Seleccionar Parcela:</label>
                            <select id="parcela-select" class="form-control" required>
                                <option value="">-- Seleccionar parcela --</option>
                                ${parcelasOptions}
                            </select>
                        </div>
                        <div class="form-group">
                            <button type="submit" class="btn btn-primary">Asignar Parcela</button>
                        </div>
                    </form>
                </div>
            `;

            ui.showModal('Asignar Parcela', assignHTML);

            // Setup form handler
            const form = document.getElementById('assign-parcela-form');
            if (form) {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const parcelaId = document.getElementById('parcela-select').value;
                    if (parcelaId) {
                        await this.assignParcela(parcelaId, consorcistaId);
                    }
                });
            }

        } catch (error) {
            console.error('Error loading available parcelas:', error);
            ui.showToast('Error al cargar las parcelas disponibles', 'error');
        }
    }

    async assignParcela(parcelaId, consorcistaId) {
        try {
            const response = await fetch(`/api/records/parcela/${parcelaId}/consorcista`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    consorcistaid: consorcistaId
                })
            });

            if (!response.ok) {
                throw new Error('Error al asignar la parcela');
            }

            const result = await response.json();
            ui.showToast(result.message, 'success');
            ui.hideModal();
            
            // Refresh the parcelas management view
            await this.manageParcelas(consorcistaId);

        } catch (error) {
            console.error('Error assigning parcela:', error);
            ui.showToast('Error al asignar la parcela', 'error');
        }
    }

    async unassignParcela(parcelaId, consorcistaId) {
        if (!confirm('¿Estás seguro de que quieres desasignar esta parcela del consorcista?')) {
            return;
        }

        try {
            const response = await fetch(`/api/records/parcela/${parcelaId}/consorcista`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    consorcistaid: null
                })
            });

            if (!response.ok) {
                throw new Error('Error al desasignar la parcela');
            }

            const result = await response.json();
            ui.showToast(result.message, 'success');
            
            // Refresh the parcelas management view
            await this.manageParcelas(consorcistaId);

        } catch (error) {
            console.error('Error unassigning parcela:', error);
            ui.showToast('Error al desasignar la parcela', 'error');
        }
    }
}

// Initialize consorcistas manager
window.consorcistaManager = new ConsorcistaManager();