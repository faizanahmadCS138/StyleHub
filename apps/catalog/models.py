"""
catalog/models.py

Category        — hierarchical product categories (parent/child)
Tag             — M2M labels for products
Product         — core product with pricing & metadata
ProductImage    — multiple images per product (Cloudinary)
ProductVariant  — size × color combinations with individual stock
"""

from decimal import Decimal
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


# ─────────────────────────────────────────────────────────────
# Category
# ─────────────────────────────────────────────────────────────

class Category(TimeStampedModel):
    """
    Hierarchical category tree.
    e.g.  Men → Tops → T-Shirts
    A top-level category has parent=None.
    """
    name   = models.CharField(max_length=100, unique=True)
    slug   = models.SlugField(max_length=120, unique=True, blank=True)
    parent = models.ForeignKey(
                 'self',
                 on_delete=models.SET_NULL,
                 null=True, blank=True,
                 related_name='children',
             )
    image       = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        if self.parent:
            return f'{self.parent.name} → {self.name}'
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────
# Tag
# ─────────────────────────────────────────────────────────────

class Tag(models.Model):
    """Simple label attached to products (e.g. 'new-arrival', 'bestseller')."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────
# Product
# ─────────────────────────────────────────────────────────────

class Product(TimeStampedModel):
    """
    Core product record.
    Actual purchasable units live in ProductVariant (size + color + stock).
    """

    GENDER_CHOICES = [
        ('men',   'Men'),
        ('women', 'Women'),
        ('kids',  'Kids'),
    ]

    name        = models.CharField(max_length=255)
    slug        = models.SlugField(max_length=280, unique=True, blank=True)
    sku         = models.CharField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)

    category   = models.ForeignKey(
                     Category,
                     on_delete=models.SET_NULL,
                     null=True, blank=True,
                     related_name='products',
                 )
    tags       = models.ManyToManyField(Tag, blank=True, related_name='products')

    base_price          = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.PositiveIntegerField(default=0, help_text="Discount percentage (0-100%). E.g. enter 20 for 20% off.")
    sale_price          = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Auto-calculated from discount percentage, or enter manually.")
    is_on_sale          = models.BooleanField(default=False)

    brand       = models.CharField(max_length=100, blank=True,default = 'StyleHub')
    gender      = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex')

    is_active   = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            # Auto-generate SKU from slug prefix if not provided
            self.sku = self.slug[:30].upper().replace('-', '')

        # Auto calculate sale price from discount percentage
        if self.base_price:
            if self.discount_percentage and self.discount_percentage > 0:
                discount_amount = self.base_price * (Decimal(self.discount_percentage) / Decimal(100))
                self.sale_price = (self.base_price - discount_amount).quantize(Decimal('0.01'))
                self.is_on_sale = True
            elif self.sale_price and self.sale_price < self.base_price:
                diff = self.base_price - self.sale_price
                self.discount_percentage = int(round((diff / self.base_price) * 100))
                self.is_on_sale = True
            else:
                self.sale_price = None
                self.discount_percentage = 0
                self.is_on_sale = False

        super().save(*args, **kwargs)

    @property
    def display_price(self):
        """Returns sale_price if on sale, otherwise base_price."""
        return self.sale_price if self.is_on_sale and self.sale_price else self.base_price

    @property
    def primary_image(self):
        """Returns the primary image or the first available image."""
        img = self.images.filter(is_primary=True).first()
        return img or self.images.first()

    @property
    def secondary_image(self):
        """Returns the second image for hover effect or color variant."""
        imgs = self.images.all()
        if len(imgs) > 1:
            return imgs[1]
        return self.primary_image

    @property
    def color_swatches(self):
        """Returns list of distinct color dicts with name & hex code."""
        swatches = []
        seen = set()
        for variant in self.variants.filter(is_active=True):
            if variant.color and variant.color.strip().lower() not in seen:
                seen.add(variant.color.strip().lower())
                swatches.append({
                    'color': variant.color.strip(),
                    'color_hex': variant.color_hex or '#222222',
                })
        return swatches

    @property
    def is_in_stock(self):
        """True if at least one variant has stock > 0."""
        return self.variants.filter(stock_quantity__gt=0).exists()


# ─────────────────────────────────────────────────────────────
# ProductImage
# ─────────────────────────────────────────────────────────────

class ProductImage(models.Model):
    """
    One product can have many images.
    Images are stored on Cloudinary via DEFAULT_FILE_STORAGE.
    """
    product       = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image         = models.ImageField(upload_to='products/')
    alt_text      = models.CharField(max_length=200, blank=True)
    is_primary    = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f'Image for {self.product.name}'

    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────
# ProductVariant
# ─────────────────────────────────────────────────────────────
class Size(models.Model):
    CATEGORY_CHOICES = [
        ('adult', 'Adult Apparel'),
        ('waist', 'Waist / Bottoms'),
        ('kids', 'Kids / Toddler'),
    ]
    name = models.CharField(max_length=20)  # e.g., "30", "M", "06-12M"
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='waist')
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['category', 'display_order']
        unique_together = ('name', 'category')
         
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    
    # Clean ForeignKey field
    size = models.ForeignKey(Size, on_delete=models.CASCADE,default = 1,
    related_name='product_variants')
    
    color = models.CharField(max_length=50, blank=True)
    color_hex = models.CharField(
        max_length=7, 
        blank=True, 
        null=True, 
        help_text="Hex code e.g. #FF0000. Leave blank for multi-color."
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    sku_suffix = models.CharField(max_length=20, blank=True)
    additional_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True, verbose_name="Active?")

    class Meta:
        unique_together = ('product', 'size', 'color')

    def __str__(self):
        parts = [self.product.name]
        if self.size:
            parts.append(self.size.name)
        if self.color:
            parts.append(self.color)
        return ' / '.join(parts)

    def save(self, *args, **kwargs):
        if not self.sku_suffix:
            clean_color = "".join(c for c in self.color if c.isalnum()).upper()[:3]
            size_code = self.size.name if self.size else 'NOSIZE'
            self.sku_suffix = f"-{clean_color}-{size_code}"
            
        super().save(*args, **kwargs)

    @property
    def price(self):
        return self.product.display_price + self.additional_price

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0