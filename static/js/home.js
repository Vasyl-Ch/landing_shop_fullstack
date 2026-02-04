/**
 * Home Page JavaScript - Load and display content
 */

class HomePage {
    constructor() {
        this.init();
    }
    
    async init() {
        await this.loadFeaturedProducts();
        await this.loadNewArrivals();
        await this.loadCategories();
        await this.loadHeaderCategories();
        this.updateProfileMenu();
    }
    
    /**
     * Load featured products
     */
    async loadFeaturedProducts() {
        const container = document.getElementById('featuredProducts');
        if (!container) return;
        
        try {
            const data = await API.get('/api/products/featured/');
            const products = data.products || [];
            
            container.innerHTML = '';
            products.forEach(product => {
                container.appendChild(this.createProductCard(product));
            });
        } catch (error) {
            console.error('Failed to load featured products:', error);
            container.innerHTML = '<p class="text-center">Не удалось загрузить товары</p>';
        }
    }
    
    /**
     * Load new arrivals
     */
    async loadNewArrivals() {
        const container = document.getElementById('newArrivals');
        if (!container) return;
        
        try {
            const data = await API.get('/api/products/new-arrivals/');
            const products = data.products || [];
            
            container.innerHTML = '';
            products.forEach(product => {
                container.appendChild(this.createProductCard(product));
            });
        } catch (error) {
            console.error('Failed to load new arrivals:', error);
            container.innerHTML = '<p class="text-center">Не удалось загрузить товары</p>';
        }
    }
    
    /**
     * Load categories
     */
    async loadCategories() {
        const container = document.getElementById('categoriesGrid');
        if (!container) return;
        
        try {
            const data = await API.get('/api/categories/');
            const categories = data.categories || [];
            
            container.innerHTML = '';
            categories.forEach(category => {
                container.appendChild(this.createCategoryCard(category));
            });
        } catch (error) {
            console.error('Failed to load categories:', error);
            container.innerHTML = '<p class="text-center">Не удалось загрузить категории</p>';
        }
    }
    
    /**
     * Load header categories for dropdown
     */
    async loadHeaderCategories() {
        const menu = document.getElementById('catalogMenu');
        if (!menu) return;
        
        try {
            const data = await API.get('/api/categories/');
            const categories = data.categories || [];
            
            menu.innerHTML = '';
            categories.forEach(category => {
                const link = document.createElement('a');
                link.href = `/products/category/${category.slug}/`;
                link.textContent = category.name;
                menu.appendChild(link);
            });
        } catch (error) {
            console.error('Failed to load header categories:', error);
        }
    }
    
    /**
     * Update profile menu based on auth status
     */
    updateProfileMenu() {
        const menu = document.getElementById('profileMenu');
        if (!menu) return;
        
        // Check if user is authenticated (you'll need to implement this based on your Django setup)
        const isAuthenticated = this.checkAuth();
        
        menu.innerHTML = '';
        
        if (isAuthenticated) {
            // Authenticated user menu
            const links = [
                { href: '/users/profile/', text: 'Профиль' },
                { href: '/orders/my-orders/', text: 'Мои заказы' },
                { href: '/users/account/settings/', text: 'Настройки' },
                { href: '/users/logout/', text: 'Выйти' }
            ];
            
            links.forEach(item => {
                const link = document.createElement('a');
                link.href = item.href;
                link.textContent = item.text;
                menu.appendChild(link);
            });
        } else {
            // Guest menu
            const links = [
                { href: '/users/login/', text: 'Вход' },
                { href: '/users/register/', text: 'Регистрация' }
            ];
            
            links.forEach(item => {
                const link = document.createElement('a');
                link.href = item.href;
                link.textContent = item.text;
                menu.appendChild(link);
            });
        }
    }
    
    /**
     * Check authentication status
     */
    checkAuth() {
        // This should check your Django session/auth
        // For demo purposes, we'll check localStorage
        return localStorage.getItem('isAuthenticated') === 'true';
    }
    
    /**
     * Create product card element
     */
    createProductCard(product) {
        const card = document.createElement('div');
        card.className = 'product-card';
        
        const hasDiscount = product.compare_price && product.compare_price > product.price;
        const discount = hasDiscount 
            ? Math.round((1 - product.price / product.compare_price) * 100)
            : 0;
        
        card.innerHTML = `
            <div class="product-card-image">
                <img src="${product.image}" alt="${product.name}">
                ${hasDiscount ? `<span class="product-badge">-${discount}%</span>` : ''}
            </div>
            <div class="product-card-content">
                <h3 class="product-card-title">${product.name}</h3>
                <p class="product-card-category">${product.category}</p>
                <div class="product-card-price">
                    <div class="product-price">${Utils.formatPrice(product.price)}</div>
                    ${hasDiscount ? `
                        <div>
                            <span class="product-price-old">${Utils.formatPrice(product.compare_price)}</span>
                            <span class="product-discount">-${discount}%</span>
                        </div>
                    ` : ''}
                </div>
                <div class="product-stock ${product.stock > 0 ? 'in-stock' : 'out-of-stock'}">
                    ${product.stock > 0 ? '✓ В наличии' : '✗ Нет в наличии'}
                </div>
                ${product.stock > 0 ? `
                    <button class="btn btn-primary btn-block add-to-cart-btn" data-product-id="${product.id}">
                        В корзину
                    </button>
                ` : `
                    <button class="btn btn-secondary btn-block" disabled>
                        Нет в наличии
                    </button>
                `}
            </div>
        `;
        
        return card;
    }
    
    /**
     * Create category card element
     */
    createCategoryCard(category) {
        const card = document.createElement('a');
        card.className = 'category-card';
        card.href = `/products/category/${category.slug}/`;
        
        card.innerHTML = `
            <div class="category-card-image">
                <img src="${category.image}" alt="${category.name}">
            </div>
            <div class="category-card-content">
                <h3 class="category-card-title">${category.name}</h3>
                <span class="category-card-link">
                    Смотреть
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M1 8a.5.5 0 0 1 .5-.5h11.793l-3.147-3.146a.5.5 0 0 1 .708-.708l4 4a.5.5 0 0 1 0 .708l-4 4a.5.5 0 0 1-.708-.708L13.293 8.5H1.5A.5.5 0 0 1 1 8z"/>
                    </svg>
                </span>
            </div>
        `;
        
        return card;
    }
    
}

// ========================================
// INITIALIZE
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    new HomePage();
});
