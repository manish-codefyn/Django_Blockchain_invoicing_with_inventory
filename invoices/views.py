from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView,TemplateView,View
from django.urls import reverse_lazy,reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db import transaction
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.utils import timezone
from .models import Invoice, InvoiceItem, InvoicePayment, InvoiceActivityLog
from .forms import InvoiceForm, InvoiceItemFormSet, InvoicePaymentForm,InvoiceUpdateForm
from notifications.models import Notification
from django.db.models import Count, Sum, Q
import logging
logger = logging.getLogger(__name__)
from rest_framework.renderers import JSONRenderer
from utils.email_utils import send_invoice_email
from core.models import SiteSetting
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from utils.utils import fetch_resources
from django.http import HttpResponseRedirect
from clients.models import Client
from products.models import Product,ProductCategory
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt 
from django.db.models import ExpressionWrapper, F, DecimalField
from decimal import Decimal

@require_POST
def update_invoice_status(request):
    if request.method == "POST":
        invoice_id = request.POST.get("invoice_id")
        new_status = request.POST.get("status")
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            invoice.status = new_status
            invoice.save()
            return JsonResponse({
                "success": True,
                "status_display": invoice.get_status_display()
            })
        except Invoice.DoesNotExist:
            return JsonResponse({"success": False, "message": "Invoice not found"})
    return JsonResponse({"success": False, "message": "Invalid request"})

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'invoices/list.html'
    context_object_name = 'invoices'

    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.has_perm('invoices.can_view_all_invoices'):
            queryset = queryset.filter(user=self.request.user)
        
        # Filtering
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        client = self.request.GET.get('client')
        if client:
            queryset = queryset.filter(client_id=client)
            
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(date_issued__gte=date_from)
            
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(date_issued__lte=date_to)
            
        return queryset.order_by('-date_issued')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clients'] = Client.objects.all()
        context['status_choices'] = Invoice.STATUS_CHOICES
        return context
    
    
class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    fields = ['client', 'date_issued', 'due_date', 'currency', 'tax', 'discount', 'notes', 'terms']
    template_name = 'invoices/invoice_form.html'
    
    def get_success_url(self):
        return reverse_lazy('invoices:invoice-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Invoice saved successfully.")
        # Process items from form data
        items_data = self.request.POST.get('items_data')
        if items_data:
            try:
                items = json.loads(items_data)
                for item in items:
                    InvoiceItem.objects.create(
                        invoice=self.object,
                        description=item['description'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        tax=item['tax'],
                        tax_included=item['tax_included']
                    )
            except Exception as e:
                if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(e)})
                form.add_error(None, f"Error saving items: {str(e)}")
                return super().form_invalid(form)
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect_url': self.get_success_url()})
        
        return response



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        context['currency_choices'] = Invoice.CURRENCY_CHOICES
        return context
    

class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    fields = ['client', 'date_issued', 'due_date', 'currency', 'tax', 'discount', 'notes', 'terms', 'status','payment_method']
    template_name = 'invoices/invoice_form.html'
    
    def get_success_url(self):
        return reverse_lazy('invoices:invoice-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Process items from form data
        items_data = self.request.POST.get('items_data')
        if items_data:
            try:
                # First delete all existing items
                self.object.items.all().delete()
                
                # Create new items from the submitted data
                items = json.loads(items_data)
                for item in items:
                    product = None
                    if item.get('product'):
                        try:
                            product = Product.objects.get(id=item['product'])
                        except Product.DoesNotExist:
                            pass
                            
                    InvoiceItem.objects.create(
                        invoice=self.object,
                        product=product,
                        description=item['description'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        tax=item['tax'],
                        tax_included=item.get('tax_included', False)
                    )
                    
            except Exception as e:
                if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(e)})
                form.add_error(None, f"Error saving items: {str(e)}")
                return super().form_invalid(form)
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'redirect_url': self.get_success_url()
            })
        
        return response
    
    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Form validation failed',
                'errors': form.errors.get_json_data()
            }, status=400)
        return super().form_invalid(form)
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        context['currency_choices'] = Invoice.CURRENCY_CHOICES
        context['status_choices'] = Invoice.STATUS_CHOICES
        context['payment_method'] = Invoice.PAYMENT_METHOD_CHOICES
        context['update'] = True 
        return context
    

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoices/detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity_logs'] = self.object.activity_logs.all().order_by('-timestamp')[:10]
        return context


class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'invoices/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoices:invoice-list')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Invoice has been successfully deleted.")
        return response


# AJAX views for dynamic functionality
def get_client_details(request, client_id):
    client = get_object_or_404(Client, pk=client_id)
    data = {
        'name': client.name,
        'email': client.email,
        'address': client.address,
        'tax_id': client.tax_id,
        'payment_terms': client.payment_terms,
    }
    return JsonResponse(data)


def get_product_details(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    data = {
        'name': product.name,
        'description': product.description,
        'unit_price': str(product.unit_price),
        'tax_rate': str(product.tax_rate),
    }
    return JsonResponse(data)


def add_payment(request, invoice_id):
    if request.method == 'POST':
        try:
            invoice = get_object_or_404(Invoice, pk=invoice_id)
            payment_data = json.loads(request.POST.get('payment_data', '{}'))
            
            # Validate payment data
            if not payment_data.get('amount') or float(payment_data['amount']) <= 0:
                return JsonResponse({'success': False, 'error': 'Invalid payment amount'}, status=400)
            
            if not payment_data.get('payment_method'):
                return JsonResponse({'success': False, 'error': 'Payment method is required'}, status=400)
            
            payment = InvoicePayment.objects.create(
                invoice=invoice,
                amount=payment_data['amount'],
                payment_date=payment_data['payment_date'],
                payment_method=payment_data['payment_method'],
                transaction_id=payment_data.get('transaction_id', ''),
                notes=payment_data.get('notes', ''),
                created_by=request.user
            )
            
            # Update invoice status if fully paid
            if invoice.balance_due <= 0:
                invoice.status = 'paid'
                invoice.payment_received = True
                invoice.payment_date = payment.payment_date
                invoice.save()
            
            return JsonResponse({
                'success': True, 
                'payment_id': str(payment.id),
                'balance_due': float(invoice.balance_due),
                'payment_status': invoice.payment_status
            })
        
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid payment data format'}, status=400)
        except Exception as e:
            logger.error(f"Error adding payment: {str(e)}")
            return JsonResponse({'success': False, 'error': 'An error occurred while recording payment'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


# def add_payment(request, invoice_id):
#     if request.method == 'POST':
#         invoice = get_object_or_404(Invoice, pk=invoice_id)
#         payment_data = json.loads(request.POST.get('payment_data', '{}'))
        
#         payment = InvoicePayment.objects.create(
#             invoice=invoice,
#             amount=payment_data['amount'],
#             payment_date=payment_data['payment_date'],
#             payment_method=payment_data['payment_method'],
#             transaction_id=payment_data.get('transaction_id', ''),
#             notes=payment_data.get('notes', ''),
#             created_by=request.user
#         )
        
#         # Update invoice status if fully paid
#         if invoice.balance_due <= 0:
#             invoice.status = 'paid'
#             invoice.payment_received = True
#             invoice.payment_date = payment.payment_date
#             invoice.save()
        
#         return JsonResponse({'success': True, 'payment_id': str(payment.id)})
#     return JsonResponse({'success': False}, status=400)





class InvoiceJSONView(LoginRequiredMixin, DetailView):
    model = Invoice
    renderer_classes = [JSONRenderer]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.has_perm('invoices.can_view_all_invoices'):
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    def render_to_response(self, context, **response_kwargs):
        invoice = self.get_object()
        data = invoice.to_dict(self.request)
        return JsonResponse(data, safe=False, **response_kwargs)
    

@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, id=pk, user=request.user)
    site = SiteSetting.objects.first()
    
    template = get_template('invoices/pdf_template.html')
    html = template.render({'invoice': invoice, 'site': site})
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=fetch_resources)
    if pisa_status.err:
        return HttpResponse('We had some errors generating the PDF')
    return response


@login_required
def mark_as_paid(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    if invoice.status != 'paid':
        invoice.status = 'paid'
        invoice.save()
        messages.success(request, 'Invoice marked as paid!')
    return redirect('invoices:invoice-detail', pk=pk)


class InvoiceSendView(View):
    def get(self, request, pk, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=pk)
        if invoice.client.email:
            send_invoice_email(invoice, invoice.client.email)
            messages.success(request, f"Invoice #{invoice.invoice_number} was sent to {invoice.client.email}")
        else:
            messages.error(request, "Client email not found. Cannot send invoice.")
        return redirect('invoices:invoice-detail', pk=invoice.pk)



class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Total revenue from paid invoices
        total_revenue = Invoice.objects.filter(status='paid').annotate(
            total=ExpressionWrapper(F('tax') + F('discount'), output_field=DecimalField())
        ).aggregate(sum_total=Sum('total'))['sum_total'] or 0

        invoice_counts = Invoice.objects.values('status').annotate(count=Count('id'))
        status_map = {item['status']: item['count'] for item in invoice_counts}

        # Pending amount from draft/sent invoices
        pending_amount = Invoice.objects.filter(status__in=['draft', 'sent']).annotate(
            total=ExpressionWrapper(F('tax') + F('discount'), output_field=DecimalField())
        ).aggregate(sum_total=Sum('total'))['sum_total'] or 0

        # Overdue
        overdue_qs = Invoice.objects.filter(status='overdue')
        overdue_count = overdue_qs.count()

        # Total balance due for all overdue invoices
        overdue_critical_amount = sum((invoice.balance_due for invoice in overdue_qs), Decimal('0.00'))

        # Overdue invoices older than 7 days
        critical_overdue_invoices = overdue_qs.filter(
            due_date__lt=timezone.now().date() - timezone.timedelta(days=7)
        )
        # Recent Invoices
        recent_invoices = Invoice.objects.select_related('client').order_by('-created_at')[:10]

        # Monthly invoice chart data
        monthly_data = (
            Invoice.objects
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        chart_labels = [entry['month'].strftime('%b %Y') for entry in monthly_data]
        chart_data = [entry['count'] for entry in monthly_data]

        context.update({
            'total_revenue': total_revenue,
            'invoices_paid': status_map.get('paid', 0),
            'pending_invoices': status_map.get('draft', 0) + status_map.get('sent', 0),
            'pending_amount': pending_amount,
            'overdue_invoices': overdue_count,
            'overdue_critical_amount': overdue_critical_amount,
            'critical_overdue_invoices': critical_overdue_invoices,
            'recent_invoices': recent_invoices,
            'chart_labels': chart_labels,
            'chart_data': chart_data,
            'total_clients': Client.objects.all().count(),
            'total_products': Product.objects.all().count(),
            'total_categories': ProductCategory.objects.all().count(),
        })

        return context
