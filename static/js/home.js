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
            // In production, this would call your Django API
            // For now, we'll use mock data
            const products = this.getMockProducts(8);
            
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
            const products = this.getMockProducts(8);
            
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
            const categories = this.getMockCategories();
            
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
            const categories = this.getMockCategories();
            
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
    
    /**
     * Get mock products for demonstration
     * In production, replace with actual API call to Django backend
     */
    getMockProducts(count = 8) {
        const products = [
            {
                id: 1,
                name: 'iPhone 15 Pro',
                slug: 'iphone-15-pro',
                category: 'Телефоны',
                price: 119900,
                compare_price: 129900,
                image: 'https://images.unsplash.com/photo-1592286927505-dfd7d7a0e73c?w=400&h=400&fit=crop',
                stock: 15
            },
            {
                id: 2,
                name: 'AirPods Pro 2',
                slug: 'airpods-pro-2',
                category: 'Аксессуары',
                price: 27900,
                compare_price: null,
                image: 'https://images.unsplash.com/photo-1606841837239-c5a1a4a07af7?w=400&h=400&fit=crop',
                stock: 50
            },
            {
                id: 3,
                name: 'MacBook Pro 14"',
                slug: 'macbook-pro-14',
                category: 'Ноутбуки',
                price: 189900,
                compare_price: 209900,
                image: 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400&h=400&fit=crop',
                stock: 8
            },
            {
                id: 4,
                name: 'iPad Air',
                slug: 'ipad-air',
                category: 'Планшеты',
                price: 64900,
                compare_price: null,
                image: 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400&h=400&fit=crop',
                stock: 20
            },
            {
                id: 5,
                name: 'Apple Watch Series 9',
                slug: 'apple-watch-9',
                category: 'Часы',
                price: 42900,
                compare_price: 49900,
                image: 'https://images.unsplash.com/photo-1434494878577-86c23bcb06b9?w=400&h=400&fit=crop',
                stock: 12
            },
            {
                id: 6,
                name: 'Magic Keyboard',
                slug: 'magic-keyboard',
                category: 'Аксессуары',
                price: 12900,
                compare_price: null,
                image: 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400&h=400&fit=crop',
                stock: 30
            },
            {
                id: 7,
                name: 'Nike Air Max',
                slug: 'nike-air-max',
                category: 'Обувь',
                price: 14990,
                compare_price: 19990,
                image: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop',
                stock: 0
            },
            {
                id: 8,
                name: 'Sony WH-1000XM5',
                slug: 'sony-wh-1000xm5',
                category: 'Наушники',
                price: 34900,
                compare_price: null,
                image: 'https://images.unsplash.com/photo-1545127398-14699f92334b?w=400&h=400&fit=crop',
                stock: 18
            }
        ];
        
        return products.slice(0, count);
    }
    
    /**
     * Get mock categories for demonstration
     */
    getMockCategories() {
        return [
            {
                id: 1,
                name: 'Электроника',
                slug: 'electronics',
                image: 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=400&h=300&fit=crop'
            },
            {
                id: 2,
                name: 'Одежда',
                slug: 'clothing',
                image: 'https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=400&h=300&fit=crop'
            },
            {
                id: 3,
                name: 'Дом и сад',
                slug: 'home-garden',
                image: 'https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=400&h=300&fit=crop'
            },
            {
                id: 4,
                name: 'Спорт',
                slug: 'sports',
                image: 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=400&h=300&fit=crop'
            },
            {
                id: 5,
                name: 'Книги',
                slug: 'books',
                image: 'https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=400&h=300&fit=crop'
            },
            {
                id: 6,
                name: 'Игрушки',
                slug: 'toys',
                image: 'https://images.unsplash.com/photo-1558060370-d644479cb6f7?w=400&h=300&fit=crop'
            }
        ];
    }
}

// ========================================
// INITIALIZE
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    new HomePage();
});
