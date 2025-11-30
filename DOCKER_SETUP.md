# 🐳 Docker Setup Complete

## Files Created

### 1. **docker-compose.yml** (Root directory)
- Defines two services: `backend` (Django) and `nginx`
- Uses custom network `kgen_network`
- Backend exposed internally on port 8000
- Nginx exposed externally on port 80
- Health checks configured

### 2. **backend/Dockerfile**
- Multi-stage build for efficiency
- Python 3.12 slim base image
- Installs all dependencies including gunicorn
- Runs as non-root user for security
- Configured with health checks

### 3. **nginx/conf.d/app.conf**
- Complete Nginx configuration
- Serves React static files from `/`
- Proxies API requests to Django (`/api/`)
- Handles Django admin and media files
- Optimized caching for static assets
- SPA routing support with try_files

### 4. **.dockerignore files**
- Prevents unnecessary files from being included in Docker builds
- Excludes node_modules, .env, .git, etc.

### 5. **deploy.sh** (Local deployment)
- Automated local deployment script
- Builds Docker images
- Runs migrations and collects static files
- Shows health status

### 6. **deploy-to-ec2.sh** (EC2 deployment)
- Complete EC2 deployment automation
- Installs Docker if needed
- Uploads project files
- Builds and runs containers
- Performs health checks

## Quick Start

### Local Testing (if Docker installed)
```bash
cd /Users/shaharishay/Programming/KGen21
./deploy.sh
```

### Deploy to EC2
```bash
cd /Users/shaharishay/Programming/KGen21
./deploy-to-ec2.sh
```

## Architecture

```
Internet → EC2 (Port 80) → Nginx Container
                               ↓
                          [Static Files]
                          [React App]
                               ↓
                          [/api/* routes]
                               ↓
                          Django Container (Port 8000)
                               ↓
                          Supabase PostgreSQL
```

## Key Features

✅ **Production-ready**: Gunicorn WSGI server, optimized Docker images
✅ **Secure**: Non-root users, internal network isolation
✅ **Performant**: Multi-stage builds, static file caching
✅ **Maintainable**: Health checks, structured logging
✅ **Automated**: One-command deployment scripts

## Network Architecture

- **kgen_network**: Custom bridge network
- **Backend**: Only accessible internally (port 8000)
- **Nginx**: Public entry point (port 80)
- **Service Discovery**: Containers communicate via service names

## Environment Variables

The backend reads from `backend/.env` which includes:
- Database connection (Supabase)
- API keys (OpenAI, Composio, etc.)
- Django settings

## Volumes

- `./frontend/dist` → `/usr/share/nginx/html` (React app)
- `./nginx/conf.d` → `/etc/nginx/conf.d` (Nginx config)
- `./backend/.env` → Environment variables

## Commands

### On EC2 (after deployment):

```bash
# View logs
sudo docker compose logs -f

# Enter backend container
sudo docker compose exec backend bash

# Restart services
sudo docker compose restart

# Stop everything
sudo docker compose down

# Rebuild after changes
sudo docker compose up -d --build

# Run Django management commands
sudo docker compose exec backend python manage.py createsuperuser
sudo docker compose exec backend python manage.py shell
```

## Troubleshooting

1. **502 Bad Gateway**: Backend is still starting. Wait 30 seconds.
2. **Static files not loading**: Run `collectstatic` command
3. **Database connection failed**: Check DATABASE_URL in .env
4. **Permission denied**: Make sure scripts are executable with `chmod +x`

## Security Notes

- Change `DJANGO_SECRET_KEY` in production
- Use HTTPS in production (SSL certificates)
- Regularly update Docker images
- Monitor logs for suspicious activity
- Use firewall rules to restrict SSH access

## Next Steps

1. **Run deployment**: `./deploy-to-ec2.sh`
2. **Set up SSL**: Use Let's Encrypt with Certbot
3. **Configure domain**: Point your domain to EC2 IP
4. **Set up monitoring**: Use CloudWatch or similar
5. **Backup strategy**: Regular database backups

## Support

For issues, check:
- Docker logs: `sudo docker compose logs [service]`
- Django logs: In container output
- Nginx access logs: `/var/log/nginx/access.log`
- System resources: `docker stats`

---

**Ready for production! 🚀**