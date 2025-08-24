// Personas management functionality
class PersonasManager {
    constructor() {
        this.currentPage = 1;
        this.recordsPerPage = 20;
        this.currentFilters = {};
        this.personas = [];
        this.empresas = [];
        this.cargos = [];
        this.areas = [];
        
        this.setupEventListeners();
        this.loadLookupData();
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-personas');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadPersonas());
        }

        // Search input
        const searchInput = document.getElementById('search-persona');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.currentFilters.search = e.target.value;
                this.applyFilters();
            });
        }

        // Filter select
        const filterEmail = document.getElementById('filter-con-email');
        if (filterEmail) {
            filterEmail.addEventListener('change', (e) => {
                this.currentFilters.con_email = e.target.value;
                this.applyFilters();
            });
        }

        // Clear filters
        const clearFiltersBtn = document.getElementById('clear-personas-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        }

        // Add persona button
        const addPersonaBtn = document.getElementById('add-persona');
        if (addPersonaBtn) {
            addPersonaBtn.addEventListener('click', () => this.showAddPersonaModal());
        }

        // Export button
        const exportBtn = document.getElementById('export-personas');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportPersonas());
        }
    }

    async loadPersonas() {
        console.log('Loading personas...');
        
        const tableBody = document.getElementById('personas-table-body');
        if (!tableBody) return;
        
        ui.showLoading(tableBody);
        
        try {
            // Load personas data from API
            const response = await api.getRecords('persona', this.currentPage, this.recordsPerPage);
            this.personas = response.data || [];
            
            // Load statistics
            await this.loadStatistics();
            
            // Render table
            this.renderPersonasTable();
            
            // Render pagination
            this.renderPagination(response.pagination);
            
        } catch (error) {
            console.error('Error loading personas:', error);
            ui.showError(tableBody, 'Error al cargar las personas');
        }
    }

    async loadStatistics() {
        try {
            const totalPersonas = this.personas.length;
            const conEmail = this.personas.filter(p => p.correo_electronico && p.correo_electronico.trim()).length;
            const conTelefono = this.personas.filter(p => p.telefono && p.telefono.trim()).length;
            const conRelaciones = this.personas.filter(p => p.empresas && p.empresas.trim()).length;

            // Update statistics display
            document.getElementById('total-personas').textContent = totalPersonas;
            document.getElementById('personas-con-email').textContent = conEmail;
            document.getElementById('personas-con-telefono').textContent = conTelefono;
            document.getElementById('total-relaciones').textContent = conRelaciones;

        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    renderPersonasTable() {
        const tableBody = document.getElementById('personas-table-body');
        if (!tableBody) return;

        if (!this.personas || this.personas.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="9">No hay personas para mostrar</td></tr>';
            return;
        }

        let html = '';
        this.personas.forEach(persona => {
            html += `
                <tr>
                    <td>${persona.personaid}</td>
                    <td><strong>${persona.nombre_apellido || '-'}</strong></td>
                    <td>${this.formatEmail(persona.correo_electronico)}</td>
                    <td>${persona.telefono || '-'}</td>
                    <td>${persona.celular || '-'}</td>
                    <td>${this.formatEmpresas(persona.empresas)}</td>
                    <td>${this.formatCargos(persona.cargos)}</td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="personasManager.editPersona(${persona.personaid})">
                            Editar
                        </button>
                        <button class="btn btn-info btn-sm" onclick="personasManager.viewDetails(${persona.personaid})">
                            Detalles
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="personasManager.manageRelations(${persona.personaid})">
                            Gestionar
                        </button>
                    </td>
                </tr>
            `;
        });

        tableBody.innerHTML = html;
    }

    formatEmail(email) {
        if (!email || !email.trim()) return '-';
        return `<a href="mailto:${email}" class="email-link">${email}</a>`;
    }

    formatEmpresas(empresas) {
        if (!empresas || !empresas.trim()) return '-';
        // If multiple companies, show count and first few
        const empresasList = empresas.split(', ');
        if (empresasList.length > 2) {
            return `<span title="${empresas}">${empresasList.slice(0, 2).join(', ')}... (+${empresasList.length - 2})</span>`;
        }
        return `<span title="${empresas}">${empresas}</span>`;
    }

    formatCargos(cargos) {
        if (!cargos || !cargos.trim()) return '-';
        const cargosList = cargos.split(', ');
        if (cargosList.length > 2) {
            return `<span title="${cargos}">${cargosList.slice(0, 2).join(', ')}... (+${cargosList.length - 2})</span>`;
        }
        return `<span title="${cargos}">${cargos}</span>`;
    }

    renderPagination(pagination) {
        const paginationContainer = document.getElementById('personas-pagination');
        if (!paginationContainer || !pagination) return;

        const totalPages = pagination.pages || 1;
        
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let html = '<div class="pagination">';
        
        // Previous button
        if (this.currentPage > 1) {
            html += `<button class="btn btn-secondary" onclick="personasManager.changePage(${this.currentPage - 1})">« Anterior</button>`;
        }
        
        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const active = i === this.currentPage ? 'btn-primary' : 'btn-secondary';
            html += `<button class="btn ${active}" onclick="personasManager.changePage(${i})">${i}</button>`;
        }
        
        // Next button
        if (this.currentPage < totalPages) {
            html += `<button class="btn btn-secondary" onclick="personasManager.changePage(${this.currentPage + 1})">Siguiente »</button>`;
        }
        
        html += '</div>';
        paginationContainer.innerHTML = html;
    }

    async changePage(page) {
        this.currentPage = page;
        await this.loadPersonas();
    }

    applyFilters() {
        console.log('Applying filters:', this.currentFilters);
        this.loadPersonas();
    }

    clearFilters() {
        this.currentFilters = {};
        document.getElementById('search-persona').value = '';
        document.getElementById('filter-con-email').value = '';
        this.loadPersonas();
    }

    async loadLookupData() {
        try {
            // Load empresas, cargos, and areas for dropdowns
            const [empresasResponse, cargosResponse, areasResponse] = await Promise.all([
                fetch('/api/records/lookup/empresas'),
                fetch('/api/records/lookup/cargos'),
                fetch('/api/records/lookup/areas')
            ]);

            if (empresasResponse.ok) {
                const empresasData = await empresasResponse.json();
                this.empresas = empresasData.empresas || [];
            }

            if (cargosResponse.ok) {
                const cargosData = await cargosResponse.json();
                this.cargos = cargosData.cargos || [];
            }

            if (areasResponse.ok) {
                const areasData = await areasResponse.json();
                this.areas = areasData.areas || [];
            }

        } catch (error) {
            console.error('Error loading lookup data:', error);
        }
    }

    showAddPersonaModal() {
        const formFields = [
            { name: 'nombre_apellido', label: 'Nombre y Apellido', type: 'text', required: true },
            { name: 'correo_electronico', label: 'Email', type: 'email' },
            { name: 'telefono', label: 'Teléfono', type: 'tel' },
            { name: 'celular', label: 'Celular', type: 'tel' }
        ];

        const formHTML = ui.generateForm(formFields);
        ui.showModal('Agregar Persona', formHTML, (data) => this.createPersona(data));
    }

    async editPersona(id) {
        try {
            const persona = this.personas.find(p => p.personaid === id);
            if (!persona) {
                ui.showToast('Persona no encontrada', 'error');
                return;
            }

            const formFields = [
                { name: 'nombre_apellido', label: 'Nombre y Apellido', type: 'text', required: true },
                { name: 'correo_electronico', label: 'Email', type: 'email' },
                { name: 'telefono', label: 'Teléfono', type: 'tel' },
                { name: 'celular', label: 'Celular', type: 'tel' }
            ];

            const formHTML = ui.generateForm(formFields, persona);
            ui.showModal('Editar Persona', formHTML, (data) => this.updatePersona(id, data));

        } catch (error) {
            console.error('Error editing persona:', error);
            ui.showToast('Error al cargar la persona', 'error');
        }
    }

    viewDetails(id) {
        const persona = this.personas.find(p => p.personaid === id);
        if (!persona) {
            ui.showToast('Persona no encontrada', 'error');
            return;
        }

        const detailsHTML = `
            <div class="persona-details">
                <h4>Detalles de ${persona.nombre_apellido}</h4>
                <div class="details-grid">
                    <div><strong>ID:</strong> ${persona.personaid}</div>
                    <div><strong>Nombre y Apellido:</strong> ${persona.nombre_apellido || '-'}</div>
                    <div><strong>Email:</strong> ${persona.correo_electronico || '-'}</div>
                    <div><strong>Teléfono:</strong> ${persona.telefono || '-'}</div>
                    <div><strong>Celular:</strong> ${persona.celular || '-'}</div>
                    <div><strong>Consorcista ID:</strong> ${persona.consorcistaid || '-'}</div>
                    <div><strong>Fecha de Carga:</strong> ${persona.fecha_de_carga || '-'}</div>
                </div>
                
                ${persona.empresas ? `
                <div class="empresas-section">
                    <h5>Empresas Asociadas:</h5>
                    <div class="empresas-list">
                        ${persona.empresas.split(', ').map(empresa => `<span class="empresa-tag">${empresa}</span>`).join('')}
                    </div>
                </div>
                ` : ''}
                
                ${persona.cargos ? `
                <div class="cargos-section">
                    <h5>Cargos:</h5>
                    <div class="cargos-list">
                        ${persona.cargos.split(', ').map(cargo => `<span class="cargo-tag">${cargo}</span>`).join('')}
                    </div>
                </div>
                ` : ''}
                
                <div class="action-buttons" style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #dee2e6;">
                    <button class="btn btn-primary" onclick="personasManager.manageRelations(${persona.personaid})">
                        Gestionar Empresas y Cargos
                    </button>
                </div>
            </div>
        `;

        ui.showModal('Detalles de Persona', detailsHTML);
    }

    async createPersona(data) {
        try {
            await api.createRecord('persona', data);
            ui.showToast('Persona creada correctamente', 'success');
            ui.hideModal();
            await this.loadPersonas();
        } catch (error) {
            console.error('Error creating persona:', error);
            ui.showToast('Error al crear la persona', 'error');
        }
    }

    async updatePersona(id, data) {
        try {
            await api.updateRecord('persona', id, data);
            ui.showToast('Persona actualizada correctamente', 'success');
            ui.hideModal();
            await this.loadPersonas();
        } catch (error) {
            console.error('Error updating persona:', error);
            ui.showToast('Error al actualizar la persona', 'error');
        }
    }

    exportPersonas() {
        if (!this.personas || this.personas.length === 0) {
            ui.showToast('No hay datos para exportar', 'warning');
            return;
        }

        // Create CSV content
        const headers = ['ID', 'Nombre y Apellido', 'Email', 'Teléfono', 'Celular', 'Empresas', 'Cargos'];
        const csvContent = [
            headers.join(','),
            ...this.personas.map(p => [
                p.personaid,
                `"${p.nombre_apellido || ''}"`,
                `"${p.correo_electronico || ''}"`,
                `"${p.telefono || ''}"`,
                `"${p.celular || ''}"`,
                `"${p.empresas || ''}"`,
                `"${p.cargos || ''}"`
            ].join(','))
        ].join('\n');

        // Download CSV
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `personas_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        ui.showToast('Personas exportadas correctamente', 'success');
    }

    async manageRelations(personaId) {
        const persona = this.personas.find(p => p.personaid === personaId);
        if (!persona) {
            ui.showToast('Persona no encontrada', 'error');
            return;
        }

        try {
            // Get current relations
            const response = await fetch(`/api/records/persona/${personaId}/relaciones`);
            let relaciones = [];
            
            if (response.ok) {
                const data = await response.json();
                relaciones = data.relaciones || [];
            }

            const relationsHTML = `
                <div class="persona-relations-manager">
                    <h4>Gestionar Relaciones de ${persona.nombre_apellido}</h4>
                    
                    <div class="add-relation-form">
                        <h5>Agregar Nueva Relación</h5>
                        <form id="relation-form">
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="empresa-select">Empresa:</label>
                                    <select id="empresa-select" class="form-control" required>
                                        <option value="">Seleccionar empresa...</option>
                                        ${this.empresas.map(emp => `<option value="${emp.id}">${emp.name}</option>`).join('')}
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label for="cargo-select">Cargo:</label>
                                    <select id="cargo-select" class="form-control" required>
                                        <option value="">Seleccionar cargo...</option>
                                        ${this.cargos.map(cargo => `<option value="${cargo.id}">${cargo.name}</option>`).join('')}
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label for="area-select">Área:</label>
                                    <select id="area-select" class="form-control">
                                        <option value="">Seleccionar área...</option>
                                        ${this.areas.map(area => `<option value="${area.id}">${area.name}</option>`).join('')}
                                    </select>
                                </div>
                            </div>
                            <button type="submit" class="btn btn-primary">Agregar Relación</button>
                        </form>
                    </div>

                    <div class="current-relations">
                        <h5>Relaciones Actuales</h5>
                        <div id="relations-list">
                            ${this.renderRelationsList(relaciones, personaId)}
                        </div>
                    </div>
                </div>
            `;

            ui.showModal('Gestionar Relaciones', relationsHTML);

            // Add form submit handler
            const form = document.getElementById('relation-form');
            if (form) {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    await this.addRelation(personaId);
                });
            }

        } catch (error) {
            console.error('Error managing relations:', error);
            ui.showToast('Error al cargar las relaciones', 'error');
        }
    }

    renderRelationsList(relaciones, personaId) {
        if (!relaciones || relaciones.length === 0) {
            return '<p class="no-relations">No hay relaciones registradas</p>';
        }

        return `
            <div class="relations-table">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Empresa</th>
                            <th>Cargo</th>
                            <th>Área</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${relaciones.map(rel => `
                            <tr>
                                <td>${rel.empresa || '-'}</td>
                                <td>${rel.cargo || '-'}</td>
                                <td>${rel.area || '-'}</td>
                                <td>
                                    <button class="btn btn-danger btn-sm" onclick="personasManager.removeRelation(${rel.id}, ${personaId})">
                                        Eliminar
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    async addRelation(personaId) {
        try {
            const empresaId = document.getElementById('empresa-select').value;
            const cargoId = document.getElementById('cargo-select').value;
            const areaId = document.getElementById('area-select').value;

            if (!empresaId || !cargoId) {
                ui.showToast('Empresa y cargo son obligatorios', 'warning');
                return;
            }

            const relationData = {
                enteid: parseInt(empresaId),
                cargoid: parseInt(cargoId),
                areaid: areaId ? parseInt(areaId) : null
            };

            const response = await fetch(`/api/records/persona/${personaId}/relaciones`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(relationData)
            });

            if (response.ok) {
                ui.showToast('Relación agregada correctamente', 'success');
                ui.hideModal();
                // Refresh the personas list to show updated data
                await this.loadPersonas();
            } else {
                const error = await response.json();
                ui.showToast('Error al agregar la relación: ' + error.detail, 'error');
            }

        } catch (error) {
            console.error('Error adding relation:', error);
            ui.showToast('Error al agregar la relación', 'error');
        }
    }

    async removeRelation(relationId, personaId) {
        if (!confirm('¿Estás seguro de que quieres eliminar esta relación?')) {
            return;
        }

        try {
            const response = await fetch(`/api/records/persona/${personaId}/relaciones/${relationId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                ui.showToast('Relación eliminada correctamente', 'success');
                ui.hideModal();
                // Refresh the personas list to show updated data
                await this.loadPersonas();
            } else {
                const error = await response.json();
                ui.showToast('Error al eliminar la relación: ' + error.detail, 'error');
            }

        } catch (error) {
            console.error('Error removing relation:', error);
            ui.showToast('Error al eliminar la relación', 'error');
        }
    }
}

// Initialize personas manager
window.personasManager = new PersonasManager();