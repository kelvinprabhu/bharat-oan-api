#!/bin/bash

# Generate JWT keys if they don't exist
if [ ! -f "/app/keys/jwt_private_key.pem" ] || [ ! -f "/app/keys/jwt_public_key.pem" ]; then
    echo "Generating RSA keys..."
    openssl genrsa -out /app/keys/jwt_private_key.pem 2048
    openssl rsa -in /app/keys/jwt_private_key.pem -outform PEM -pubout -out /app/keys/jwt_public_key.pem
    chmod 600 /app/keys/jwt_private_key.pem
    chmod 644 /app/keys/jwt_public_key.pem
    echo "✓ JWT keys generated successfully"
fi

# Execute the CMD (supervisord)
exec "$@"
