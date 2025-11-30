# Deployment Guide for EC2

This guide will help you deploy the integrated frontend + backend application to your EC2 instance.

## Overview

The frontend (React + Vite) and backend (Django) are now integrated. When you run `python manage.py runserver`, Django will serve both the API endpoints and the frontend application.

## Local Testing

1. Make sure you're in the backend directory:
   ```bash
   cd backend
   ```

2. Run the Django development server:
   ```bash
   python manage.py runserver
   ```

3. Open your browser and navigate to:
   - Frontend: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs/
   - API Root: http://localhost:8000/api/

## EC2 Deployment

### Prerequisites

- EC2 instance IP: `13.62.63.125`
- Python 3.8+ installed
- Node.js installed (for building frontend)
- Supabase PostgreSQL database configured

### Step 1: Prepare the Frontend

On your local machine:

```bash
cd frontend
npm install
npm run build
```

This creates the `frontend/dist` folder with the built frontend assets.

### Step 2: Upload to EC2

Upload both the `backend` and `frontend` directories to your EC2 instance:

```bash
# Example using scp (adjust the key path and username)
scp -i your-key.pem -r backend frontend ec2-user@13.62.63.125:/home/ec2-user/KGen21/
# Or use ubuntu user depending on your AMI: ubuntu@13.62.63.125
```

### Step 3: Configure Environment on EC2

1. SSH into your EC2 instance:
   ```bash
   ssh -i your-key.pem ec2-user@13.62.63.125
   # Or: ssh -i your-key.pem ubuntu@13.62.63.125
   ```

2. Navigate to the backend directory:
   ```bash
   cd /home/ec2-user/KGen21/backend
   ```

3. Create a `.env` file based on the example:
   ```bash
   cp .env.production.example .env
   nano .env  # Edit with your actual values
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

### Step 4: Production Server Setup (Gunicorn + Nginx)

For production, you should use Gunicorn as the WSGI server and Nginx as a reverse proxy.

1. Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

2. Create a Gunicorn service file:
   ```bash
   sudo nano /etc/systemd/system/kgen21.service
   ```

   Add the following content:
   ```ini
   [Unit]
   Description=KGen21 Django Application
   After=network.target

   [Service]
   User=ec2-user
   Group=ec2-user
   WorkingDirectory=/home/ec2-user/KGen21/backend
   Environment="PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin"
   ExecStart=/usr/local/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 config.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

3. Start and enable the service:
   ```bash
   sudo systemctl start kgen21
   sudo systemctl enable kgen21
   sudo systemctl status kgen21
   ```

### Step 5: Nginx Configuration (Optional but Recommended)

1. Install Nginx:
   ```bash
   sudo yum install nginx  # For Amazon Linux
   ```

2. Create Nginx configuration:
   ```bash
   sudo nano /etc/nginx/conf.d/kgen21.conf
   ```

   Add the following:
   ```nginx
   server {
       listen 80;
       server_name ec2-13-62-63-125.eu-north-1.compute.amazonaws.com;

       client_max_body_size 10M;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location /static/ {
           alias /home/ec2-user/KGen21/backend/staticfiles/;
       }

       location /media/ {
           alias /home/ec2-user/KGen21/backend/media/;
       }

       location /assets/ {
           alias /home/ec2-user/KGen21/frontend/dist/assets/;
       }
   }
   ```

3. Start Nginx:
   ```bash
   sudo systemctl start nginx
   sudo systemctl enable nginx
   ```

### Step 6: Update Security Group

Make sure your EC2 security group allows:
- Port 80 (HTTP)
- Port 443 (HTTPS, if using SSL)
- Port 8000 (if accessing Django directly without Nginx)

## Quick Development Mode on EC2

If you just want to test quickly without setting up Gunicorn and Nginx:

```bash
cd /home/ec2-user/KGen21/backend
python manage.py runserver 0.0.0.0:8000
```

Then access your app at:
`http://ec2-13-62-63-125.eu-north-1.compute.amazonaws.com:8000`

**Note:** This is NOT recommended for production use. Use Gunicorn + Nginx for production.

## Updating the Application

When you make changes:

1. **Frontend changes:**
   ```bash
   cd frontend
   npm run build
   # Upload new dist folder to EC2
   ```

2. **Backend changes:**
   ```bash
   # Upload new backend files to EC2
   ssh ec2-user@ec2-13-62-63-125.eu-north-1.compute.amazonaws.com
   cd /home/ec2-user/KGen21/backend
   python manage.py migrate  # If there are new migrations
   sudo systemctl restart kgen21
   ```

## Troubleshooting

- **Static files not loading:** Run `python manage.py collectstatic --noinput`
- **500 errors:** Check logs with `sudo journalctl -u kgen21 -f`
- **Database connection issues:** Verify DATABASE_URL in .env
- **CORS errors:** Check CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS in settings.py

## Environment Variables

The following environment variables are used in production:
- `DEBUG=False` - Disable debug mode in production
- `ALLOWED_HOSTS` - Include your EC2 hostname and domain
- `DATABASE_URL` - Your PostgreSQL connection string
- All API keys (OpenAI, Composio, etc.)

See `.env.production.example` for a complete list.
