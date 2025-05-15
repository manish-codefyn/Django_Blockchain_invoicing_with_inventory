from django import forms
from .models import Product, ProductCategory, ProductStockMovement,ProductPriceHistory

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'sku', 'category', 'unit_price', 
            'tax_rate', 'tax_included', 'is_active', 'stock_quantity',
            'low_stock_threshold', 'image'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'step': '0.01'}),
            'low_stock_threshold': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.pk:  # New product
            instance.created_by = self.user
        instance.updated_by = self.user
        
    def save(self, commit=True):
        is_new = self.instance.pk is None
        old_price = self.instance.unit_price if not is_new else None
        instance = super().save(commit=False)

        if commit:
            instance.save()

            # Check for price change only if not new
            if not is_new:
                try:
                    original = Product.objects.get(pk=instance.pk)
                    if original.unit_price != instance.unit_price:
                        ProductPriceHistory.objects.create(
                            product=instance,
                            old_price=original.unit_price,
                            new_price=instance.unit_price,
                            changed_by=self.user,
                            change_reason='Manual update'
                        )
                except Product.DoesNotExist:
                    pass  # or log warning
        return instance

    
    def clean_category(self):
        category = self.cleaned_data.get('category')
        if category and not ProductCategory.objects.filter(id=category.id).exists():
            raise forms.ValidationError("The selected product category does not exist.")
        return category

class ProductStockMovementForm(forms.ModelForm):
    class Meta:
        model = ProductStockMovement
        fields = ['product', 'movement_type', 'quantity', 'reference', 'notes']
        widgets = {
            'product': forms.HiddenInput(),
            'notes': forms.Textarea(attrs={'rows': 2}),
            'quantity': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.created_by = self.user
        if commit:
            instance.save()
        return instance