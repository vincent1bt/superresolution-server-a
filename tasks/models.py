from django.db import models, transaction
from django.db.models.signals import pre_save
from django.db.models import Q

import uuid

class SRTask(models.Model):
    email = models.EmailField(blank=False, null=False)
    zip_id = models.CharField(max_length=40, blank=False, null=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class SRTaskStatus(models.TextChoices):
        INCOMPLETE = "INCOMPLETE"
        DONE = "DONE"
        RUNNING = "RUNNING"

    status = models.CharField(max_length=20, 
                              choices=SRTaskStatus.choices, 
                              default=SRTaskStatus.INCOMPLETE,
                              blank=False,
                              null=False)

    def __str__(self):
        return f"{self.id}-{self.status}"


"""
One default SRSpotServer record with SRSpotServerStatus = OFF is created in migrations so the
rows can be locked
"""

class SRSpotServer(models.Model):
    name = models.CharField(max_length=40, blank=False, null=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class SRSpotServerStatus(models.TextChoices):
        OFF = "OFF"
        ON = "ON"
        DEPLOYING = "DEPLOYING"

    status = models.CharField(max_length=20,
                              choices=SRSpotServerStatus.choices,
                              default=SRSpotServerStatus.DEPLOYING,
                              blank=False,
                              null=False)

    def __str__(self):
        return f"{self.id}-{self.status}"

    @classmethod
    def get_queryset(cls):
        return cls.objects
    
    """
    Locks record/row at database level.
    """

    @classmethod
    @transaction.atomic()
    def get_server_information(cls, email, zip_id):
        on_servers = cls.get_queryset().select_for_update().all()
        on_servers = list(on_servers.values_list('status', flat=True)) # Rows are locked here

        current_task = SRTask(email=email, zip_id=zip_id)

        if "ON" in on_servers: # at least one server is available
            current_task.status = SRTask.SRTaskStatus.RUNNING
            current_task.save()

            return True, current_task, None

        elif "DEPLOYING" in on_servers:
            current_task.save()

            return True, None, None
        
        current_task.save()
        # Not server available or deploying
        last_server = cls.objects.create()

        return False, None, last_server.name
        
    @classmethod
    @transaction.atomic()
    def update_server_status(cls, status, name):
        last_server = cls.get_queryset().select_for_update().filter(name=name).latest('created_at')

        # from DEPLOYING to ON
        last_server.status = status
        last_server.save(update_fields=['status'])

        return last_server.name
    
    @classmethod
    @transaction.atomic()
    def remote_server_down(cls, name):
        last_server = cls.get_queryset().select_for_update().filter(name=name).latest('created_at') # row is locked here

        # from ON to OFF
        last_server.status = SRSpotServer.SRSpotServerStatus.OFF
        last_server.save(update_fields=['status'])

        remain_servers = SRSpotServer.objects.filter(status=SRSpotServer.SRSpotServerStatus.ON)

        if remain_servers.exists():
            # if more workers/servers available they can consume the pending_tasks if any
            return last_server.name, None
        
        pending_tasks = SRTask.objects.filter(
            Q(status=SRTask.SRTaskStatus.INCOMPLETE) | Q(status=SRTask.SRTaskStatus.RUNNING)
        )

        if pending_tasks.exists():
            # if there are pending tasks and no servers/workers available we have to create a new server
            current_server = cls.objects.create()

            return last_server.name, current_server.name
    
    @classmethod
    @transaction.atomic()
    def kill_server_by_application(cls):
        servers = cls.get_queryset().select_for_update().filter(status=SRSpotServer.SRSpotServerStatus.ON)
    
        if servers.exists():
            servers_list = list(servers.values_list('name', flat=True))
            
            servers.update(status=SRSpotServer.SRSpotServerStatus.OFF)

            return servers_list
        
        return []   

def set_server_name(sender, instance, *args, **kwargs):
    if not instance.name:
        name = "a" + str(uuid.uuid4())[:20]

        while SRSpotServer.objects.filter(name=name).exists():
            name = "a" + str(uuid.uuid4())[:20]

        instance.name = name

pre_save.connect(set_server_name, sender=SRSpotServer)
