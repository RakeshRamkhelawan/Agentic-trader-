Write-Host "Stopping containers..."
docker-compose down

Write-Host "Building images with no cache and pulling latest base images..."
docker-compose build --no-cache --pull

Write-Host "Starting services..."
docker-compose up -d --force-recreate

Write-Host "Docker rebuild complete."
