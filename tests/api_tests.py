import unittest
import os
import shutil
import json
from urlparse import urlparse
from StringIO import StringIO

import sys; print sys.modules.keys()
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())

    def testGetSongs(self):
        """Gets list of songs"""

        # Populate DB
        file_1 = models.File(name="filename_1.mp3")
        song_1 = models.Song()
        file_1.song = song_1

        file_2 = models.File(name="filename_2.mp3")
        song_2 = models.Song()
        file_2.song = song_2
        
        session.add_all([song_1,song_2,file_1,file_2])        
        session.commit()
        
        # Send stuff to get endpoint
        response = self.client.get("/api/songs",headers=[("Accept", "application/json")])
        
        # General assertions
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.mimetype, "application/json")  
      
        # Data assetions
        data = json.loads(response.data)
        self.assertEqual(len(data),2)
        
        song_1 = data[0]
        self.assertEqual(song_1["file"]["name"],"filename_1.mp3")
        song_2 = data[1]
        self.assertEqual(song_2["file"]["name"],"filename_2.mp3")

    def testPostSong(self):
        """Posts a song"""
        
        # Populate JSON
        data = {"name":"filename_1.mp3"}

        # Send stuff to POST endpoint
        response = self.client.post("/api/songs", data=json.dumps(data), content_type="application/json",headers=[("Accept", "application/json")])
      
        # General assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")

        # Check content response
        data = json.loads(response.data)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["file"]["name"], "filename_1.mp3")

        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)

        song = songs[0]
        self.assertEqual(song.id, 1)
        self.assertEqual(song.file.name, "filename_1.mp3")

        
    def testUnsupportedAcceptHeader(self):
        response = self.client.get("/api/songs",
            headers=[("Accept", "application/xml")]
        )

        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"],
                         "Request must accept application/json data")
        

    def test_get_uploaded_file(self):
        path =  upload_path("test.txt")
        with open(path, "w") as f:
            f.write("File contents")

        response = self.client.get("/uploads/test.txt",headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertEqual(response.data, "File contents")

    def test_file_upload(self):
        data = {
            "file": (StringIO("File contents"), "test.txt")
        }

        #response = self.client.post("/api/files",data=data,content_type="multipart/form-data")
        print "EEN"
        response = self.client.post("/api/files",data=data,content_type="multipart/form-data", headers=[("Accept", "application/json")])

        print "ZES"        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")

        print "ZEVEN"                
        data = json.loads(response.data)
        self.assertEqual(urlparse(data["path"]).path, "/uploads/test.txt")

        print "ACHT"        
        path = upload_path("test.txt")
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            contents = f.read()
        self.assertEqual(contents, "File contents")        
        
        