# Using Docker with Flask

**Ryan Grabowski**  
*1/30/25*

---

## Help Setting Up Docker Container

Reference: [Dockerizing a Python Flask App](https://medium.com/@geeekfa/dockerizing-a-python-flask-app-a-step-by-step-guide-to-containerizing-your-web-application-d0f123159ba2)

---

## Prerequisites

- Install Docker: https://www.docker.com/get-started
- Ensure `requirements.txt` and `application.py` are correctly set up

---

## Build the Docker Image

To build the Docker image, run:
```bash
docker build -t flask_app .
```

---

## Run the Container

To run the container and expose it on port 5000:
```bash
docker run -p 5000:5000 flask_app
```

For detached mode (running in the background):
```bash
docker run -d -p 5000:5000 flask_app
```

---

## Verify the Running Container

Check if the container is running:
```bash
docker ps
```

Expected output should show something like:
```
CONTAINER ID   IMAGE       COMMAND                  STATUS        PORTS                    NAMES
xyz123abc456   flask_app   "gunicorn -b 0.0.0.0…"   Up 1 minute   0.0.0.0:5000->5000/tcp   flask_container
```

---

## Access the Application

Open a browser and go to:
```
http://localhost:5000/
```

Or use:
```bash
curl http://localhost:5000/
```

---

## Stopping the Container

To stop the container, first find the container ID:
```bash
docker ps
```

Then stop it:
```bash
docker stop <container_id>
```

---

## Running on a Different Port

To run on port 8000 instead of 5000:
```bash
docker run -p 8000:8000 flask_app
```

Then access it at:
```
http://localhost:8000/
```

---

## Checking Container Logs

To see logs from the running container:
```bash
docker logs <container_id>
```

---

## Removing Stopped Containers

To remove a stopped container:
```bash
docker rm <container_id>
```

---

## Rebuilding and Restarting

If you make changes to the app, rebuild the image:
```bash
docker build -t flask_app .
```

Then restart the container:
```bash
docker run -p 5000:5000 flask_app
```

---

## Accessing a Dockerized MongoDB Instance

To find the Docker image of your database:
```bash
docker ps
```

Find the ID associated with the image, then connect to the container:
```bash
docker exec -it [id] /bin/bash
```

Once inside the terminal, start the Mongo shell:
```bash
mongosh
```

Find where it’s connected to and copy that connection string into MongoDB Compass.
