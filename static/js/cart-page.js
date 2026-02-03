/**
 * Cart Page JavaScript - Display and manage cart items
 */

class CartPage {
    constructor() {
        this.cartItems = [];
        this.init();
    }
    
    async init() {
        await this.loadCartItems();
        this.renderCartItems();
        this.updateCartSummary();
    }
    
    /**
     * Load cart items from server
     */
    async loadCartItems() {
        try {
            // In production, fetch from Django API
            // const data = await API.get('/cart/ajax/get/');
            // this.cartItems = data.items || [];
            
            // For demo, use mock data
            this.cartItems = this.getMockCartItems();
        } catch (error) {
            console.error('Failed to load cart:', error);
            Toast.error('Не удалось загрузить корзину');
        }
    }
    
    /**
     * Render cart items
     */
    renderCartItems() {
        const container = document.getElementById('cartItems');
        const summary = document.getElementById('cartSummary');
        const actions = document.getElementById('cartActions');
        const itemsCount = document.getElementById('cartItemsCount');
        
        if (!container) return;
        
        if (this.cartItems.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🛒</div>
                    <h3 class="empty-state-title">Ваша корзина пуста</h3>
                    <p class="empty-state-description">Добавьте товары, чтобы оформить заказ</p>
                    <a href="/products/" class="btn btn-primary">Перейти в каталог</a>
                </div>
            `;
            
            if (summary) summary.style.display = 'none';
            if (actions) actions.style.display = 'none';
            if (itemsCount) itemsCount.textContent = '0';
            
            return;
        }
        
        // Show summary and actions
        if (summary) summary.style.display = 'block';
        if (actions) actions.style.display = 'flex';
        if (itemsCount) itemsCount.textContent = this.cartItems.length;
        
        // Render items
        container.innerHTML = '';
        this.cartItems.forEach(item => {
            container.appendChild(this.createCartItemElement(item));
        });
        
        // Re-bind quantity inputs
        container.querySelectorAll('.quantity-input').forEach(element => {
            new QuantityInput(element);
        });
        
        // Re-bind remove buttons
        if (window.cartManager) {
            window.cartManager.bindRemoveButtons();
            window.cartManager.bindUpdateQuantityButtons();
        }
    }
    
    /**
     * Create cart item element
     */
    createCartItemElement(item) {
        const itemElement = document.createElement('div');
        itemElement.className = 'cart-item';
        itemElement.dataset.itemId = item.id;
        
        itemElement.innerHTML = `
            <div class="cart-item-image">
                <img src="${item.product.image}" alt="${item.product.name}">
            </div>
            
            <div class="cart-item-details">
                <a href="/products/${item.product.id}/" class="cart-item-name">
                    ${item.product.name}
                </a>
                <div class="cart-item-price">
                    Цена: ${Utils.formatPrice(item.price)}
                </div>
                <div class="cart-item-category">
                    ${item.product.category}
                </div>
            </div>
            
            <div class="cart-item-actions">
                <div class="quantity-input">
                    <button class="quantity-btn" data-action="decrease">−</button>
                    <input 
                        type="number" 
                        class="quantity-value cart-quantity-input" 
                        value="${item.quantity}" 
                        min="1" 
                        max="99"
                        data-item-id="${item.id}"
                    >
                    <button class="quantity-btn" data-action="increase">+</button>
                </div>
            </div>
            
            <div class="cart-item-total" data-item-id="${item.id}">
                ${Utils.formatPrice(item.price * item.quantity)}
            </div>
            
            <button 
                class="cart-item-remove" 
                data-item-id="${item.id}"
                data-product-name="${item.product.name}"
                aria-label="Удалить ${item.product.name}"
            >
                <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                    <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                </svg>
            </button>
        `;
        
        return itemElement;
    }
    
    /**
     * Update cart summary
     */
    updateCartSummary() {
        const subtotal = this.calculateSubtotal();
        const shipping = this.calculateShipping(subtotal);
        const total = subtotal + shipping;
        
        const subtotalElement = document.getElementById('cartSubtotal');
        const shippingElement = document.getElementById('cartShipping');
        const totalElement = document.getElementById('cartTotalPrice');
        
        if (subtotalElement) subtotalElement.textContent = Utils.formatPrice(subtotal);
        if (shippingElement) {
            shippingElement.textContent = shipping === 0 ? 'Бесплатно' : Utils.formatPrice(shipping);
        }
        if (totalElement) totalElement.textContent = Utils.formatPrice(total);
    }
    
    /**
     * Calculate subtotal
     */
    calculateSubtotal() {
        return this.cartItems.reduce((sum, item) => {
            return sum + (item.price * item.quantity);
        }, 0);
    }
    
    /**
     * Calculate shipping cost
     * Free if subtotal >= 3000, otherwise 500
     */
    calculateShipping(subtotal) {
        return subtotal >= 3000 ? 0 : 500;
    }
    
    /**
     * Get mock cart items for demonstration
     */
    getMockCartItems() {
        // Simulate some items in cart
        return [
            {
                id: 1,
                product: {
                    id: 1,
                    name: 'iPhone 15 Pro',
                    slug: 'iphone-15-pro',
                    category: 'Телефоны',
                    image: 'https://images.unsplash.com/photo-1592286927505-dfd7d7a0e73c?w=400&h=400&fit=crop',
                },
                price: 119900,
                quantity: 1
            },
            {
                id: 2,
                product: {
                    id: 2,
                    name: 'AirPods Pro 2',
                    slug: 'airpods-pro-2',
                    category: 'Аксессуары',
                    image: 'https://images.unsplash.com/photo-1606841837239-c5a1a4a07af7?w=400&h=400&fit=crop',
                },
                price: 27900,
                quantity: 2
            }
        ];
    }
}

// ========================================
// INITIALIZE
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    new CartPage();
});
