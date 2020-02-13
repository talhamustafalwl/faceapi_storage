from flask import Flask, json, Response, request, render_template
from werkzeug.utils import secure_filename
import time
from os import path, getcwd
from flask_sqlalchemy import SQLAlchemy
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
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://szidfxunekyrwl:101fa5e675b12d2002771fdf860c257e96e8992fdd975e15cc634f4672edb36e@ec2-54-80-184-43.compute-1.amazonaws.com:5432/d1tanhi36jtn41'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    created = db.Column(db.Integer)

    def __init__(self, name,created):
        self.name = name
        self.created = created


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

#for token
class Client(db.Model):
    __tablename__ = 'client'
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.Integer)
    token  =db.Column(db.String)


    def __init__(self, created,token):
        self.created=created
        self.token = token
##
        

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
        unknown_encoding_image = face_recognition.face_encodings(unknown_image)[0]
        print(self.known_encoding_faces)
        results = face_recognition.compare_faces(self.known_encoding_faces, unknown_encoding_image)

        print("results", results)

        index_key = 0
        for matched in results:

            if matched:
                # so we found this user with index key and find him
                user_id = self.load_user_by_index_key(index_key)

                return user_id

            index_key = index_key + 1

        return None

app.face = Facec(app)

def success_msg(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)


def error_msg(error_message, status=500, mimetype='application/json'):
    return Response(json.dumps({"error": {"message": error_message}}), status=status, mimetype=mimetype)




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
        if 'file' not in request.files:
                name=request.form['name']
                print("Information of that face", name)
                print ("Face image is required")
                return error_msg("Face image is required.")
        else:
            print("File request", request.files)
            file = request.files['file']
            if file.mimetype not in app.config['file_allowed']:

                print("File extension is not allowed")
                return error_msg("We are only allow upload file with *.png , *.jpg, *.jepg")

            else:

                name=request.form['name']
                print("Information of that face", name)
                print("File is allowed and will be saved in ", app.config['storage'])

                filename = secure_filename(file.filename)
                trained_storage = path.join(app.config['storage'], 'trained')
                file.save(path.join(trained_storage, filename))
                print("file saved train")
                created = int(time.time())

                user_id=User(name,created)

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
                        return_output = json.dumps({"id": user_id, "name": name, "face": [face_data]})
                        #app.face.load_all()
                        return success_msg(return_output)
                    else:
                        print("An error saving face image.")
                        return error_msg("error in saving face image.")

                else:
                    print("Something happend")
                    return error_msg("An error inserting new user")    
                    

    return success_msg(return_output)



def get_user_by_id(user_id):
    user = {}
    results=db.session.query(User.id,User.name,User.created,Face.id,Face.user_id,Face.filename,Face.created).outerjoin(Face,User.id== Face.user_id).filter(User.id == user_id).all()
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
        return error_msg("Image is required")
    else:
        file = request.files['file']
        # file extension valiate
        if file.mimetype not in app.config['file_allowed']:
            return error_msg("We  only allow file with *.png , *.jpg, *.jepg")
        else:

            filename = secure_filename(file.filename)
            unknown_storage = path.join(app.config["storage"], 'unknown')
            file_path = path.join(unknown_storage, filename)
            file.save(file_path)
            print("recognize file save")
            app.face.load_all()
            user_id = app.face.recognize(filename)
            if user_id:
                user = get_user_by_id(user_id)
                message = {"message": "{0} image matched with your face".format(user["name"]),
                           "user": user}
                return success_msg(json.dumps(message))
            else:

                return error_msg("Image not matched with any person")


if __name__ == '__main__':
    app.run()




