#!/bin/bash
# SSL Certificate Setup Script for Agentic Trader Platform
# Usage: ./setup_ssl.sh [domain]

set -e

DOMAIN=${1:-localhost}
SSL_DIR="./nginx/ssl"

echo "============================================================"
echo "Agentic Trader Platform - SSL Setup"
echo "============================================================"
echo "Domain: $DOMAIN"
echo "SSL Directory: $SSL_DIR"
echo ""

# Create SSL directory
mkdir -p "$SSL_DIR"

# Check if openssl is installed
if ! command -v openssl &> /dev/null; then
    echo "ERROR: openssl is not installed. Please install it first."
    exit 1
fi

# Check if certificates already exist
if [ -f "$SSL_DIR/cert.pem" ] && [ -f "$SSL_DIR/key.pem" ]; then
    echo "SSL certificates already exist."
    read -p "Do you want to regenerate them? (y/N): " regenerate
    if [[ ! $regenerate =~ ^[Yy]$ ]]; then
        echo "Keeping existing certificates."
        exit 0
    fi
fi

echo "Generating self-signed SSL certificates..."
echo ""

# Generate private key
openssl genrsa -out "$SSL_DIR/key.pem" 2048

# Generate certificate signing request
openssl req -new -key "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.csr" -subj "/CN=$DOMAIN/O=Agentic Trader Platform/C=US"

# Generate self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in "$SSL_DIR/cert.csr" -signkey "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.pem"

# Remove CSR file (no longer needed)
rm "$SSL_DIR/cert.csr"

# Set permissions
chmod 600 "$SSL_DIR/key.pem"
chmod 644 "$SSL_DIR/cert.pem"

echo ""
echo "============================================================"
echo "SSL Certificates Generated Successfully!"
echo "============================================================"
echo "Certificate: $SSL_DIR/cert.pem"
echo "Private Key: $SSL_DIR/key.pem"
echo ""
echo "To use HTTPS:"
echo "1. Set SSL_ENABLED=true in your .env file"
echo "2. Start with SSL profile: docker-compose --profile ssl up -d"
echo ""
echo "IMPORTANT: For production, replace with certificates from"
echo "a trusted Certificate Authority (Let's Encrypt, etc.)"
echo "============================================================"
