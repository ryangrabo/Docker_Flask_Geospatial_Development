# App for Final Deplyoment System for Senior Design Project 1725
## Classifying Invasive Species Using Drone Images and Deep Learning

### Create venv
```bash
python3 -m venv venv
```

### Enter venv
```bash
venv\Scripts\activate    
```
or
```bash
source venv/bin/activate
```

### Create Docker Container
```bash
docker build -t flask_app . 
```
```bash
run -p 5000:5000 flask_app  
```

```bash
python3 -m venv myenv
source myenv/bin/activate
pip3 install -r requirements.txt
```
```bash
 docker-compose up --build
```