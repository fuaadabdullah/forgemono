#!/bin/bash
#
# Create GCP VM for GoblinOS Assistant Backend
# Project: goblin-assistant-479511
#

set -euo pipefail

PROJECT_ID="goblin-assistant-479511"
ZONE="us-central1-a"
INSTANCE_NAME="goblin-assistant-backend"
MACHINE_TYPE="e2-medium"
BOOT_DISK_SIZE="30GB"
IMAGE_FAMILY="ubuntu-2204-lts"
IMAGE_PROJECT="ubuntu-os-cloud"

echo "🚀 Creating GCP VM for GoblinOS Assistant Backend"
echo ""
echo "Project:  ${PROJECT_ID}"
echo "Zone:     ${ZONE}"
echo "Instance: ${INSTANCE_NAME}"
echo "Type:     ${MACHINE_TYPE}"
echo ""

# Create the instance
gcloud compute instances create "${INSTANCE_NAME}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}" \
  --machine-type="${MACHINE_TYPE}" \
  --boot-disk-size="${BOOT_DISK_SIZE}" \
  --boot-disk-type=pd-standard \
  --image-family="${IMAGE_FAMILY}" \
  --image-project="${IMAGE_PROJECT}" \
  --tags=http-server,https-server,goblin-assistant \
  --metadata=enable-oslogin=true \
  --scopes=cloud-platform \
  --metadata-from-file=startup-script=<(cat << 'STARTUP_SCRIPT'
#!/bin/bash
# Startup script for GoblinOS Assistant Backend

set -x
exec > >(tee /var/log/startup-script.log)
exec 2>&1

echo "Starting GoblinOS Assistant setup..."

# Update system
apt-get update
apt-get upgrade -y

# Install dependencies
apt-get install -y \
  curl \
  wget \
  git \
  nginx \
  certbot \
  python3-certbot-nginx \
  docker.io \
  docker-compose \
  jq

# Enable Docker
systemctl enable docker
systemctl start docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu || true

# Create app directory
mkdir -p /opt/goblin-assistant
chown -R ubuntu:ubuntu /opt/goblin-assistant

echo "Startup script complete"
STARTUP_SCRIPT
)

echo ""
echo "✅ VM created successfully!"
echo ""
echo "Next steps:"
echo "1. Wait 2-3 minutes for VM to boot"
echo "2. SSH into the VM:"
echo "   gcloud compute ssh ${INSTANCE_NAME} --project=${PROJECT_ID} --zone=${ZONE}"
echo "3. Run the deployment script"
echo ""
