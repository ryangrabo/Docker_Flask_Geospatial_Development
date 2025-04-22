# SETUP and Run
## Install necessary dependencies:
### Install docker
Please note that docker desktop cannot be used on Linux, if you want to run the container with GPU acceleration.
1. Follow the steps [here](https://docs.docker.com/engine/install/ubuntu/) (assuming Ubuntu installation):
2. Verify that you can run the following command:
```bash
sudo docker run hello-world
```
3. Follow post-setup steps [here](https://docs.docker.com/engine/install/linux-postinstall/) to run containers without sudo.
4. Verify that you can run the following command without sudo:
```bash
docker run hello-world
```

### Setup NVIDIA Driver
1. Install the NVIDIA CUDA Driver [here](https://developer.nvidia.com/cuda-downloads).
2. Verify that you can run the following command:
```bash
nvidia-smi
```

### Setup NVIDIA Container Toolkit and Configure Docker to recognize it
1. Install NVIDIA container toolkit using apt [here](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#with-apt-ubuntu-debian).
2. Go further down in the guide [here](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#configuring-docker) to configure docker to recognize it. You only need to follow the initial steps to configure docker and restart docker engine. Setting up rootless mode or any further steps are unecessary.
3. Verify that this command outputs NVIDIA runtime:
```bash
docker info | grep -i nvidia
```
Example output:
```
 Runtimes: io.containerd.runc.v2 nvidia runc
```

### Install mongodb
1. Install MongoDB Community Server [here](https://www.mongodb.com/try/download/community-kubernetes-operator). Ensure that you select the correct platform.
2. (optional) Install MongoDB Compass to view DB in GUI [here](https://www.mongodb.com/docs/compass/current/install/).

## Clone Github and Build Container:
### Clone Github:
```bash
git clone https://github.com/ryangrabo/Docker_Flask_Geospatial_Development
```

### Build container 
1. Create a .env file with the following keys (set th empty ones yourself):
```
FLASK_APP=
FLASK_ENV=
SECRET_KEY=
MAPBOX_TOKEN=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=
```

2. Create wheels folder for large torchvision library:

```bash
mkdir wheels
pip download torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -d wheels
```

3. Build the Docker container:
```bash
docker compose up --build
```
View the website at [localhost:5000](http:/localhost:5000). Note that a PSU account is needed to access the website.

## Done with setup! Some other useful commands:
### Start/stop containers without rebuilding container:
- Start
```bash
docker start mongodbtest
docker start flask_app
```
- Stop
```bash
docker stop mongodbtest
docker stop flask_app
```
### View running containers and logs
- view running containers:
```bash
docker ps
```
- view all containers:
```bash
docker ps -a
```
- follow logs of a container:
  - Database
  ```bash
  docker logs -f mongodbtest
  ```
  - Flask App
  ```bash
  docker logs -f flask_app
  ```
