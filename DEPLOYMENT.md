# Deployment Guide - Expenzo

## Pre-Deployment Checklist

### ✅ Security Settings
- [ ] `SECRET_KEY` is set in environment variables (strong, randomly generated)
- [ ] `FLASK_DEBUG=False` in production environment
- [ ] `MONGO_URI` is secure and uses authentication
- [ ] `.env` file is NOT committed to git (already in .gitignore)

### ✅ Environment Variables Required
```bash
SECRET_KEY=your-strong-secret-key-here
MONGO_URI=your-mongodb-connection-string
DB_NAME=expen
FLASK_DEBUG=False
PORT=5000
```

### ✅ Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Deployment Platforms

### Option 1: Render.com

1. **Create new Web Service**
   - Connect your GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

2. **Set Environment Variables**
   - Go to Environment tab
   - Add all required variables (SECRET_KEY, MONGO_URI, etc.)

3. **Deploy**
   - Render will automatically deploy on push

### Option 2: Railway

1. **Create new project**
   - Connect GitHub repository
   - Railway will auto-detect Flask

2. **Set Environment Variables**
   - Add in Railway dashboard

3. **Deploy**
   - Railway auto-deploys on push

### Option 3: Heroku

1. **Create Procfile**
   ```
   web: gunicorn app:app
   ```

2. **Set Config Vars**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set MONGO_URI=your-mongodb-uri
   heroku config:set FLASK_DEBUG=False
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

### Option 4: AWS/EC2

1. **Install dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip python3-venv nginx
   ```

2. **Setup application**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```

3. **Create systemd service**
   ```ini
   [Unit]
   Description=Expenzo Flask App
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/Expenzo
   Environment="PATH=/home/ubuntu/Expenzo/venv/bin"
   ExecStart=/home/ubuntu/Expenzo/venv/bin/gunicorn app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **Configure Nginx** (reverse proxy)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## Database Setup

### MongoDB Atlas (Recommended)

1. Create account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a cluster
3. Create database user
4. Whitelist your IP (or 0.0.0.0/0 for all IPs in production)
5. Get connection string
6. Update `MONGO_URI` in environment variables

## Post-Deployment Verification

### ✅ Test All Routes
- [ ] `/` - Landing page
- [ ] `/register` - Registration
- [ ] `/login` - Login
- [ ] `/dashboard` - Dashboard (requires login)
- [ ] `/cards` - Cards page
- [ ] `/income` - Income page
- [ ] `/expense` - Expense page
- [ ] `/transactions` - Transactions page
- [ ] `/limits` - Limits page
- [ ] `/subscriptions` - Subscriptions page
- [ ] `/visualization` - Visualization page
- [ ] `/profile` - Profile page

### ✅ Test API Endpoints
- [ ] `/api/cards` - GET, POST
- [ ] `/api/income` - GET, POST, DELETE
- [ ] `/api/expense` - GET, POST, DELETE
- [ ] `/api/transactions` - GET, DELETE
- [ ] `/api/limits` - GET, POST, PUT, DELETE
- [ ] `/api/subscriptions` - GET, POST, PUT, DELETE

### ✅ Security Checks
- [ ] Debug mode is OFF
- [ ] Secret key is strong and unique
- [ ] MongoDB connection is secure
- [ ] No sensitive data in code
- [ ] HTTPS enabled (if using custom domain)

## Troubleshooting

### Common Issues

1. **500 Internal Server Error**
   - Check application logs
   - Verify environment variables are set
   - Check MongoDB connection

2. **Database Connection Failed**
   - Verify MONGO_URI is correct
   - Check IP whitelist in MongoDB Atlas
   - Verify database credentials

3. **Static Files Not Loading**
   - Check static folder path
   - Verify Flask static_folder configuration
   - Check file permissions

## Monitoring

### Recommended Tools
- **Application Monitoring**: Sentry, LogRocket
- **Uptime Monitoring**: UptimeRobot, Pingdom
- **Error Tracking**: Sentry

## Backup Strategy

1. **Database Backups**
   - MongoDB Atlas provides automatic backups
   - Set up regular manual backups if needed

2. **Code Backups**
   - Use Git for version control
   - Regular commits and pushes

## Performance Optimization

1. **Enable Caching**
   - Use Flask-Caching for static content
   - Implement Redis for session storage (optional)

2. **CDN for Static Files**
   - Use CloudFlare or AWS CloudFront
   - Serve CSS/JS/images from CDN

3. **Database Indexing**
   - Add indexes on frequently queried fields
   - Index on `user_id` for all collections

## Support

For issues or questions, check:
- Application logs
- Error handlers (check terminal/console)
- MongoDB connection status

