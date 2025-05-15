from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid
from django.conf import settings
from django.urls import reverse

User = settings.AUTH_USER_MODEL

class ProductCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_included = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_products')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})" if self.sku else self.name

    def get_absolute_url(self):
        return reverse('products:product-detail', kwargs={'pk': self.id})

    @property
    def current_stock_status(self):
        if self.stock_quantity <= 0:
            return 'out_of_stock'
        elif self.stock_quantity <= self.low_stock_threshold:
            return 'low_stock'
        return 'in_stock'

    @property
    def stock_status_display(self):
        status = self.current_stock_status
        if status == 'out_of_stock':
            return '<span class="badge bg-danger">Out of Stock</span>'
        elif status == 'low_stock':
            return '<span class="badge bg-warning text-dark">Low Stock</span>'
        return '<span class="badge bg-success">In Stock</span>'

    def save(self, *args, **kwargs):
        if not self.sku:
            try:
                prefix = self.category.name[:3].upper() if self.category_id else 'PRO'
            except ProductCategory.DoesNotExist:
                prefix = 'PRO'
            unique_part = uuid.uuid4().hex[:6].upper()
            self.sku = f"{prefix}-{unique_part}"
        super().save(*args, **kwargs)

class ProductPriceHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name='price_history', on_delete=models.CASCADE)
    old_price = models.DecimalField(max_digits=12, decimal_places=2)
    new_price = models.DecimalField(max_digits=12, decimal_places=2)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_reason = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product Price History'
        verbose_name_plural = 'Product Price Histories'
        ordering = ['-changed_at']

    def __str__(self):
        return f"Price change for {self.product.name} from {self.old_price} to {self.new_price}"

class ProductStockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
        ('transfer', 'Transfer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name='stock_movements', on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product Stock Movement'
        verbose_name_plural = 'Product Stock Movements'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} of {self.quantity} for {self.product.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product stock quantity
        product = self.product
        if self.movement_type in ['purchase', 'return']:
            product.stock_quantity += self.quantity
        elif self.movement_type in ['sale', 'adjustment', 'transfer']:
            product.stock_quantity -= self.quantity
        product.save()