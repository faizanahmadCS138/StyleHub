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
            # Initialize Session Cart dict for guests
            session_cart = self.session.get('cart')
            if session_cart is None:
                session_cart = self.session['cart'] = {}
            self.session_cart = session_cart

    def merge_session_cart(self, user=None):
        """
        Transfers items from guest session storage into the user's database cart upon login.
        """
        target_user = user or self.user
        if not target_user or not target_user.is_authenticated:
            return

        # Fetch or create the user's DB cart
        db_cart, _ = Cart.objects.get_or_create(user=target_user)

        # 1. Merge items from session dict (if any exist)
        session_cart = self.session.get('cart', {})
        if session_cart:
            for variant_id_str, item_data in session_cart.items():
                try:
                    variant = ProductVariant.objects.get(id=int(variant_id_str))
                    qty = item_data.get('quantity', 1)

                    item, created = CartItem.objects.get_or_create(cart=db_cart, variant=variant)
                    if created:
                        item.quantity = qty
                    else:
                        item.quantity += qty

                    if item.quantity > variant.stock_quantity:
                        item.quantity = variant.stock_quantity

                    item.save()
                except (ProductVariant.DoesNotExist, ValueError):
                    continue

            # Clear session cart after merging
            self.session['cart'] = {}
            self.session.modified = True

    def add(self, variant_id, quantity=1, override_quantity=False):
        print("===================")
        print(self.user)
        print(self.user.is_authenticated)
        print(self.request.user)    
        print("===================")
        """Add a variant or update its quantity."""
        variant = ProductVariant.objects.get(id=variant_id)
        variant_id_str = str(variant_id)
        if quantity > variant.stock_quantity:
            raise ValueError(f"Only {variant.stock_quantity} left in stock.")
        
        # 1. DB Cart (Authenticated Users)
        if self.user.is_authenticated:
            item, created = CartItem.objects.get_or_create(cart=self.cart, variant=variant)
            if created:
                item.quantity = quantity
            else:
                if override_quantity:
                    item.quantity = quantity
                else:
                    item.quantity += quantity
            item.save()
            return item

        # 2. Session Cart (Guest Users)
        else:
            if variant_id_str in self.session_cart:
                if override_quantity:
                    self.session_cart[variant_id_str]['quantity'] = quantity
                else:
                    self.session_cart[variant_id_str]['quantity'] += quantity
            else:
                self.session_cart[variant_id_str] = {
                    'quantity': quantity,
                    'price': str(variant.product.display_price + variant.additional_price)
                }
            self.session.modified = True
            return self.session_cart[variant_id_str]

    def remove(self, variant_id):
        """Remove a variant from the cart."""
        variant_id_str = str(variant_id)

        if self.user.is_authenticated:
            CartItem.objects.filter(cart=self.cart, variant_id=variant_id).delete()
        else:
            if variant_id_str in self.session_cart:
                del self.session_cart[variant_id_str]
                self.session.modified = True

    def get_items(self):
        """Returns a standardized list of item dictionaries for views/APIs."""
        items = []

        if self.user.is_authenticated:
            cart_items = CartItem.objects.filter(cart=self.cart).select_related(
                'variant__product', 'variant__size'
            )
            for item in cart_items:
                product = item.variant.product
                primary_img = product.primary_image
                items.append({
                    'id': item.id,
                    'variant_id': item.variant.id,
                    'product_slug': product.slug,
                    'product_url': reverse('catalog:product-detail', kwargs={'slug': product.slug}),
                    'product_name': product.name,
                    'size': item.variant.size.name if item.variant.size else '',
                    'color': item.variant.color,
                    'price': float(item.unit_price),
                    'quantity': item.quantity,
                    'subtotal': float(item.subtotal),
                    'image': primary_img.image.url if primary_img else '/static/images/placeholder.jpg',
                })
        else:
            variant_ids = self.session_cart.keys()
            variants = ProductVariant.objects.filter(id__in=variant_ids).select_related('product', 'size')
            variant_map = {str(v.id): v for v in variants}

            for v_id, data in self.session_cart.items():
                variant = variant_map.get(v_id)
                if not variant:
                    continue
                product = variant.product
                primary_img = product.primary_image
                unit_price = float(product.display_price + variant.additional_price)
                subtotal = unit_price * data['quantity']

                items.append({
                    'id': v_id,
                    'variant_id': variant.id,
                    'product_slug': product.slug,
                    'product_url': reverse('catalog:product-detail', kwargs={'slug': product.slug}),
                    'product_name': product.name,
                    'size': variant.size.name if variant.size else '',
                    'color': variant.color,
                    'price': unit_price,
                    'quantity': data['quantity'],
                    'subtotal': subtotal,
                    'image': primary_img.image.url if primary_img else '/static/images/placeholder.jpg',
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
        """Empties the cart."""
        if self.user.is_authenticated:
            CartItem.objects.filter(cart=self.cart).delete()
        else:
            self.session['cart'] = {}
            self.session.modified = True

    