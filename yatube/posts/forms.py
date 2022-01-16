from django.forms import ModelForm, ValidationError
from .models import Post, Comment
from django.utils.translation import gettext_lazy as _
from django import forms


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image', 'rating']



def clean_text(self):
    data = self.cleaned_data['text']
    if data == '':
        raise ValidationError('Это поле обязательно для заполнения.')
    return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text',]
        labels = {'text': _('Текст'),
                  }
        help_texts = {'text': _('Ваш комментарий'),
                      }
