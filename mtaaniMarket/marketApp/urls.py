# marketApp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('shop/', views.shop, name='shop'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    
    # Authentication
    path('login/', views.loginUser, name='login'),
    path('register/', views.registerUser, name='register'),
    path('logout/', views.logoutUser, name='logout'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.view_profile, name='view_profile'),
    
    # Buyer pages
    path('buyer/home/', views.buyer_home, name='buyer_home'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('my-wishlist/', views.my_wishlist, name='my_wishlist'),
    path('express-interest/<int:product_id>/', views.express_interest, name='express_interest'),
    path('leave-review/<int:order_id>/', views.leave_review, name='leave_review'),
    path('contact-whatsapp/<int:product_id>/', views.contact_via_whatsapp, name='contact_via_whatsapp'),
    
    # Seller pages
    path('seller/home/', views.seller_home, name='seller_home'),
    path('seller/products/', views.seller_products, name='seller_products'),
    path('seller/orders/', views.seller_orders, name='seller_orders'),
    path('seller/reviews/', views.seller_reviews, name='seller_reviews'),
    path('seller/analytics/', views.seller_analytics, name='seller_analytics'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    
    # Messaging
    path('messages/', views.messages_list, name='messages_list'),
    path('messages/conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('messages/start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('notifications/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('notifications/clear/', views.clear_notifications, name='clear_notifications'),
    path('check-notifications/', views.check_notifications, name='check_notifications'),
    path('api/mark-notification-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),

# To this:
path('api/mark-notification-read/<int:notification_id>/', views.mark_as_read, name='mark_notification_read'),

    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('admin/report/<int:report_id>/', views.admin_update_report, name='admin_update_report'),
    
    # Reports
    path('report/', views.report_content, name='report_content'),
    
    # API endpoints
    path('api/toggle-wishlist/', views.api_toggle_wishlist, name='api_toggle_wishlist'),
    path('api/notifications-count/', views.api_notifications_count, name='api_notifications_count'),
    path('toggle-wishlist/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    
    # Add this missing notification URL (using existing view)
    path('mark-as-read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
]