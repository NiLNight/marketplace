from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    """
    Административный интерфейс для категорий с поддержкой drag-and-drop
    """
    mptt_level_indent = 20
    list_display = ('tree_actions', 'indented_title', 'product_count')
    list_display_links = ('indented_title',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'slug', 'description')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('products')

    def product_count(self, instance):
        return instance.products.count()

    product_count.short_description = _('Количество товаров')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для товаров с расширенными возможностями
    """
    list_display = (
        'thumbnail_preview',
        'title',
        'price_with_discount',
        'stock_status',
        'category_tree',
        'is_active',
        'created'
    )
    list_filter = (
        'is_active',
        ('category', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ('title', 'description', 'category__title')
    readonly_fields = (
        'created',
        'updated',
        'thumbnail_preview',
        'price_with_discount'
    )
    autocomplete_fields = ('category', 'user')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {
            'fields': (
                'title',
                'slug',
                'description',
                'category',
                'user'
            )
        }),
        (_('Цена и наличие'), {
            'fields': (
                'price',
                'discount',
                'price_with_discount',
                'stock'
            )
        }),
        (_('Изображения'), {
            'fields': (
                'thumbnail',
                'thumbnail_preview'
            )
        }),
        (_('Статус'), {
            'fields': ('is_active',)
        }),
        (_('Метаданные'), {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        })
    )

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.thumbnail.url
            )
        return '-'

    thumbnail_preview.short_description = _('Превью')

    def stock_status(self, obj):
        if obj.stock > 10:
            color = 'green'
        elif obj.stock > 0:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.stock
        )

    stock_status.short_description = _('Остаток')
    stock_status.admin_order_field = 'stock'

    def category_tree(self, obj):
        return format_html(
            '{} > {}',
            obj.category.parent.title if obj.category.parent else '-',
            obj.category.title
        )

    category_tree.short_description = _('Иерархия категорий')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category',
            'user'
        ).prefetch_related('category__parent')
