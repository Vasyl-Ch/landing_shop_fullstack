"""
Migration to fix CartItem records with None price_at_addition
"""
from django.db import migrations


def fix_cart_item_prices(apps, schema_editor):
    """
    Fix CartItem records where price_at_addition is None
    Set it to the current product price
    """
    CartItem = apps.get_model('cart', 'CartItem')
    
    # Update all CartItem records with None price_at_addition
    cart_items_with_none_price = CartItem.objects.filter(price_at_addition__isnull=True)
    
    for cart_item in cart_items_with_none_price:
        if cart_item.product and cart_item.product.price:
            cart_item.price_at_addition = cart_item.product.price
            cart_item.save()


def reverse_fix_cart_item_prices(apps, schema_editor):
    """
    Reverse migration - set price_at_addition back to None
    """
    CartItem = apps.get_model('cart', 'CartItem')
    CartItem.objects.filter(price_at_addition__isnull=False).update(price_at_addition=None)


class Migration(migrations.Migration):
    dependencies = [
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fix_cart_item_prices, reverse_fix_cart_item_prices),
    ]
