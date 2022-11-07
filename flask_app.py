from pytz import country_names
from flask import Flask, request, flash, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy 
import geojson
from sqlalchemy import lateral
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

#https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///QuestMaps.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "random string"


import folium

db = SQLAlchemy(app)

class UserQuest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey("user.id")) 
    quest_id = db.Column(db.ForeignKey("quest.id"))
    quest = db.relationship("Quest")#, back_populates="users")
    #user = db.relationship("User", back_populates="quests")
    locations = db.relationship("UserQuestLocation")#, back_populates="userquest")

    def get_GeoJson(self, Status = 'Unvisited'):

        print(self.locations[0])
        #fList = list(map(Location.get_GeoJson,self.locations))
        fList = []
        if Status == 'Visited':
            for location in self.locations:
                if location.completion_date:
                    fList.append(location.location.get_GeoJson())
        
        if Status == 'Unvisited':
            for location in self.quest.locations:
                ## inject the userquest.id ????
                fList.append(location.get_GeoJson())

        if Status == 'In progress':
            for location in self.locations:
                if not location.completion_date:
                    fList.append(location.location.get_GeoJson())
        if len(fList):

            feature_collection = geojson.FeatureCollection(fList)
            dump = geojson.dumps(feature_collection, sort_keys=True)
            return dump
        return None

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(60))
    quests = db.relationship("UserQuest") #, back_populates="quest")

    def __init__(self, name, email):
        self.name = name
        self.email = email

# many-to-many relationship between user and quest.

class Quest(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    author = db.Column(db.String(100))
    quest_name = db.Column(db.String(100))
    locations = db.relationship("Location", lazy="joined")
    #users = db.relationship("UserQuest", back_populates="quest")


    def __init__(self, author, quest_name):
        self.author = author
        self.quest_name = quest_name

    def get_GeoJson(self):

        print(self.locations[0])
        #fList = list(map(Location.get_GeoJson,self.locations))
        fList = []
        for location in self.locations:
            fList.append(location.get_GeoJson())

        feature_collection = geojson.FeatureCollection(fList)
        dump = geojson.dumps(feature_collection, sort_keys=True)
        return dump

    

    def createLocations(self, FC):
        for feature in FC.features:
            #print(feature)

            location = Location(
                quest = self,
                location_name = feature.properties["name"],
                latitude = feature.geometry.coordinates[1],
                longitude = feature.geometry.coordinates[0],
                description = feature.properties["description"])



#change the erd so its locations and a many-to-many with quest


class Location(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    # foriegn key
    quest_id = db.Column(db.Integer,db.ForeignKey("quest.id"))
    quest = db.relationship("Quest", back_populates ="locations")

    location_name = db.Column(db.String(100))
    latitude = db.Column(db.Float(100))
    longitude = db.Column(db.Float(100))
    description = db.Column(db.String())
    

    #userquests = db.relationship("UserQuest", back_populates ="location")

    def get_GeoJson(self):
        form = render_template('locationform.html',location=self )
        feature = geojson.Feature(geometry=geojson.Point((self.longitude, self.latitude)),
        properties= {
            "name":self.location_name,
            "description":self.description, 
            "form":form
            })
        return feature


    def __init__(self,location_name,latitude,longitude,description,quest):
        self.location_name = location_name
        self.latitude = latitude
        self.longitude = longitude 
        self.description = description
        self.quest = quest
        








class UserQuestLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userquest_id = db.Column(db.ForeignKey("user_quest.id"))
    location_id = db.Column(db.ForeignKey("location.id"))
    completion_date = db.Column(db.DateTime())
    notes = db.Column(db.String())
    userquest = db.relationship("UserQuest", back_populates="locations")
    location= db.relationship("Location")# ,back_populates="userquests")

    def __init__(self,completion_date, notes):
        self.completion_date = completion_date
        self.notes = notes


#class students(db.Model):
#    id = db.Column('quest_id', db.Integer, primary_key = True)

app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
admin = Admin(app, name='QuestMaps', template_mode='bootstrap3')
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Quest, db.session))
admin.add_view(ModelView(UserQuest, db.session))
admin.add_view(ModelView(Location, db.session))
admin.add_view(ModelView(UserQuestLocation, db.session))
    




@app.route('/')
def index():
    return render_template('index.html', quests = Quest.query.all() )

# To do - add URLs "user/1/quest" and "user/1/quest/1/map"


@app.route("/user/<int:id>/quests")
def user_quest_list(id):
    user = db.session.query(User).get_or_404(id)
    return render_template('user_quest_list.html', user = user)


@app.route("/userquest/<int:id>/location/<int:locationid>/create" , methods = ['POST'])
def user_quest_location_create(id, locationid,):
    userquest = db.session.query(UserQuest).get_or_404(id)

    #check if userquest has location in   
    #if if it does then throw error
    # if not then create one from values in the form
    #Then save it 
    #redirect to the id
    return redirect(url_for("user_quest_map", id=id, map_only = True))

@app.route("/userquest/<int:id>/map")
def user_quest_map(id):
    map_only = request.args.get("map_only", False)
        
    userquest = db.session.query(UserQuest).get_or_404(id)
    start_coords = (46.9540700, 142.7360300)
    folium_map = folium.Map(location=start_coords, zoom_start=14)
    gjGeo = userquest.get_GeoJson()
    if(gjGeo): 
        gj = folium.GeoJson(
            gjGeo, 
            name= userquest.quest.quest_name,
            marker=folium.map.Marker(icon = folium.Icon(color='red')),
            #marker=folium.vector_layers.CircleMarker(),
            tooltip=folium.GeoJsonTooltip(fields=['name'],
                labels=False, ),
            popup =folium.GeoJsonPopup(fields=['name','description',"form"],
                labels=False, ),
                
            ).add_to(folium_map)

    gjGeo2 = userquest.get_GeoJson('Visited')
    if(gjGeo2): 
        gj_visited = folium.GeoJson(
            gjGeo2, 
            name= userquest.quest.quest_name + " Visited",
            marker=folium.map.Marker(icon = folium.Icon(color = 'green', icon = 'check')),
            #marker=folium.vector_layers.CircleMarker(icon = folium.Icon(color = 'green')),
            tooltip=folium.GeoJsonTooltip(fields=['name'],
                labels=False, ),
            ).add_to(folium_map)


    gjGeo3 = userquest.get_GeoJson('In progress')
    if(gjGeo3): 
        gj_in_progress = folium.GeoJson(
            gjGeo3, 
            name= userquest.quest.quest_name + " In progress",
            marker=folium.map.Marker(icon = folium.Icon(color = 'orange')),
            #marker=folium.vector_layers.CircleMarker(icon = folium.Icon(color = 'orange')),
            tooltip=folium.GeoJsonTooltip(fields=['name'],
                labels=False, ),
            ).add_to(folium_map)


    folium_map.fit_bounds(folium_map.get_bounds(), padding=(30, 30))
    
    print ("map_only" , map_only)
    if map_only :
        return  folium_map._repr_html_()

    return render_template('quest_map.html', quest_map = folium_map._repr_html_(), quest_name=userquest.quest.quest_name )


@app.route('/map')
def map():
    start_coords = (46.9540700, 142.7360300)
    folium_map = folium.Map(location=start_coords, zoom_start=14)
    gj = folium.GeoJson(
      "UNESCO.geojson", 
      name="UNESCO World Hertitage Sites in UK",
      #marker=folium.map.Marker(),
      marker=folium.vector_layers.CircleMarker()
      ).add_to(folium_map)
    folium_map.fit_bounds(folium_map.get_bounds(), padding=(30, 30))
    #return folium_map._repr_html_()
    return render_template('map.html', quest_map = folium_map._repr_html_() )


@app.route("/quest/<int:id>/map")
def quest_map(id):
    quest = db.session.query(Quest).get_or_404(id)
    start_coords = (46.9540700, 142.7360300)
    folium_map = folium.Map(location=start_coords, zoom_start=14)
    gj = folium.GeoJson(
      quest.get_GeoJson(), 
      name= quest.quest_name,
      marker=folium.map.Marker(),
      #marker=folium.vector_layers.CircleMarker(),
      tooltip=folium.GeoJsonTooltip(fields=['name'],
        labels=False, ),
      ).add_to(folium_map)
    folium_map.fit_bounds(folium_map.get_bounds(), padding=(30, 30))
    return render_template('quest_map.html', quest_map = folium_map._repr_html_(), quest_name=quest.quest_name )

@app.route('/about/') # routes "/about" to the html page "about.html"
def about():
    return render_template('about.html') 

@app.route('/settings/')# routes "/settings" to the html page "settings.html"
def settings():
    return render_template('settings.html')


@app.route('/start')
def start():
    db.create_all()
    quest = db.session.query(Quest).get(1)
    if not quest:    
        quest = Quest(author ='Liam', quest_name = 'UNESCO')
        db.session.add(quest)
    

    location = db.session.query(Location).get(1)
    if not location:
        with open("./UNESCO.geojson", "r") as UNESCO :
            FC = geojson.load(UNESCO)
            quest.createLocations(FC)
        '''
        location = Location(quest = quest,location_name = 'Durham Castle',latitude = 54.774, longitude = -1.575, description = 'Durham Castle and Cathedral')

        location = Location(quest = quest,location_name = 'Forth Bridge',latitude = 56.000421, longitude = -3.388726, description = 'A bridge')
        '''
        #db.session.add(location)



    user = db.session.query(User).get(1)
    if not user:
        user = User(name = 'Liam', email = '16dalel@utcsheffield.org.uk')
        db.session.add(user)




    db.session.commit()
    return render_template('about.html')
'''
@app.route('/db')
def show_all():
    return render_template('show_all.html', students = students.query.all() )
'''


@app.route('/new', methods = ['GET', 'POST'])
def new():
    if request.method == 'POST':
        if not request.form['name'] or not request.form['city'] or not request.form['addr']:
            flash('Please enter all the fields', 'error')
        else:
            student = students(request.form['name'], request.form['city'],
                request.form['addr'], request.form['pin'])

            db.session.add(student)
            db.session.commit()
            flash('Record was successfully added')
            return redirect(url_for('show_all'))
    return render_template('new.html')

if __name__ == '__main__':
    db.create_all()
    app.run(debug = True)
