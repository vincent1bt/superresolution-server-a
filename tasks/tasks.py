from django.forms.models import model_to_dict

from celery import shared_task
from tasks.models import SRSpotServer, SRTask

from pathlib import Path
from datetime import datetime, timedelta
import os
import io

from superresolution import celery_app

from .utils import (
    upload_zip_images, 
    create_gcloud_vm, 
    delete_gcloud_vm
)

parent_file = Path(__file__).resolve().parent

"""
Local Tasks
"""

@shared_task
def upload_files_task(zip_id):
    zip_location = f"{parent_file}/temp_zip_files/{zip_id}.zip"

    with open(zip_location, 'rb') as zip_data:
        zip_images = io.BytesIO(zip_data.read())
        url = upload_zip_images(zip_images, zip_id)

    os.remove(zip_location)

    return url

@shared_task
def create_new_server_task(server_name):
    """
    Creates a new Google Cloud Virtual machine using the
    Python API
    """
    response = create_gcloud_vm(server_name)

    # Handle errors, status, logging

    print(response)

@shared_task
def check_server_status_task(server_name):
    last_server = SRSpotServer.get(name=server_name)

    # Use GoogleCloud API to check server status

@shared_task
def get_server_information_task(email, zip_id):
    server_available, task, server_name = SRSpotServer.get_server_information(email, zip_id)

    if task:
        task = model_to_dict(task, fields=["id", "zip_id"])

    return server_available, task, server_name

@shared_task
def send_task_to_server(args):
    url, server_info = args
    server_available, task, server_name = server_info

    if server_available and task:
        celery_app.send_task('remote.run_sr_task', [task.get("id"), task.get("zip_id")], queue='images')

    elif not server_available:
        response = create_gcloud_vm(server_name)
        # Handle errors, status, logging

@shared_task
def keep_or_kill_server_task(task_id):
    last_task = SRTask.objects.latest('created_at')

    if last_task.id == task_id:
        # after 25 minutes no new tasks arrived
        names = SRSpotServer.kill_server_by_application()

        for name in names:
            response = delete_gcloud_vm(name)

            # Log the execution + server deleted 
"""
Remote Tasks
"""

@shared_task
def remote_server_ready(name):
    """
    Called when remote server is done
    """
    # task has to wait until we add a new task from the request
    server_name = SRSpotServer.update_server_status(SRSpotServer.SRSpotServerStatus.ON, name)

    # Log the execution + server_name

    pending_tasks = SRTask.objects.filter(status=SRTask.SRTaskStatus.INCOMPLETE).only("id", "zip_id")

    for task in pending_tasks:
        celery_app.send_task('remote.run_sr_task', [task.id, task.zip_id], queue='images')
    
    pending_tasks.update(status=SRTask.SRTaskStatus.RUNNING)

    # Log the execution + tasks_added 

@shared_task
def remote_server_off(name):
    last_server_name, new_server_name = SRSpotServer.remote_server_down(name)

    if new_server_name:
        response = create_gcloud_vm(new_server_name)

        # Log the execution + new server created 
    response = delete_gcloud_vm(last_server_name)
    # Log the execution + server down

@shared_task
def task_finished(task_id):
    """
    Called when the remote server has processed the images from the task_id
    """
    current_task = SRTask.objects.get(id=task_id)
    current_task.status = SRTask.SRTaskStatus.DONE
    current_task.save(update_fields=['status'])

    pending_tasks = SRTask.objects.filter(status=SRTask.SRTaskStatus.RUNNING)

    # we have the last task of the queue
    if not pending_tasks.exists():
        to_time = datetime.utcnow() + timedelta(minutes=25)

        keep_or_kill_server_task.apply_async((task_id,), eta=to_time)