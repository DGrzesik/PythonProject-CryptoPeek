from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

sort_types = (
    ("Default", "Default"),
    ("A-Z", "A-Z"),
    ("Z-A", "Z-A"),
    ("ArrowUp", "Price ↑"),
    ("ArrowDown", "Price ↓"),
    ("ArrowUpMC", "Market Cap ↑"),
    ("ArrowDownMC", "Market Cap ↓"),
    ("ArrowUpPC", "Price Change ↑"),
    ("ArrowDownPC", "Prince Change ↓")
)


class CryptoListForm(forms.Form):
    name = forms.CharField(label="Name:",widget=forms.TextInput(attrs={'placeholder': 'Search by name...'}), required=False)
    from_price = forms.FloatField(label='Beginning price:',widget=forms.TextInput(attrs={'placeholder': 'Lowest value...'}), required=False)
    to_price = forms.FloatField(label="Highest price:",widget=forms.TextInput(attrs={'placeholder': 'Highest value...'}), required=False)
    sort = forms.ChoiceField(label="Sort:", choices=sort_types, required=False)


class GraphForm(forms.Form):
    date_from = forms.DateField(widget=forms.TextInput(attrs={'placeholder': 'Beginning date(rrrr-mm-dd)'}),
                                required=False)
    date_to = forms.DateField(widget=forms.TextInput(attrs={'placeholder': 'Ending date(rrrr-mm-dd)'}), required=False)

class SignInForm(forms.Form):
    username=forms.CharField(label="Username:")
    password=forms.CharField(label="Password:",widget=forms.PasswordInput)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user or not user.is_active:
            raise forms.ValidationError("Invalid username or password.")
        return self.cleaned_data

    def login(self, request):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        return user


class SignUpForm(UserCreationForm):
    first_name=forms.CharField(label='Name:')
    last_name=forms.CharField(label="Surname:")
    email=forms.EmailField(label="Email:")
    class Meta:
        model = User
        fields = ('username','first_name','last_name','email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None