from datetime import timedelta
import json
from operator import itemgetter
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest , HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum , Q ,F
from django.utils import timezone
from django.shortcuts import render,redirect,get_object_or_404
from custom_admin.models import Product , Variant ,Category , Offer 
from .models import CustomUser as GrabifyUser ,Cart , Address , OrderDetails , OrderItems ,Wishlist , Wallet
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
import random
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from .forms import SignupForm , UserProfileEditForm , AddressForm ,AddFundsForm
from django.contrib.auth import authenticate, login as auth_login , logout
import logging
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.template.loader import render_to_string
from django.utils.text import slugify

from django.urls import reverse
from django.conf import settings
import uuid
from paypal.standard.forms import PayPalPaymentsForm
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        try:
            user = GrabifyUser.objects.get(pk=user_id)
            cart_items = Cart.objects.filter(user=user)
            cart_item_count = cart_items.count()

            total_sum = cart_items.aggregate(Sum('total'))['total__sum'] or 0
        except GrabifyUser.DoesNotExist:
            total_sum = 0
            cart_items = []
            cart_item_count = 0
    else:
        total_sum = 0
        cart_items = []
        cart_item_count = 0

    products = Product.objects.all()
    
    return render(request, 'index.html', { 'products' : products, 'total_sum': total_sum, 'cart_items': cart_items, 'cart_item_count': cart_item_count})

def base(request):
    user_id = request.user.id
    user = GrabifyUser.objects.get(pk=user_id)
    cart_items = Cart.objects.filter(user=user)
    cart_item_count = cart_items.count()
    
    total_sum = cart_items.aggregate(Sum('total'))['total__sum'] or 0
    return render(request,'base.html',{'total_sum': total_sum, 'cart_items': cart_items, 'cart_item_count' : cart_item_count})

def shop_mobile_list(request):
    products = Product.objects.all()
    
    items_per_page = 8  

    paginator = Paginator(products, items_per_page)
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    return render(request, 'shop-mobile.html', {'products': products})

def shop_lap_list(request):
    products = Product.objects.all()

    # Number of products per page
    items_per_page = 8  

    paginator = Paginator(products, items_per_page)
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    return render(request, 'shop-lap.html', {'products': products})


def product_details(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return HttpResponseNotFound("Product not found")

    variant_images = Variant.objects.filter(product=product)
    is_out_of_stock = product.quantity < 1
    
    try:
        category_offer = Offer.objects.get(category=product.category)
        offer_price = product.price - category_offer.discount_amount
    except Offer.DoesNotExist:
        category_offer = None
        offer_price = product.price
    
    if category_offer:
        return render(request, 'product_details.html', {'offer_price': offer_price, 'product': product, 'variant_images': variant_images, 'offer': category_offer, 'is_out_of_stock': is_out_of_stock})
    
    offer = Offer.objects.all()
    if offer:
        offer_price = 0
        for off in offer:
            if offer_price <= off.discount_amount:
                offer = off
        offer_price = product.price - offer.discount_amount
        return render(request, 'product_details.html', {'offer_price': offer_price, 'product': product, 'variant_images': variant_images, 'offer': offer, 'is_out_of_stock': is_out_of_stock})

    return render(request, 'product_details.html', {'product': product, 'variant_images': variant_images, 'is_out_of_stock': is_out_of_stock})

def signin(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']
            fullname = form.cleaned_data['fullname']

            if password1 == password2:
                if GrabifyUser.objects.filter(email=email).exists():
                    error_message = "Email is already in use"
                    return render(request, 'signin.html', {'form': form, 'error_message': error_message, 'error_flag': True})
                else:
                    request.session['email'] = email
                    request.session['password1'] = password1
                    request.session['fullname'] = fullname

                    sent_otp(request)
                    return render(request, 'otp_page.html', {'email': email})
            else:
                error_message = "Passwords do not match"
                return render(request, 'signin.html', {'form': form, 'error_message': error_message, 'error_flag': True})
        else:
            error_message = "Form is not valid"
            return render(request, 'signin.html', {'form': form, 'error_message': error_message, 'error_flag': True})
    else:
        form = SignupForm()

    return render(request, 'signin.html', {'form': form})

def sent_otp(request):
    s = ''.join(str(random.randint(0, 9)) for _ in range(6))

    email = request.session.get('email', None)
    password1 = request.session.get('password1', None)
    fullname = request.session.get('fullname', None)
    if email is None or password1 is None:
        error_message = "Email is already in use"
        return render(request, "signin.html", {'error_message': error_message, 'error_flag': True})

    request.session["otp"] = s

    try:
        send_mail("OTP for signup", s, 'grabify06@gmail.com', [email], fail_silently=False)
    except Exception as e:
        messages.error(request, f'Error sending OTP email: {str(e)}')
        return render(request, "signin.html", {'messages': f'Error sending OTP email: {str(e)}'})

    return render(request, "otp_page.html")

def otp_varification(request):
    if request.method == 'POST':
        otp_ = request.POST.get('otp')
        if otp_ == request.session["otp"]:
            newuser = GrabifyUser(fullname=request.session['fullname'], email=request.session['email'])
            newuser.set_password(request.session['password1'])
            newuser.status = 'Active'
            newuser.save()

            user = authenticate(request, username=newuser.email, password=request.session['password1'])
            
            if user is not None:
                auth_login(request, user)

                success_message = "Signin successfull"
                return render(request, 'login.html', {'success_message': success_message, 'success_flag': True})
            else:
                error_message = "Authentication failed"
                return render(request, 'login.html', {'error_message': error_message, 'error_flag': True})
        else:
            error_message = "OTP mismatch"
            return render(request, 'otp_page.html', {'error_message': error_message, 'error_flag': True})
        
def custom_login(request):
    if request.method == "POST":
        email_or_username = request.POST.get('email_or_username')
        password = request.POST.get('password')

        try:
            user = GrabifyUser.objects.get(email=email_or_username)
        except GrabifyUser.DoesNotExist:
            user = None

        if user and check_password(password, user.password):
            authenticated_user = authenticate(request, email=user.email, password=password)

            if authenticated_user is not None:
                if authenticated_user.is_superuser:
                    auth_login(request, authenticated_user)
                    return redirect('custom_admin:dashbord')
                else:
                    auth_login(request, authenticated_user)
                    return redirect('index')
            else:
                error_message = "Authentication failed"
        else:
            error_message = "Invalid email or password"
        return render(request, 'login.html', {'error_message': error_message, 'error_flag': True})

    return render(request, 'login.html')

def cart_management(request):
    if request.user.is_authenticated:
        user = request.user
        cart_items = Cart.objects.filter(user=user)
        total_sum = cart_items.aggregate(Sum('total'))['total__sum'] or 0
        return render(request, 'cart.html', {'total_sum': total_sum, 'cart_items': cart_items})
    else:
        error_message = 'Somthing went wrong please login and try again'
        return render(request, 'login.html' , {'error_message': error_message , 'error_flag':True})

def add_to_cart(request):
    if request.method == 'POST' and request.user.is_authenticated:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        size = request.POST.get('attribute_pa_size')

        try:
            product_id = int(product_id)
        except (ValueError, TypeError):
            return render(request, 'product_details.html', {'error_message': 'Invalid product ID'})

        user = request.user
        product = get_object_or_404(Product, pk=product_id)
        
        if size:
            variant = Variant.objects.get(product=product , size=size)
            if variant.quantity == 0:
                error_message = 'This product size is now out of stock !'
                return render(request, 'product_details.html', {'product': product, 'error_message': error_message, 'error_flag': True})
            
            if quantity > variant.quantity:
                error_message = f'The product size has only {variant.quantity} available. Please select a quantity less than or equal to {variant.quantity}.'
                return render(request, 'product_details.html', {'product': product, 'error_message': error_message, 'error_flag': True})
        else:
            error_message = f'please choose your size'
            return render(request, 'product_details.html', {'product': product, 'error_message': error_message, 'error_flag': True})
        
        cart_item, created = Cart.objects.get_or_create(user=user, product=product)
        try:
            wishlist_product = Wishlist.objects.get(product = product)
            wishlist_product.delete()
        except:
            pass
            
        # Update quantity
        cart_item.quantity = quantity
        cart_item.size = size
        cart_item.save()
        
        success_message = 'New item added into Cart'
        cart_items = Cart.objects.filter(user=user)
        total_sum = cart_items.aggregate(Sum('total'))['total__sum'] or 0
        return render(request, 'cart.html', {'total_sum': total_sum, 'cart_items': cart_items , 'success_message':success_message ,'success_flag':True })
    

    return render(request, 'product_details.html', {'error_message': 'Invalid request', 'product_id': request.POST.get('product_id')})
    

@require_POST
def update_cart(request):
    action = request.POST.get('action')
    user_id = request.user.id
    user = GrabifyUser.objects.get(pk=user_id)
    
    if action == 'remove':
        product_id = request.POST.get('product_id')
        Cart.objects.filter(user=user, product__id=product_id).delete()

    return redirect('cart_management')

def quantity_plus(request , product_id):
    user = request.user
    product = Product.objects.get(pk = product_id)   
    cart_item = Cart.objects.get(user = user , product = product)
    variant = Variant.objects.get(product = product , size = cart_item.size)
    
    if variant.quantity < cart_item.quantity+1:
        error_message = f"Quantity not available for {cart_item.product.name}. It only has {variant.quantity} quantity."
        cart_items = Cart.objects.filter(user=user)
        total_sum = cart_items.aggregate(Sum('total'))['total__sum'] or 0
        return render(request, 'cart.html', {'cart_items': cart_items, 'total_sum': total_sum, 'error_message': error_message, 'error_flag': True})
    else:
        cart_item.quantity += 1
        cart_item.save()
        return redirect('cart_management')
    
def quantity_minus(request , product_id):
    user = request.user
    product = Product.objects.get(pk = product_id)
    cart_item = Cart.objects.get(user = user , product = product)
    if cart_item.quantity <= 1:
        cart_item.quantity = 1
        cart_item.save()
        return redirect('cart_management')
    else:
        cart_item.quantity -= 1
        cart_item.save()
        return redirect('cart_management')
        


def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    cart_items = list(cart_items.values())
    for item in cart_items:
        item['total'] = float(item['total'])

    total = sum(item['total'] for item in cart_items) + 50

    host = request.get_host()

    paypal_checkout = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': total,
        'invoice': uuid.uuid4(),
        'currency_code': 'USD',
        'notify_url': f"http://{host}{reverse('paypal-ipn')}",
        'return_url': f"http://{host}{reverse('payment_completed')}",
        'cancel_url': f"http://{host}{reverse('payment_failed')}",
    }

    paypal_payment_button = PayPalPaymentsForm(initial=paypal_checkout)

    if request.method == 'POST':
        selected_address_id = request.POST.get('selectedAddressId')
        payment_option = request.POST.get('payment_option')
        user_id = request.user.id
        user = GrabifyUser.objects.get(pk=user_id)
        cart_items = Cart.objects.filter(user=user)
        
        # Convert Decimal fields to floats
        cart_items = list(cart_items.values())
        for item in cart_items:
            item['total'] = float(item['total'])

        total_sum = sum(item['total'] for item in cart_items) + 50

        if selected_address_id and payment_option == 'cash_on_delivery':
            for cart_item in cart_items:
                product = Product.objects.get(pk=cart_item['product_id'])
                variant = Variant.objects.get(product=product, size=cart_item['size'])
                request.session['selected_address_id'] = selected_address_id
                if cart_item['quantity'] > variant.quantity:
                    if variant.quantity <= 0:
                        error_message = 'We are really sorry the item is sold out all pieces'
                        cart_items = Cart.objects.filter(user=user)
                        total_sum = sum(item.total for item in cart_items) or 0
                        return render(request, 'cart.html', {'cart_items': cart_items, 'total_sum': total_sum, 'error_message': error_message, 'error_flag': True})
                    else:
                        quantity = variant.quantity
                        error_message = f'We are really sorry the item size has only {quantity} pieces now'
                        cart_items = Cart.objects.filter(user=user)
                        total_sum = sum(item.total for item in cart_items) or 0
                        return render(request, 'cart.html', {'cart_items': cart_items, 'total_sum': total_sum, 'error_message': error_message, 'error_flag': True})

            user_id = request.user.id
            user = GrabifyUser.objects.get(pk=user_id)
            address = Address.objects.get(pk=selected_address_id)
            saddress = ''
            saddress += address.first_name
            saddress += " ,"
            saddress += address.address_1
            saddress += " ,"
            saddress += address.telephone
            address = saddress

            order_details = OrderDetails.objects.create(
                user=user,
                address=address,
                payment='cash_on_delivery',
                total=total_sum,
                status='Accepted',
                created_at=timezone.now()
            )

            for cart_item in cart_items:
                OrderItems.objects.create(
                    order_id=order_details,
                    product_id=cart_item['product_id'],
                    quantity=cart_item['quantity']
                )
                product = Product.objects.get(pk=cart_item['product_id'])
                variant = Variant.objects.get(product=product, size=cart_item['size'])
                variant.quantity -= cart_item['quantity']
                variant.save()
                product.quantity -= cart_item['quantity']
                product.save()

            return redirect('success')

        elif selected_address_id and payment_option == 'online_payment':

            payment_option = 'Paypal'
            request.session['checkout_data'] = {
                'selected_address_id': selected_address_id,
                'payment_option': payment_option,
                'cart_items': cart_items,
                'total_sum': total_sum
            }

            return render(request, 'confirm_payment.html', {'paypal_payment_button': paypal_payment_button})

        else:
            error_message = 'Select valid address details or payment method'
            user_id = request.user.id
            user = GrabifyUser.objects.get(pk=user_id)
            user_addresses = Address.objects.filter(user=user)
            cart_items = Cart.objects.filter(user=user)

            total_sum = sum(item.total for item in cart_items) or 0
            form = AddressForm()
            return render(request, 'checkout.html', {'user_addresses': user_addresses, 'cart_items': cart_items,'form': form, 'total_sum': total_sum, 'error_message': error_message, 'error_flag': True, 'paypal_payment_button': paypal_payment_button})

    user_id = request.user.id
    user = GrabifyUser.objects.get(pk=user_id)
    user_addresses = Address.objects.filter(user=user)
    cart_items = Cart.objects.filter(user=user)
    offer_price = 0
    for item in cart_items:
        category = item.product.category
        try:
            offer = Offer.objects.get(category = category)
            offer_price += offer.discount_amount
            item.total -= offer.discount_amount
            offer = True
            
        except:
            offer = None

    total_sum = sum(item.total for item in cart_items) or 0
    
    form = AddressForm()     
    return render(request, 'checkout.html', { 'offer_price' : offer_price , 'user_addresses': user_addresses, 'cart_items': cart_items, 'total_sum': total_sum, 'form': form, 'paypal_payment_button': paypal_payment_button})

def payment_completed_view(request):
    user = request.user
    

    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        return render(request, 'checkout.html', {'error_message': 'Somthing went wrong Please try again ' , 'error_flag':True })

    selected_address_id = checkout_data.get('selected_address_id')
    payment_option = checkout_data.get('payment_option')
    cart_items = checkout_data.get('cart_items')
    total_sum = checkout_data.get('total_sum')
    
    try:
        address = Address.objects.get(pk=selected_address_id)
        saddress = ''
        saddress += address.first_name
        saddress += " ,"
        saddress += address.address_1
        saddress += " ,"
        saddress += address.telephone
        address = saddress
        
    except Address.DoesNotExist:
        return HttpResponse("The specified address does not exist.")

    # Create a new OrderDetails instance
    order_details = OrderDetails.objects.create(
        user=user,
        address=address,
        payment='paypal',
        total=total_sum,
        status='Accepted',
        created_at=timezone.now()
    )

    # Create OrderItems instances for each cart item
    for item in cart_items:
        product_id = item.get('product_id')
        variant_id = item.get('variant_id')
        quantity = item.get('quantity')

        # Retrieve product and variant objects
        product = Product.objects.get(pk=product_id)
        variant = Variant.objects.get(pk=variant_id) if variant_id else None

        # Create OrderItems instance
        OrderItems.objects.create(
            order_id=order_details,
            product=product,
            variant=variant,
            quantity=quantity
        )
    
    return render(request, 'payment_completed.html')

def payment_failed_view(request):
    return render(request , 'payment_faild.html')


def submit_address(request):
    user = request.user
    user_addresses = Address.objects.filter(user=user)
    cart_items = Cart.objects.filter(user=user)
    total_sum = cart_items.aggregate(Sum('total'))['total__sum'] or 0

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            new_address = Address.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                telephone=form.cleaned_data['telephone'],
                company=form.cleaned_data['company'],
                address_1=form.cleaned_data['address_1'],
                city=form.cleaned_data['city'],
                postcode=form.cleaned_data['postcode'],
                country=form.cleaned_data['country'],
                region=form.cleaned_data['region'],
            )

            success_message = 'Address submitted successfully.'
            form = AddressForm()
            return render(request, 'checkout.html', {'user_addresses': user_addresses, 'cart_items': cart_items, 'total_sum': total_sum, 'form': form, 'success_message': success_message, 'success_flag': True , 'new_address' : new_address})
        else:
            error_message = 'Please fill valid data in all required fields.'
            return render(request, 'checkout.html', {'user_addresses': user_addresses, 'cart_items': cart_items, 'total_sum': total_sum, 'form': form, 'error_message': error_message, 'error_flag': True})
    else:
        error_message = 'Invalid request method.'
        form = AddressForm()
        return render(request, 'checkout.html', {'user_addresses': user_addresses, 'cart_items': cart_items, 'total_sum': total_sum, 'form': form, 'error_message': error_message, 'error_flag': True})
        
def success_page(request):
    return render(request,'successpage.html')

@login_required(login_url='login')
def user_profile(request):
    user_id = request.user.id
    user = GrabifyUser.objects.get(pk=user_id)
    cart_items = Cart.objects.filter(user=user)
    orders = OrderDetails.objects.all()
    wishlist_items = Wishlist.objects.all()

    # Create a list to store the data for each order
    order_data = []
    for order in orders:
        user_name = order.user.fullname
        payment = order.payment  
        product_name = ", ".join(item.product.name for item in OrderItems.objects.filter(order_id=order))
        order_date = order.created_at.strftime("%d %b %Y")
        arriving_date = order.created_at + timedelta(days=5)
        status = order.status
        if status == 'Delevered':
            step=[i for i in range(6)]
        elif status == 'Shipped':
            step=[i for i in range(5)]
        elif status == 'Packed':
            step=[i for i in range(4)]
        elif status == 'Accepted':
            step=[i for i in range(3)]
        elif status == 'Placed':
            step=[i for i in range(2)]
        else:
            step=[i for i in range(1)]

        # Append data for each order to the list
        order_data.append({
            'order_id': order.id,
            'user_name': user_name,
            'payment':payment,
            'product_name': product_name,
            'order_date': order_date,
            'arriving_date': arriving_date,
            'status': status,
            'step' : step,
        })

    order_count = orders.count()
    cart_count = cart_items.count()
    wishlist_count = wishlist_items.count()
    order_data = sorted(order_data, key=itemgetter('order_id'), reverse=True)
    
    return render(request , 'user_profile.html',{'wishlist_count':wishlist_count, 'order_data':order_data , 'user':user , 'order_count':order_count , 'cart_count':cart_count })

def edit_profile(request):
    user_id = request.user.id
    user = GrabifyUser.objects.get(pk=user_id)

    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_profile') 
    else:
        form = UserProfileEditForm(instance=user)

    return render(request, 'edit_profile.html', {'form': form , 'email' : user.email})

def user_orders(request):
    orders = OrderDetails.objects.all()

    # Create a list to store the data for each order
    order_data = []
    for order in orders:
        user_name = order.user.fullname  
        payment = order.payment
        product_name = ", ".join(item.product.name for item in OrderItems.objects.filter(order_id=order))
        order_date = order.created_at.strftime("%d %b %Y")
        arriving_date = order.created_at + timedelta(days=5)
        status = order.status
        if status == 'Delevered':
            step=[i for i in range(6)]
        elif status == 'Shipped':
            step=[i for i in range(5)]
        elif status == 'Packed':
            step=[i for i in range(4)]
        elif status == 'Accepted':
            step=[i for i in range(3)]
        elif status == 'Placed':
            step=[i for i in range(2)]
        else:
            step=[i for i in range(1)]

        # Append data for each order to the list
        order_data.append({
            'order_id': order.id,
            'payment': payment,
            'user_name': user_name,
            'product_name': product_name,
            'order_date': order_date,
            'arriving_date': arriving_date,
            'total': order.total,
            'status': status,
            'step': step,
        })
    order_data = sorted(order_data, key=itemgetter('order_id'), reverse=True)
    
        
    return render(request , 'user_orders.html' , {'order_data':order_data })

def cancel_order_view(request, order_id):
    order = get_object_or_404(OrderDetails, id=order_id)

    if order.status != 'Cancelled':
        wallet = Wallet.objects.get(user = request.user)
        wallet.balance += order.total
        wallet.save()
        order.status = 'Cancelled'
        order.save()
        messages.success(request, 'Order successfully cancelled.')
    else:
        messages.error(request, 'Cannot cancel this order.')

    return redirect('user_orders')

def user_address(request):
    user_id = request.user.id
    user = GrabifyUser.objects.get(pk=user_id)
    user_addresses = Address.objects.filter(user=user)
    
    return render(request , 'user_address.html' , {'user_addresses':user_addresses})

def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)

    user_id = request.user.id
    user = GrabifyUser.objects.get(pk=user_id)    
    if user == address.user:
        address.delete()

    return redirect('user_address') 

def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    user_id = request.user.id
    user = GrabifyUser.objects.get(pk=user_id)

    if user == address.user:
        if request.method == 'POST':
            form = AddressForm(request.POST)
            if form.is_valid():
                # Update address fields with form data
                address.first_name = form.cleaned_data['first_name']
                address.last_name = form.cleaned_data['last_name']
                address.email = form.cleaned_data['email']
                address.address_1 = form.cleaned_data['address_1']
                address.company = form.cleaned_data['company']
                address.region = form.cleaned_data['region']
                address.city = form.cleaned_data['city']
                address.country = form.cleaned_data['country']
                address.postcode = form.cleaned_data['postcode']
                address.telephone = form.cleaned_data['telephone']

                address.save()
                return redirect('user_address')
        else:
            # Initialize the form with initial data
            form = AddressForm(initial={
                'first_name': address.first_name,
                'last_name': address.last_name,
                'email':address.email,
                'company':address.company,
                'city':address.city,
                'address_1': address.address_1,
                'region': address.region,
                'country': address.country,
                'postcode': address.postcode,
                'telephone': address.telephone,
            })
            
        return render(request, 'edit_address.html', {'form': form, 'address': address})

    return redirect('user_address')

def add_address(request):
    user_id = request.user.id
    user = GrabifyUser.objects.get(pk=user_id)
    user_addresses = Address.objects.filter(user=user)

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            new_address = Address.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                telephone=form.cleaned_data['telephone'],
                company=form.cleaned_data['company'],
                address_1=form.cleaned_data['address_1'],
                city=form.cleaned_data['city'],
                postcode=form.cleaned_data['postcode'],
                country=form.cleaned_data['country'],
                region=form.cleaned_data['region'],
            )

            
            success_message = 'Address submitted successfully.'
            return render(request , 'user_address.html', {'user_addresses':user_addresses, 'success_message':success_message , 'success_flag' : True})
        else:
            error_message = 'Please fill valid data in all required fields.'
            return render(request , 'add_address.html' , {'form': form , 'error_message':error_message , 'error_flag': True})
    else:
        error_message = 'Invalid request method.'
        form = AddressForm()
        return render(request, 'add_address.html', {'user_addresses': user_addresses, 'form': form, 'error_message': error_message, 'error_flag': True})

def change_password(request):
    user_id = request.user.id
    user = GrabifyUser.objects.get(pk=user_id)

    if request.method == "POST":
        existing_password = request.POST.get('existing_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if check_password(existing_password, user.password):
            if new_password == confirm_password:
                try:
                    validate_password(new_password)
                except ValidationError as e:
                    error_message = ', '.join(e.messages)
                    return render(request, 'change_password.html', {'error_message': error_message, 'error_flag': True })

                user.set_password(new_password)
                user.save()
                logout(request)
                success_message = 'Password change successful'
                return render(request, 'login.html', {'success_message': success_message, 'success_flag': True })
            else:
                error_message = 'New password and confirm password do not match'
        else:
            error_message = 'Existing password is incorrect'

        return render(request, 'change_password.html', {'error_message': error_message, 'error_flag': True })

    return render(request, 'change_password.html')
     
def generate_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = GrabifyUser.objects.get(email=email)
        except GrabifyUser.DoesNotExist:
            user = None
        if user:
            s = ''.join(str(random.randint(0, 9)) for _ in range(6))
            request.session["otp"] = s

            try:
                send_mail("OTP for Password reset", s, 'grabify06@gmail.com', [email], fail_silently=False)
            except Exception as e:
                error_message = f'Error sending OTP email: {str(e)}'
                return render(request, "generate_otp.html", {'error_message': error_message , 'error_flag' : True})
            return render(request , 'forgot_password_otp.html', {'email':email} )
        else:
            
            error_message =  'The email is not registered'
            return render(request , 'generate_otp.html' , {'error_message':error_message , 'error_flag':True})
           
    return render(request, 'generate_otp.html')

def forgot_password_otp_varification(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        otp_entered = request.POST.get('otp')
        stored_otp = str(request.session.get("otp"))

        if stored_otp and otp_entered == stored_otp:
            request.session.pop("otp", None)
            return render(request, 'password_reset.html',{'email': email})
        else:
            error_message = "OTP mismatch"
            return render(request, 'forgot_password_otp.html', {'error_message': error_message, 'error_flag': True})

    return redirect('forgot_password_otp')
                         
        
def password_reset(request):    
    if request.method == 'POST':
        email = request.POST.get('email')
        user = GrabifyUser.objects.get(email = email)
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password and confirm_password and new_password == confirm_password:
            try:
                validate_password(new_password)
            except ValidationError as e:
                error_message = ', '.join(e.messages)
                return render(request, 'password_reset.html', {'error_message': error_message,'email':email, 'error_flag': True })
            
            user.set_password(new_password)
            user.save()
            success_message = 'Password reset is completed'
            return render(request, "login.html", {'success_message':success_message , 'success_flag': True})
        else:
            error_message = 'New password and confirm password do not match'
            return render(request, 'password_reset.html' , {'error_message': error_message , 'error_flag':True , 'email' : email})
        
    return render(request, 'password_reset.html')


def custom_logout(request):
    logout(request)
    return redirect('login') 


def order_details(request, order_id):
    order = OrderDetails.objects.get(pk = order_id)
    order_address = order.address

    order_data = []
    user_name = order.user.fullname
    payment = order.payment  
    product_name = ", ".join(item.product.name for item in OrderItems.objects.filter(order_id=order))
    order_date = order.created_at.strftime("%d %b %Y")
    arriving_date = order.created_at + timedelta(days=5)
    status = order.status

    order_data.append({
        'order_id': order.id,
        'payment' : payment , 
        'user_name': user_name,
        'product_name': product_name,
        'order_date': order_date,
        'total': order.total,
        'arriving_date': arriving_date,
        'status': status,
    })
    
    if status == 'Delevered':
        step=[i for i in range(6)]
    elif status == 'Shipped':
        step=[i for i in range(5)]
    elif status == 'Packed':
        step=[i for i in range(4)]
    elif status == 'Accepted':
        step=[i for i in range(3)]
    elif status == 'Placed':
        step=[i for i in range(2)]
    else:
        step=[i for i in range(1)]
    
    return render(request, 'order_details.html', {'order_data': order_data ,'order_id':order_id , 'order_address': order_address , 'step':step})

def search_view(request):
    query = request.GET.get('q', '').lower()

    products = Product.objects.filter(Q(name__icontains=query) | Q(category__name__icontains = query))
    return render(request, 'search_result.html', {'products': products, 'query': query})


def filter_products(request):
    category = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Product.objects.all()


    if category:
        products = products.filter(category__name__iexact=category)

    if min_price is not None and max_price is not None:
        products = products.filter(price__range=(min_price, max_price))
        
    return render(request, 'search_result.html', {'products': products})


def download_invoice(request, order_id):
    order = get_object_or_404(OrderDetails, pk=order_id)
    order_item = OrderItems.objects.filter(order_id = order.id)
    arriving_date = order.created_at + timedelta(days=5)



    invoice_content = render_to_string('invoice.html', {'order': order , 'arriving_date':arriving_date , 'order_item':order_item})

    # Create a filename for the downloaded invoice (replace 'invoice_' with your desired filename prefix)
    filename = f"invoice_{slugify(order.id)}.html"

    # Set response headers for file download
    response = HttpResponse(invoice_content, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        wishlist_item.quantity = F('quantity') + 1
        wishlist_item.save()
    
    return redirect('wishlist')

def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

def remove_from_wishlist(request, item_id):
    wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
    wishlist_item.delete()
    return redirect('wishlist')


@login_required
def wallet_view(request):
    wallet = Wallet.objects.get_or_create(user=request.user)[0]
    return render(request, 'wallet.html', {'wallet': wallet})

@login_required
def add_funds(request):
    wallet = Wallet.objects.get_or_create(user=request.user)[0]
    if request.method == 'POST':
        form = AddFundsForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            wallet.balance += amount
            wallet.save()
            return redirect('wallet')
    else:
        form = AddFundsForm()
    return render(request, 'add_funds.html', {'form': form})