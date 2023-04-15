from django import forms


class LoadPhotoForm(forms.Form):
    """
        Photo upload form on the site
    """
    img = forms.ImageField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.img = None

    def clean_img(self):
        self.img = self.cleaned_data["img"]
        return self.img
