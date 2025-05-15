from django.urls import path
from .views import (
    ProductListView, ProductCreateView, ProductUpdateView, 
    ProductDetailView, ProductDeleteView,
    ProductCategoryListView, ProductCategoryCreateView,
    ProductCategoryUpdateView, ProductCategoryDeleteView,
    ProductStockMovementCreateView, product_autocomplete
)

app_name = 'products'

urlpatterns = [
    # Product URLs
    path('', ProductListView.as_view(), name='product-list'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('<uuid:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('<uuid:pk>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('<uuid:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),
    
    # Category URLs
    path('categories/', ProductCategoryListView.as_view(), name='category-list'),
    path('categories/create/', ProductCategoryCreateView.as_view(), name='category-create'),
    path('categories/<uuid:pk>/update/', ProductCategoryUpdateView.as_view(), name='category-update'),
    path('categories/<uuid:pk>/delete/', ProductCategoryDeleteView.as_view(), name='category-delete'),
    
    # Stock Movement
    path('stock-movement/create/', ProductStockMovementCreateView.as_view(), name='stock-movement-create'),
    
    # AJAX
    path('autocomplete/', product_autocomplete, name='product-autocomplete'),
]