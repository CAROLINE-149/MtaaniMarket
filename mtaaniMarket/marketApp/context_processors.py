# marketApp/context_processors.py
from .models import Category

def categories_processor(request):
    """
    Makes categories available in all templates
    """
    return {
        'all_categories': Category.objects.all()
    }