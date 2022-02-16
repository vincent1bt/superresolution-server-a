from celery.canvas import group, chain
from django.shortcuts import redirect, render
from django.http import FileResponse

from django.contrib import messages

import uuid

from .models import SRTask

from .utils import download_zip_images, make_zip_images

from .tasks import (
    upload_files_task, 
    get_server_information_task, 
    send_task_to_server,
)

def index(request):
    if request.method == 'GET': return render(request, 'index.html')
    
    image_files = request.FILES.getlist('images')
    email = request.POST.get('email')

    zip_id = uuid.uuid4()

    make_zip_images(image_files, zip_id)
    
    chain(
        group(
            upload_files_task.s(zip_id),
            get_server_information_task.s(email, zip_id)
        ) |
        send_task_to_server.s()
    ).apply_async()

    messages.success(request, 'Your images are being processed, please wait some minutes')
    
    return redirect("tasks:download")

def download(request):
    if request.method == 'GET': return render(request, "download.html")
    email = request.POST.get("email")

    user_task = SRTask.objects.filter(email=email, status=SRTask.SRTaskStatus.DONE) # add for multiple task for the same email

    if not user_task.exists():
        messages.error(request, 'Your images are not ready yet')
        
        return render(request, "download.html")

    user_task = user_task.latest("created_at")

    name = f"done/{user_task.zip_id}.zip"
    storage_file = download_zip_images(name)

    zip_file = storage_file.file

    return FileResponse(
        zip_file, 
        filename="enhanced.zip", 
        as_attachment=True, 
        content_type='application/x-zip-compressed'
    )

