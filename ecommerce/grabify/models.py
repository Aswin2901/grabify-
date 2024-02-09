from datetime import timedelta
from django.utils import timezone
from django.db import models
from custom_admin.models import Product , Variant
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, fullname, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, fullname=fullname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, fullname, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, fullname, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    fullname = models.CharField(max_length=100)
    password = models.CharField(max_length=120)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('blocked', 'Blocked'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group, related_name='customuser_set', blank=True, help_text='The groups this user belongs to.')
    user_permissions = models.ManyToManyField(Permission, related_name='customuser_set', blank=True, help_text='Specific permissions for this user.')

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fullname']

    def __str__(self):
        return self.email
    
    
    
class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=25,null=True)
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calculate total before saving
        self.total = self.quantity * self.product.price
        super().save(*args, **kwargs)
        

class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    company = models.CharField(max_length=255, blank=True, null=True)
    address_1 = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    postcode = models.CharField(max_length=20)
    country = models.CharField(max_length=255)  # You may want to use a Country model with a ForeignKey
    region = models.CharField(max_length=255)  # You may want to use a Region model with a ForeignKey

    def __str__(self):
        return f"{self.first_name} {self.last_name}'s Address"
    
    
class OrderDetails(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    address = models.CharField(max_length=255 , null=True)
    payment = models.CharField(max_length=255 , null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    STATUS_CHOICES = (
        ('Accepted', 'Accepted'),
        ('Cancelled', 'Cancelled'),
        ('Placed', 'Placed'),
        ('Packed','Packed'),
        ('Shipped','shipped'),
        ('Delevered', 'Delevered'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Accepted')
    created_at = models.DateTimeField(null=True)
    arriving_date = models.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        # Set arriving_date as created_at + 5 days
        if not self.arriving_date:
            self.arriving_date = self.created_at + timedelta(days=5)

        super(OrderDetails, self).save(*args, **kwargs)
    
class OrderItems(models.Model):
    order_id = models.ForeignKey(OrderDetails, on_delete=models.CASCADE)
    product = models.ForeignKey(Product , on_delete=models.CASCADE )
    variant = models.ForeignKey(Variant , on_delete = models.CASCADE , null = True)
    quantity = models.CharField(max_length=255 , null=True)
    
class Wishlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, null=True)
    
     
    def __str__(self):
        return f"Wishlist for {self.user.email} containing {self.product.name}"

class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Wallet of {self.user.username}"