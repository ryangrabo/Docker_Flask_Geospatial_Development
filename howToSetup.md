## How to properly set up Docker Container (first time install)
Some additional steps we need to consider since the last time we set up from scratch:
- create a .env file with the following keys (set them yourself):
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

- In cli (or wherever you can access file structure), create a directory called "wheels", then run this:

```
pip download torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -d wheels
```

