from django import forms

from .models import Strategy

class StrategyForm(forms.ModelForm):

    class Meta:
        model = Strategy
        fields = ('name', 'indicator1','indicator2','comparator')