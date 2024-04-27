from django import forms
from .models import SubjectTable

class AcquiredSubjectForm(forms.ModelForm):
    class Meta:
        model = SubjectTable
        fields = []

    subjects = forms.ModelMultipleChoiceField(
        queryset=SubjectTable.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )