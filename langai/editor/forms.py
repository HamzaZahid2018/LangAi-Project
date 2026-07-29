from django import forms
from .models import Document
from .ai_engine import SUPPORTED_LANGUAGES
class DocumentForm(forms.ModelForm):
    class Meta:
        model  = Document
        fields = ['title', 'content', 'language']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'placeholder': 'Document Title...',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control custom-input',
                'rows': 8,
                'placeholder': 'Start Writing here...',
            }),
            'language': forms.Select(attrs={
                'class': 'form-select custom-input',
            }),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if len(content) < 10:
            raise forms.ValidationError("Content must be at least 10 characters.")
        if len(content) > 50000:
            raise forms.ValidationError("Content is too long (max 50,000 characters).")
        return content


class TextProcessForm(forms.Form):
    OPERATIONS = [
        ('grammar',    ' Grammar Check'),
        ('translate',  ' Translate'),
        ('plagiarism', ' Plagiarism Check'),
        ('summarize',  ' Summarize'),
    ]

    LANG_CHOICES = [('', '— Select Language —')] + list(SUPPORTED_LANGUAGES.items())
    SENTENCE_CHOICES = [(i, f'{i} sentences') for i in range(1, 9)]

    text = forms.CharField(
        widget=forms.Textarea(attrs={
            'id': 'mainTextarea',
            'class': 'form-control main-textarea',
            'placeholder': 'Type Or Paste Your Text Here... Or Use The Microphone ',
            'rows': 10,
        }),
        max_length=10000,
    )
    operation = forms.ChoiceField(
        choices=OPERATIONS,
        widget=forms.HiddenInput(attrs={'id': 'operationField'})
    )
    target_language = forms.ChoiceField(
        choices=LANG_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select custom-input',
            'id': 'targetLangSelect'
        })
    )
    sentences_count = forms.ChoiceField(
        choices=SENTENCE_CHOICES,
        required=False,
        initial=3,
        widget=forms.Select(attrs={
            'class': 'form-select custom-input',
            'id': 'sentencesCount'
        })
    )

    def clean(self):
        cleaned = super().clean()
        operation = cleaned.get('operation')
        text      = cleaned.get('text', '').strip()

        if not text:
            raise forms.ValidationError("Please enter some text.")

        if operation == 'translate':
            lang = cleaned.get('target_language')
            if not lang:
                raise forms.ValidationError("Please Select A Target Language for Translation.")

        return cleaned