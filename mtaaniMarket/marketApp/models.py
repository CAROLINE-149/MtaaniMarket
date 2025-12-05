from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

class Profile(models.Model):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, 
                                 validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_ratings = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
    def update_rating(self, new_rating):
        """Update user rating when new review is added"""
        total_score = self.rating * self.total_ratings
        self.total_ratings += 1
        self.rating = (total_score + new_rating) / self.total_ratings
        self.save()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                               related_name='subcategories')
    icon = models.CharField(max_length=50, blank=True, null=True)  # For font-awesome icons
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_all_products_count(self):
        """Get total products in this category including subcategories"""
        count = self.products.count()
        for subcat in self.subcategories.all():
            count += subcat.get_all_products_count()
        return count

class Product(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('pending', 'Pending Sale'),
        ('inactive', 'Inactive'),
        ('draft', 'Draft'),
    )
    
    CONDITION_CHOICES = (
        ('new', 'Brand New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    )
    
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique_for_date='created_at')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, 
                                validators=[MinValueValidator(0)])
    original_price = models.DecimalField(max_digits=10, decimal_places=2, 
                                         null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, 
                                 null=True, related_name='products')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    brand = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    location = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    views = models.IntegerField(default=0)
    is_negotiable = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['price']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    
    def increment_views(self):
        """Increment product view count"""
        self.views += 1
        self.save(update_fields=['views'])
    
    def mark_as_sold(self):
        """Mark product as sold"""
        self.status = 'sold'
        self.save(update_fields=['status'])
    
    def is_available(self):
        """Check if product is available for purchase"""
        return self.status == 'active' and self.quantity > 0

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=200, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
           ordering = ['-is_primary', 'uploaded_at']
    
    def __str__(self):
        return f"Image for {self.product.title}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('interested', 'Interested'),
        ('contacted', 'Contacted'),
        ('negotiating', 'Negotiating'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    )
    
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    agreed_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='interested')
    message = models.TextField(blank=True, null=True)
    buyer_contact = models.CharField(max_length=20, blank=True, null=True)
    whatsapp_contacted = models.BooleanField(default=False)
    meeting_preference = models.CharField(max_length=50, blank=True, null=True)  # pickup/delivery/etc
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.product.title}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        if not self.agreed_price and self.product:
            self.agreed_price = self.product.price
        super().save(*args, **kwargs)
    
    def get_total_price(self):
        """Calculate total order price"""
        if self.agreed_price:
            return self.agreed_price * self.quantity
        return self.product.price * self.quantity

class WhatsAppContact(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='whatsapp_contacts_made')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='whatsapp_contacts_received')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='whatsapp_contacts')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='whatsapp_contacts')
    contact_time = models.DateTimeField(auto_now_add=True)
    message_sent = models.TextField(blank=True, null=True)
    is_responded = models.BooleanField(default=False)
    responded_at = models.DateTimeField(null=True, blank=True)
    response_time_seconds = models.IntegerField(null=True, blank=True)  # Time to response in seconds
    
    class Meta:
        ordering = ['-contact_time']
    
    def __str__(self):
        return f"{self.buyer.username} → {self.seller.username} - {self.product.title}"
    
    def calculate_response_time(self):
        """Calculate response time if responded"""
        if self.is_responded and self.responded_at:
            time_diff = self.responded_at - self.contact_time
            self.response_time_seconds = time_diff.total_seconds()
            self.save()

class Review(models.Model):
    RATING_CHOICES = (
        (1, '1 - Very Poor'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    )
    
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, 
                                related_name='reviews')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), 
                                                                    MaxValueValidator(5)])
    title = models.CharField(max_length=200, blank=True, null=True)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['reviewer', 'seller', 'product']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.reviewer.username} - {self.rating} stars"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update seller's rating when new review is added
        if is_new:
            self.seller.profile.update_rating(self.rating)
    
    def mark_helpful(self):
        """Mark review as helpful"""
        self.helpful_count += 1
        self.save(update_fields=['helpful_count'])
    
    def mark_not_helpful(self):
        """Mark review as not helpful"""
        self.not_helpful_count += 1
        self.save(update_fields=['not_helpful_count'])

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.user.username}'s wishlist - {self.product.title}"

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history', 
                             null=True, blank=True)
    query = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    filters = models.JSONField(default=dict, blank=True)  # Store filter criteria as JSON
    results_count = models.IntegerField(default=0)
    searched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Search Histories"
        ordering = ['-searched_at']
    
    def __str__(self):
        return f"{self.query} - {self.searched_at.strftime('%Y-%m-%d %H:%M')}"

class Notification(models.Model):
    TYPE_CHOICES = (
        ('new_order', 'New Order'),
        ('order_update', 'Order Status Update'),
        ('new_message', 'New Message'),
        ('new_review', 'New Review'),
        ('price_drop', 'Price Drop Alert'),
        ('wishlist_available', 'Wishlist Item Available'),
        ('system', 'System Notification'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_content_type = models.CharField(max_length=100, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save(update_fields=['is_read'])

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, 
                                related_name='conversations')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='conversations')
    last_message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='last_message_for')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        participants_names = ', '.join([user.username for user in self.participants.all()])
        return f"Conversation: {participants_names}"
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        return self.participants.exclude(id=user.id).first()

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

class Report(models.Model):
    TYPE_CHOICES = (
        ('product', 'Product'),
        ('user', 'User'),
        ('review', 'Review'),
        ('message', 'Message'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    report_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    reported_product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, 
                                      related_name='reports_received')
    reported_review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True)
    reason = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Report #{self.id} - {self.get_report_type_display()}"

class Analytics(models.Model):
    """Store analytics data for sellers"""
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    products_viewed = models.IntegerField(default=0)
    products_sold = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    new_followers = models.IntegerField(default=0)
    whatsapp_contacts = models.IntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['seller', 'date']
        verbose_name_plural = "Analytics"
    
    def __str__(self):
        return f"Analytics for {self.seller.username} - {self.date}"


from django.utils.text import slugify