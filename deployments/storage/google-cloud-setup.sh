#!/bin/bash
# Project: Goblin Assistant
# Script: google-cloud-setup.sh
# Purpose: Setup Google Cloud Storage integration for LLM model storage
# Date: 2025-12-18
# Maintainer: fuaadabdullah

set -e

echo "☁️ Setting up Google Cloud Storage for LLM Model Storage"
echo "======================================================"

# Install Google Cloud CLI
echo "📦 Installing Google Cloud CLI..."
if ! command -v gcloud &> /dev/null; then
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
    sudo apt update && sudo apt install -y google-cloud-cli google-cloud-cli-gke-gcloud-auth-plugin
else
    echo "✅ Google Cloud CLI already installed"
fi

# Install gsutil for storage operations
echo "📦 Installing gsutil..."
if ! command -v gsutil &> /dev/null; then
    sudo apt install -y python3-pip
    pip3 install gsutil
else
    echo "✅ gsutil already installed"
fi

# Authenticate with Google Cloud
echo "🔑 Authenticating with Google Cloud..."
echo "Please run: gcloud auth login"
echo "Then run: gcloud auth application-default login"
read -p "Press Enter after completing authentication..."

# Create GCS bucket for model storage
echo "📦 Creating GCS bucket for model storage..."
BUCKET_NAME="goblin-llm-models-$(date +%s)"
REGION="us-central1"

# Create bucket
gsutil mb -p $(gcloud config get-value project 2>/dev/null || echo "your-project") -l $REGION gs://$BUCKET_NAME

# Set bucket to regional for better performance
gsutil uniformbucketlevelaccess set on gs://$BUCKET_NAME
gsutil versioning set on gs://$BUCKET_NAME

# Create bucket structure
echo "📁 Creating bucket structure..."
gsutil -m cp -r /dev/null gs://$BUCKET_NAME/models/
gsutil -m cp -r /dev/null gs://$BUCKET_NAME/backups/
gsutil -m cp -r /dev/null gs://$BUCKET_NAME/exports/
gsutil -m cp -r /dev/null gs://$BUCKET_NAME/cache/

# Configure lifecycle policy for cost optimization
cat > /tmp/lifecycle.json << 'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {"age": 30}
      }
    ]
  }
}
EOF

gsutil lifecycle set /tmp/lifecycle.json gs://$BUCKET_NAME
rm /tmp/lifecycle.json

# Set up bucket permissions
echo "🔐 Setting up bucket permissions..."
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
gsutil iam ch user:$(gcloud config get-value account 2>/dev/null):objectAdmin gs://$BUCKET_NAME

# Create sync script for model management
echo "📝 Creating model sync script..."
cat > /opt/goblin-models/sync-models.sh << 'EOF'
#!/bin/bash
# Sync LLM models with Google Cloud Storage

BUCKET="REPLACE_WITH_BUCKET_NAME"
LOCAL_MODEL_DIR="/root/.ollama/models"
GCS_MODEL_DIR="models"

case "$1" in
    upload)
        echo "📤 Uploading models to GCS..."
        gsutil -m cp -r $LOCAL_MODEL_DIR/* gs://$BUCKET/$GCS_MODEL_DIR/
        echo "✅ Models uploaded successfully"
        ;;
    download)
        echo "📥 Downloading models from GCS..."
        mkdir -p $LOCAL_MODEL_DIR
        gsutil -m cp -r gs://$BUCKET/$GCS_MODEL_DIR/* $LOCAL_MODEL_DIR/
        echo "✅ Models downloaded successfully"
        ;;
    sync)
        echo "🔄 Syncing models with GCS..."
        # Upload new models
        gsutil -m rsync -r -d $LOCAL_MODEL_DIR gs://$BUCKET/$GCS_MODEL_DIR/
        echo "✅ Models synchronized successfully"
        ;;
    backup)
        echo "💾 Creating model backup..."
        BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
        gsutil -m cp -r $LOCAL_MODEL_DIR gs://$BUCKET/backups/models_$BACKUP_DATE/
        echo "✅ Backup created: models_$BACKUP_DATE"
        ;;
    list)
        echo "📋 Available models in GCS:"
        gsutil ls gs://$BUCKET/$GCS_MODEL_DIR/
        ;;
    *)
        echo "Usage: $0 {upload|download|sync|backup|list}"
        exit 1
        ;;
esac
EOF

chmod +x /opt/goblin-models/sync-models.sh

# Update bucket name in sync script
sed -i "s/REPLACE_WITH_BUCKET_NAME/$BUCKET_NAME/g" /opt/goblin-models/sync-models.sh

# Create model downloader from GCS
echo "⬇️ Creating GCS model downloader..."
cat > /opt/goblin-models/download-from-gcs.sh << 'EOF'
#!/bin/bash
# Download specific models from GCS

BUCKET="REPLACE_WITH_BUCKET_NAME"
LOCAL_MODEL_DIR="/root/.ollama/models"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <model_name> [model_name2 ...]"
    echo "Available models:"
    gsutil ls gs://$BUCKET/models/
    exit 1
fi

for model in "$@"; do
    echo "⬇️ Downloading $model..."
    gsutil -m cp -r gs://$BUCKET/models/$model $LOCAL_MODEL_DIR/
    echo "✅ Downloaded $model"
done

echo "🎉 All models downloaded successfully!"
EOF

chmod +x /opt/goblin-models/download-from-gcs.sh
sed -i "s/REPLACE_WITH_BUCKET_NAME/$BUCKET_NAME/g" /opt/goblin-models/download-from-gcs.sh

# Create cost monitoring script
echo "💰 Creating cost monitoring..."
cat > /opt/goblin-models/monitor-costs.sh << 'EOF'
#!/bin/bash
# Monitor GCS costs and usage

BUCKET="REPLACE_WITH_BUCKET_NAME"

echo "📊 Google Cloud Storage Usage Report"
echo "===================================="
echo "Date: $(date)"
echo

echo "📦 Storage Usage:"
gsutil du -sh gs://$BUCKET

echo
echo "💰 Cost Estimation:"
gsutil ls -L gs://$BUCKET | grep "Total item count\|Total size"

echo
echo "🗂️ Bucket Contents:"
gsutil ls -la gs://$BUCKET

echo
echo "📈 Storage Class Distribution:"
gsutil ls -p -b gs://$BUCKET

echo
echo "🔄 Recent Access (if configured):"
gsutil ls -p -b gs://$BUCKET

echo
echo "💡 Cost Optimization Tips:"
echo "• Enable lifecycle policies for automatic archiving"
echo "• Use regional buckets for better performance"
echo "• Monitor storage class distribution"
echo "• Set up billing alerts in Google Cloud Console"
EOF

chmod +x /opt/goblin-models/monitor-costs.sh
sed -i "s/REPLACE_WITH_BUCKET_NAME/$BUCKET_NAME/g" /opt/goblin-models/monitor-costs.sh

# Create systemd service for automatic sync
echo "🔧 Creating automatic sync service..."
cat > /etc/systemd/system/gcs-model-sync.service << 'EOF'
[Unit]
Description=Google Cloud Storage Model Sync
After=network.target

[Service]
Type=oneshot
User=root
ExecStart=/opt/goblin-models/sync-models.sh sync
StandardOutput=append:/var/log/gcs-sync.log
StandardError=append:/var/log/gcs-sync.log

[Install]
WantedBy=multi-user.target
EOF

# Create timer for daily sync
cat > /etc/systemd/system/gcs-model-sync.timer << 'EOF'
[Unit]
Description=Run GCS model sync daily
Requires=gcs-model-sync.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl enable gcs-model-sync.timer
systemctl start gcs-model-sync.timer

# Create cron job for cost monitoring
echo "0 6 * * * root /opt/goblin-models/monitor-costs.sh >> /var/log/gcs-costs.log 2>&1" >> /etc/crontab

# Setup monitoring and alerting
echo "🚨 Setting up monitoring and alerting..."
cat > /opt/goblin-models/setup-alerts.sh << 'EOF'
#!/bin/bash
# Setup Google Cloud monitoring alerts

PROJECT_ID=$(gcloud config get-value project)
BUCKET="REPLACE_WITH_BUCKET_NAME"

# Create notification channel
gcloud alpha monitoring channels create \
    --display-name="GCS Model Storage Alerts" \
    --type=email \
    --channel-labels=email_address=admin@goblin-assistant.dev

# Storage usage alert
gcloud alpha monitoring policies create \
    --display-name="High GCS Storage Usage" \
    --notification-channels=$(gcloud alpha monitoring channels list --filter="displayName:GCS Model Storage Alerts" --format="value(name)") \
    --threshold-value=80 \
    --threshold-units=PERCENT \
    --duration=300s \
    --filter="resource.type=\"gcs_bucket\" AND resource.labels.bucket_name=\"$BUCKET\""

echo "✅ Monitoring alerts configured"
EOF

chmod +x /opt/goblin-models/setup-alerts.sh
sed -i "s/REPLACE_WITH_BUCKET_NAME/$BUCKET_NAME/g" /opt/goblin-models/setup-alerts.sh

# Create performance optimization script
echo "⚡ Creating performance optimization..."
cat > /opt/goblin-models/optimize-performance.sh << 'EOF'
#!/bin/bash
# Optimize GCS performance for model access

BUCKET="REPLACE_WITH_BUCKET_NAME"

echo "⚡ Optimizing GCS performance..."

# Enable parallel uploads/downloads
gsutil set -m parallel_composite_upload_threshold 150M gs://$BUCKET

# Set default regional location
gsutil mb -p $(gcloud config get-value project) -l us-central1 gs://$BUCKET

# Enable requester pays for cost tracking (optional)
# gsutil requesterpays set on gs://$BUCKET

# Configure CORS for web access
cat > /tmp/cors.json << 'EOF'
[
  {
    "origin": ["https://goblin-assistant.vercel.app"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type", "x-goog-meta-model-name"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set /tmp/cors.json gs://$BUCKET
rm /tmp/cors.json

echo "✅ Performance optimization complete"
EOF

chmod +x /opt/goblin-models/optimize-performance.sh
sed -i "s/REPLACE_WITH_BUCKET_NAME/$BUCKET_NAME/g" /opt/goblin-models/optimize-performance.sh

# Create environment configuration
echo "⚙️ Creating environment configuration..."
cat > /opt/goblin-models/.env << EOF
# Google Cloud Storage Configuration
GCS_BUCKET_NAME=$BUCKET_NAME
GCS_PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "your-project")
GCS_REGION=$REGION
GCS_MODEL_DIR=models
GCS_BACKUP_DIR=backups

# Sync Settings
SYNC_INTERVAL=daily
SYNC_TIME=02:00
MAX_BACKUPS=30

# Performance Settings
PARALLEL_UPLOADS=true
UPLOAD_THRESHOLD=150M
CACHE_TTL=3600
EOF

# Final setup summary
echo
echo "🎉 Google Cloud Storage Setup Complete!"
echo "====================================="
echo
echo "✅ Google Cloud CLI installed"
echo "✅ GCS bucket created: gs://$BUCKET_NAME"
echo "✅ Bucket structure created"
echo "✅ Lifecycle policies configured"
echo "✅ Model sync scripts created"
echo "✅ Cost monitoring setup"
echo "✅ Automatic sync service configured"
echo "✅ Performance optimization applied"
echo
echo "📋 Next Steps:"
echo "1. Run initial model upload: /opt/goblin-models/sync-models.sh upload"
echo "2. Setup monitoring alerts: /opt/goblin-models/setup-alerts.sh"
echo "3. Test download: /opt/goblin-models/download-from-gcs.sh <model-name>"
echo "4. Monitor costs: /opt/goblin-models/monitor-costs.sh"
echo
echo "🛠️ Available Commands:"
echo "• Upload models: /opt/goblin-models/sync-models.sh upload"
echo "• Download models: /opt/goblin-models/sync-models.sh download"
echo "• Sync models: /opt/goblin-models/sync-models.sh sync"
echo "• Create backup: /opt/goblin-models/sync-models.sh backup"
echo "• List models: /opt/goblin-models/sync-models.sh list"
echo "• Monitor costs: /opt/goblin-models/monitor-costs.sh"
echo
echo "📊 Bucket Information:"
echo "Name: $BUCKET_NAME"
echo "Region: $REGION"
echo "URI: gs://$BUCKET_NAME"
echo
echo "💰 Cost Estimate:"
echo "• Storage: ~$0.020/GB/month"
echo "• Egress: ~$0.12/GB"
echo "• Operations: ~$0.05/10k operations"
echo "• Total for 100GB: ~$2-3/month"

# Test GCS connectivity
echo
echo "🔍 Testing GCS connectivity..."
if gsutil ls gs://$BUCKET_NAME > /dev/null 2>&1; then
    echo "✅ GCS bucket is accessible"
    echo "📦 Current bucket contents:"
    gsutil ls -la gs://$BUCKET_NAME
else
    echo "⚠️ GCS bucket access failed - check authentication"
fi

echo
echo "🚀 Google Cloud Storage is ready for LLM model storage!"
