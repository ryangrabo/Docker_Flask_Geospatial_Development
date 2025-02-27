# App for Final Deplyoment System for Senior Design Project 1725
## Classifying Invasive Species Using Drone Images and Deep Learning

## Intall docker and mongodb

### install docker engine and docker desktop
You need to install docker engine and docker desktop

### install mongodb
You need to install mongodb

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