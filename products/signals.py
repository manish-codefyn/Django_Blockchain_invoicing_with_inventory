# products/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Product, ProductPriceHistory

@receiver(pre_save, sender=Product)
def track_price_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # Skip if new

    try:
        original = sender.objects.get(pk=instance.pk)
        if original.unit_price != instance.unit_price:
            ProductPriceHistory.objects.create(
                product=instance,
                old_price=original.unit_price,
                new_price=instance.unit_price,
                changed_by=instance.updated_by,  # or another method of tracking user
                change_reason='Manual update'
            )
    except sender.DoesNotExist:
        pass
