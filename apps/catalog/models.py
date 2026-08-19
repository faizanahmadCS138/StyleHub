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
from django.utils.functional import cached_property
from apps.core.models import TimeStampedModel
from django.contrib.postgres.indexes import GinIndex

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
        indexes = [
        models.Index(fields=['is_active', 'is_featured']),
        models.Index(fields=['category', 'is_active']),
        models.Index(fields=['gender', 'is_active']),
        models.Index(fields=['is_on_sale']),
        GinIndex(fields=['name'], name='product_name_trgm', opclasses=['gin_trgm_ops']),
        GinIndex(fields=['brand'], name='product_brand_trgm', opclasses=['gin_trgm_ops']),
        GinIndex(fields=['description'], name='product_desc_trgm', opclasses=['gin_trgm_ops']),
    ]

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

    # @property
    # def primary_image(self):
    #     """Returns the primary image or the first available image."""
    #     img = self.images.filter(is_primary=True).first()
    #     return img or self.images.first()

    # @property
    # def secondary_image(self):
    #     """Returns the second image for hover effect or color variant."""
    #     imgs = self.images.all()
    #     if len(imgs) > 1:
    #         return imgs[1]
    #     return self.primary_image

    # @property
    # def color_swatches(self):
    #     """Returns list of distinct color dicts with name, hex code & associated primary image URL."""
    #     swatches = []
    #     seen = set()
    #     for variant in self.variants.filter(is_active=True):
    #         color_name = variant.color.strip() if variant.color else ''
    #         if color_name and color_name.lower() not in seen:
    #             seen.add(color_name.lower())
    #             matching_img = (
    #                 self.images.filter(color__iexact=color_name, is_primary=True).first()
    #                 or self.images.filter(color__iexact=color_name).first()
    #             )
    #             img_url = matching_img.image.url if (matching_img and matching_img.image) else (self.primary_image.image.url if (self.primary_image and self.primary_image.image) else '')
    #             swatches.append({
    #                 'color': color_name,
    #                 'color_hex': variant.color_hex or '#222222',
    #                 'image_url': img_url,
    #             })
    #     return swatches
    @cached_property
    def primary_image(self):
        """Returns the primary image or the first available image (uses prefetch cache)."""
        imgs = list(self.images.all())   # .all() with NOTHING chained = uses prefetch cache
        for img in imgs:
            if img.is_primary:
                return img
        return imgs[0] if imgs else None
    
    @cached_property
    def secondary_image(self):
        """Returns the second image for hover effect or color variant."""
        imgs = list(self.images.all())
        if len(imgs) > 1:
            return imgs[1]
        return self.primary_image

    @cached_property
    def color_swatches(self):
        """Returns list of distinct color dicts. Built from already-fetched images/variants — zero extra queries."""
        images = list(self.images.all())
        variants = [v for v in self.variants.all() if v.is_active]

        swatches = []
        seen = set()
        for variant in variants:
            color_name = variant.color.strip() if variant.color else ''
            key = color_name.lower()
            if color_name and key not in seen:
                seen.add(key)
                matching_img = next(
                    (img for img in images if img.color and img.color.strip().lower() == key and img.is_primary),
                    None
                ) or next(
                    (img for img in images if img.color and img.color.strip().lower() == key),
                    None
                )
                fallback = matching_img or self.primary_image
                img_url = fallback.image.url if (fallback and fallback.image) else ''
                swatches.append({
                    'color': color_name,
                    'color_hex': variant.color_hex or '#222222',
                    'image_url': img_url,
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
    color         = models.CharField(max_length=50, blank=True, default='', help_text="Color name associated with this image, e.g. Blue, Black")
    is_primary    = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f'Image for {self.product.name}'

    def save(self, *args, **kwargs):
        # Ensure only one primary image per color (or uncolored group) per product
        if self.is_primary:
            color_str = self.color.strip() if self.color else ''
            ProductImage.objects.filter(
                product=self.product,
                color__iexact=color_str,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
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
        indexes = [
        models.Index(fields=['product', 'is_active']),
        models.Index(fields=['stock_quantity']),
    ]

    def __str__(self):
        parts = [self.product.name]
        if self.size:
            parts.append(self.size.name)
        if self.color:
            parts.append(self.color)
        return ' / '.join(parts)

    @property
    def variant_image(self):
        """Returns the primary image matching this variant's color, or fallback to product primary image."""
        if self.color:
            color_name = self.color.strip().lower()
            images = list(self.product.images.all())   # uses prefetch cache now
            matching_img = next(
                (img for img in images if img.color and img.color.strip().lower() == color_name and img.is_primary), None
            ) or next(
                (img for img in images if img.color and img.color.strip().lower() == color_name), None
            )
            if matching_img and matching_img.image:
                return matching_img
        return self.product.primary_image

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