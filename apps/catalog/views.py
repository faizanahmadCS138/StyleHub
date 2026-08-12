from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.db.models import Avg, Count
from .models import Category, Product


# ─────────────────────────────────────────────────────────────
# Home
# ─────────────────────────────────────────────────────────────

def home_view(request):
    """
    Homepage:
    - Featured products (is_featured=True)
    - Active top-level categories (parent=None)
    - New arrivals (latest 8 active products)
    - Sale products (is_on_sale=True)
    """
    featured_products = Product.objects.filter(
        is_active=True, is_featured=True
    ).prefetch_related('images')[:8]

    new_arrivals = Product.objects.filter(
        is_active=True
    ).prefetch_related('images').order_by('-created_at')[:8]

    sale_products = Product.objects.filter(
        is_active=True, is_on_sale=True
    ).prefetch_related('images')[:8]

    top_categories = Category.objects.filter(
        is_active=True, parent=None
    ).order_by('display_order')[:6]

    context = {
        'featured_products': featured_products,
        'new_arrivals'     : new_arrivals,
        'sale_products'    : sale_products,
        'top_categories'   : top_categories,
    }
    return render(request, 'catalog/home.html', context)


# ─────────────────────────────────────────────────────────────
# Product List
# ─────────────────────────────────────────────────────────────

from django.db.models import Avg, Count, Q  # make sure Avg, Count are imported alongside your existing Q

def product_list_view(request):
    """
    Outfitters-style Product Listing Page with Category Breadcrumbs & Category-specific Tags.
    Query params:
        category  → filter by category slug
        tag       → filter by tag slug
        gender    → men / women / kids
        min_price → minimum price
        max_price → maximum price
        sort      → newest | price_asc | price_desc
        q         → keyword search
    """
    from .models import Tag

    products = Product.objects.filter(is_active=True).prefetch_related('images', 'variants', 'tags').annotate(
        avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
        review_count=Count('reviews', filter=Q(reviews__is_approved=True)),
    )

    category_slug = request.GET.get('category')
    tag_slug      = request.GET.get('tag')
    gender        = request.GET.get('gender')
    min_price     = request.GET.get('min_price')
    max_price     = request.GET.get('max_price')
    sort          = request.GET.get('sort', 'newest')
    query         = request.GET.get('q', '').strip()

    selected_category = None
    selected_tag = None
    breadcrumbs = []
    category_tags = []

    # 1. Category Filtering & Breadcrumbs
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)

        # Build clean breadcrumb trail
        if selected_category.parent:
            breadcrumbs.append({'name': selected_category.parent.name.upper(), 'slug': selected_category.parent.slug})
            breadcrumbs.append({'name': selected_category.name.upper(), 'slug': selected_category.slug})
        else:
            breadcrumbs.append({'name': selected_category.name.upper(), 'slug': selected_category.slug})

        # Include products from category and its subcategories
        category_ids = [selected_category.id] + list(
            selected_category.children.values_list('id', flat=True)
        )
        products = products.filter(category__in=category_ids)

        # ONLY fetch Tags attached to products in this specific category!
        category_tags = Tag.objects.filter(
            products__category__in=category_ids,
            products__is_active=True
        ).distinct()
    else:
        breadcrumbs.append({'name': 'ALL PRODUCTS', 'slug': ''})
        category_tags = Tag.objects.filter(products__is_active=True).distinct()

    # 2. Tag Filtering
    if tag_slug:
        selected_tag = Tag.objects.filter(slug=tag_slug).first()
        if selected_tag:
            products = products.filter(tags=selected_tag)

    if gender:
        products = products.filter(gender=gender)

    if min_price:
        products = products.filter(base_price__gte=min_price)

    if max_price:
        products = products.filter(base_price__lte=max_price)

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    # 3. Sorting
    sort_options = {
        'newest'    : '-created_at',
        'price_asc' : 'base_price',
        'price_desc': '-base_price',
    }
    products = products.order_by(sort_options.get(sort, '-created_at'))

    # 4. Pagination
    paginator   = Paginator(products, 20)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)

    all_categories = Category.objects.filter(is_active=True, parent=None).order_by('display_order')

    context = {
        'page_obj'         : page_obj,
        'all_categories'   : all_categories,
        'selected_category': selected_category,
        'selected_tag'     : selected_tag,
        'category_tags'    : category_tags,
        'breadcrumbs'      : breadcrumbs,
        'gender'           : gender,
        'min_price'        : min_price,
        'max_price'        : max_price,
        'sort'             : sort,
        'query'            : query,
        'tag_slug'         : tag_slug,
    }
    return render(request, 'catalog/product_list.html', context)
# ─────────────────────────────────────────────────────────────
# Product Detail
# ─────────────────────────────────────────────────────────────

import json

def product_detail_view(request, slug):
    """
    Single product page matching Outfitters design.
    Provides breadcrumbs, image gallery, ordered sizes, colors, and variant JSON for live stock lookup.
    """
    product = get_object_or_404(
        Product.objects.prefetch_related('images', 'variants__size', 'tags', 'category__parent'),
        slug=slug,
        is_active=True,
    )
    reviews = product.reviews.filter(is_approved=True).select_related('user').order_by('-created_at')
    review_stats = product.reviews.filter(is_approved=True).aggregate(
        avg_rating=Avg('rating'), review_count=Count('id')
    )
    user_has_reviewed = (
        request.user.is_authenticated
        and product.reviews.filter(user=request.user).exists()
    )

    # 1. Breadcrumb trail
    breadcrumbs = []
    if product.category:
        if product.category.parent:
            breadcrumbs.append({'name': product.category.parent.name.upper(), 'slug': product.category.parent.slug})
        breadcrumbs.append({'name': product.category.name.upper(), 'slug': product.category.slug})

    # 2. Images gallery
    images = list(product.images.all().order_by('display_order'))
    primary_image = product.primary_image

    # 3. Variants & Sizes (sorted by display_order)
    variants = product.variants.filter(is_active=True).select_related('size')

    sizes_map = {}
    for v in variants:
        if v.size and v.size.name not in sizes_map:
            sizes_map[v.size.name] = {
                'id': v.size.id,
                'name': v.size.name,
                'display_order': v.size.display_order,
                'has_stock': v.stock_quantity > 0,
            }
        elif v.size and v.stock_quantity > 0:
            sizes_map[v.size.name]['has_stock'] = True

    sorted_sizes = sorted(sizes_map.values(), key=lambda s: s['display_order'])

    # 4. Colors
    colors_map = {}
    for v in variants:
        if v.color and v.color.strip() not in colors_map:
            color_name = v.color.strip()
            matching_img = (
                product.images.filter(color__iexact=color_name, is_primary=True).first()
                or product.images.filter(color__iexact=color_name).first()
            )
            img_url = matching_img.image.url if (matching_img and matching_img.image) else ''
            colors_map[color_name] = {
                'name': color_name,
                'hex': v.color_hex or '#222222',
                'image_url': img_url,
            }

    colors_list = list(colors_map.values())
    requested_color = request.GET.get('color', '').strip()

    # If requested color exists in product colors, re-order colors_list so requested_color is first
    selected_color = None
    if requested_color:
        for idx, c in enumerate(colors_list):
            if c['name'].lower() == requested_color.lower():
                selected_color = c['name']
                colors_list.insert(0, colors_list.pop(idx))
                break

    if not selected_color and colors_list:
        selected_color = colors_list[0]['name']

    # 2. Images gallery - order so selected_color images appear first
    all_images = list(product.images.all().order_by('display_order'))
    if selected_color:
        color_imgs = [img for img in all_images if img.color and img.color.strip().lower() == selected_color.lower()]
        other_imgs = [img for img in all_images if img not in color_imgs]
        images = color_imgs + other_imgs
    else:
        images = all_images

    primary_image = images[0] if images else product.primary_image

    # 5. Related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
    ).exclude(pk=product.pk).prefetch_related('images')[:4]

    # 6. JSON Data for interactive JS variant selection & stock checking
    variants_data = [
        {
            'id': v.id,
            'size': v.size.name if v.size else '',
            'color': v.color.strip() if v.color else '',
            'stock': v.stock_quantity,
            'price': str(product.display_price + v.additional_price),
        }
        for v in variants
    ]

    context = {
        'product'         : product,
        'breadcrumbs'      : breadcrumbs,
        'images'          : images,
        'primary_image'   : primary_image,
        'sizes'           : sorted_sizes,
        'colors'          : colors_list,
        'selected_color'  : selected_color,
        'related_products': related_products,
        'variants_json'   : json.dumps(variants_data),
        # Reviews
        'reviews'          : reviews,
        'avg_rating'       : review_stats['avg_rating'] or 5,
        'review_count'     : review_stats['review_count'],
        'user_has_reviewed': user_has_reviewed,
    }
    return render(request, 'catalog/product_detail.html', context)
# ─────────────────────────────────────────────────────────────
# Category Page
# ─────────────────────────────────────────────────────────────

def category_view(request, slug):
    """
    Dedicated category landing page.
    Reuses the product list logic but filtered to one category.
    """
    category = get_object_or_404(Category, slug=slug, is_active=True)
    # Pass category slug into GET params and delegate to product_list_view logic
    request.GET = request.GET.copy()
    request.GET['category'] = slug
    return product_list_view(request)


# ─────────────────────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────────────────────

def search_view(request):
    """Full-text search results page."""
    request.GET = request.GET.copy()
    return product_list_view(request)
