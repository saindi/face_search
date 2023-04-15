from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from face.forms import LoadPhotoForm
from face.models import FaceModel

from services import FaceCompare


class FaceSearchView(LoginRequiredMixin, View):
    """
        View for finding a face
    """
    def get(self, request):
        context = {"form": LoadPhotoForm()}
        return render(request, 'face/search.html', context)

    def post(self, request):
        form = LoadPhotoForm(request.POST, request.FILES)

        if form.is_valid():
            faces_on_upload_img = FaceCompare(form.img, FaceModel.objects.all()).compare()

            FaceModel.get_info_on_faces(faces_on_upload_img)

            context = {
                "faces": faces_on_upload_img,
            }

            return render(request, 'face/result.html', context)

        else:
            context = {"form": form}
            return render(request, 'face/search.html', context)
