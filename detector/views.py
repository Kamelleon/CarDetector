import json
from django.http import HttpResponse
from django.shortcuts import render, redirect
import numpy as np
from django.views import View
from django.contrib import messages
from .forms import DetectionModelForm, UploadForm
from detector.models.manager import ModelManager


class ImageUploader(View):
    uploaded_image = None

    def get(self, request):

        context = {
            'form': UploadForm()
        }

        return render(request, "detector/image_uploader.html", context)

    def post(self, request):
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            image = form.cleaned_data["image"]
            numpy_converted_file = np.fromstring(image.read(), np.uint8)
            ImageUploader.uploaded_image = numpy_converted_file
            return HttpResponse(json.dumps({"redirect_url": "/model/"}))  # For AJAX response
        else:
            messages.error(request, "Incorrect image-like file. Try again.")
            return HttpResponse(json.dumps({"redirect_url": "/"}))  # For AJAX response


class ModelChooser(View):
    selected_model = None

    def get(self, request):
        if ImageUploader.uploaded_image is not None:

            context = {
                "detection_model_form": DetectionModelForm()
            }

            return render(request, "detector/model_chooser.html", context=context)
        else:
            messages.error(request,"You need to upload an image first")
            return redirect("detector:image-uploader")

    def post(self, request):
        detection_model_form = DetectionModelForm(request.POST)

        if detection_model_form.is_valid():
            selected_model = detection_model_form.cleaned_data['model']
            model_manager = ModelManager(selected_model)

            try:
                rendered_image, number_of_detections = model_manager.perform_detection_on(ImageUploader.uploaded_image)
            except Exception:
                messages.error(request, "An error occured during detection. Check your image and try again.")
                return redirect("detector:image-uploader")

            ImagePreviewer.rendered_image = rendered_image
            ImagePreviewer.number_of_detections = number_of_detections
            return redirect("detector:image-previewer")
        else:
            messages.error(request, "Selected pretrained model doesn't exists. Try again.")
            return redirect("detector:image-uploader")


class ImagePreviewer(View):
    rendered_image = None
    number_of_detections = 0

    def get(self, request):
        if ImagePreviewer.rendered_image is not None:

            context = {
                "image": ImagePreviewer.rendered_image,
                "number_of_detections": ImagePreviewer.number_of_detections
            }
            return render(request, "detector/image_previewer.html", context=context)

        else:
            messages.error(request, "You need to upload an image first")
            return redirect("detector:image-uploader")
