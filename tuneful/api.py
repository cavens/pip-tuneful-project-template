import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

import models
import decorators
from tuneful import app
from database import session
from utils import upload_path


@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
    
    # Get the posts from the database
    songs = session.query(models.Song).all()

    # Convert the songs to JSON and return a response
    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype="application/json")
  

  
@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def songs_post():
    
    # Retreive data
    data = request.json

    # Post song
    file_1 = models.File(name=data["name"])
    song_1 = models.Song()
    file_1.song = song_1

    session.add(file_1,song_1)
    session.commit()
    
    # Construct and send back response
    data = json.dumps(file_1.song.as_dictionary())
    return Response(data,201,mimetype="application/json")


@app.route("/uploads/<filename>", methods=["GET"])
@decorators.accept("application/json")
def uploaded_file(filename):
    return send_from_directory(upload_path(), filename)  
  
  
  
@app.route("/api/files", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("multipart/form-data")
def file_post():
    file = request.files.get("file")
    if not file:
        data = {"message": "Could not find file data"}
        return Response(json.dumps(data), 422, mimetype="application/json")
    filename = secure_filename(file.filename)
    db_file = models.File(name=filename)
    session.add(db_file)
    session.commit()
    file.save(upload_path(filename))
    data = db_file.as_dictionary()
    return Response(json.dumps(data), 201, mimetype="application/json")

  
  
  
