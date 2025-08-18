from django import forms
from .models import Profile
from .models import Post


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio']  # fields you want users to update

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'post_image']
        widgets = {
            'content': forms.Textarea(attrs={'rows':3, 'placeholder':'What’s on your mind?'}),
        }