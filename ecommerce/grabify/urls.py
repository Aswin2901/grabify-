from django.urls import path , include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('index/',views.index , name="index"),
    path('base/',views.base , name="base"),
    path('shop_lap_list/',views.shop_lap_list , name="shop_lap_list"),
    path('shop_mobile_list/',views.shop_mobile_list , name= "shop_mobile_list"),
    path('product_details/<int:product_id>/', views.product_details, name='product_details'),
    path('signin/', views.signin, name='signin'),
    path('otp_verification/',views.otp_varification,name="otp_verification"),
    path('',views.custom_login,name='login'), 
    path('cart/',views.cart_management , name='cart_management'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('update_cart', views.update_cart, name='update_cart'),
    path('update_quantity/', views.update_quantity, name='update_quantity'),
    path('checkout/',views.checkout , name='checkout'),
    path('submit_address/', views.submit_address, name='submit_address'),
    path('success/',views.success_page,name='success'),
    path('user-profile/',views.user_profile,name='user_profile'),
    path('user_orders/',views.user_orders , name='user_orders'),
    path('user_cancel_order/<int:order_id>/', views.cancel_order_view, name='user_cancel_order'),
    path('user_address/',views.user_address , name='user_address'),
    path('delete_address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('edit_address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('add_address/',views.add_address , name='add_address'),
    path('edit_profile/',views.edit_profile , name='edit_profile'),
    path('change_password/',views.change_password , name='change_password'),
    path('generate_otp/',views.generate_otp,name="generate_otp"),
    path('forgot_password_otp_varification/',views.forgot_password_otp_varification,name="forgot_password_otp_varification"),
    path('password-reset/',views.password_reset,name="password_reset"),
    path('logout/', views.custom_logout, name='logout'),
    path('order-details/<int:order_id>/', views.order_details, name='order_details'),
    path('search/', views.search_view, name='search'),
    path('filter_product/', views.filter_products, name='filter_products'),
    path('download_invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
    path('whishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('add-funds/', views.add_funds, name='add_funds'),
    path('wallet/', views.wallet_view, name='wallet'),
    
    path('paypal/', include('paypal.standard.ipn.urls')),
    path('payment-completed/', views.payment_completed_view, name='payment_completed'),
    path('payment-failed/', views.payment_failed_view, name='payment_failed'),
]

urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)