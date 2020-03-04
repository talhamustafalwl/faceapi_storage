from flask import Flask, json, Response, request, render_template
from werkzeug.utils import secure_filename
import time
from os import path, getcwd
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import time
#first command on console for local test(pipenv shell)
#Storing traing images in storage/training and for recognzing storage/training folder
#working in local But after heroku deploy give directory error

app = Flask(__name__)

#using here sqlalchemy
#change env to prod during live
ENV = 'prod'

if ENV == 'dev':

    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://talha:talha@localhost/face'
else:
    app.debug = False
    #heroku addons:create heroku-postgresql:hobby-dev --app appname
    #heroku config --app appname(generate postgresql db)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://rqdsdpzcdocsdt:6fbbdc2a16b3994454ef1bf17b043d3e8005f8798aa138ec660aabc996eda99a@ec2-34-233-186-251.compute-1.amazonaws.com:5432/dee9e6frullrdv'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    created = db.Column(db.Integer)
    user_id = db.Column(db.Integer)

    def __init__(self, name,created,user_id):
        self.name = name
        self.created = created
        self.user_id = user_id


class Face(db.Model):
    __tablename__ = 'face'
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.Integer)
    filename = db.Column(db.Text())
    user_id  =db.Column(db.Integer,nullable=False)


    def __init__(self, user_id,filename,created):
        self.user_id=user_id
        self.filename = filename
        self.created = created


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,nullable=False)
    created = db.Column(db.Integer)
    name= db.Column(db.String(80))
    sync = db.Column(db.Integer)
    time_in = db.Column(db.Integer)
    time_out = db.Column(db.Integer)
    break_in = db.Column(db.Integer)
    break_out = db.Column(db.Integer)
    toggletime= db.Column(db.Integer)
    togglebreak = db.Column(db.Integer)
    filenamein = db.Column(db.Text())
    filenameout = db.Column(db.Text())
    breaktime = db.Column(db.Integer)

    def __init__(self, user_id,created,name,sync,time_in,time_out,break_in,break_out,toggletime,togglebreak,filenamein,filenameout,breaktime):
        self.user_id=user_id
        self.created = created
        self.name=name
        self.sync=sync
        self.time_in=time_in
        self.time_out=time_out
        self.break_in=break_in
        self.break_out=break_out
        self.toggletime=toggletime
        self.togglebreak=togglebreak
        self.filenamein=filenamein
        self.filenameout=filenameout
        self.breaktime= breaktime



app.config['file_allowed'] = ['image/png', 'image/jpeg', 'image/jpg']
app.config['storage'] = path.join(getcwd(), 'storage')



import face_recognition
from os import path


class Facec:
    def __init__(self, app):
        self.storage = app.config["storage"]
        self.faces = []  # storage all faces in caches array of face object
        self.known_encoding_faces = []  # faces data for recognition
        self.face_user_keys = {}
        #self.load_all()

    def load_user_by_index_key(self, index_key=0):

        key_str = str(index_key)

        if key_str in self.face_user_keys:
            return self.face_user_keys[key_str]

        return None

    def load_train_file_by_name(self, name):
        trained_storage = path.join(self.storage, 'trained')
        return path.join(trained_storage, name)

    def load_unknown_file_by_name(self, name):
        unknown_storage = path.join(self.storage, 'unknown')
        return path.join(unknown_storage, name)

    def load_all(self):
        print("called load all")
        #results = self.db.select('SELECT faces.id, faces.user_id, faces.filename, faces.created FROM faces')
        results =db.session.query(Face.id,Face.user_id,Face.filename,Face.created).all()
        print("----------------------")
        print(results)
        print("----------------------")
        for row in results:

            user_id = row[1]
            
            filename = row[2]
            face = {
                "id": row[0],
                "user_id": user_id,
                "filename": filename,
                "created": row[3]
            }
            self.faces.append(face)
            print("loading images face_image")

            face_image = face_recognition.load_image_file(self.load_train_file_by_name(filename))
            print("loading images face_image_encoding")
            face_image_encoding = face_recognition.face_encodings(face_image)[0]
            print("done images face_image_encoding")
            index_key = len(self.known_encoding_faces)
            self.known_encoding_faces.append(face_image_encoding)
            index_key_string = str(index_key)
            self.face_user_keys['{0}'.format(index_key_string)] = user_id

    def recognize(self, unknown_filename):
        print("called recognize")
        unknown_image = face_recognition.load_image_file(self.load_unknown_file_by_name(unknown_filename))
        ##handle index out of range
        if not len(face_recognition.face_encodings(unknown_image)):
            print( "can't be encoded")
            return None
        ##
        unknown_encoding_image = face_recognition.face_encodings(unknown_image)[0] 
        if self.known_encoding_faces == []:
            print("array is empty")
            self.load_all()
        resultsval = face_recognition.face_distance(self.known_encoding_faces, unknown_encoding_image)
        print("resultsval", resultsval)
        
        #results = face_recognition.compare_faces(self.known_encoding_faces, unknown_encoding_image, tolerance=0.5)
        #print("results", results)


        min=1
        for valuee in resultsval:
             if min >= valuee:
                 min = valuee
        print(min)
        if min < 0.56:
            import numpy as np
            print(np.where(resultsval == min)[0][0])
            index_key=np.where(resultsval == min)[0][0]
            user_id = self.load_user_by_index_key(index_key)
            return user_id
        return None
         
       # index_key = 0
       # for matched in results:
#
       #     if matched:
       #         # so we found this user with index key and find him
       #         user_id = self.load_user_by_index_key(index_key)
#
       #         return user_id
#
       #     index_key = index_key + 1
#
       # return None



app.face = Facec(app)

def success_msg(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)


def error_msg(error_message, status=203, mimetype='application/json'):
    return Response(error_message, status=status, mimetype=mimetype)



@app.route('/api/addtoken', methods=['POST'])
def token():
    print("token api called")
    if request.method == 'POST':
        token=request.form['token']
        print("tokren==", token)
        created = int(time.time())
        token_add=Client(created,token)
        db.session.add(token_add)
        db.session.commit()
        return_output = json.dumps({"id": token_add.id, "token": token_add.token})
        return success_msg(return_output)


# Hompage
@app.route('/', methods=['GET'])
def page_home():
    return render_template('index.html')


@app.route('/api', methods=['GET'])
def homepage():
    output = json.dumps({"msg": '/api/train=(name,file) <--add file and name of person, /api/recognize=(file) <--add file(pic) to recognize, api/users/:id (GET,DELETE)'})
    return success_msg(output)


@app.route('/api/train', methods=['POST'])
def submit():
    if request.method == 'POST':
        if 'auth' not in request.headers or request.headers['auth'] != "abc123xyz":
           print ("not authenticated")
           error =json.dumps({"message":"not authenticated","status":"400", "data": []})
           return error_msg(error)

        elif 'user_id' not in request.form:
            print ("user_id is required")
            error =json.dumps({"message":"user_id is not provided","status":"400", "data": []})
            return error_msg(error)

        elif 'name' not in request.form:
            print ("name is required")
            error =json.dumps({"message":"name is not provided","status":"400", "data": []})
            return error_msg(error)
        elif 'file' not in request.files:
                name=request.form['name']
                print("Information of that face", name)
                print ("Face image is required")
                error =json.dumps({"message":"Image not provided","status":"400", "data": []})
                return error_msg(error)
        else:
            print("File request", request.files)
            file = request.files['file']
            if file.mimetype not in app.config['file_allowed']:

                print("File extension is not allowed")
                error =json.dumps({"message":"File extension is not allowed","status":"400", "data": []})
                return error_msg(error)

            else:

                name=request.form['name']
                user_id=request.form['user_id']
                print("Information of that face", name)
                print("File is allowed and will be saved in ", app.config['storage'])

                filename = secure_filename(file.filename)
                trained_storage = path.join(app.config['storage'], 'trained')
                file.save(path.join(trained_storage, filename))
                print("file saved train")
                created = int(time.time())

                user_id=User(name,created,user_id)

                db.session.add(user_id)
                db.session.commit()
                if user_id:

                    print("User saved in data", name, user_id.id)
                    user_id=user_id.id
                    face_id=Face(user_id,filename,created)
                    db.session.add(face_id)
                    db.session.commit()
                    if face_id:
                        print("cool face has been saved",face_id.id)
                        face_data = {"id": face_id.id, "filename": filename, "created": created}
                        return_output = json.dumps({"message":"training done","status":"200", "data": {"face":[face_data], "name": name,"id": user_id}})
                        app.face = Facec(app)
                        app.face.load_all()
                        return success_msg(return_output)
                    else:
                        print("An error saving face image.")
                        error =json.dumps({"message":"An error saving face image.","status":"400", "data": []})
                        return error_msg(error)

                else:
                    print("Something happend")
                    error =json.dumps({"message":"An error inserting new user","status":"400", "data": []})
                    return error_msg(error)    
                    

    return success_msg(return_output)



def get_user_by_id(user_id):
    user = {}
    results=db.session.query(User.id,User.name,User.created,Face.id,Face.user_id,Face.filename,Face.created,User.user_id).outerjoin(Face,User.id== Face.user_id).filter(User.id == user_id).all()
    index = 0
    for row in results:
     # print(row)
        face = {
            "id": row[3],
            "user_id": row[4],
            "filename": row[5],
            "created": row[6],
        }
        if index == 0:
            user = {
                "id": row[0],
                "name": row[1],
                "created": row[2],
                "user_id": row[7],
                "faces": [],
            }
        if row[3]:
            user["faces"].append(face)
        index = index + 1

    if 'id' in user:
        return user
    return None



def delete_user_by_id(user_id):
    print(user_id)
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    Face.query.filter_by(user_id=user_id).delete()
    db.session.commit()

@app.route('/api/users/<int:user_id>', methods=['GET', 'DELETE'])
def user_profile(user_id):
    if request.method == 'GET':
        user = get_user_by_id(user_id)
        if user:
            return success_msg(json.dumps(user), 200)
        else:
            return error_msg("User not found", 404)
    if request.method == 'DELETE':
        delete_user_by_id(user_id)
        app.face = Facec(app)
        app.face.load_all()
        return success_msg(json.dumps({"deleted": True}))

   
# router for recognize a unknown face
@app.route('/api/recognize', methods=['POST'])
def recognize():
    if 'file' not in request.files:
        error =json.dumps({"message":"Image is required","status":"400", "data": []})
        return error_msg(error)
    else:
        file = request.files['file']
        # file extension valiate
        if file.mimetype not in app.config['file_allowed']:
            error =json.dumps({"message":"We  only allow file with *.png , *.jpg, *.jepg","status":"400", "data": []})
            return error_msg(error)
        else:

            filename = secure_filename(file.filename)
            unknown_storage = path.join(app.config["storage"], 'unknown')
            file_path = path.join(unknown_storage, filename)
            file.save(file_path)
            print("recognize file save")
            #app.face = Facec(app)
            #app.face.load_all()
            user_id = app.face.recognize(filename)
            print("recognizion done")
            if user_id:
                print("user matched id={}".format(user_id))
                user = get_user_by_id(user_id) 

                if 'button' in request.form: #only if
                    res = Attendance.query.filter_by(user_id = user["user_id"]).order_by(Attendance.id.desc()).first()
                    
                    if request.form['button'] == "time":
                        print("button time")
                        if res == None or res.toggletime == 0:
                            stringp="Welcome"
                            user_id=user["user_id"]
                            name=user["name"]
                            created=int(time.time())
                            sync=0
                            toggletime=1
                            togglebreak=0
                            time_in=int(time.time())
                            time_out=0
                            break_in=0
                            break_out=0
                            breaktime=0
                            filenamein=filename
                            filenameout=''

                            attendance_id=Attendance(user_id,created,name,sync,time_in,time_out,break_in,break_out,toggletime,togglebreak,filenamein,filenameout,breaktime)
                            db.session.add(attendance_id)
                            db.session.commit()
                            
                        else:
                            print("in else condition")
                            stringp="Good Bye"
                            res.toggletime=0
                            res.sync=0
                            res.time_out=int(time.time())
                            res.filenameout=filename
                            dt_object1 = datetime.fromtimestamp(res.time_in)
                            print(dt_object1)
                            db.session.commit()
                            #dt_object1 = datetime.fromtimestamp(res.time_in)
                            #dt_object2 = datetime.fromtimestamp(res.time_out)
                            
                        
                    if request.form['button'] == "break":
                        print("in break condition")
                        if res.toggletime == 1:
                            print("Can take break")
                            if res.togglebreak == 0:
                                stringp="Good bye take break"
                                res.break_in=int(time.time())
                                res.sync=0
                                res.togglebreak=1
                                db.session.commit()
                                print("break out")
                               
                            elif res.togglebreak == 1:
                                stringp="Welcome back from break"
                                res.break_out=int(time.time())
                                res.togglebreak=0
                                res.sync=0
                                rr=(res.break_out - res.break_in)
                                res.breaktime=res.breaktime + rr
                                db.session.commit()
                                print("break")
                               
                            else:
                                print("error")
                        else:
                            print("break else condition")
                            message =json.dumps({"message":"Not time in","status":"400", "data": []})
                            return error_msg(message)
                
                
                message =json.dumps({"message":"{} {}".format(stringp,user["name"]),"status":"200", "data": [user]})
                return success_msg(message)

            else:
                error =json.dumps({"message":"Image not matched with any person","status":"400", "data": []})
                return error_msg(error)

            



if __name__ == '__main__':
    app.run(host="0.0.0.0")




