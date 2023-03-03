from django import forms
from .models import CartProduct


class CartProductForm(forms.ModelForm):
    class Meta:
        model = CartProduct
        fields = ["quantity"]
