from django.conf import settings
    
def create_configuration(name):
    project_name = settings.GCP_PROJECT_NAME
    zone = settings.GCP_ZONE
    region = settings.GCP_REGION

    config = {
        'name': name,
        "canIpForward": False,
        "confidentialInstanceConfig": {
            "enableConfidentialCompute": False
        },
        "deletionProtection": False,
        "description": "",
        "disks": [
            {
            "autoDelete": True,
            "boot": True,
            "deviceName": name,
            "diskEncryptionKey": {},
            "initializeParams": {
                "diskSizeGb": "30",
                "diskType": f"projects/{project_name}/zones/{zone}/diskTypes/pd-balanced",
                "labels": {},
                "sourceImage": "projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20220118"
            },
            "mode": "READ_WRITE",
            "type": "PERSISTENT"
            }
        ],
        "displayDevice": {
            "enableDisplay": False
        },
        "guestAccelerators": [
            {
            "acceleratorCount": 1,
            "acceleratorType": f"projects/{project_name}/zones/{zone}/acceleratorTypes/nvidia-tesla-t4"
            }
        ],
        "labels": {},
        "machineType": f"projects/{project_name}/zones/{zone}/machineTypes/n1-standard-1",
        "metadata": {
            "items": [
                {
                    "key": "shutdown-script",
                    "value": "#!/bin/bash\n  \nNAME=$(curl http://metadata.google.internal/computeMetadata/v1/instance/name -H \"Metadata-Flavor: Google\")\n\nsudo docker exec -it \\\n    tf_app \\\n    celery call tasks.tasks.remote_server_off \\\n    --queue=default -k '{\"name\": ${NAME}}'"
                },
                {
                    "key": "startup-script",
                    "value": "#!/bin/bash\n \nNAME=$(curl http://metadata.google.internal/computeMetadata/v1/instance/name -H \"Metadata-Flavor: Google\")\n\nsudo docker run \\\n    --gpus all \\\n    -e SERVER_NAME=${NAME} \\\n    --name tf_app tf:remote"
                }
            ]
        },
        "networkInterfaces": [
            {
            "accessConfigs": [
                {
                "name": "External NAT",
                "networkTier": "PREMIUM"
                }
            ],
            "subnetwork": f"projects/{project_name}/regions/{region}/subnetworks/default"
            }
        ],
        "reservationAffinity": {
            "consumeReservationType": "ANY_RESERVATION"
        },
        "scheduling": {
            "provisioningModel": "SPOT",
            "instanceTerminationAction": "DELETE",
            "onHostMaintenance": "TERMINATE",
            "automaticRestart": False,
        },
        "serviceAccounts": [
            {
            "email": settings.GCP_SERVICE_EMAIL,
            "scopes": [
                "https://www.googleapis.com/auth/cloud-platform"
            ]
            }
        ],
        "shieldedInstanceConfig": {
            "enableIntegrityMonitoring": True,
            "enableSecureBoot": False,
            "enableVtpm": True
        },
        "tags": {
            "items": []
        },
        "zone": f"projects/{project_name}/zones/{zone}"
    }

    return config