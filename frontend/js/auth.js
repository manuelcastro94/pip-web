// Authentication manager
class AuthManager {
    constructor() {
        this.token = localStorage.getItem('access_token');
        this.user = null;
        
        if (localStorage.getItem('user')) {
            try {
                this.user = JSON.parse(localStorage.getItem('user'));
            } catch (e) {
                console.error('Error parsing user data:', e);
                this.clearAuth();
            }
        }
        
        // Setup API interceptor immediately, before init
        this.setupAPIInterceptor();
        
        this.init();
    }

    async init() {
        // Check if we're on login page
        if (window.location.pathname.includes('login.html')) {
            return;
        }

        // Check authentication
        if (!this.token) {
            this.redirectToLogin();
            return;
        }

        // Verify token is still valid
        try {
            await this.verifyToken();
            this.setupAuthenticatedUI();
        } catch (error) {
            console.error('Token verification failed:', error);
            this.redirectToLogin();
        }
    }

    async verifyToken() {
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });

        if (!response.ok) {
            throw new Error('Token verification failed');
        }

        const userData = await response.json();
        this.user = userData;
        localStorage.setItem('user', JSON.stringify(userData));
        return userData;
    }

    setupAuthenticatedUI() {
        // Add user info to header
        this.addUserInfoToHeader();
        
        // Interceptor is already setup in constructor
    }

    addUserInfoToHeader() {
        const header = document.querySelector('.header .container');
        if (header && this.user) {
            // Remove existing user info if any
            const existingUserInfo = header.querySelector('.user-info');
            if (existingUserInfo) {
                existingUserInfo.remove();
            }

            const userInfo = document.createElement('div');
            userInfo.className = 'user-info';
            userInfo.innerHTML = `
                <div class="user-profile">
                    <img src="${this.user.picture || '/default-avatar.png'}" alt="${this.user.name}" class="user-avatar">
                    <span class="user-name">${this.user.name}</span>
                    <button class="btn btn-secondary btn-sm logout-btn" onclick="authManager.logout()">
                        Cerrar Sesión
                    </button>
                </div>
            `;
            
            header.appendChild(userInfo);
        }
    }

    setupAPIInterceptor() {
        // Override fetch to automatically add auth headers
        const originalFetch = window.fetch;
        window.fetch = async (url, options = {}) => {
            // Only add auth headers for API calls
            if (url.startsWith('/api/') && !url.includes('/api/auth/')) {
                console.log(`API call to: ${url}`);
                console.log(`Token available: ${!!this.token}`);
                console.log(`Token: ${this.token?.substring(0, 20)}...`);
                
                options.headers = {
                    ...options.headers,
                    'Authorization': `Bearer ${this.token}`
                };
                
                console.log('Headers:', options.headers);
            }

            const response = await originalFetch(url, options);
            
            console.log(`Response status for ${url}: ${response.status}`);
            
            // If we get 401, redirect to login
            if (response.status === 401) {
                this.redirectToLogin();
            }
            
            return response;
        };
    }

    logout() {
        this.clearAuth();
        this.redirectToLogin();
    }

    clearAuth() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        this.token = null;
        this.user = null;
    }

    redirectToLogin() {
        if (!window.location.pathname.includes('login.html')) {
            window.location.href = '/login.html';
        }
    }

    isAuthenticated() {
        return !!this.token && !!this.user;
    }

    getUser() {
        return this.user;
    }

    isAdmin() {
        return this.user && this.user.is_admin;
    }
}

// Initialize auth manager
window.authManager = new AuthManager();