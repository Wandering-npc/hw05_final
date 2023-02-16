from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Форма для создания и редактирования постов."""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': ('Текст поста'),
            'group': ('Группа'),
        }
        help_texts = {
            'text': ('Текст вашего поста'),
            'group': ('Выберите группу для поста'),
        }

    def clean_subject(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError('Вы ничего не написали')
        return data
class CommentForm(forms.ModelForm):
    """Форма создания комментариев"""
    class Meta:
        model = Comment
        fields = ('text',)
