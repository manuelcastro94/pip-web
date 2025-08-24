// API client for CEPIP backend
class APIClient {
    constructor() {
        this.baseURL = 'http://localhost:8000/api';
        this.headers = {
            'Content-Type': 'application/json',
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            headers: this.headers,
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // GET request
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST request
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PUT request
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // Specific API methods
    async getStats() {
        return this.get('/stats');
    }

    async getRecords(table = 'main', page = 1, limit = 20) {
        return this.get(`/records/${table}?page=${page}&limit=${limit}`);
    }

    async getRecord(table, id) {
        return this.get(`/records/${table}/${id}`);
    }

    async createRecord(table, data) {
        return this.post(`/records/${table}`, data);
    }

    async updateRecord(table, id, data) {
        return this.put(`/records/${table}/${id}`, data);
    }

    async deleteRecord(table, id) {
        return this.delete(`/records/${table}/${id}`);
    }

    async getTables() {
        return this.get('/tables');
    }

    async generateReport(reportType, params = {}) {
        return this.post(`/reports/${reportType}`, params);
    }

    async getSettings() {
        return this.get('/settings');
    }

    async updateSettings(settings) {
        return this.put('/settings', settings);
    }
}

// Global API client instance
const api = new APIClient();