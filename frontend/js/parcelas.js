// Parcelas management functionality
class ParcelasManager {
    constructor() {
        this.currentPage = 1;
        this.recordsPerPage = 20;
        this.currentFilters = {};
        this.parcelas = [];
        this.statistics = {};
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-parcelas');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadParcelas());
        }

        // Search input
        const searchInput = document.getElementById('search-parcela');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.currentFilters.search = e.target.value;
                this.applyFilters();
            });
        }

        // Filter selects
        const filterPlanta = document.getElementById('filter-planta');
        if (filterPlanta) {
            filterPlanta.addEventListener('change', (e) => {
                this.currentFilters.tieneplanta = e.target.value;
                this.applyFilters();
            });
        }

        const filterAlquilada = document.getElementById('filter-alquilada');
        if (filterAlquilada) {
            filterAlquilada.addEventListener('change', (e) => {
                this.currentFilters.alquilada = e.target.value;
                this.applyFilters();
            });
        }

        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        }

        // Add parcela button
        const addParcelaBtn = document.getElementById('add-parcela');
        if (addParcelaBtn) {
            addParcelaBtn.addEventListener('click', () => this.showAddParcelaModal());
        }

        // Export button
        const exportBtn = document.getElementById('export-parcelas');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportParcelas());
        }
    }

    async loadParcelas() {
        console.log('Loading parcelas...');
        
        const tableBody = document.getElementById('parcelas-table-body');
        if (!tableBody) return;
        
        ui.showLoading(tableBody);
        
        try {
            // Load parcelas data from API
            const response = await api.getRecords('parcela', this.currentPage, this.recordsPerPage);
            this.parcelas = response.data || [];
            
            // Load statistics
            await this.loadStatistics();
            
            // Render table
            this.renderParcelasTable();
            
            // Render pagination
            this.renderPagination(response.pagination);
            
        } catch (error) {
            console.error('Error loading parcelas:', error);
            ui.showError(tableBody, 'Error al cargar las parcelas');
        }
    }

    async loadStatistics() {
        try {
            // Get statistics from the current data and API
            const totalParcelas = this.parcelas.length;
            const conPlanta = this.parcelas.filter(p => p.tieneplanta).length;
            const alquiladas = this.parcelas.filter(p => p.alquilada).length;
            
            // Calculate total surface
            const superficieTotal = this.parcelas.reduce((total, p) => {
                return total + (parseFloat(p.superficie_has) || 0);
            }, 0);

            // Update statistics display
            document.getElementById('total-parcelas').textContent = totalParcelas;
            document.getElementById('parcelas-con-planta').textContent = conPlanta;
            document.getElementById('parcelas-alquiladas').textContent = alquiladas;
            document.getElementById('superficie-total').textContent = superficieTotal.toFixed(2) + ' ha';

        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    renderParcelasTable() {
        const tableBody = document.getElementById('parcelas-table-body');
        if (!tableBody) return;

        if (!this.parcelas || this.parcelas.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="9">No hay parcelas para mostrar</td></tr>';
            return;
        }

        let html = '';
        this.parcelas.forEach(parcela => {
            html += `
                <tr>
                    <td>${parcela.parcelaid}</td>
                    <td><strong>${parcela.parcela || '-'}</strong></td>
                    <td>${parcela.calle || '-'}</td>
                    <td>${parcela.numero || '-'}</td>
                    <td>${this.formatSuperficie(parcela.superficie_has)}</td>
                    <td>${this.formatBoolean(parcela.tieneplanta)}</td>
                    <td>${this.formatBoolean(parcela.alquilada)}</td>
                    <td>${this.getConsorcistaNombre(parcela.consorcista_nombre, parcela.consorcistaid)}</td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="parcelasManager.editParcela(${parcela.parcelaid})">
                            Editar
                        </button>
                        <button class="btn btn-info btn-sm" onclick="parcelasManager.viewDetails(${parcela.parcelaid})">
                            Detalles
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="parcelasManager.manageConsorcista(${parcela.parcelaid})">
                            Consorcista
                        </button>
                    </td>
                </tr>
            `;
        });

        tableBody.innerHTML = html;
    }

    formatSuperficie(superficie) {
        if (!superficie || superficie === 0) return '-';
        return parseFloat(superficie).toFixed(2) + ' ha';
    }

    formatBoolean(value) {
        if (value === true || value === 'true' || value === 1) {
            return '<span class="badge badge-success">Sí</span>';
        } else if (value === false || value === 'false' || value === 0) {
            return '<span class="badge badge-secondary">No</span>';
        }
        return '<span class="badge badge-light">-</span>';
    }

    getConsorcistaNombre(consorcistaNombre, consorcistaid) {
        // Use the joined consorcista name if available, otherwise show ID
        if (consorcistaNombre) return consorcistaNombre;
        if (!consorcistaid) return '-';
        return `Consorcista #${consorcistaid}`;
    }

    renderPagination(pagination) {
        const paginationContainer = document.getElementById('parcelas-pagination');
        if (!paginationContainer || !pagination) return;

        const totalPages = pagination.pages || 1;
        
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let html = '<div class="pagination">';
        
        // Previous button
        if (this.currentPage > 1) {
            html += `<button class="btn btn-secondary" onclick="parcelasManager.changePage(${this.currentPage - 1})">« Anterior</button>`;
        }
        
        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const active = i === this.currentPage ? 'btn-primary' : 'btn-secondary';
            html += `<button class="btn ${active}" onclick="parcelasManager.changePage(${i})">${i}</button>`;
        }
        
        // Next button
        if (this.currentPage < totalPages) {
            html += `<button class="btn btn-secondary" onclick="parcelasManager.changePage(${this.currentPage + 1})">Siguiente »</button>`;
        }
        
        html += '</div>';
        paginationContainer.innerHTML = html;
    }

    async changePage(page) {
        this.currentPage = page;
        await this.loadParcelas();
    }

    applyFilters() {
        // This would apply client-side filtering or make a new API call with filters
        console.log('Applying filters:', this.currentFilters);
        // For now, just reload data
        this.loadParcelas();
    }

    clearFilters() {
        this.currentFilters = {};
        document.getElementById('search-parcela').value = '';
        document.getElementById('filter-planta').value = '';
        document.getElementById('filter-alquilada').value = '';
        this.loadParcelas();
    }

    showAddParcelaModal() {
        const formFields = [
            { name: 'parcela', label: 'Parcela', type: 'text', required: true },
            { name: 'calle', label: 'Calle', type: 'text' },
            { name: 'numero', label: 'Número', type: 'number' },
            { name: 'superficie_has', label: 'Superficie (ha)', type: 'number', step: '0.01' },
            { name: 'tieneplanta', label: 'Tiene Planta', type: 'checkbox' },
            { name: 'alquilada', label: 'Alquilada', type: 'checkbox' },
            { name: 'fraccion', label: 'Fracción', type: 'text' }
        ];

        const formHTML = ui.generateForm(formFields);
        ui.showModal('Agregar Parcela', formHTML, (data) => this.createParcela(data));
    }

    async editParcela(id) {
        try {
            const parcela = this.parcelas.find(p => p.parcelaid === id);
            if (!parcela) {
                ui.showToast('Parcela no encontrada', 'error');
                return;
            }

            const formFields = [
                { name: 'parcela', label: 'Parcela', type: 'text', required: true },
                { name: 'calle', label: 'Calle', type: 'text' },
                { name: 'numero', label: 'Número', type: 'number' },
                { name: 'superficie_has', label: 'Superficie (ha)', type: 'number', step: '0.01' },
                { name: 'tieneplanta', label: 'Tiene Planta', type: 'checkbox' },
                { name: 'alquilada', label: 'Alquilada', type: 'checkbox' },
                { name: 'fraccion', label: 'Fracción', type: 'text' }
            ];

            const formHTML = ui.generateForm(formFields, parcela);
            ui.showModal('Editar Parcela', formHTML, (data) => this.updateParcela(id, data));

        } catch (error) {
            console.error('Error editing parcela:', error);
            ui.showToast('Error al cargar la parcela', 'error');
        }
    }

    async createParcela(data) {
        try {
            await api.createRecord('parcela', data);
            ui.showToast('Parcela creada correctamente', 'success');
            ui.hideModal();
            await this.loadParcelas();
        } catch (error) {
            console.error('Error creating parcela:', error);
            ui.showToast('Error al crear la parcela', 'error');
        }
    }

    async updateParcela(id, data) {
        try {
            await api.updateRecord('parcela', id, data);
            ui.showToast('Parcela actualizada correctamente', 'success');
            ui.hideModal();
            await this.loadParcelas();
        } catch (error) {
            console.error('Error updating parcela:', error);
            ui.showToast('Error al actualizar la parcela', 'error');
        }
    }

    viewDetails(id) {
        const parcela = this.parcelas.find(p => p.parcelaid === id);
        if (!parcela) {
            ui.showToast('Parcela no encontrada', 'error');
            return;
        }

        const detailsHTML = `
            <div class="parcela-details">
                <h4>Detalles de la Parcela ${parcela.parcela}</h4>
                <div class="details-grid">
                    <div><strong>ID:</strong> ${parcela.parcelaid}</div>
                    <div><strong>Parcela:</strong> ${parcela.parcela || '-'}</div>
                    <div><strong>Calle:</strong> ${parcela.calle || '-'}</div>
                    <div><strong>Número:</strong> ${parcela.numero || '-'}</div>
                    <div><strong>Superficie:</strong> ${this.formatSuperficie(parcela.superficie_has)}</div>
                    <div><strong>Fracción:</strong> ${parcela.fraccion || '-'}</div>
                    <div><strong>Porcentaje Reglamento:</strong> ${parcela.porcentaje_reglamento || '-'}%</div>
                    <div><strong>Tiene Planta:</strong> ${parcela.tieneplanta ? 'Sí' : 'No'}</div>
                    <div><strong>Alquilada:</strong> ${parcela.alquilada ? 'Sí' : 'No'}</div>
                    <div><strong>Fecha de Carga:</strong> ${parcela.fecha_de_carga || '-'}</div>
                    <div><strong>Consorcista:</strong> ${this.getConsorcistaNombre(parcela.consorcista_nombre, parcela.consorcistaid)}</div>
                    <div><strong>Ente ID:</strong> ${parcela.enteid || '-'}</div>
                </div>
            </div>
        `;

        ui.showModal('Detalles de Parcela', detailsHTML);
    }

    exportParcelas() {
        if (!this.parcelas || this.parcelas.length === 0) {
            ui.showToast('No hay datos para exportar', 'warning');
            return;
        }

        // Create CSV content
        const headers = ['ID', 'Parcela', 'Calle', 'Número', 'Superficie (ha)', 'Tiene Planta', 'Alquilada', 'Fracción'];
        const csvContent = [
            headers.join(','),
            ...this.parcelas.map(p => [
                p.parcelaid,
                `"${p.parcela || ''}"`,
                `"${p.calle || ''}"`,
                p.numero || '',
                p.superficie_has || '',
                p.tieneplanta ? 'Sí' : 'No',
                p.alquilada ? 'Sí' : 'No',
                `"${p.fraccion || ''}"`
            ].join(','))
        ].join('\n');

        // Download CSV
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `parcelas_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        ui.showToast('Parcelas exportadas correctamente', 'success');
    }

    async manageConsorcista(parcelaId) {
        try {
            // Load consorcistas for dropdown
            if (!this.consorcistas) {
                const response = await fetch('/api/records/lookup/consorcistas');
                const data = await response.json();
                this.consorcistas = data.consorcistas || [];
            }

            const parcela = this.parcelas.find(p => p.parcelaid === parcelaId);
            if (!parcela) {
                ui.showToast('Parcela no encontrada', 'error');
                return;
            }

            const consorcistasOptions = this.consorcistas.map(c => 
                `<option value="${c.id}" ${parcela.consorcistaid === c.id ? 'selected' : ''}>${c.name}</option>`
            ).join('');

            const manageHTML = `
                <div class="parcela-consorcista-manager">
                    <h4>Gestionar Consorcista - Parcela ${parcela.parcela}</h4>
                    <form id="consorcista-assignment-form">
                        <div class="form-group">
                            <label for="consorcista-select">Asignar Consorcista:</label>
                            <select id="consorcista-select" class="form-control">
                                <option value="">-- Sin asignar --</option>
                                ${consorcistasOptions}
                            </select>
                        </div>
                        <div class="form-group">
                            <p><strong>Consorcista actual:</strong> ${this.getConsorcistaNombre(parcela.consorcista_nombre, parcela.consorcistaid)}</p>
                        </div>
                    </form>
                </div>
            `;

            ui.showModal('Gestionar Consorcista', manageHTML, async (data) => {
                await this.updateParcelaConsorcista(parcelaId, data.consorcista);
            });

            // Setup form handler
            const form = document.getElementById('consorcista-assignment-form');
            if (form) {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const consorcistaId = document.getElementById('consorcista-select').value;
                    await this.updateParcelaConsorcista(parcelaId, consorcistaId);
                });
            }

        } catch (error) {
            console.error('Error managing consorcista:', error);
            ui.showToast('Error al cargar la gestión de consorcistas', 'error');
        }
    }

    async updateParcelaConsorcista(parcelaId, consorcistaId) {
        try {
            const response = await fetch(`/api/records/parcela/${parcelaId}/consorcista`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    consorcistaid: consorcistaId || null
                })
            });

            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }

            const result = await response.json();
            ui.showToast(result.message, 'success');
            ui.hideModal();
            
            // Reload parcelas to show updated assignment
            await this.loadParcelas();

        } catch (error) {
            console.error('Error updating parcela consorcista:', error);
            ui.showToast('Error al actualizar la asignación', 'error');
        }
    }
}

// Initialize parcelas manager
window.parcelasManager = new ParcelasManager();