# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum  # Added Sum
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
import json
from urllib.parse import quote
import re  # Added for WhatsApp number formatting
from .decorators import role_required, buyer_required, seller_required, admin_required

from .forms import (
    SignupForm, ProductForm, ProfileForm, ReviewForm, 
    ExpressInterestForm, SearchForm, MessageForm, ReportForm,
    OrderStatusForm, OrderFilterForm
)
from .models import (
    Profile, Product, ProductImage, Category, Order, 
    WhatsAppContact, Review, Wishlist, SearchHistory,
    Notification, Conversation, Message, Report, Analytics
)

# ==================== AUTHENTICATION VIEWS ====================

def registerUser(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            
            if role not in ['buyer', 'seller']:
                form.add_error('role', 'Invalid role')
                return render(request, 'marketApp/register_form.html', {'form': form})
            
            user = form.save()
            Profile.objects.create(
                user=user, 
                role=role,
                phone_number=form.cleaned_data.get('phone_number', ''),
                location=form.cleaned_data.get('location', '')
            )  
            
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome, {user.username}!')
            
            if role == 'buyer':
                return redirect('buyer_home')
            else:
                return redirect('seller_home')
    else:
        form = SignupForm()
    return render(request, 'marketApp/register_form.html', {'form': form})

def loginUser(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            try:
                role = user.profile.role
                
                if role == 'buyer':
                    return redirect('buyer_home')
                elif role == 'seller':
                    return redirect('seller_home')
                else:
                    return redirect('home')
            except Profile.DoesNotExist:
                # Create profile if it doesn't exist
                Profile.objects.create(user=user, role='buyer')
                return redirect('home')
        else:
            return render(request, 'marketApp/login_form.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'marketApp/login_form.html')

def logoutUser(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')

# ==================== PUBLIC VIEWS ====================

def home(request):
    # Featured products
    featured_products = Product.objects.filter(
        status='active', 
        is_featured=True
    ).order_by('-created_at')[:8]
    
    # New arrivals
    new_products = Product.objects.filter(
        status='active'
    ).order_by('-created_at')[:8]
    
    # Popular categories
    popular_categories = Category.objects.filter(
        is_featured=True
    )[:6]
    
    context = {
        'featured_products': featured_products,
        'new_products': new_products,
        'popular_categories': popular_categories,
    }
    return render(request, 'marketApp/home.html', context)

def about(request):
    context = {}
    return render(request, 'marketApp/about.html', context)
@login_required
def shop(request):
    # Get filter parameters
    category_id = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search_query = request.GET.get('q', '')
    condition = request.GET.get('condition')
    location = request.GET.get('location')
    is_negotiable = request.GET.get('negotiable') == 'true'
    sort_by = request.GET.get('sort', '-created_at')
    
    products = Product.objects.filter(status='active')
    
    # Apply filters
    if category_id:
        products = products.filter(category_id=category_id)
    
    if min_price:
        products = products.filter(price__gte=min_price)
    
    if max_price:
        products = products.filter(price__lte=max_price)
    
    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__icontains=search_query)
        )
    
    if condition:
        products = products.filter(condition=condition)
    
    if location:
        products = products.filter(location__icontains=location)
    
    if is_negotiable:
        products = products.filter(is_negotiable=True)
    
    # Get sort parameter
    if sort_by in ['price', '-price', '-created_at', '-views', 'title', '-title']:
        products = products.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user's wishlist product IDs
    user_wishlist_ids = []
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        if request.user.profile.role == 'buyer':
            user_wishlist_ids = list(Wishlist.objects.filter(
                user=request.user
            ).values_list('product_id', flat=True))
    
    # Check if any filter is active
    any_filter_active = any([
        search_query, category_id, min_price, max_price, 
        condition, location, is_negotiable, sort_by != '-created_at'
    ])
    
    # Get categories for dropdown
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'selected_condition': condition,
        'selected_location': location,
        'is_negotiable': is_negotiable,
        'sort_by': sort_by,
        'any_filter_active': any_filter_active,
        'user_wishlist_ids': user_wishlist_ids,
    }
    return render(request, 'marketApp/shop.html', context)
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Increment view count
    product.increment_views()
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        status='active'
    ).exclude(pk=product.pk)[:4]
    
    # Get seller's other products
    seller_products = Product.objects.filter(
        seller=product.seller,
        status='active'
    ).exclude(pk=product.pk)[:4]
    
    # Get reviews for this product
    reviews = Review.objects.filter(product=product)[:10]
    
    # Check if product is in user's wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists()
    
    context = {
        'product': product,
        'related_products': related_products,
        'seller_products': seller_products,
        'reviews': reviews,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'marketApp/product_detail.html', context)

def category_products(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    products = Product.objects.filter(
        category=category,
        status='active'
    ).order_by('-created_at')
    
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'marketApp/category_products.html', context)

# ==================== BUYER VIEWS ====================

@login_required
@role_required(allowed_roles=['buyer'])

def buyer_home(request):
    # Order statistics
    orders = Order.objects.filter(buyer=request.user)
    total_orders = orders.count()
    
    # Count orders by status
    interested_orders = orders.filter(status='interested').count()
    contacted_orders = orders.filter(status='contacted').count()
    confirmed_orders = orders.filter(status='confirmed').count()
    completed_orders = orders.filter(status='completed').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    
    # Pending orders (all statuses except completed and cancelled)
    pending_orders = orders.exclude(status__in=['completed', 'cancelled']).count()
    
    # Wishlist count
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    
    # Notification count
    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    # Unread messages count (if you have a Message model)
    unread_messages = 0  # Set to 0 for now or implement if you have messaging
    # If you have a Message model, you can do:
    # unread_messages = Message.objects.filter(
    #     recipient=request.user,
    #     is_read=False
    # ).count()
    
    # Recent orders (last 5)
    recent_orders = orders.order_by('-created_at')[:5]
    
    # Recent wishlist items (last 4)
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).order_by('-added_at')[:4]
    
    # Recent notifications (last 5)
    recent_notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Recommended products (you can implement your own logic here)
    recommended_products = Product.objects.filter(
        status='active'
    ).order_by('-views', '-created_at')[:6]
    
    # Current date
    from django.utils.timezone import now
    current_date = now()
    
    context = {
        # Order counts
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'interested_orders': interested_orders,
        'contacted_orders': contacted_orders,  # Added this
        'confirmed_orders': confirmed_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,  # Added this
        
        # Other counts
        'wishlist_count': wishlist_count,
        'unread_notifications': unread_notifications,
        'unread_messages': unread_messages,
        
        # Recent items
        'recent_orders': recent_orders,
        'wishlist_items': wishlist_items,
        'recent_notifications': recent_notifications,
        'recommended_products': recommended_products,
        'current_date': current_date,
    }
    return render(request, 'marketApp/buyer_home.html', context)


@login_required
@role_required(allowed_roles=['buyer'])
def express_interest(request, product_id):
    product = get_object_or_404(Product, pk=product_id, status='active')
    
    if request.method == 'POST':
        message = request.POST.get('message', '')
        contact_number = request.POST.get('contact_number', '')
        
        # Create order/interest
        order = Order.objects.create(
            buyer=request.user,
            product=product,
            seller=product.seller,
            message=message,
            buyer_contact=contact_number or request.user.profile.phone_number,
            status='interested'
        )
        
        # Create notification for seller
        Notification.objects.create(
            user=product.seller,
            notification_type='order',
            title='New Interest in Your Product',
            message=f"{request.user.username} is interested in your product: {product.title}",
            related_object_id=order.id
        )
        
        messages.success(request, 'Interest expressed successfully! The seller will contact you soon.')
        return redirect('order_detail', order_id=order.id)
    
    context = {
        'product': product,
    }
    return render(request, 'marketApp/express_interest.html', context)

@login_required
@role_required(allowed_roles=['buyer'])
def contact_via_whatsapp(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    # Use phone_number instead of whatsapp_number
    if not product.seller.profile.phone_number:
        messages.error(request, 'Seller has not provided a contact number.')
        return redirect('product_detail', pk=product_id)
    
    # Create WhatsApp contact record
    WhatsAppContact.objects.create(
        buyer=request.user,
        seller=product.seller,
        product=product
    )
    
    # Clean and format the phone number for WhatsApp
    phone_number = product.seller.profile.phone_number.strip()
    
    # Remove any non-digit characters except plus sign
    phone_number = re.sub(r'[^\d+]', '', phone_number)
    
    # Add country code if missing (assuming Kenya +254)
    if not phone_number.startswith('+'):
        if phone_number.startswith('0'):
            phone_number = '+254' + phone_number[1:]
        elif phone_number.startswith('7'):
            phone_number = '+254' + phone_number
        elif phone_number.startswith('254'):
            phone_number = '+' + phone_number
        else:
            # If it doesn't start with 0, 7, or 254, assume it's already international
            phone_number = '+' + phone_number
    
    default_message = f"Hello! I'm interested in your product: {product.title} (Price: Ksh {product.price})"
    encoded_message = quote(default_message)
    whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
    
    # Log for debugging
    print(f"DEBUG: Original phone: {product.seller.profile.phone_number}")
    print(f"DEBUG: Formatted for WhatsApp: {phone_number}")
    print(f"DEBUG: WhatsApp URL: {whatsapp_url}")
    
    return redirect(whatsapp_url)

@login_required
@role_required(allowed_roles=['buyer'])
def my_orders(request):
    # Get filter parameters
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    
    # Apply filters
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(product__title__icontains=search_query) |
            Q(product__description__icontains=search_query) |
            Q(seller__username__icontains=search_query)
        )
    
    # Get counts for each status
    total_count = Order.objects.filter(buyer=request.user).count()
    interested_count = Order.objects.filter(buyer=request.user, status='interested').count()
    contacted_count = Order.objects.filter(buyer=request.user, status='contacted').count()
    confirmed_count = Order.objects.filter(buyer=request.user, status='confirmed').count()
    completed_count = Order.objects.filter(buyer=request.user, status='completed').count()
    cancelled_count = Order.objects.filter(buyer=request.user, status='cancelled').count()
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_orders': total_count,
        'interested_count': interested_count,
        'contacted_count': contacted_count,
        'confirmed_count': confirmed_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
    }
    return render(request, 'marketApp/my_orders.html', context)
@login_required
@role_required(allowed_roles=['buyer'])
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id, buyer=request.user)
    context = {
        'order': order,
    }
    return render(request, 'marketApp/order_detail.html', context)

@login_required
@role_required(allowed_roles=['buyer'])
def my_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).order_by('-added_at')
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'marketApp/my_wishlist.html', context)

@require_POST
@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if not created:
        wishlist_item.delete()
        return JsonResponse({'added': False, 'message': 'Removed from wishlist'})
    
    return JsonResponse({'added': True, 'message': 'Added to wishlist'})

@login_required
@role_required(allowed_roles=['buyer'])
def leave_review(request, order_id):
    order = get_object_or_404(Order, pk=order_id, buyer=request.user, status='completed')
    
    # Check if review already exists
    existing_review = Review.objects.filter(
        reviewer=request.user,
        seller=order.seller,
        product=order.product
    ).first()
    
    if request.method == 'POST':
        if existing_review:
            form = ReviewForm(request.POST, instance=existing_review)
        else:
            form = ReviewForm(request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.seller = order.seller
            review.product = order.product
            review.order = order
            review.is_verified_purchase = True
            review.save()
            
            messages.success(request, 'Review submitted successfully!')
            return redirect('order_detail', order_id=order_id)
    else:
        if existing_review:
            form = ReviewForm(instance=existing_review)
        else:
            form = ReviewForm()
    
    context = {
        'form': form,
        'order': order,
        'existing_review': existing_review,
    }
    return render(request, 'marketApp/leave_review.html', context)

# ==================== SELLER VIEWS ====================

@login_required
@role_required(allowed_roles=['seller'])
def seller_home(request):
    # Get seller's statistics
    total_products = Product.objects.filter(seller=request.user).count()
    active_products = Product.objects.filter(seller=request.user, status='active').count()
    total_orders = Order.objects.filter(seller=request.user).count()
    pending_orders = Order.objects.filter(seller=request.user, status='interested').count()
    
    # Recent orders
    recent_orders = Order.objects.filter(seller=request.user).order_by('-created_at')[:5]
    
    # Recent notifications (last 3)
    recent_notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:3]
    
    # Unread notifications count
    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    context = {
        'total_products': total_products,
        'active_products': active_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'recent_notifications': recent_notifications,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'marketApp/seller_home.html', context)

@login_required
@role_required(allowed_roles=['seller'])
def seller_products(request):
    products = Product.objects.filter(seller=request.user).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        products = products.filter(status=status_filter)
    
    # Get counts for tabs
    total_count = Product.objects.filter(seller=request.user).count()
    active_count = Product.objects.filter(seller=request.user, status='active').count()
    sold_count = Product.objects.filter(seller=request.user, status='sold').count()
    inactive_count = Product.objects.filter(seller=request.user, status='inactive').count()
    
    context = {
        'products': products,
        'status_filter': status_filter,
        'total_count': total_count,
        'active_count': active_count,
        'sold_count': sold_count,
        'inactive_count': inactive_count,
    }
    return render(request, 'marketApp/seller_products.html', context)

@login_required
@role_required(allowed_roles=['seller'])
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            
            # Debug: Print uploaded files
            print("FILES received:", request.FILES)
            images = request.FILES.getlist('images')
            print(f"Number of images: {len(images)}")
            
            # Handle multiple images
            for i, image in enumerate(images):
                print(f"Saving image {i+1}: {image.name}, size: {image.size}")
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=(i == 0)
                )
            
            messages.success(request, 'Product added successfully!')
            return redirect('seller_products')
        else:
            print("Form errors:", form.errors)
    else:
        form = ProductForm()
    
    categories = Category.objects.all()
    
    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'marketApp/add_product.html', context)

@login_required
@role_required(allowed_roles=['seller'])
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id, seller=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            
            # Handle image updates
            images = request.FILES.getlist('images')
            for image in images:
                ProductImage.objects.create(
                    product=product,
                    image=image
                )
            
            messages.success(request, 'Product updated successfully!')
            return redirect('seller_products')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'marketApp/edit_product.html', context)

@require_POST
@login_required
@role_required(allowed_roles=['seller'])
def delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id, seller=request.user)
    product.delete()
    messages.success(request, 'Product deleted successfully!')
    return redirect('seller_products')

@login_required
@role_required(allowed_roles=['seller'])
def seller_orders(request):
    orders = Order.objects.filter(seller=request.user).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
    }
    return render(request, 'marketApp/seller_orders.html', context)

@login_required
@role_required(allowed_roles=['seller'])
def update_order_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id, seller=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status in dict(Order.STATUS_CHOICES).keys():
            old_status = order.status
            order.status = new_status
            order.notes = notes
            order.save()
            
            # Create notification for buyer
            Notification.objects.create(
                user=order.buyer,
                notification_type='order',
                title='Order Status Updated',
                message=f"Your order #{order.order_number} status changed from {old_status} to {new_status}",
                related_object_id=order.id
            )
            
            messages.success(request, f'Order status updated to {new_status}.')
    
    return redirect('seller_orders')

@login_required
@role_required(allowed_roles=['seller'])
def seller_reviews(request):
    reviews = Review.objects.filter(seller=request.user).order_by('-created_at')
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'reviews': reviews,
        'avg_rating': avg_rating,
        'total_reviews': reviews.count(),
    }
    return render(request, 'marketApp/seller_reviews.html', context)

@login_required
@role_required(allowed_roles=['seller'])
def seller_analytics(request):
    # You would typically implement more complex analytics here
    # This is a basic implementation
    
    # Fix: Use Sum instead of models.Sum
    context = {
        'total_sales': Order.objects.filter(seller=request.user, status='completed').count(),
        'total_revenue': Order.objects.filter(
            seller=request.user, 
            status='completed'
        ).aggregate(Sum('agreed_price'))['agreed_price__sum'] or 0,
        'total_views': Product.objects.filter(
            seller=request.user
        ).aggregate(Sum('views'))['views__sum'] or 0,
    }
    return render(request, 'marketApp/seller_analytics.html', context)

# ==================== PROFILE VIEWS ====================

@login_required
def profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'marketApp/profile.html', context)

@login_required
def view_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    
    # Get user's products if they are a seller
    products = None
    if profile.role == 'seller':
        products = Product.objects.filter(
            seller=user,
            status='active'
        ).order_by('-created_at')[:6]
    
    # Get user's reviews
    reviews = Review.objects.filter(seller=user).order_by('-created_at')[:5]
    
    context = {
        'viewed_user': user,
        'viewed_profile': profile,
        'products': products,
        'reviews': reviews,
    }
    return render(request, 'marketApp/view_profile.html', context)

# ==================== NOTIFICATION VIEWS ====================

@login_required
def notifications(request):
    # Get filter parameter
    active_tab = request.GET.get('tab', 'all')
    
    # Base queryset
    notifications_qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Apply filters
    if active_tab == 'unread':
        notifications_qs = notifications_qs.filter(is_read=False)
    elif active_tab == 'orders':
        notifications_qs = notifications_qs.filter(notification_type='order')
    elif active_tab == 'messages':
        notifications_qs = notifications_qs.filter(notification_type='message')
    elif active_tab == 'system':
        notifications_qs = notifications_qs.filter(notification_type='system')
    
    # Counts for tabs
    total_count = Notification.objects.filter(user=request.user).count()
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    order_count = Notification.objects.filter(user=request.user, notification_type='order').count()
    message_count = Notification.objects.filter(user=request.user, notification_type='message').count()
    system_count = Notification.objects.filter(user=request.user, notification_type='system').count()
    
    # Pagination
    paginator = Paginator(notifications_qs, 20)
    page_number = request.GET.get('page')
    notifications_page = paginator.get_page(page_number)
    
    context = {
        'notifications': notifications_page,
        'active_tab': active_tab,
        'total_count': total_count,
        'unread_count': unread_count,
        'order_count': order_count,
        'message_count': message_count,
        'system_count': system_count,
    }
    return render(request, 'marketApp/notifications.html', context)

@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications')

@login_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    messages.success(request, 'Notification deleted.')
    return redirect('notifications')

@login_required
def clear_notifications(request):
    Notification.objects.filter(user=request.user).delete()
    messages.success(request, 'All notifications cleared.')
    return redirect('notifications')

@login_required
def check_notifications(request):
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': unread_count})

@require_POST
@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})

# ==================== MESSAGING VIEWS ====================

@login_required
def messages_list(request):
    conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'marketApp/messages_list.html', context)

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id, participants=request.user)
    
    # Mark all messages as read
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            conversation.save()  # Update updated_at
            return redirect('conversation_detail', conversation_id=conversation_id)
    
    context = {
        'conversation': conversation,
        'other_user': conversation.get_other_participant(request.user),
    }
    return render(request, 'marketApp/conversation_detail.html', context)

@login_required
def start_conversation(request, user_id):
    other_user = get_object_or_404(User, pk=user_id)
    
    # Check if conversation already exists
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    return redirect('conversation_detail', conversation_id=conversation.id)

# ==================== REPORT VIEWS ====================

@login_required
def report_content(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        reason = request.POST.get('reason')
        description = request.POST.get('description')
        
        report = Report.objects.create(
            reporter=request.user,
            report_type=report_type,
            reason=reason,
            description=description
        )
        
        # Set the appropriate foreign key based on report type
        if report_type == 'product':
            product_id = request.POST.get('product_id')
            if product_id:
                report.reported_product = get_object_or_404(Product, pk=product_id)
        elif report_type == 'user':
            user_id = request.POST.get('user_id')
            if user_id:
                report.reported_user = get_object_or_404(User, pk=user_id)
        elif report_type == 'review':
            review_id = request.POST.get('review_id')
            if review_id:
                report.reported_review = get_object_or_404(Review, pk=review_id)
        
        report.save()
        messages.success(request, 'Report submitted successfully. Our team will review it.')
        return redirect('home')
    
    return render(request, 'marketApp/report_content.html')

# ==================== API VIEWS ====================

@require_POST
@login_required
def api_toggle_wishlist(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        product = get_object_or_404(Product, pk=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            wishlist_item.delete()
            return JsonResponse({
                'success': True,
                'added': False,
                'message': 'Removed from wishlist'
            })
        
        return JsonResponse({
            'success': True,
            'added': True,
            'message': 'Added to wishlist'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
def api_notifications_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

# ==================== ADMIN VIEWS ====================

@login_required
@role_required(allowed_roles=['admin'])
def admin_dashboard(request):
    # Admin statistics
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    pending_reports = Report.objects.filter(status='pending').count()
    
    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_reports': pending_reports,
    }
    return render(request, 'marketApp/admin_dashboard.html', context)

@login_required
@role_required(allowed_roles=['admin'])
def admin_reports(request):
    reports = Report.objects.all().order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    context = {
        'reports': reports,
        'status_filter': status_filter,
    }
    return render(request, 'marketApp/admin_reports.html', context)

@login_required
@role_required(allowed_roles=['admin'])
def admin_update_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')
        
        if status in dict(Report.STATUS_CHOICES).keys():
            report.status = status
            report.admin_notes = admin_notes
            report.save()
            
            messages.success(request, f'Report #{report.id} updated to {status}.')
    
    return redirect('admin_reports')
@require_POST
@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})
@login_required
@require_POST
def update_notification_preferences(request):
    """Update user's notification preferences"""
    # This is a simple implementation - you might want to store these in user's profile
    # or create a NotificationPreference model
    
    # Get form data
    order_notifications = request.POST.get('order_notifications') == 'on'
    message_notifications = request.POST.get('message_notifications') == 'on'
    review_notifications = request.POST.get('review_notifications') == 'on'
    system_notifications = request.POST.get('system_notifications') == 'on'
    
    # Here you would save these preferences to the database
    # For now, we'll just show a success message
    messages.success(request, 'Notification preferences updated successfully!')
    
    return redirect('notifications')

