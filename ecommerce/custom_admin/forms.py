from django import forms
from .models import Offer , Category
class TimePeriodForm(forms.Form):
    time_period_choices = [
        ('yearly', 'Yearly'),
        ('monthly', 'Monthly'),
        ('weekly', 'Weekly'),
    ]

    time_period = forms.ChoiceField(choices=time_period_choices, initial='yearly')
    
class ProductFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('all', 'All'),
        ('active', 'Active'),
        ('outofstock', 'Out of Stock'),
    ]

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    
    
class UserFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('all', 'All'),
        ('active', 'Active'),
        ('blocked', 'Blocked'),
    ]

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    
    
class OrderFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('all', 'All'),
        ('Accepted', 'Accepted'),
        ('Cancelled', 'Cancelled'),
        ('Placed', 'Placed'),
        ('Packed', 'Packed'),
        ('Shipped', 'Shipped'),
        ('Delevered', 'Delevered'),
    ]

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    
    
class OfferForm(forms.ModelForm):
    start_date = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.TextInput(attrs={'placeholder': 'Enter date (YYYY-MM-DD)'})
    )
    end_date = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.TextInput(attrs={'placeholder': 'Enter date (YYYY-MM-DD)'})
    )

    category = forms.ModelChoiceField(queryset=Category.objects.all(), empty_label="Select a category", required=False)

    class Meta:
        model = Offer
        fields = ['id', 'name', 'description', 'discount_amount', 'start_date', 'end_date', 'category']
        widgets = {
            'id': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].label_from_instance = lambda obj: obj.name