from django.db import models
from django.utils import timezone

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    

class Product(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='product_images/')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    offer = models.ForeignKey('Offer' , on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('outofstock', 'Out Of Stock'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(auto_now=True)

def __str__(self):
        return self.name
    
class Variant(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='variant_images')
    image = models.ImageField(upload_to='product_images/variants/', null=True)
    SIZE_CHOICES = [
        ('S', 'S'),
        ('XS', 'XS'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
    ]
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, null=True)
    quantity = models.PositiveIntegerField(null=True, default=0)
    
class Offer(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    discount_amount = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)