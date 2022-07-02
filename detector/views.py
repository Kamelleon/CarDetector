import base64
import json

import django.utils.datastructures
from django.core.files import File
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
import cv2
import numpy as np
from django.views import View
from django.contrib import messages
from .forms import DetectionModelForm, UploadForm


class FileUploader(View):
    uploaded_image = None

    def get(self, request):
        form = UploadForm()
        context = {'form': form}
        return render(request, "detector/file_uploader.html", context)

    def post(self, request):
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            print("Form is valid")
            file = request.FILES["image"]
            numpy_converted_file = np.fromstring(file.read(), np.uint8)
            FileUploader.uploaded_image = numpy_converted_file
            return HttpResponse(json.dumps({"redirect_url":"/model/"}))
        else:
            print("Form invalid")
            messages.error(request,"Incorrect image-like file. Try again.")
            return HttpResponse(json.dumps({"redirect_url":"/"}))


class ModelChooser(View):
    selected_model = None

    def get(self, request):
        detection_model_form = DetectionModelForm()
        context = {
            "detection_model_form": detection_model_form
        }
        return render(request, "detector/model_chooser.html", context=context)

    def post(self, request):
        detection_model_form = DetectionModelForm(request.POST)
        if detection_model_form.is_valid():
            selected_model = detection_model_form.cleaned_data['model']
            from detector.models.manager import ModelManager
            model_manager = ModelManager(selected_model)
            try:
                rendered_image, number_of_detections = model_manager.perform_detection_on(FileUploader.uploaded_image)
            except Exception as e:
                messages.error(request, str(e))
                return redirect("detector:file-uploader")
            if model_manager.is_detection_successful:
                ImagePreviewer.rendered_image = rendered_image
                ImagePreviewer.number_of_detections = number_of_detections
                return redirect("detector:image-previewer")
            return redirect("detector:file-uploader")
        else:
            return redirect("detector:file-uploader")


class ImagePreviewer(View):
    rendered_image = None
    number_of_detections = 0

    def get(self, request):
        context = {
            "image": ImagePreviewer.rendered_image,
            "number_of_detections":ImagePreviewer.number_of_detections
        }
        return render(request, "detector/image_previewer.html", context=context)
