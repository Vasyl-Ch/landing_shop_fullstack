/**
 * Cart Page JavaScript - Display and manage cart items
 */

class CartPage {
    constructor() {
        this.cartItems = [];
        this.cartData = null;
        this.init();
    }
    
    async init() {
        // Don't reload cart items - use existing DOM from Django template
        // Just bind events to existing elements
        this.bindEventsToExistingElements();
        this.updateCartSummary();
    }
    
    /**
     * Bind events to existing DOM elements from Django template
     */
    bindEventsToExistingElements() {
        // CartManager will handle quantity inputs and other events
        // Just make sure the cart summary is updated correctly
        if (window.cartManager) {
            // Re-bind update quantity buttons for existing items
            window.cartManager.bindUpdateQuantityButtons();
            window.cartManager.bindRemoveButtons();
            window.cartManager.bindClearCartButton();
        }
    }
    
    /**
     * Update cart summary from current DOM data
     */
    updateCartSummary() {
        // Get current data from server to ensure accuracy
        this.loadCartData().then(data => {
            if (data) {
                this.updateSummaryDisplay(data);
            }
        });
    }
    
    /**
     * Load cart data from server
     */
    async loadCartData() {
        try {
            const data = await API.get('/cart/ajax/get/');
            this.cartData = data;
            return data;
        } catch (error) {
            console.error('Failed to load cart data:', error);
            return null;
        }
    }
    
    /**
     * Update summary display with server data
     */
    updateSummaryDisplay(data) {
        const subtotal = data.subtotal || 0;
        const shipping = data.shipping_cost || 0;
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
    
}

// ========================================
// INITIALIZE
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    new CartPage();
});
