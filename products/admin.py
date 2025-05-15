from django.contrib import admin
from .models import Product, ProductCategory, ProductPriceHistory, ProductStockMovement

class ProductPriceHistoryInline(admin.TabularInline):
    model = ProductPriceHistory
    extra = 0
    readonly_fields = ['old_price', 'new_price', 'changed_by', 'changed_at']
    can_delete = False

class ProductStockMovementInline(admin.TabularInline):
    model = ProductStockMovement
    extra = 0
    readonly_fields = ['created_by', 'created_at']
    can_delete = False

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'unit_price', 'stock_quantity', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'sku', 'description']
    inlines = [ProductPriceHistoryInline, ProductStockMovementInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'sku', 'category', 'image')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'tax_rate', 'tax_included')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'low_stock_threshold', 'is_active')
        }),
    )

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']

@admin.register(ProductPriceHistory)
class ProductPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'old_price', 'new_price', 'changed_at']
    list_filter = ['changed_at']
    search_fields = ['product__name']
    readonly_fields = ['product', 'old_price', 'new_price', 'changed_by', 'changed_at']

@admin.register(ProductStockMovement)
class ProductStockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reference']
    readonly_fields = ['product', 'created_by', 'created_at']