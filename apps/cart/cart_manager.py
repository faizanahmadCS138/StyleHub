# from colorama import winterm
from .models import Cart, CartItem
from apps.catalog.models import ProductVariant
from django.urls import reverse


class StyleHubCartManager:
    """
    Unified Cart Manager handling Session Cart (Guests) & DB Cart (Logged-in Users)
    """
    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.user = request.user

        if not self.session.session_key:
            self.session.create()

        if self.user.is_authenticated:
            # Load or create DB Cart for authenticated user
            self.cart, _ = Cart.objects.get_or_create(user=self.user)
            # Ensure session key is linked
            if not self.cart.session_key:
                self.cart.session_key = self.session.session_key
                self.cart.save()
        else:
            # Load or create DB Cart for guest using session key
            self.cart, _ = Cart.objects.get_or_create(
                session_key=self.session.session_key,
                user=None,
            )

    def merge_session_cart(self, user=None, guest_session_key=None):
        """
        Merge the guest DB cart into the authenticated user's DB cart.
        """

        target_user = user or self.user

        if not target_user or not target_user.is_authenticated:
            return

        # Use the OLD guest session key captured before login().
        session_key = guest_session_key or self.session.session_key

        if not session_key:
            return

        # Find guest cart using the OLD session key
        guest_cart = Cart.objects.filter(
            session_key=session_key,
            user=None
        ).first()

        if not guest_cart:
            return

        # Get/create logged-in user's cart
        user_cart, _ = Cart.objects.get_or_create(
            user=target_user
        )

        # Get guest cart items
        guest_items = (
            CartItem.objects
            .filter(cart=guest_cart)
            .select_related('variant')
        )

        for guest_item in guest_items:

            user_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                variant=guest_item.variant
            )

        if created:
            user_item.quantity = guest_item.quantity
        else:
            user_item.quantity += guest_item.quantity

        # Don't exceed stock
        if user_item.quantity > guest_item.variant.stock_quantity:
            user_item.quantity = guest_item.variant.stock_quantity

        user_item.save()

        # Delete old guest cart
        guest_cart.delete()

        # Update manager's cart
        self.cart = user_cart

    def add(self, variant_id, quantity=1, override_quantity=False):

        variant = ProductVariant.objects.get(
            id=variant_id
        )

        if quantity > variant.stock_quantity:
            raise ValueError(
                f"Only {variant.stock_quantity} left in stock."
            )

        item, created = CartItem.objects.get_or_create(
            cart=self.cart,
            variant=variant
        )

        if created:
            item.quantity = quantity

        else:
            if override_quantity:
                item.quantity = quantity
            else:
                item.quantity += quantity

        if item.quantity > variant.stock_quantity:
                item.quantity = variant.stock_quantity

        item.save()

        return item
    
    def remove(self, variant_id):

        CartItem.objects.filter(
            cart=self.cart,
            variant_id=variant_id
        ).delete()

    def get_items(self):
        """Returns a standardized list of cart items."""

        items = []

        cart_items = (
            CartItem.objects
            .filter(cart=self.cart)
            .select_related(
            'variant__product',
            'variant__size'
            )
        )

        for item in cart_items:

            variant = item.variant
            product = variant.product
            variant_img = variant.variant_image

            items.append({
                'id': item.id,
                'variant_id': variant.id,
                'product_slug': product.slug,
                'product_url': reverse(
                    'catalog:product-detail',
                    kwargs={'slug': product.slug}
                ) + (f"?color={variant.color.strip()}" if variant.color else ""),
                'product_name': product.name,
                'size': (
                    variant.size.name
                    if variant.size
                    else ''
                ),
                'color': variant.color,
                'price': float(item.unit_price),
                'quantity': item.quantity,
                'subtotal': float(item.subtotal),
                'image': (
                    variant_img.image.url
                    if (variant_img and variant_img.image)
                    else '/static/images/placeholder.jpg'
                ),
            })

        return items    

    def get_summary(self):
        """Returns total item count and order subtotal."""
        items = self.get_items()
        total_qty = sum(item['quantity'] for item in items)
        subtotal = sum(item['subtotal'] for item in items)
        return {
            'total_items': total_qty,
            'subtotal': subtotal,
        }

    def clear(self):
        CartItem.objects.filter(
            cart=self.cart
        ).delete()

    