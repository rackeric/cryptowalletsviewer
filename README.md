# flask-blog

A blog CMS app using python Flask and MongoDB.

Dockerfile is included.

- Python
- Flask
- Flask-Auth
- FlaskMongoAlchemy
- Bootstrap
- MongoDB
- Docker

- docker pull rackeric/flask_app1
- docker pull rackeric/mongo

- docker run -d --name mongo rackeric/mongo:latest
- docker run -d -p 5000:5000 --name flaskapp1 --link mongo rackeric/flask_app1:latest
