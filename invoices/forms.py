from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, InvoicePayment
from django.db.models import Sum

from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem

from django import forms
from .models import Invoice


class InvoiceUpdateForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'client', 'date_issued', 'due_date', 'status', 
            'payment_method', 'currency', 'notes', 'terms',
            'tax', 'discount'
        ]
        widgets = {
            'date_issued': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'terms': forms.Textarea(attrs={'rows': 3}),
        }
# class InvoiceUpdateForm(forms.ModelForm):
#     class Meta:
#         model = Invoice
#         fields = [
#             'client', 'date_issued', 'due_date', 'status', 'payment_method',
#             'currency', 'notes', 'terms', 'tax', 'discount', 'payment_received',
#             'payment_date', 'payment_details', 'is_archived'
#         ]
#         widgets = {
#             'client': forms.Select(attrs={'class': 'form-select'}),
#             'date_issued': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
#             'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
#             'status': forms.Select(attrs={'class': 'form-select'}),
#             'payment_method': forms.Select(attrs={'class': 'form-select'}),
#             'currency': forms.Select(attrs={'class': 'form-select'}),
#             'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional notes'}),
#             'terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Terms & Conditions'}),
#             'tax': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter tax %'}),
#             'discount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter discount %'}),
#             'payment_received': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Payment received'}),
#             'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
#             'payment_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Payment details'}),
#             'is_archived': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }


class InvoiceForm(forms.ModelForm):
    def clean_payment_details(self):
        pd = self.cleaned_data.get('payment_details')
        if pd and not isinstance(pd, (dict, str)):
            try:
                return dict(pd)
            except (TypeError, ValueError):
                raise forms.ValidationError("Payment details must be a dictionary or JSON string")
        return pd
    class Meta:
        model = Invoice
        fields = [
            'client', 'date_issued', 'due_date', 'status', 
            'payment_method', 'currency', 'notes', 'terms',
            'tax', 'discount'
        ]
        widgets = {
            'date_issued': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'terms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'currency': forms.Select(attrs={
                'class': 'form-control',
                'id': 'currencySelect'
                }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control',
                'id': 'paymentMethod'
                }),
            'status': forms.Select(attrs={
                'class': 'form-control',
                'id': 'statusSelect'
                }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'id':'discount',
            
                }),
            'tax': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'taxRate'
                }),
        }
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(InvoiceForm, self).__init__(*args, **kwargs)
        
        # Limit clients to those associated with the user if they lack the permission
        if self.user and not self.user.has_perm('invoices.can_view_all_invoices'):
            self.fields['client'].queryset = self.fields['client'].queryset.filter(
                user=self.user
            )
        
        # Set initial status to 'draft' for new invoices
        if not self.instance.pk:
            self.initial['status'] = 'draft'
        
        # Apply 'form-control' class to all fields for Bootstrap styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        date_issued = cleaned_data.get('date_issued')
        due_date = cleaned_data.get('due_date')
        
        if date_issued and due_date and due_date < date_issued:
            self.add_error('due_date', "Due date cannot be before the issue date.")
        
        return cleaned_data

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'description', 'quantity', 'unit_price', 'tax', 'tax_included']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tax_included': forms.CheckboxInput(attrs={'class': 'tax-included-checkbox'}),
        }

InvoiceItemFormSet = inlineformset_factory(
    Invoice, 
    InvoiceItem, 
    fields=('description', 'quantity', 'unit_price', 'tax', 'tax_included', 'product'),
    extra=1,
    can_delete=True,
    widgets={
        'quantity': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        'unit_price': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        'tax': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        'tax_included': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        'description': forms.TextInput(attrs={'class': 'form-control'}),
        'product': forms.Select(attrs={'class': 'form-select'}),
    }
)

class InvoicePaymentForm(forms.ModelForm):
    class Meta:
        model = InvoicePayment
        fields = ['amount', 'payment_date', 'payment_method', 'transaction_id', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop('invoice', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.invoice = self.invoice
        instance.created_by = self.user
        if commit:
            instance.save()
        return instance