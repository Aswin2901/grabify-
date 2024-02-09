from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'custom_admin'

urlpatterns = [
    path('admin_login',views.admin_login , name="admin_login"),
    path('',views.dashbord , name="dashbord"),
    path('user/',views.user_list , name="user_list"),
    path('add_product/', views.add_product, name='add_product'),
    path('products/', views.product_list, name='product_list'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('deactivate_product/<int:product_id>/', views.deactivate_product, name='deactivate_product'),  
    path('activate_product/<int:product_id>/', views.activate_product, name='activate_product'),
    path('block_user/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock_user/<int:user_id>/', views.unblock_user, name='unblock_user'), 
    path('category/' , views.category_list , name="category_list"),
    path('add_category/', views.add_category, name='add_category'),
    path('edit_category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('activate_category/<int:category_id>/', views.activate_category, name='activate_category'),
    path('deactivate_category/<int:category_id>/', views.deactivate_category, name='deactivate_category'),
    path('order-management/', views.order_management, name='order_management'),
    path('change_order_status/<int:order_id>/', views.change_order_status, name='change_order_status'),
    path('order_details/<int:order_id>/', views.order_details, name='order_details'),
    path('add_variants/<int:product_id>/', views.add_variants, name='add_variants'),
    path('sales-report/', views.sales_report, name='sales_report'),
    path('sales-report/pdf/', views.generate_pdf, name='generate_pdf'),
    path('sales-report/excel/', views.generate_excel, name='generate_excel'),
    path('admin/offer/', views.OfferAdminView.as_view(), name='offer_admin'),
    path('delete_offer/', views.delete_offer, name='delete_offer'),
    path('logout/', views.logout_view, name='logout'),

]

urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)