from flask import Flask
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
#
# websites i used to help with this project
# 
# https://stackoverflow.com/questions/22275412/sqlalchemy-return-all-distinct-column-values
# https://stackoverflow.com/questions/47027451/python-appending-to-a-list-in-a-dictionary
# https://hackersandslackers.com/database-queries-sqlalchemy-orm/
# 
# 
# 
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website=db.Column(db.String(120))
    seeking_talent=db.Column(db.Boolean,default=False)
    genres = db.Column("genres", db.ARRAY(db.String))
    seeking_description=db.Column(db.String(120))
    shows=db.relationship('Show',backref='venue')
    
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website=db.Column(db.String(120))
    seeking_description=db.Column(db.String(120))
    seeking_venue=db.Column(db.Boolean,default=False)
    shows = db.relationship('Show', backref='artist', lazy = True)
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show(db.Model):
    __tablename__ = 'show'
    id= db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=True)
    artist_id=db.Column(db.Integer,db.ForeignKey('artist.id'), nullable=True)
    start_time=db.Column(db.DateTime)