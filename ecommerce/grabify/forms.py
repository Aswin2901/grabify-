from django import forms
from .models import CustomUser , Address
from django.core.exceptions import ValidationError
import string , re

class SignupForm(forms.Form):
    fullname = forms.CharField(max_length=100)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        
        return cleaned_data
    

def validate_no_special_characters(value):
    special_characters = string.punctuation
    if any(char in special_characters for char in value):
        raise ValidationError("Fullname should not contain special characters.")
    if any(char.isdigit() for char in value):
        raise ValidationError("Fullname should not contain numbers.")

class UserProfileEditForm(forms.ModelForm):
    fullname = forms.CharField(validators=[validate_no_special_characters])

    class Meta:
        model = CustomUser
        fields = ['fullname']

    def clean_fullname(self):
        fullname = self.cleaned_data.get('fullname')
        validate_no_special_characters(fullname)  # Manually call the validator
        return fullname
    
class AddressForm(forms.Form):
    COUNTRY_CHOICES = [
        ('', '--- Please Select ---'),
        ('Aaland Islands', 'Aaland Islands'),
        ('Afghanistan', 'Afghanistan'),
        ('Albania', 'Albania'),
        ('India', 'India'),
    ]

    REGION_CHOICES = [
    ('', '--- Please Select ---'),
    ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'),
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chandigarh', 'Chandigarh'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'),
    ('Delhi', 'Delhi'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Lakshadweep', 'Lakshadweep'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Puducherry', 'Puducherry'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
]

    first_name = forms.CharField(label='First Name', max_length=100)
    last_name = forms.CharField(label='Last Name', max_length=100)
    email = forms.EmailField(label='E-Mail')
    telephone = forms.CharField(label='Telephone', max_length=20)
    company = forms.CharField(label='Company', required=False)
    address_1 = forms.CharField(label='Address', max_length=255)
    city = forms.CharField(label='City', max_length=100)
    postcode = forms.CharField(label='Post Code', max_length=20)
    country = forms.ChoiceField(label='Country', choices=COUNTRY_CHOICES)
    region = forms.ChoiceField(label='Region / State', choices=REGION_CHOICES)

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not re.match("^[a-zA-Z]*$", first_name):
            raise forms.ValidationError("First name should only contain letters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not re.match("^[a-zA-Z]*$", last_name):
            raise forms.ValidationError("Last name should only contain letters.")
        return last_name

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if not re.match("^\d{10}$", telephone):
            raise forms.ValidationError("Telephone must be a 10-digit number.")
        return telephone

    def clean_postcode(self):
        postcode = self.cleaned_data.get('postcode')
        if not re.match("^\d{6}$", postcode):
            raise forms.ValidationError("Postal code must be a 6-digit number.")
        return postcode

    def clean_email(self):
        email = self.cleaned_data.get('email')
        return email
    
class ChangePasswordForm(forms.Form):
    existing_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    
class AddFundsForm(forms.Form):
    amount = forms.DecimalField(label='Amount', min_value=0.01, max_digits=10, decimal_places=2)
