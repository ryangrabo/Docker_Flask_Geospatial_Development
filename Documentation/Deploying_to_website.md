# Deploying the Application to `invasivespecies.bd.psu.edu`

## Steps Taken

### 1. Update Packages
First, updated the system package lists to ensure everything is current:
```bash
sudo apt update
```

### 2. Install NGINX
Installed NGINX to serve the application:
```bash
sudo apt install nginx
```

### 3. Start NGINX
Started the NGINX service:
```bash
sudo systemctl start nginx
```

### 4. Configure NGINX Site
Created a new NGINX config file for the domain:
```bash
sudo nano /etc/nginx/sites-available/invasivespecies.bd.psu.edu
```

Added server configuration pointing to the application running on port `5000`.

### 5. Enable the Site
Created a symbolic link to enable the new site:
```bash
sudo ln -s /etc/nginx/sites-available/invasivespecies.bd.psu.edu /etc/nginx/sites-enabled/
```

Removed the default site config:
```bash
sudo rm /etc/nginx/sites-enabled/default
```

### 6. Test NGINX Configuration
Verified that the NGINX configuration is correct:
```bash
sudo nginx -t
```

### 7. Reload NGINX
Reloaded NGINX to apply the new configuration:
```bash
sudo systemctl reload nginx
```

### 8. Confirm Application is Running
Tested that the application is accessible:
```bash
curl http://localhost:5000
```

Confirmed redirect to `/login` indicating the app is running properly.

## Notes
- Be cautious with typos and commands like `sudo cd`, which won’t work since `cd` is a shell built-in.
- Make sure the `.conf` file in `sites-available` matches your domain setup and port the app is listening on.

```bash
docker compose up --build
git pull
sudo -i
exit
ls
cd ../
cd ..
cd landon
cd /etc/ssl/certs
xdg-open etc/ssl/certs
mv ~/Desktop/invasivespecies_bd_psu_edu_cert.cer /etc/ssl/certs
sudo mv ~/Desktop/invasivespecies_bd_psu_edu_cert.cer /etc/ssl/certs
ifconfig
./ryan_change_github.sh
```

## NGINX Configuration Snippet

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name invasivespecies.bd.psu.edu www.invasivespecies.bd.psu.edu;
    return 301 https://$host$request_uri;
}

# Handle HTTPS requests
server {
    listen 443 ssl;
    server_name invasivespecies.bd.psu.edu www.invasivespecies.bd.psu.edu;

    ssl_certificate     /etc/ssl/certs/invasivespecies_bd_psu_edu_cert.cer;
    ssl_certificate_key /etc/ssl/private/server.key;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```