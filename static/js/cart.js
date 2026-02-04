/**
 * Cart JavaScript - Shopping Cart functionality
 */

class CartManager {
    constructor() {
        this.cartCountElement = document.getElementById('cartCount');
        this.cartTotalElement = document.getElementById('cartTotal');
        this.updateTimeout = null; // For debouncing
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
        // Check dependencies
        if (!window.API) {
            console.error('API utility not loaded');
            return;
        }

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
        // Check Utils dependency
        if (!window.Utils) {
            console.error('Utils utility not loaded');
            return;
        }

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
        // Check dependencies
        if (!window.API) {
            console.error('API utility not loaded');
            if (window.Toast) {
                Toast.error('Ошибка загрузки модулей');
            }
            return;
        }

        if (!window.Toast) {
            console.error('Toast utility not loaded');
            return;
        }

        try {
            const data = await API.post('/cart/ajax/add/', {
                product_id: productId,
                quantity: quantity,
            });

            if (data.success) {
                // Toast.success(data.message || 'Товар добавлен в корзину'); // Убрано
                this.updateCartDisplay(data);

                // Animate cart icon
                this.animateCartIcon();
            } else {
                Toast.error(data.message || 'Ошибка при добавлении товара');
            }
        } catch (error) {
            console.error('Add to cart error:', error);
            Toast.error('Не удалось добавить товар в корзину');
        }
    }

    /**
     * Bind quantity update buttons
     */
    bindUpdateQuantityButtons() {
        // Remove existing event listeners to prevent duplicates
        // Only bind to cart-related quantity inputs (not product page inputs)
        document.querySelectorAll('.quantity-input').forEach(container => {
            const cartInput = container.querySelector('.cart-quantity-input');

            if (cartInput) {
                // This is a cart quantity input, handle cart logic
                const newContainer = container.cloneNode(true);
                container.parentNode.replaceChild(newContainer, container);

                const input = newContainer.querySelector('.quantity-value');
                const decreaseBtn = newContainer.querySelector('.quantity-btn[data-action="decrease"]');
                const increaseBtn = newContainer.querySelector('.quantity-btn[data-action="increase"]');

                if (input && input.classList.contains('cart-quantity-input')) {
                    const itemId = input.dataset.itemId;

                    // Input change event
                    input.addEventListener('change', async (e) => {
                        e.preventDefault();
                        const quantity = parseInt(input.value) || 1;
                        if (quantity > 0) {
                            await this.updateQuantity(itemId, quantity);
                        }
                    });

                    // Decrease button
                    if (decreaseBtn) {
                        decreaseBtn.addEventListener('click', async (e) => {
                            e.preventDefault();
                            e.stopPropagation();

                            let currentQuantity = parseInt(input.value) || 1;
                            if (currentQuantity > 1) {
                                input.value = currentQuantity - 1;
                                input.dispatchEvent(new Event('change', {bubbles: true}));
                            }
                        });
                    }

                    // Increase button
                    if (increaseBtn) {
                        increaseBtn.addEventListener('click', async (e) => {
                            e.preventDefault();
                            e.stopPropagation();

                            let currentQuantity = parseInt(input.value) || 1;
                            input.value = currentQuantity + 1;
                            input.dispatchEvent(new Event('change', {bubbles: true}));
                        });
                    }
                }
            }
            // If no cart-quantity-input class, let main.js QuantityInput handle it
        });
    }

    /**
     * Update item quantity with debouncing
     */
    async updateQuantity(itemId, quantity) {
        // Check dependencies
        if (!window.API) {
            console.error('API utility not loaded');
            Toast.error('Ошибка загрузки модулей');
            return;
        }

        if (!window.Toast) {
            console.error('Toast utility not loaded');
            return;
        }

        // Clear existing timeout
        if (this.updateTimeout) {
            clearTimeout(this.updateTimeout);
        }

        // Debounce the update request
        this.updateTimeout = setTimeout(async () => {
            try {
                const data = await API.post('/cart/ajax/update/', {
                    item_id: itemId,
                    quantity: quantity,
                });

                if (data.success) {
                    this.updateCartDisplay(data);
                    this.updateCartPage(data);
                    // Toast.success('Количество обновлено'); // Убрано
                } else {
                    Toast.error(data.message || 'Ошибка при обновлении количества');
                    // Восстанавливаем предыдущее значение в input
                    const input = document.querySelector(`input[data-item-id="${itemId}"]`);
                    if (input && data.old_quantity) {
                        input.value = data.old_quantity;
                    } else {
                        // Перезагружаем страницу если не можем восстановить
                        this.loadCart();
                    }
                }
            } catch (error) {
                console.error('Update quantity error:', error);
                Toast.error('Не удалось обновить количество. Попробуйте еще раз.');
                // Перезагружаем корзину при ошибке
                this.loadCart();
            }
        }, 300); // 300ms delay
    }

    /**
     * Bind remove item buttons
     */
    bindRemoveButtons() {
        // Remove existing event listeners to prevent duplicates
        document.querySelectorAll('.cart-item-remove').forEach(button => {
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);

            newButton.addEventListener('click', async (e) => {
                e.preventDefault();

                const itemId = newButton.dataset.itemId;
                const productName = newButton.dataset.productName;

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
                // Toast.success('Товар удален из корзины'); // Убрано
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
                // Toast.success('Корзина очищена'); // Убрано
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
        const subtotal = data.subtotal !== undefined ? data.subtotal : data.cart_total || 0;
        const shippingText = data.shipping_text || 'В соответствии с тарифами перевозчика';
        const total = subtotal;

        // Update subtotal
        const subtotalElement = document.getElementById('cartSubtotal');
        if (subtotalElement) {
            subtotalElement.textContent = Utils.formatPrice(subtotal);
        }

        // Update shipping
        const shippingElement = document.getElementById('cartShipping');
        if (shippingElement) {
            shippingElement.textContent = shippingText;
        }

        // Update total
        const totalElement = document.getElementById('cartTotalPrice');
        if (totalElement) {
            totalElement.textContent = Utils.formatPrice(total);
        }

        // Update individual item totals
        if (data.items) {
            data.items.forEach(item => {
                // Find the item total element by data-item-id
                const itemTotalElements = document.querySelectorAll(`[data-item-id="${item.id}"]`);
                itemTotalElements.forEach(element => {
                    if (element.classList.contains('cart-item-total')) {
                        const itemTotal = item.total_price !== undefined ? item.total_price : 0;
                        element.textContent = Utils.formatPrice(itemTotal);
                    }
                });
            });
        }

        // Update free shipping message
        this.updateFreeShippingMessage(subtotal);
    }

    /**
     * Update free shipping message
     */
    updateFreeShippingMessage(cartTotal) {
        const freeShippingThreshold = 1000;

        // Find or create free shipping message element
        let shippingMessage = document.querySelector('.free-shipping-message');
        if (!shippingMessage) {
            const summaryDiv = document.querySelector('.cart-summary');
            if (summaryDiv) {
                shippingMessage = document.createElement('p');
                shippingMessage.className = 'free-shipping-message';
                shippingMessage.style.cssText = 'font-size: 0.875rem; color: var(--color-text-secondary); margin-top: var(--spacing-md);';
                summaryDiv.appendChild(shippingMessage);
            }
        }

        if (shippingMessage) {
            if (cartTotal >= freeShippingThreshold) {
                shippingMessage.textContent = '✓ Бесплатная доставка!';
                shippingMessage.style.color = 'var(--color-success)';
            } else {
                const remaining = freeShippingThreshold - cartTotal;
                shippingMessage.textContent = `До бесплатной доставки: €${remaining.toFixed(0)}`;
                shippingMessage.style.color = 'var(--color-text-secondary)';
            }
        }
    }

    /**
     * Show empty cart state
     */
    showEmptyCart() {
        const cartItemsContainer = document.querySelector('.cart-items');
        const cartSummary = document.querySelector('.cart-summary');
        const cartActions = document.querySelector('.cart-actions');

        // Remove free shipping message
        const shippingMessage = document.querySelector('.free-shipping-message');
        if (shippingMessage) {
            shippingMessage.remove();
        }

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
