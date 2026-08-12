from django.contrib import admin
from django.utils.html import format_html
from django.db import transaction

from apps.newsletter.services import send_new_product_email
from .models import Category, Product, ProductImage, ProductVariant, Tag, Size


# ─────────────────────────────────────────────────────────────
# Inlines
# ─────────────────────────────────────────────────────────────

class ProductImageInline(admin.TabularInline):
    model   = ProductImage
    extra   = 1
    fields  = ('image', 'image_preview', 'color', 'alt_text', 'is_primary', 'display_order')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px; border-radius:4px;" />', obj.image.url)
        return '—'
    image_preview.short_description = 'Preview'


class ProductVariantInline(admin.TabularInline):
    search_fields = ('size',)
    model  = ProductVariant
    extra  = 1
    can_delete = True
    autocomplete_fields = ['size']
    
    fields = ('size', 'color', 'color_hex', 'stock_quantity', 'additional_price', 'sku_suffix','is_active')

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category','display_order', 'created_at') if hasattr(Size, 'created_at') else ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)
    ordering = ('category', 'display_order')

# ─────────────────────────────────────────────────────────────
# Category Admin
# ─────────────────────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'parent', 'is_active', 'display_order', 'created_at')
    list_filter   = ('is_active', 'parent')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'name')


# ─────────────────────────────────────────────────────────────
# Tag Admin
# ─────────────────────────────────────────────────────────────

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


# ─────────────────────────────────────────────────────────────
# Product Admin
# ─────────────────────────────────────────────────────────────

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = (
        'name','product_image', 'category', 'gender', 'base_price', 'discount_percentage', 'sale_price',
        'is_on_sale', 'is_active', 'is_featured', 'stock_status', 'created_at',
    )
    list_filter   = ('is_active', 'is_featured', 'is_on_sale', 'gender', 'category')
    search_fields = ('name', 'sku', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('tags',)
    list_editable = ('discount_percentage','is_active', 'is_featured', 'is_on_sale')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['category']
    inlines = [ProductImageInline, ProductVariantInline]

    fieldsets = (
        ('Basic Info',   {'fields': ('name', 'slug', 'sku', 'description', 'brand', 'gender')}),
        ('Category & Tags', {'fields': ('category', 'tags')}),
        ('Pricing',      {'fields': ('base_price', 'discount_percentage', 'sale_price', 'is_on_sale')}),
        ('Visibility',   {'fields': ('is_active', 'is_featured')}),
        ('Timestamps',   {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    def product_image(self, obj):
        primary_img = obj.images.filter(is_primary=True).first() or obj.images.first()
        if primary_img and primary_img.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />', primary_img.image.url)
        return '—'
    
    product_image.short_description = 'Image'
    def stock_status(self, obj):
        if obj.is_in_stock:
            return format_html('<span style="color:green;">✔ In Stock</span>')
        return format_html('<span style="color:red;">✘ Out of Stock</span>')
    stock_status.short_description = 'Stock'


    def save_model(self, request, obj, form, change):
        """
            Detect whether this is a newly created product.
        """
        obj._is_new_product = not change

        super().save_model(request, obj, form, change)


    def save_related(self, request, form, formsets, change):
        """
            Save ProductImage/ProductVariant first.
        Then send the newsletter after the database transaction commits.
        """
        super().save_related(request, form, formsets, change)

        if getattr(form.instance, '_is_new_product', False):
            transaction.on_commit(
                lambda: send_new_product_email(form.instance)
            )