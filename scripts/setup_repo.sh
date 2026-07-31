#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Radiology AI Platform — Setup Script
# Initializes the development environment for the Radiology AI Platform.
#
# Usage:
#   chmod +x scripts/setup_repo.sh
#   ./scripts/setup_repo.sh
#
# Prerequisites:
#   - Docker 24+
#   - Docker Compose v2
#   - Python 3.11+
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}==========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Get the repository root (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

print_header "Radiology AI Platform — Setup"

# ─────────────────────────────────────────────────────────────────────────────
# 1. Check dependencies
# ─────────────────────────────────────────────────────────────────────────────
print_header "Step 1: Checking dependencies"

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        print_success "$1 found: $(command -v "$1")"
        return 0
    else
        print_error "$1 not found"
        return 1
    fi
}

MISSING_DEPS=0
check_command docker || MISSING_DEPS=1
check_command docker-compose || check_command "docker compose" || MISSING_DEPS=1
check_command python3 || MISSING_DEPS=1
check_command git || MISSING_DEPS=1

if [ "$MISSING_DEPS" -eq 1 ]; then
    print_error "Missing dependencies. Please install them and re-run."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)'; then
    print_success "Python $PYTHON_VERSION (≥3.11)"
else
    print_error "Python 3.11+ required, found $PYTHON_VERSION"
    exit 1
fi

# Check Docker daemon
if ! docker info >/dev/null 2>&1; then
    print_error "Docker daemon is not running. Start Docker and re-run."
    exit 1
fi
print_success "Docker daemon is running"

# ─────────────────────────────────────────────────────────────────────────────
# 2. Create directory structure
# ─────────────────────────────────────────────────────────────────────────────
print_header "Step 2: Creating directory structure"

DIRECTORIES=(
    "data/raw"
    "data/deidentified"
    "data/reports/generated"
    "data/reports/reviewed"
    "data/reports/final"
    "data/metadata"
    "data/checksums"
    "data/examples"
    "logs"
    "models/pretrained"
    "models/fine_tuned"
    "src"
    "tests"
    "notebooks"
)

for dir in "${DIRECTORIES[@]}"; do
    mkdir -p "$dir"
    # Create .gitkeep to preserve empty dirs
    touch "$dir/.gitkeep"
    print_success "Created: $dir"
done

# Set restrictive permissions on data directories (PHI protection)
chmod 700 data/raw data/deidentified 2>/dev/null || true
print_success "Set restrictive permissions on data/ directories"

# ─────────────────────────────────────────────────────────────────────────────
# 3. Create .env file (if not exists)
# ─────────────────────────────────────────────────────────────────────────────
print_header "Step 3: Environment configuration"

if [ ! -f ".env" ]; then
    # Generate random secrets
    POSTGRES_PASSWORD=$(openssl rand -hex 24 2>/dev/null || echo "change_me_to_random")
    MINIO_PASSWORD=$(openssl rand -hex 24 2>/dev/null || echo "change_me_to_random")
    REDIS_PASSWORD=$(openssl rand -hex 24 2>/dev/null || echo "change_me_to_random")
    SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "change_me_to_random")
    ORTHANC_PASSWORD=$(openssl rand -hex 16 2>/dev/null || echo "change_me")
    GRAFANA_PASSWORD=$(openssl rand -hex 12 2>/dev/null || echo "admin")
    FLOWER_PASSWORD=$(openssl rand -hex 12 2>/dev/null || echo "change_me")

    cat > .env << EOF
# ─────────────────────────────────────────────────────────────────────────────
# Radiology AI Platform — Environment Variables
# IMPORTANT: This file contains secrets. Do NOT commit to Git.
# ─────────────────────────────────────────────────────────────────────────────

# PostgreSQL
POSTGRES_USER=radiology_admin
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=radiology

# MinIO (S3-compatible object storage)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=$MINIO_PASSWORD

# Redis
REDIS_PASSWORD=$REDIS_PASSWORD

# API / JWT
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_HOURS=24

# Orthanc PACS
ORTHANC_PASSWORD=$ORTHANC_PASSWORD

# Grafana
GRAFANA_PASSWORD=$GRAFANA_PASSWORD

# Flower (Celery monitor)
FLOWER_PASSWORD=$FLOWER_PASSWORD

# AI / Model settings
MODEL_PATH=./models/pretrained
CUDA_VISIBLE_DEVICES=0
MODEL_DEVICE=auto

# Logging
LOG_LEVEL=INFO
STRUCTLOG_LEVEL=INFO

# Environment
ENVIRONMENT=development
DEBUG=true
EOF
    chmod 600 .env
    print_success "Created .env with generated secrets"
    print_warning "Review and customize .env before production use"
else
    print_warning ".env already exists, skipping"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 4. Create Python virtual environment
# ─────────────────────────────────────────────────────────────────────────────
print_header "Step 4: Python virtual environment"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    print_success "Created virtual environment: .venv"
else
    print_warning ".venv already exists, skipping"
fi

# Activate and install
source .venv/bin/activate
print_success "Activated virtual environment"

# Upgrade pip
pip install --upgrade pip setuptools wheel >/dev/null 2>&1
print_success "Upgraded pip"

# Install dependencies
if [ -f "setup/requirements.txt" ]; then
    print_warning "Installing Python dependencies (this may take several minutes)..."
    pip install -r setup/requirements.txt
    print_success "Installed Python dependencies"
else
    print_warning "setup/requirements.txt not found, skipping"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 5. Start Docker services
# ─────────────────────────────────────────────────────────────────────────────
print_header "Step 5: Starting Docker services"

cd setup

# Pull images first (so failures show before starting)
print_warning "Pulling Docker images (this may take a while on first run)..."
if docker-compose pull 2>/dev/null || docker compose pull; then
    print_success "Pulled Docker images"
else
    print_warning "Some images failed to pull (will retry on up)"
fi

# Start services
print_warning "Starting services..."
if docker-compose up -d 2>/dev/null; then
    print_success "Started services (docker-compose v1)"
elif docker compose up -d; then
    print_success "Started services (docker compose v2)"
else
    print_error "Failed to start Docker services"
    exit 1
fi

cd "$REPO_ROOT"

# Wait for services to be healthy
print_warning "Waiting for services to be healthy (30s)..."
sleep 30

# Check service status
print_warning "Service status:"
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose ps 2>/dev/null || true
else
    docker compose ps 2>/dev/null || true
fi

# ─────────────────────────────────────────────────────────────────────────────
# 6. Initialize database (placeholder for Alembic migrations)
# ─────────────────────────────────────────────────────────────────────────────
print_header "Step 6: Database initialization"

# Check if PostgreSQL is ready
for i in {1..30}; do
    if docker exec radiology-postgres pg_isready -U radiology_admin >/dev/null 2>&1; then
        print_success "PostgreSQL is ready"
        break
    fi
    sleep 2
    if [ $i -eq 30 ]; then
        print_warning "PostgreSQL not ready after 60s — skip DB init"
    fi
done

# ─────────────────────────────────────────────────────────────────────────────
# 7. Final verification
# ─────────────────────────────────────────────────────────────────────────────
print_header "Step 7: Verification"

# Test Orthanc
if curl -s -u "admin:${ORTHANC_PASSWORD:-change_me}" http://localhost:8042/system >/dev/null 2>&1; then
    print_success "Orthanc is responding at http://localhost:8042"
else
    print_warning "Orthanc not yet responding (may still be starting up)"
fi

# Test MinIO
if curl -s http://localhost:9000/minio/health/live >/dev/null 2>&1; then
    print_success "MinIO is responding at http://localhost:9000"
else
    print_warning "MinIO not yet responding"
fi

# Test Redis
if docker exec radiology-redis redis-cli -a "${REDIS_PASSWORD:-change_me}" ping >/dev/null 2>&1; then
    print_success "Redis is responding"
else
    print_warning "Redis not yet responding"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 8. Summary
# ─────────────────────────────────────────────────────────────────────────────
print_header "Setup Complete!"

echo ""
echo -e "${GREEN}Your Radiology AI Platform development environment is ready!${NC}"
echo ""
echo "Services:"
echo "  • Orthanc PACS:    http://localhost:8042  (admin / ${ORTHANC_PASSWORD:-change_me})"
echo "  • MinIO Console:   http://localhost:9001  (minioadmin / ********)"
echo "  • API Docs:        http://localhost:8000/docs  (when API is running)"
echo "  • Flower Monitor:  http://localhost:5555  (admin / ${FLOWER_PASSWORD:-change_me})"
echo "  • Grafana:         http://localhost:3000  (admin / ${GRAFANA_PASSWORD:-admin})"
echo "  • Prometheus:      http://localhost:9090"
echo ""
echo "Next steps:"
echo "  1. Review and customize .env"
echo "  2. Test DICOM de-identification:"
echo "     python scripts/dicom_deidentify.py --input data/examples/ --output data/deidentified/ --verify"
echo "  3. Read the documentation in docs/"
echo "  4. Start development!"
echo ""
echo -e "${YELLOW}⚠ Important security notes:${NC}"
echo "  • .env contains secrets — NEVER commit it to Git"
echo "  • data/raw/ and data/deidentified/ must never be committed"
echo "  • Use only de-identified DICOM files in this repository"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  • Architecture:  docs/ARCHITECTURE.md"
echo "  • Roadmap:       docs/ROADMAP.md"
echo "  • Security:      docs/SECURITY.md"
echo "  • Data Guide:    docs/DATA_GUIDE.md"
echo "  • Integrations:  docs/INTEGRATIONS.md"
echo "  • API Spec:      docs/API_SPEC.md"
echo ""
