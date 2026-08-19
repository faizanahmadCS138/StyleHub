from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.db.models import Avg, Count
from .models import Category, Product
from django.http import JsonResponse
from django.urls import reverse
from .models import Tag
from django.views.decorators.cache import cache_page
from django.db import connection, reset_queries
import time
from django.db.models import Prefetch
from .models import ProductImage, ProductVariant
# ─────────────────────────────────────────────────────────────
# Home
# ─────────────────────────────────────────────────────────────

@cache_page(60 * 5)  # cache for 5 minutes
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

from django.db.models import Avg, Count, F, Q
def product_list_view(request, template_name='catalog/product_list.html'):
    """
    Outfitters-style PLP with sticky-count facet filters:
    discount, gender, product type (leaf category), size, color, price range.
    Ultra-fast execution optimized for remote DB connection.
    """
    reset_queries()
    start = time.time()
    # 1. Base lean queryset
    base_products = Product.objects.filter(is_active=True)

    # ── Structural params ─────────────────────────────────────
    category_slug = request.GET.get('category')
    tag_slug      = request.GET.get('tag')
    sort          = request.GET.get('sort', 'newest')
    query         = request.GET.get('q', '').strip()

    # ── Facet params (multi-select checkboxes) ─────────────────
    selected_discounts = request.GET.getlist('discount')       # e.g. ['30','40']
    selected_genders    = request.GET.getlist('gender')        # e.g. ['men']
    selected_types       = request.GET.getlist('product_type')  # leaf Category ids
    selected_sizes        = request.GET.getlist('size')          # Size ids
    selected_colors        = request.GET.getlist('color')         # color names
    min_price   = request.GET.get('min_price')
    max_price   = request.GET.get('max_price')

    selected_category = None
    breadcrumbs = []
    category_tags = []

    # 1. Category (from URL path e.g. /category/men-tshirts/)
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        if selected_category.parent:
            breadcrumbs.append({'name': selected_category.parent.name.upper(), 'slug': selected_category.parent.slug})
        breadcrumbs.append({'name': selected_category.name.upper(), 'slug': selected_category.slug})

        category_ids = [selected_category.id] + list(selected_category.children.values_list('id', flat=True))
        base_products = base_products.filter(category__in=category_ids)
        category_tags = list(Tag.objects.filter(products__category__in=category_ids)[:8])
    else:
        breadcrumbs.append({'name': 'ALL PRODUCTS', 'slug': ''})
        category_tags = list(Tag.objects.all()[:8])

    if tag_slug:
        selected_tag = Tag.objects.filter(slug=tag_slug).first()
        if selected_tag:
            base_products = base_products.filter(tags=selected_tag)

    if query:
        base_products = base_products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    # ── Build individual filter functions ──────────────────────
    def f_discount(qs):
        if not selected_discounts:
            return qs
        q_obj = Q()
        for d in selected_discounts:
            if d == '0':
                q_obj |= Q(discount_percentage=0)
            else:
                q_obj |= Q(discount_percentage=int(d))
        return qs.filter(q_obj)

    def f_gender(qs):
        return qs.filter(gender__in=selected_genders) if selected_genders else qs

    def f_type(qs):
        return qs.filter(category_id__in=selected_types) if selected_types else qs

    def f_size(qs):
        return qs.filter(variants__size_id__in=selected_sizes).distinct() if selected_sizes else qs

    def f_color(qs):
        return qs.filter(variants__color__in=selected_colors).distinct() if selected_colors else qs

    def f_price(qs):
        if min_price:
            qs = qs.filter(base_price__gte=min_price)
        if max_price:
            qs = qs.filter(base_price__lte=max_price)
        return qs

    all_filters = {
        'discount': f_discount,
        'gender'  : f_gender,
        'type'    : f_type,
        'size'    : f_size,
        'color'   : f_color,
        'price'   : f_price,
    }

    # ── Final result set: apply every facet ─────────────────────
    result_products = base_products
    for fn in all_filters.values():
        result_products = fn(result_products)

    # 3. Sorting
    sort_options = {
        'newest'    : '-created_at',
        'price_asc' : 'base_price',
        'price_desc': '-base_price',
    }
    result_products = result_products.order_by(sort_options.get(sort, '-created_at'))

    # 4. Pagination (15 items per page max)
    paginator   = Paginator(result_products, 15)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)

    # Hydrate ONLY the 15 items on current page with images, variants, ratings
    if page_obj.object_list:
        page_ids = [p.id for p in page_obj.object_list]
        hydrated_products = Product.objects.filter(id__in=page_ids).prefetch_related(
            'images', 'variants', 'variants__size', 'tags'
        ).annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True)),
        )
        hydrated_map = {p.id: p for p in hydrated_products}
        page_obj.object_list = [hydrated_map[pid] for pid in page_ids if pid in hydrated_map]

    # Fast lightweight facet options
    all_categories = Category.objects.filter(is_active=True, parent=None).order_by('display_order')
    
    # Fast static/pre-built facet lists for instant rendering
    gender_counts = [
        {'gender': 'men', 'count': ''},
        {'gender': 'women', 'count': ''},
        {'gender': 'kids', 'count': ''},
    ]

    type_counts = Category.objects.filter(is_active=True, parent__isnull=False).values('id', 'name').annotate(category__id=F('id'), category__name=F('name'))

    from apps.catalog.models import Size
    size_counts = Size.objects.all().values('id', 'name', 'display_order').annotate(variants__size__id=F('id'), variants__size__name=F('name'), variants__size__display_order=F('display_order')).order_by('display_order')

    color_counts = [
        {'variants__color': 'Black', 'variants__color_hex': '#000000'},
        {'variants__color': 'Blue', 'variants__color_hex': '#1a365d'},
        {'variants__color': 'Brown', 'variants__color_hex': '#744210'},
        {'variants__color': 'Green', 'variants__color_hex': '#22543d'},
        {'variants__color': 'Multi Color', 'variants__color_hex': '#e2e8f0'},
        {'variants__color': 'Off White', 'variants__color_hex': '#faf5ff'},
        {'variants__color': 'Stone', 'variants__color_hex': '#a0aec0'},
    ]

    discount_counts = [
        {'discount_percentage': 50},
        {'discount_percentage': 40},
        {'discount_percentage': 30},
        {'discount_percentage': 20},
        {'discount_percentage': 10},
    ]

    context = {
        'page_obj'         : page_obj,
        'all_categories'   : all_categories,
        'selected_category': selected_category,
        'category_tags'    : category_tags,
        'breadcrumbs'      : breadcrumbs,
        'sort'             : sort,
        'query'            : query,

        # facet data + current selections (for checked state)
        'discount_counts'    : discount_counts,
        'selected_discounts' : selected_discounts,

        'gender_counts'   : gender_counts,
        'selected_genders': selected_genders,

        'type_counts'  : list(type_counts),
        'selected_types': selected_types,

        'size_counts'  : list(size_counts),
        'selected_sizes': selected_sizes,

        'color_counts'  : color_counts,
        'selected_colors': selected_colors,

        'min_price': min_price,
        'max_price': max_price,

        'total_results': paginator.count,
    }
    print(f"⏱ {len(connection.queries)} queries, {time.time()-start:.2f}s in view")
    for q in connection.queries:
        if float(q['time']) > 0.05:  # flag anything slower than 50ms
            print(f"  SLOW ({q['time']}s): {q['sql'][:120]}")
    return render(request, template_name, context)
# def product_list_view(request):
#     """
#     Outfitters-style Product Listing Page with Category Breadcrumbs & Category-specific Tags.
#     Query params:
#         category  → filter by category slug
#         tag       → filter by tag slug
#         gender    → men / women / kids
#         min_price → minimum price
#         max_price → maximum price
#         sort      → newest | price_asc | price_desc
#         q         → keyword search
#     """
#     from .models import Tag

#     products = Product.objects.filter(is_active=True).prefetch_related('images', 'variants', 'tags').annotate(
#         avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
#         review_count=Count('reviews', filter=Q(reviews__is_approved=True)),
#     )

#     category_slug = request.GET.get('category')
#     tag_slug      = request.GET.get('tag')
#     gender        = request.GET.get('gender')
#     min_price     = request.GET.get('min_price')
#     max_price     = request.GET.get('max_price')
#     sort          = request.GET.get('sort', 'newest')
#     query         = request.GET.get('q', '').strip()

#     selected_category = None
#     selected_tag = None
#     breadcrumbs = []
#     category_tags = []

#     # 1. Category Filtering & Breadcrumbs
#     if category_slug:
#         selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)

#         # Build clean breadcrumb trail
#         if selected_category.parent:
#             breadcrumbs.append({'name': selected_category.parent.name.upper(), 'slug': selected_category.parent.slug})
#             breadcrumbs.append({'name': selected_category.name.upper(), 'slug': selected_category.slug})
#         else:
#             breadcrumbs.append({'name': selected_category.name.upper(), 'slug': selected_category.slug})

#         # Include products from category and its subcategories
#         category_ids = [selected_category.id] + list(
#             selected_category.children.values_list('id', flat=True)
#         )
#         products = products.filter(category__in=category_ids)

#         # ONLY fetch Tags attached to products in this specific category!
#         category_tags = Tag.objects.filter(
#             products__category__in=category_ids,
#             products__is_active=True
#         ).distinct()
#     else:
#         breadcrumbs.append({'name': 'ALL PRODUCTS', 'slug': ''})
#         category_tags = Tag.objects.filter(products__is_active=True).distinct()

#     # 2. Tag Filtering
#     if tag_slug:
#         selected_tag = Tag.objects.filter(slug=tag_slug).first()
#         if selected_tag:
#             products = products.filter(tags=selected_tag)

#     if gender:
#         products = products.filter(gender=gender)

#     if min_price:
#         products = products.filter(base_price__gte=min_price)

#     if max_price:
#         products = products.filter(base_price__lte=max_price)

#     if query:
#         products = products.filter(
#             Q(name__icontains=query) |
#             Q(description__icontains=query) |
#             Q(brand__icontains=query) |
#             Q(tags__name__icontains=query)
#         ).distinct()

#     # 3. Sorting
#     sort_options = {
#         'newest'    : '-created_at',
#         'price_asc' : 'base_price',
#         'price_desc': '-base_price',
#     }
#     products = products.order_by(sort_options.get(sort, '-created_at'))

#     # 4. Pagination
#     paginator   = Paginator(products, 20)
#     page_number = request.GET.get('page', 1)
#     page_obj    = paginator.get_page(page_number)

#     all_categories = Category.objects.filter(is_active=True, parent=None).order_by('display_order')

#     context = {
#         'page_obj'         : page_obj,
#         'all_categories'   : all_categories,
#         'selected_category': selected_category,
#         'selected_tag'     : selected_tag,
#         'category_tags'    : category_tags,
#         'breadcrumbs'      : breadcrumbs,
#         'gender'           : gender,
#         'min_price'        : min_price,
#         'max_price'        : max_price,
#         'sort'             : sort,
#         'query'            : query,
#         'tag_slug'         : tag_slug,
#     }
#     return render(request, 'catalog/product_list.html', context)
# ─────────────────────────────────────────────────────────────
# Product Detail
# ─────────────────────────────────────────────────────────────

import json

@cache_page(60 * 5)
def product_detail_view(request, slug):
    """
    Single product page matching Outfitters design.
    Provides breadcrumbs, image gallery, ordered sizes, colors, and variant JSON for live stock lookup.
    """
    product = get_object_or_404(
        Product.objects.select_related('category__parent').prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.order_by('display_order')),
            Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True).select_related('size')),
            'tags',
        ),
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

    # 2. Images & variants — plain .all(), uses the Prefetch cache, zero extra queries
    all_images = list(product.images.all())
    variants = list(product.variants.all())

    # 3. Sizes
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

    # 4. Colors — built from all_images in Python, no DB hits
    colors_map = {}
    for v in variants:
        if v.color and v.color.strip() not in colors_map:
            color_name = v.color.strip()
            key = color_name.lower()
            matching_img = next(
                (img for img in all_images if img.color and img.color.strip().lower() == key and img.is_primary),
                None
            ) or next(
                (img for img in all_images if img.color and img.color.strip().lower() == key),
                None
            )
            img_url = matching_img.image.url if (matching_img and matching_img.image) else ''
            colors_map[color_name] = {
                'name': color_name,
                'hex': v.color_hex or '#222222',
                'image_url': img_url,
            }

    colors_list = list(colors_map.values())
    requested_color = request.GET.get('color', '').strip()

    selected_color = None
    if requested_color:
        for idx, c in enumerate(colors_list):
            if c['name'].lower() == requested_color.lower():
                selected_color = c['name']
                colors_list.insert(0, colors_list.pop(idx))
                break

    if not selected_color and colors_list:
        selected_color = colors_list[0]['name']

    # 5. Reorder images so selected_color images appear first (still in-memory, no DB hit)
    if selected_color:
        color_imgs = [img for img in all_images if img.color and img.color.strip().lower() == selected_color.lower()]
        other_imgs = [img for img in all_images if img not in color_imgs]
        images = color_imgs + other_imgs
    else:
        images = all_images

    primary_image = images[0] if images else product.primary_image

    # 6. Related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
    ).exclude(pk=product.pk).prefetch_related('images')[:4]

    # 7. JSON for JS variant selection
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
        'reviews'          : reviews,
        'avg_rating'       : review_stats['avg_rating'] or 5,
        'review_count'     : review_stats['review_count'],
        'user_has_reviewed': user_has_reviewed,
    }
    return render(request, 'catalog/product_detail.html', context)
# ─────────────────────────────────────────────────────────────
# Category Page
# ─────────────────────────────────────────────────────────────

@cache_page(60 * 5)  # cache for 5 minutes
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

@cache_page(60 * 5)  # cache for 5 minutes
def search_view(request):
    """Full-text search results page (Outfitters style)."""
    request.GET = request.GET.copy()
    return product_list_view(request, template_name='catalog/search_results.html')


@cache_page(60 * 3)  # cache for 3 minutes
def live_search_view(request):
    """
    Lightweight AJAX endpoint powering the search overlay.
    Returns tag-based suggestions + top 8 matching products as JSON.
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        # Nothing typed yet -> just show popular suggestions
        popular = (
            Tag.objects.filter(products__is_active=True)
            .distinct()
            .order_by('name')[:6]
        )
        return JsonResponse({
            'suggestions': [t.name for t in popular],
            'products': [],
            'total': 0,
        })

    base_qs = Product.objects.filter(is_active=True).filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(brand__icontains=query) |
        Q(tags__name__icontains=query)
    ).distinct()

    total = base_qs.count()
    products = base_qs.prefetch_related('images')[:8]

    suggestions = list(
        Tag.objects.filter(name__icontains=query, products__is_active=True)
        .distinct()
        .values_list('name', flat=True)[:6]
    )

    def product_payload(p):
        img = p.primary_image
        return {
            'name': p.name,
            'brand': p.brand or '',
            'url': reverse('catalog:product-detail', args=[p.slug]),
            'image': img.image.url if (img and hasattr(img, 'image') and img.image) else '',
            'price': f"{p.display_price:,.0f}",
            'original_price': f"{p.base_price:,.0f}" if p.is_on_sale else None,
        }

    return JsonResponse({
        'suggestions': suggestions,
        'total': total,
        'products': [product_payload(p) for p in products],
    })