# marketApp/forms.py - CORRECTED VERSION
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Product, ProductImage, Category, Review, Order, Report

# Custom widget for multiple file uploads - ACTUALLY USE THIS
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class SignupForm(UserCreationForm):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, 
        required=True,
        widget=forms.RadioSelect
    )
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    location = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'phone_number', 'location']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

# CHOOSE ONE: Either use the custom multiple file field OR simple single image

# OPTION 1: With custom multiple file field (USE THIS ONE)
class ProductForm(forms.ModelForm):
    # Use the custom MultipleFileField
    images = MultipleFileField(
        required=False,
        label='Upload Images (Multiple)'
    )
    
    class Meta:
        model = Product
        fields = [
            'title', 'description', 'price', 'original_price', 
            'category', 'condition', 'brand', 'location', 
            'quantity', 'is_negotiable', 'is_featured'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['original_price'].required = False

# OPTION 2: Simple single image (COMMENT THIS OUT if using Option 1)
# class ProductForm(forms.ModelForm):
#     # Single image upload - simpler approach
#     image = forms.ImageField(
#         required=False,
#         label='Product Image'
#     )
    
#     class Meta:
#         model = Product
#         fields = [
#             'title', 'description', 'price', 'original_price', 
#             'category', 'condition', 'brand', 'location', 
#             'quantity', 'is_negotiable', 'is_featured'
#         ]
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 4}),
#             'condition': forms.Select(attrs={'class': 'form-control'}),
#             'category': forms.Select(attrs={'class': 'form-control'}),
#         }
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['category'].queryset = Category.objects.all()
#         self.fields['original_price'].required = False

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary']
        widgets = {
            'alt_text': forms.TextInput(attrs={'placeholder': 'Brief description of image'}),
        }

class ProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    
    class Meta:
        model = Profile
        fields = [
            'phone_number', 'whatsapp_number', 'location', 
            'profile_picture', 'bio'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+254 7XX XXX XXX'}),
            'whatsapp_number': forms.TextInput(attrs={'placeholder': '+254 7XX XXX XXX'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Update user fields if provided
        if self.user:
            username = self.cleaned_data.get('username')
            email = self.cleaned_data.get('email')
            
            if username and username != self.user.username:
                self.user.username = username
            if email and email != self.user.email:
                self.user.email = email
            self.user.save()
        
        if commit:
            profile.save()
        return profile

class ReviewForm(forms.ModelForm):
    RATING_CHOICES = (
        (1, '★☆☆☆☆ - Very Poor'),
        (2, '★★☆☆☆ - Poor'),
        (3, '★★★☆☆ - Average'),
        (4, '★★★★☆ - Good'),
        (5, '★★★★★ - Excellent'),
    )
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label='Rating'
    )
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Brief summary of your review'}),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['rating'].initial = 3

class ExpressInterestForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Tell the seller why you\'re interested in this product...'
        }),
        required=True,
        label='Message to Seller'
    )
    contact_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Your contact number (optional)'})
    )
    meeting_preference = forms.ChoiceField(
        choices=[
            ('pickup', 'I can pick up'),
            ('delivery', 'I need delivery'),
            ('meetup', 'We can meet somewhere'),
            ('not_sure', 'Not sure yet')
        ],
        required=False,
        label='Meeting Preference'
    )

class SearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search for products...',
            'class': 'form-control'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories'
    )
    min_price = forms.DecimalField(
        required=False,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'placeholder': 'Min price'})
    )
    max_price = forms.DecimalField(
        required=False,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'placeholder': 'Max price'})
    )
    condition = forms.ChoiceField(
        choices=[('', 'Any Condition')] + list(Product.CONDITION_CHOICES),
        required=False
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Location'})
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Newest First'),
            ('price', 'Price: Low to High'),
            ('-price', 'Price: High to Low'),
            ('-views', 'Most Viewed')
        ],
        required=False,
        initial='-created_at'
    )

class MessageForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Type your message here...',
            'class': 'form-control'
        }),
        required=True,
        label=''
    )

class ReportForm(forms.ModelForm):
    REPORT_TYPE_CHOICES = (
        ('product', 'Product'),
        ('user', 'User'),
        ('review', 'Review'),
        ('message', 'Message'),
        ('other', 'Other'),
    )
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    
    class Meta:
        model = Report
        fields = ['report_type', 'reason', 'description']
        widgets = {
            'reason': forms.TextInput(attrs={'placeholder': 'Brief reason for reporting...'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Please provide details about what you\'re reporting...'
            }),
        }

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add any additional notes...'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class OrderFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'All Status')] + list(Order.STATUS_CHOICES)
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    )