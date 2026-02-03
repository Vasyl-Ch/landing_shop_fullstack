/**
 * Cart JavaScript - Shopping Cart functionality
 */

class CartManager {
    constructor() {
        this.cartCountElement = document.getElementById('cartCount');
        this.cartTotalElement = document.getElementById('cartTotal');
        this.init();
    }
    
    init() {
        // Load cart on page load
        this.loadCart();
        
        // Bind add to cart buttons
        this.bindAddToCartButtons();
        
        // Bind update quantity buttons
        this.bindUpdateQuantityButtons();
        
        // Bind remove buttons
        this.bindRemoveButtons();
        
        // Bind clear cart button
        this.bindClearCartButton();
    }
    
    /**
     * Load cart data from server
     */
    async loadCart() {
        try {
            const data = await API.get('/cart/ajax/get/');
            this.updateCartDisplay(data);
        } catch (error) {
            console.error('Failed to load cart:', error);
        }
    }
    
    /**
     * Update cart display in header
     */
    updateCartDisplay(data) {
        if (this.cartCountElement) {
            this.cartCountElement.textContent = data.cart_items_count || 0;
            
            // Hide badge if cart is empty
            if (data.cart_items_count === 0) {
                this.cartCountElement.style.display = 'none';
            } else {
                this.cartCountElement.style.display = 'flex';
            }
        }
        
        if (this.cartTotalElement) {
            this.cartTotalElement.textContent = Utils.formatPrice(data.cart_total || 0);
        }
    }
    
    /**
     * Bind "Add to Cart" buttons
     */
    bindAddToCartButtons() {
        document.querySelectorAll('.add-to-cart-btn').forEach(button => {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                
                const productId = button.dataset.productId;
                const quantityInput = button.closest('form')?.querySelector('input[name="quantity"]');
                const quantity = quantityInput ? parseInt(quantityInput.value) : 1;
                
                await this.addToCart(productId, quantity);
            });
        });
        
        // Also handle form submissions
        document.querySelectorAll('.add-to-cart-form').forEach(form => {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(form);
                const productId = formData.get('product_id');
                const quantity = parseInt(formData.get('quantity')) || 1;
                
                await this.addToCart(productId, quantity);
            });
        });
    }
    
    /**
     * Add item to cart
     */
    async addToCart(productId, quantity = 1) {
        try {
            const data = await API.post('/cart/ajax/add/', {
                product_id: productId,
                quantity: quantity,
            });
            
            if (data.success) {
                Toast.success(data.message || 'Товар добавлен в корзину');
                this.updateCartDisplay(data);
                
                // Animate cart icon
                this.animateCartIcon();
            } else {
                Toast.error(data.message || 'Ошибка при добавлении товара');
            }
        } catch (error) {
            Toast.error('Не удалось добавить товар в корзину');
            console.error('Add to cart error:', error);
        }
    }
    
    /**
     * Bind quantity update buttons
     */
    bindUpdateQuantityButtons() {
        document.querySelectorAll('.cart-quantity-input').forEach(input => {
            const container = input.closest('.quantity-input');
            if (!container) return;
            
            const itemId = input.dataset.itemId;
            
            // Listen to quantity changes
            input.addEventListener('change', async () => {
                const quantity = parseInt(input.value);
                await this.updateQuantity(itemId, quantity);
            });
        });
    }
    
    /**
     * Update item quantity
     */
    async updateQuantity(itemId, quantity) {
        try {
            const data = await API.post('/cart/ajax/update/', {
                item_id: itemId,
                quantity: quantity,
            });
            
            if (data.success) {
                this.updateCartDisplay(data);
                this.updateCartPage(data);
            } else {
                Toast.error(data.message || 'Ошибка при обновлении количества');
            }
        } catch (error) {
            Toast.error('Не удалось обновить количество');
            console.error('Update quantity error:', error);
        }
    }
    
    /**
     * Bind remove item buttons
     */
    bindRemoveButtons() {
        document.querySelectorAll('.cart-item-remove').forEach(button => {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                
                const itemId = button.dataset.itemId;
                const productName = button.dataset.productName;
                
                Modal.confirm(
                    'Удалить товар?',
                    `Вы уверены, что хотите удалить "${productName}" из корзины?`,
                    async () => {
                        await this.removeItem(itemId);
                    }
                );
            });
        });
    }
    
    /**
     * Remove item from cart
     */
    async removeItem(itemId) {
        try {
            const data = await API.post('/cart/ajax/remove/', {
                item_id: itemId,
            });
            
            if (data.success) {
                Toast.success('Товар удален из корзины');
                this.updateCartDisplay(data);
                this.updateCartPage(data);
                
                // Remove item from DOM
                const itemElement = document.querySelector(`[data-item-id="${itemId}"]`)?.closest('.cart-item');
                if (itemElement) {
                    itemElement.style.animation = 'fadeOut 0.3s ease-out';
                    setTimeout(() => itemElement.remove(), 300);
                }
                
                // Show empty state if no items
                if (data.cart_items_count === 0) {
                    this.showEmptyCart();
                }
            } else {
                Toast.error(data.message || 'Ошибка при удалении товара');
            }
        } catch (error) {
            Toast.error('Не удалось удалить товар');
            console.error('Remove item error:', error);
        }
    }
    
    /**
     * Bind clear cart button
     */
    bindClearCartButton() {
        const clearBtn = document.getElementById('clearCartBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                
                Modal.confirm(
                    'Очистить корзину?',
                    'Вы уверены, что хотите удалить все товары из корзины?',
                    async () => {
                        await this.clearCart();
                    }
                );
            });
        }
    }
    
    /**
     * Clear all items from cart
     */
    async clearCart() {
        try {
            const data = await API.post('/cart/ajax/clear/', {});
            
            if (data.success) {
                Toast.success('Корзина очищена');
                this.updateCartDisplay(data);
                this.showEmptyCart();
            } else {
                Toast.error(data.message || 'Ошибка при очистке корзины');
            }
        } catch (error) {
            Toast.error('Не удалось очистить корзину');
            console.error('Clear cart error:', error);
        }
    }
    
    /**
     * Update cart page with new data
     */
    updateCartPage(data) {
        // Update subtotal
        const subtotalElement = document.getElementById('cartSubtotal');
        if (subtotalElement) {
            subtotalElement.textContent = Utils.formatPrice(data.subtotal || 0);
        }
        
        // Update shipping
        const shippingElement = document.getElementById('cartShipping');
        if (shippingElement) {
            shippingElement.textContent = Utils.formatPrice(data.shipping_cost || 0);
        }
        
        // Update total
        const totalElement = document.getElementById('cartTotalPrice');
        if (totalElement) {
            totalElement.textContent = Utils.formatPrice(data.cart_total || 0);
        }
        
        // Update individual item totals
        if (data.items) {
            data.items.forEach(item => {
                const itemTotalElement = document.querySelector(`[data-item-id="${item.id}"] .cart-item-total`);
                if (itemTotalElement) {
                    itemTotalElement.textContent = Utils.formatPrice(item.total_price);
                }
            });
        }
    }
    
    /**
     * Show empty cart state
     */
    showEmptyCart() {
        const cartItemsContainer = document.querySelector('.cart-items');
        const cartSummary = document.querySelector('.cart-summary');
        const cartActions = document.querySelector('.cart-actions');
        
        if (cartItemsContainer) {
            cartItemsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🛒</div>
                    <h3 class="empty-state-title">Ваша корзина пуста</h3>
                    <p class="empty-state-description">Добавьте товары, чтобы оформить заказ</p>
                    <a href="/products/" class="btn btn-primary">Перейти в каталог</a>
                </div>
            `;
        }
        
        if (cartSummary) {
            cartSummary.style.display = 'none';
        }
        
        if (cartActions) {
            cartActions.style.display = 'none';
        }
    }
    
    /**
     * Animate cart icon when item is added
     */
    animateCartIcon() {
        const cartBtn = document.querySelector('.cart-btn');
        if (cartBtn) {
            cartBtn.style.animation = 'none';
            setTimeout(() => {
                cartBtn.style.animation = 'bounce 0.5s ease-out';
            }, 10);
        }
    }
}

// ========================================
// GUEST CART TOKEN
// ========================================
class GuestCartManager {
    static getToken() {
        return this.getCookie('guest_cart_token');
    }
    
    static setToken(token) {
        const expires = new Date();
        expires.setDate(expires.getDate() + 30); // 30 days
        document.cookie = `guest_cart_token=${token}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`;
    }
    
    static getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
}

// ========================================
// ANIMATIONS
// ========================================
const style = document.createElement('style');
style.textContent = `
    @keyframes bounce {
        0%, 100% { transform: scale(1); }
        25% { transform: scale(1.1); }
        50% { transform: scale(0.9); }
        75% { transform: scale(1.05); }
    }
    
    @keyframes fadeOut {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(-20px); }
    }
`;
document.head.appendChild(style);

// ========================================
// INITIALIZE
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    window.cartManager = new CartManager();
});

// Make CartManager available globally
window.CartManager = CartManager;
window.GuestCartManager = GuestCartManager;
