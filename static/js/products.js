/**
 * Products Page JavaScript - Catalog with filters and sorting
 */

class ProductsPage {
    constructor() {
        this.currentPage = 1;
        this.itemsPerPage = 12;
        this.allProducts = [];
        this.filteredProducts = [];
        this.filters = {
            categories: [],
            priceMin: null,
            priceMax: null,
            availability: ['in_stock'],
            sort: '-created_at'
        };
        
        this.init();
    }
    
    async init() {
        await this.loadProducts();
        this.loadCategories();
        this.bindEventListeners();
        this.renderProducts();
        this.renderPagination();
    }
    
    /**
     * Load all products
     */
    async loadProducts() {
        try {
            // In production, fetch from Django API
            this.allProducts = this.getMockProducts();
            this.filteredProducts = [...this.allProducts];
        } catch (error) {
            console.error('Failed to load products:', error);
            Toast.error('Не удалось загрузить товары');
        }
    }
    
    /**
     * Load categories for filters
     */
    loadCategories() {
        const container = document.getElementById('categoryFilters');
        if (!container) return;
        
        const categories = [...new Set(this.allProducts.map(p => p.category))];
        
        categories.forEach(category => {
            const option = document.createElement('div');
            option.className = 'filter-option';
            option.innerHTML = `
                <label>
                    <input type="checkbox" name="category" value="${category}">
                    ${category}
                </label>
            `;
            container.appendChild(option);
        });
    }
    
    /**
     * Bind event listeners
     */
    bindEventListeners() {
        // Category filters
        document.querySelectorAll('input[name="category"]').forEach(input => {
            input.addEventListener('change', () => this.handleCategoryFilter());
        });
        
        // Price filter
        const applyPriceBtn = document.getElementById('applyPriceFilter');
        if (applyPriceBtn) {
            applyPriceBtn.addEventListener('click', () => this.handlePriceFilter());
        }
        
        // Availability filter
        document.querySelectorAll('input[name="availability"]').forEach(input => {
            input.addEventListener('change', () => this.handleAvailabilityFilter());
        });
        
        // Sort
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.filters.sort = e.target.value;
                this.applyFilters();
            });
        }
        
        // Reset filters
        const resetBtn = document.getElementById('resetFilters');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetFilters());
        }
    }
    
    /**
     * Handle category filter change
     */
    handleCategoryFilter() {
        const selectedCategories = Array.from(
            document.querySelectorAll('input[name="category"]:checked')
        ).map(input => input.value);
        
        // If "all" is checked, uncheck others
        if (selectedCategories.includes('all')) {
            document.querySelectorAll('input[name="category"]').forEach(input => {
                if (input.value !== 'all') input.checked = false;
            });
            this.filters.categories = [];
        } else {
            // Uncheck "all"
            const allCheckbox = document.querySelector('input[name="category"][value="all"]');
            if (allCheckbox) allCheckbox.checked = false;
            
            this.filters.categories = selectedCategories;
        }
        
        this.applyFilters();
    }
    
    /**
     * Handle price filter
     */
    handlePriceFilter() {
        const minInput = document.getElementById('priceMin');
        const maxInput = document.getElementById('priceMax');
        
        this.filters.priceMin = minInput.value ? parseFloat(minInput.value) : null;
        this.filters.priceMax = maxInput.value ? parseFloat(maxInput.value) : null;
        
        this.applyFilters();
    }
    
    /**
     * Handle availability filter
     */
    handleAvailabilityFilter() {
        const selectedAvailability = Array.from(
            document.querySelectorAll('input[name="availability"]:checked')
        ).map(input => input.value);
        
        this.filters.availability = selectedAvailability;
        this.applyFilters();
    }
    
    /**
     * Apply all filters
     */
    applyFilters() {
        this.filteredProducts = this.allProducts.filter(product => {
            // Category filter
            if (this.filters.categories.length > 0) {
                if (!this.filters.categories.includes(product.category)) {
                    return false;
                }
            }
            
            // Price filter
            if (this.filters.priceMin !== null && product.price < this.filters.priceMin) {
                return false;
            }
            if (this.filters.priceMax !== null && product.price > this.filters.priceMax) {
                return false;
            }
            
            // Availability filter
            if (this.filters.availability.length > 0) {
                const isInStock = product.stock > 0;
                const shouldShowInStock = this.filters.availability.includes('in_stock');
                const shouldShowOutOfStock = this.filters.availability.includes('out_of_stock');
                
                if (isInStock && !shouldShowInStock) return false;
                if (!isInStock && !shouldShowOutOfStock) return false;
            }
            
            return true;
        });
        
        // Apply sorting
        this.sortProducts();
        
        // Reset to page 1
        this.currentPage = 1;
        
        // Re-render
        this.renderProducts();
        this.renderPagination();
        this.updateResultsCount();
    }
    
    /**
     * Sort products
     */
    sortProducts() {
        const sort = this.filters.sort;
        
        this.filteredProducts.sort((a, b) => {
            if (sort === 'price') {
                return a.price - b.price;
            } else if (sort === '-price') {
                return b.price - a.price;
            } else if (sort === 'name') {
                return a.name.localeCompare(b.name);
            } else if (sort === '-name') {
                return b.name.localeCompare(a.name);
            } else if (sort === '-created_at') {
                return b.id - a.id; // Assuming higher ID = newer
            }
            return 0;
        });
    }
    
    /**
     * Reset all filters
     */
    resetFilters() {
        // Reset checkboxes
        document.querySelectorAll('input[name="category"]').forEach(input => {
            input.checked = input.value === 'all';
        });
        
        document.querySelectorAll('input[name="availability"]').forEach(input => {
            input.checked = input.value === 'in_stock';
        });
        
        // Reset price
        document.getElementById('priceMin').value = '';
        document.getElementById('priceMax').value = '';
        
        // Reset sort
        document.getElementById('sortSelect').value = '-created_at';
        
        // Reset filters object
        this.filters = {
            categories: [],
            priceMin: null,
            priceMax: null,
            availability: ['in_stock'],
            sort: '-created_at'
        };
        
        this.applyFilters();
    }
    
    /**
     * Render products
     */
    renderProducts() {
        const container = document.getElementById('productsGrid');
        if (!container) return;
        
        const start = (this.currentPage - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        const productsToShow = this.filteredProducts.slice(start, end);
        
        if (productsToShow.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <div class="empty-state-icon">🔍</div>
                    <h3 class="empty-state-title">Товары не найдены</h3>
                    <p class="empty-state-description">Попробуйте изменить фильтры</p>
                    <button class="btn btn-primary" id="emptyResetFilters">Сбросить фильтры</button>
                </div>
            `;
            
            document.getElementById('emptyResetFilters')?.addEventListener('click', () => {
                this.resetFilters();
            });
            
            return;
        }
        
        container.innerHTML = '';
        productsToShow.forEach(product => {
            container.appendChild(this.createProductCard(product));
        });
        
        // Re-bind cart buttons
        if (window.cartManager) {
            window.cartManager.bindAddToCartButtons();
        }
    }
    
    /**
     * Create product card
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
                <a href="/products/${product.id}/">
                    <img src="${product.image}" alt="${product.name}">
                </a>
                ${hasDiscount ? `<span class="product-badge">-${discount}%</span>` : ''}
            </div>
            <div class="product-card-content">
                <a href="/products/${product.id}/">
                    <h3 class="product-card-title">${product.name}</h3>
                </a>
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
     * Render pagination
     */
    renderPagination() {
        const container = document.getElementById('pagination');
        if (!container) return;
        
        const totalPages = Math.ceil(this.filteredProducts.length / this.itemsPerPage);
        
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        let html = '';
        
        // Previous button
        if (this.currentPage > 1) {
            html += `<a href="#" data-page="${this.currentPage - 1}">← Назад</a>`;
        } else {
            html += `<span class="disabled">← Назад</span>`;
        }
        
        // Page numbers
        const maxButtons = 7;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxButtons / 2));
        let endPage = Math.min(totalPages, startPage + maxButtons - 1);
        
        if (endPage - startPage + 1 < maxButtons) {
            startPage = Math.max(1, endPage - maxButtons + 1);
        }
        
        // First page
        if (startPage > 1) {
            html += `<a href="#" data-page="1">1</a>`;
            if (startPage > 2) {
                html += `<span>...</span>`;
            }
        }
        
        // Page buttons
        for (let i = startPage; i <= endPage; i++) {
            if (i === this.currentPage) {
                html += `<span class="active">${i}</span>`;
            } else {
                html += `<a href="#" data-page="${i}">${i}</a>`;
            }
        }
        
        // Last page
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                html += `<span>...</span>`;
            }
            html += `<a href="#" data-page="${totalPages}">${totalPages}</a>`;
        }
        
        // Next button
        if (this.currentPage < totalPages) {
            html += `<a href="#" data-page="${this.currentPage + 1}">Вперед →</a>`;
        } else {
            html += `<span class="disabled">Вперед →</span>`;
        }
        
        container.innerHTML = html;
        
        // Bind click events
        container.querySelectorAll('a[data-page]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = parseInt(link.dataset.page);
                this.renderProducts();
                this.renderPagination();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    }
    
    /**
     * Update results count
     */
    updateResultsCount() {
        const countElement = document.getElementById('resultsCount');
        if (countElement) {
            countElement.textContent = this.filteredProducts.length;
        }
    }
    
    /**
     * Get mock products (same as home page, but more)
     */
    getMockProducts() {
        const baseProducts = [
            { id: 1, name: 'iPhone 15 Pro', category: 'Телефоны', price: 119900, compare_price: 129900, image: 'https://images.unsplash.com/photo-1592286927505-dfd7d7a0e73c?w=400', stock: 15 },
            { id: 2, name: 'AirPods Pro 2', category: 'Аксессуары', price: 27900, compare_price: null, image: 'https://images.unsplash.com/photo-1606841837239-c5a1a4a07af7?w=400', stock: 50 },
            { id: 3, name: 'MacBook Pro 14"', category: 'Ноутбуки', price: 189900, compare_price: 209900, image: 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400', stock: 8 },
            { id: 4, name: 'iPad Air', category: 'Планшеты', price: 64900, compare_price: null, image: 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400', stock: 20 },
            { id: 5, name: 'Apple Watch Series 9', category: 'Часы', price: 42900, compare_price: 49900, image: 'https://images.unsplash.com/photo-1434494878577-86c23bcb06b9?w=400', stock: 12 },
            { id: 6, name: 'Magic Keyboard', category: 'Аксессуары', price: 12900, compare_price: null, image: 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400', stock: 30 },
            { id: 7, name: 'Nike Air Max', category: 'Обувь', price: 14990, compare_price: 19990, image: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400', stock: 0 },
            { id: 8, name: 'Sony WH-1000XM5', category: 'Наушники', price: 34900, compare_price: null, image: 'https://images.unsplash.com/photo-1545127398-14699f92334b?w=400', stock: 18 },
            { id: 9, name: 'Samsung Galaxy S24', category: 'Телефоны', price: 89900, compare_price: null, image: 'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=400', stock: 25 },
            { id: 10, name: 'Dell XPS 15', category: 'Ноутбуки', price: 159900, compare_price: 179900, image: 'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=400', stock: 10 },
            { id: 11, name: 'Adidas Ultraboost', category: 'Обувь', price: 17990, compare_price: null, image: 'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=400', stock: 15 },
            { id: 12, name: 'Kindle Paperwhite', category: 'Электроника', price: 14900, compare_price: null, image: 'https://images.unsplash.com/photo-1592496431122-2349e0fbc666?w=400', stock: 40 },
            { id: 13, name: 'Canon EOS R6', category: 'Камеры', price: 259900, compare_price: 289900, image: 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=400', stock: 5 },
            { id: 14, name: 'JBL Flip 6', category: 'Аксессуары', price: 12990, compare_price: null, image: 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400', stock: 35 },
            { id: 15, name: 'Asus ROG Gaming Mouse', category: 'Аксессуары', price: 8990, compare_price: 10990, image: 'https://images.unsplash.com/photo-1527814050087-3793815479db?w=400', stock: 50 },
        ];
        
        return baseProducts;
    }
}

// ========================================
// INITIALIZE
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    new ProductsPage();
});
