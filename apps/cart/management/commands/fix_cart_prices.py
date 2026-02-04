from django.core.management.base import BaseCommand
from apps.cart.models import CartItem


class Command(BaseCommand):
    help = 'Fix cart item prices where price_at_addition is None'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what will be fixed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find cart items with None price_at_addition
        cart_items_to_fix = CartItem.objects.filter(price_at_addition__isnull=True)
        
        if not cart_items_to_fix.exists():
            self.stdout.write(self.style.SUCCESS('No cart items need price fixing'))
            return
        
        self.stdout.write(f'Found {cart_items_to_fix.count()} cart items to fix')
        
        fixed_count = 0
        for cart_item in cart_items_to_fix:
            if cart_item.product and cart_item.product.price:
                if dry_run:
                    self.stdout.write(
                        f'Would fix: {cart_item.product.name} - '
                        f'Set price to {cart_item.product.price}'
                    )
                else:
                    cart_item.price_at_addition = cart_item.product.price
                    cart_item.save()
                    fixed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Fixed: {cart_item.product.name} - '
                            f'Price set to {cart_item.product.price}'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Cannot fix: {cart_item.product.name if cart_item.product else "Unknown product"} - '
                        f'No product price available'
                    )
                )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully fixed {fixed_count} cart item prices')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Dry run completed. Use without --dry-run to apply changes.')
            )
