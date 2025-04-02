## How to properly set up Docker Container (first time install)
Some additional steps we need to consider since the last time we set up from scratch:
- Download and install nvidia drivers, install nvidia-container-toolkit
```console
$ curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
  sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo
```
```console
$ sudo dnf install -y nvidia-container-toolkit
```
```
$ sudo nvidia-ctk runtime configure --runtime=docker
```
```console
$ sudo systemctl restart docker
```

- Create a .env file with the following keys (set them yourself):
```
FLASK_APP=
FLASK_ENV=
SECRET_KEY=
GMAPS_API_KEY=
MAPBOX_TOKEN=
AZUREMAP_TOKEN=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=
```

- In dockerfile, make sure lines 15-29 are formatted as follows (you do NOT need the wheels files for this to work!):

```
# Copy requirements first for caching
COPY requirements.txt ./
COPY requirements.lock ./


# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
# COPY wheels/ /wheels/
# RUN pip install --no-cache-dir /wheels/*

RUN pip install --no-cache-dir -r requirements.lock
```

