#!/bin/bash
# Build and tag the Goblin Sandbox Docker image
# Usage: ./build.sh [tag]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="goblin/sandbox"
TAG="${1:-latest}"

echo "🔨 Building Goblin Sandbox image..."
echo "   Image: ${IMAGE_NAME}:${TAG}"

docker build \
    -t "${IMAGE_NAME}:${TAG}" \
    -f "${SCRIPT_DIR}/Dockerfile" \
    "${SCRIPT_DIR}"

echo ""
echo "✅ Build complete!"
echo ""
echo "To verify the image:"
echo "  docker run --rm ${IMAGE_NAME}:${TAG} python3 -c \"print('Hello from sandbox!')\""
echo ""
echo "To push to a registry:"
echo "  docker tag ${IMAGE_NAME}:${TAG} your-registry/${IMAGE_NAME}:${TAG}"
echo "  docker push your-registry/${IMAGE_NAME}:${TAG}"
echo ""
echo "To use with Goblin Assistant:"
echo "  export SANDBOX_IMAGE=${IMAGE_NAME}:${TAG}"
echo "  flyctl secrets set SANDBOX_IMAGE=${IMAGE_NAME}:${TAG}"
