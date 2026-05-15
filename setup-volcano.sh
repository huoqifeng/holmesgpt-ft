#!/bin/bash
# Setup script for HolmesGPT with Volcano scheduler

set -e

echo "🌋 Setting up HolmesGPT with Volcano scheduler..."

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install it first."
    exit 1
fi

# Check if Volcano is installed
if ! kubectl get crd queues.scheduling.volcano.sh &> /dev/null; then
    echo "📦 Installing Volcano..."
    kubectl apply -f https://raw.githubusercontent.com/volcano-sh/volcano/master/installer/volcano-development.yaml
    echo "⏳ Waiting for Volcano to be ready..."
    kubectl wait --for=condition=ready pod -l app=volcano-admission -n volcano-system --timeout=300s
else
    echo "✅ Volcano is already installed"
fi

# Deploy HolmesGPT configurations
echo "🚀 Deploying HolmesGPT with Volcano support..."
kubectl apply -f volcano-config.yaml
kubectl apply -f manifest.yaml

echo "✅ HolmesGPT setup with Volcano completed!"
echo ""
echo "📝 Next steps:"
echo "1. Deploy training: kubectl scale deployment holmesgpt-training --replicas=1 -n holmesgpt-ft"
echo "2. Deploy workers: kubectl scale deployment holmesgpt-ray-workers --replicas=2 -n holmesgpt-ft"
echo "3. Monitor training: kubectl scale deployment holmesgpt-monitor --replicas=1 -n holmesgpt-ft"
echo "4. Access services:"
echo "   - Ray Dashboard: kubectl port-forward svc/holmesgpt-training-service 8265:8265 -n holmesgpt-ft"
echo "   - TensorBoard: kubectl port-forward svc/holmesgpt-training-service 6006:6006 -n holmesgpt-ft"
echo ""
echo "🌋 Volcano queue: holmesgpt-queue"
echo "⚡ Priority class: holmesgpt-high-priority"