# App for Final Deplyoment System for Senior Design Project 1725
## Classifying Invasive Species Using Drone Images and Deep Learning

## Intall docker and mongodb

### install docker engine and docker desktop
You need to install docker engine and docker desktop

### install mongodb
You need to install mongodb


## install wheels for big library
'''bash
mkdir wheels
pip download torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -d wheels
'''
## Create Docker Container
### build the docker container
```bash
 docker compose up --build
```

### connect to the website
[http://localhost:5000/](http://localhost:5000/)

### Old method of building:
Using this method will **NOT** setup the database, so it will not function correctly.
```bash
docker build -t flask_app . 
```
```bash
run -p 5000:5000 flask_app  
```

# TODO
## immediate
- Add message to display to user when they try to upload image that isn't a jpg. Also shouldn't display process time when the image isn't processed.
- lower resolution of images that are displayed through html. Uses a lot of RAM because of this uneccesarily. Should only be full resolution if the user clicks on it
- need more stress tests of the system. Uploading LOTS of images and seeing what occurs. See what causes the system to crash so those aspects of the system can be improved and made more efficient.

## longer term
### restructure [runInference.html](https://github.com/ryangrabo/Docker_Flask_Geospatial_Development/blob/main/app/templates/runInference.html)
- restructure to really just be one button where user can select a group of images or folder of images
- have inference and saving be done automatically, don't need all of the buttons that we currently have
- add ability to simply drag and drop images
### other
- move AWAY from Ultralytics and unnecessary libraries
    - we should attempt to export the model weights and build the model and use without Ultralytics. This would allow us to use way less libraries and theoretically cutdown on the massive size of the image and container
- figure out why image is so large (libraries are ~10 GB but the entire thing is still like 17GB without any images in the databse)
- make it so that images that are NOT saved to the database for the map aren't still stored in fs.chunks and fs.files
    - maybe make it so that fs.files and fs.chunks are automatically cleared when they reach a certain size? or just have it delete immediately if the results aren't stored in sendAndReceivePlantInfoTest. Not sure.
# Flow of Authentication

## User clicks login (/login)
- Generates a state token (CSRF protection).
- Redirects user to Microsoft login.

## User logs into Microsoft
- If successful, Microsoft redirects to `/getAToken` with an authorization code.

## Token exchange (/getAToken)
- Verifies state token (CSRF protection).
- Requests an access token from Azure.
- Saves user session and redirects to the homepage.

## Logout (/logout)
- Clears session and redirects to Azure AD logout.

# Security Considerations
 **CSRF Protection:** Uses `state` parameter to prevent unauthorized login requests.  
 **Session Handling:** Stores user info securely using Flask’s session.  
 **Confidential Authentication:** Uses client secret, meaning it is suitable for server-side applications.  
 **No Excessive Permissions:** `SCOPE = []`, meaning no personal user info is accessed.