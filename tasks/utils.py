import googleapiclient.discovery
from pathlib import Path
from time import sleep
import io

from django.conf import settings
from zipfile import ZipFile, ZipInfo

from superresolution.utils import google_storage as g_storage
from .gcloud_config import create_configuration

service = googleapiclient.discovery.build('compute', 'v1', credentials=settings.GS_CREDENTIALS)
project_name = settings.GCP_PROJECT_NAME
zone = settings.GCP_ZONE

parent_file = Path(__file__).resolve().parent

def make_zip_images(images, zip_id):
    archive = io.BytesIO()

    temp_location = f"{parent_file}/temp_zip_files/{zip_id}.zip"

    with ZipFile(archive, 'w') as zip_archive:
        for image_file in images:
            zip_entry_name = image_file.name
            zip_file = ZipInfo(zip_entry_name)

            zip_archive.writestr(zip_file, image_file.read())
        
    archive.seek(0)

    Path(temp_location).write_bytes(archive.getbuffer())

def download_zip_images(name):
    zip_file = g_storage.open(name)

    return zip_file

def upload_zip_images(zip_images, zip_id):
    target_path = f"/current/{zip_id}.zip"

    path = g_storage.save(target_path, zip_images)
    url = g_storage.url(path)
    
    return url

def create_gcloud_vm(name):
    config = create_configuration(name)

    request = service.instances().insert(
        project=project_name,
        zone=zone,
        body=config)
    
    operation = request.execute()

    while operation['status'] != 'DONE':
        sleep(3)
        operation = service.zoneOperations().wait(
            project=project_name,
            zone=zone,
            operation=operation['name']).execute()

    return operation

def delete_gcloud_vm(name):
    request = service.instances().delete(
        project=project_name,
        zone=zone,
        instance=name)
    
    operation = request.execute()

    while operation['status'] != 'DONE':
        sleep(3)
        operation = service.zoneOperations().wait(
            project=project_name,
            zone=zone,
            operation=operation['name']).execute()

    return operation