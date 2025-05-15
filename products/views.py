from django.views.generic import ListView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404,redirect
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Product, ProductCategory, ProductStockMovement
from .forms import ProductForm, ProductCategoryForm, ProductStockMovementForm
import logging
from django.contrib import messages
from django.views.generic.edit import CreateView
from django.core.exceptions import ObjectDoesNotExist
logger = logging.getLogger(__name__)


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        category = self.request.GET.get('category')
        stock_status = self.request.GET.get('stock_status')
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(sku__icontains=search_query)
            )

        if category:
            queryset = queryset.filter(category__id=category)
        
        if stock_status:
            if stock_status == 'in_stock':
                queryset = queryset.filter(stock_quantity__gt=F('low_stock_threshold'))
            elif stock_status == 'low_stock':
                queryset = queryset.filter(
                    stock_quantity__gt=0,
                    stock_quantity__lte=F('low_stock_threshold')
                )
            elif stock_status == 'out_of_stock':
                queryset = queryset.filter(stock_quantity__lte=0)
        
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_stock_status'] = self.request.GET.get('stock_status', '')
        return context
    

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:product-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, f'Product "{self.object.name}" created successfully.')
            logger.info(f'Product created: {self.object.name} (ID: {self.object.id})')
            return response
        except ProductCategory.DoesNotExist as e:
            logger.warning(f'ProductCategory missing during creation: {e}')
            messages.error(self.request, "Selected product category does not exist.")
            form.add_error('category', 'Selected product category was not found.')
            return self.form_invalid(form)
        except Exception as e:
            logger.exception("Unexpected error during product creation")
            messages.error(self.request, "An unexpected error occurred while creating the product.")
            form.add_error(None, str(e))
            return self.form_invalid(form)
        

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    
    def get_success_url(self):
        return reverse_lazy('products:product-detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Product "{self.object.name}" updated successfully.')
        return response

class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['movement_form'] = ProductStockMovementForm(
            initial={'product': self.object},
            user=self.request.user
        )
        context['stock_movements'] = self.object.stock_movements.all().order_by('-created_at')[:10]
        context['price_history'] = self.object.price_history.all().order_by('-changed_at')[:10]
        return context

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'products/product_confirm_delete.html'
    success_url = reverse_lazy('products:product-list')

    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        messages.success(request, f'Product "{product.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

class ProductCategoryListView(LoginRequiredMixin, ListView):
    model = ProductCategory
    template_name = 'products/category_list.html'
    context_object_name = 'categories'

class ProductCategoryCreateView(LoginRequiredMixin, CreateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Category "{self.object.name}" created successfully.')
        return response

class ProductCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Category "{self.object.name}" updated successfully.')
        return response

class ProductCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductCategory
    template_name = 'products/category_confirm_delete.html'
    success_url = reverse_lazy('products:category-list')

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        messages.success(request, f'Category "{category.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

class ProductStockMovementCreateView(LoginRequiredMixin, CreateView):
    model = ProductStockMovement
    form_class = ProductStockMovementForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'Stock movement recorded successfully.')
        return redirect('products:product-detail', pk=self.object.product.pk)

def product_autocomplete(request):
    if request.GET.get('q'):
        q = request.GET['q']
        products = Product.objects.filter(
            Q(name__icontains=q) | Q(sku__icontains=q),
            is_active=True
        ).order_by('name')[:10]
        results = [{
            'id': str(product.id),
            'text': f"{product.name} ({product.sku}) - {product.unit_price}",
            'unit_price': str(product.unit_price),
            'tax_rate': str(product.tax_rate),
            'tax_included': product.tax_included,
        } for product in products]
        return JsonResponse({'results': results}, safe=False)
    return JsonResponse({'results': []})