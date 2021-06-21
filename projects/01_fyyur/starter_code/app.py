#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler, error
from flask_wtf import Form
from sqlalchemy.orm import backref
from werkzeug.wrappers import response
from forms import *
from models import *
from flask_migrate import Migrate, current
import sys

# TODO: connect to a local postgresql database


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  
  # we get every variation of state and city
  city_state=db.session.query(Venue).distinct(Venue.state,Venue.city).all()
  format=[]
  for cs in city_state:
    #we group the venues with the same state and city
    csvenues=db.session.query(Venue).filter_by(state=cs.state,city=cs.city).all()
    venueformat=[]
    for venue in csvenues:
      current_time=datetime.now()
      #we get upcoming by filtering date and id
      upcoming_query=db.session.query(Show).filter(Show.venue_id == venue.id , Show.start_time > current_time).all()
      venueformat.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows":len(upcoming_query)
      })
  #assemble the data
    format.append({
    "city": cs.city,
    "state": cs.state,
    "venues":venueformat
    })
    


  return render_template('pages/venues.html', areas=format);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search=request.form.get('search_term', '')
  resualt=db.session.query(Venue).filter(Venue.name.ilike(f'%{search}%')).all()
  formatted_query=[]
  for venue in resualt:
    current_time=datetime.now()
    upcoming_query=db.session.query(Show).filter(Show.venue_id == venue.id , Show.start_time > current_time).all()
    num_upcoming_shows = len(upcoming_query)
    formatted_query.append({
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': num_upcoming_shows
    })
  responseFORMAT={
    "count": 1,
    "data": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
    
  }
  response={
  "count":len(resualt),
  "data":formatted_query,
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  venue = db.session.query(Venue).get(venue_id)
  if venue is None :
    return render_template('errors/404.html')

  current_date=datetime.now()
  #get each query individually 
  #past_Shows=db.session.query(Show).filter(Show.venue_id==venue_id,Show.start_time < current_date).all()
  # upcoming_shows=db.session.query(Show).filter(Show.venue_id==venue_id, Show.start_time > current_date).all()

  past_Shows=db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id,Show.start_time < current_date).all()
  upcoming_shows=db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id, Show.start_time > current_date).all()
  data={
    "id": venue_id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": [],
    "upcoming_shows": [],
    "past_shows_count": len(past_Shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
#assemble data going through each query
  for pshow in past_Shows:
    data["past_shows"].append({
      "artist_id": pshow.artist_id,
      "artist_name": pshow.artist.name,
      "artist_image_link": pshow.artist.image_link,
      "start_time":format_datetime(str(pshow.start_time))
    })
  for ushow in upcoming_shows:
    data["upcoming_shows"].append({
      "artist_id": ushow.artist_id,
      "artist_name": ushow.artist.name,
      "artist_image_link": ushow.artist.image_link,
      "start_time":format_datetime(str(ushow.start_time)) 
    })


  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  form = VenueForm(request.form)
  if not form.validate():
    return render_template('forms/new_venue.html', form=form)
  error = False
  try:
    venue=Venue(
      name=request.form.get('name'),
      city=request.form.get('city'),
      address=request.form.get('address'),
     state=request.form.get('state'),
     phone=request.form.get('phone'),
     genres=request.form.getlist('genres'),
     image_link=request.form.get('image_link'),
     facebook_link=request.form.get('facebook_link'),
     website=request.form.get('website_link'),
     seeking_description=request.form.get('seeking_description'),
     seeking_talent=True if request.form.get('seeking_talent') == 'y' else False ,
     
    )
    db.session.add(venue)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info()) 
  finally:
    db.session.close()
    if error:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    
  



  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
 
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  
  try:
    db.session.query(Venue).filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artist=db.session.query(Artist).all()
  format=[]
  for art in artist:
    format.append({
    "id": art.id,
    "name": art.name,
    })
  

  return render_template('pages/artists.html', artists=format)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search=request.form.get('search_term', '')
  resualt=db.session.query(Artist).filter(Artist.name.ilike(f'%{search}%')).all()
  formatted_query=[]
  for artist in resualt:
    current_time=datetime.now()
    upcoming_query=db.session.query(Show).filter(Show.artist_id == artist.id,Show.start_time > current_time ).all()
    num_upcoming_shows = len(upcoming_query)
    formatted_query.append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': num_upcoming_shows
    })

  responseFORMAT={
    "count": 1,
    "data": [{
      "id": 4,
      "name": "Guns N Petals",
      "num_upcoming_shows": 0,
    }]
  }
  response={
  "count":len(resualt),
  "data":formatted_query,
  }
  return render_template('pages/search_artists.html', results=response, search_term=search)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = db.session.query(Artist).get(artist_id)
  if artist is None :
    return render_template('errors/404.html')
    
  current_date=datetime.now()
  #past_Shows=db.session.query(Show).filter(Show.artist_id==artist_id,Show.start_time < current_date).all()
  #upcoming_shows=db.session.query(Show).filter(Show.artist_id==artist_id,Show.start_time > current_date).all()
  
  past_Shows=db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id,Show.start_time < current_date).all()
  upcoming_shows=db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id,Show.start_time > current_date).all()


  data={
    "id": artist_id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": [],
    "upcoming_shows": [],
    "past_shows_count": len(past_Shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  for pshow in past_Shows:
    data["past_shows"].append({
      "venue_id": pshow.venue_id,
      "venue_name": pshow.venue.name,
      "venue_image_link": pshow.venue.image_link,
      "start_time":format_datetime(str(pshow.start_time))
    })
  for ushow in upcoming_shows:
    data["upcoming_shows"].append({
      "venue_id": ushow.venue_id,
      "venue_name": ushow.venue.name,
      "venue_image_link": ushow.venue.image_link,
      "start_time":format_datetime(str(ushow.start_time)) 
    })
    
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()


  # TODO: populate form with fields from artist with ID <artist_id>
  artist= db.session.query(Artist).get(artist_id)

  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.genres.data = artist.genres
  form.phone.data = artist.phone
  form.image_link.data = artist.image_link
  form.website_link.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = db.session.query(Artist).get(artist_id)
  try:
    artist.name = request.form.get('name')
    artist.city = request.form.get('city')
    artist.state  = request.form.get('state')
    artist.genres = request.form.getlist('genres')
    artist.phone=request.form.get('phone')
    artist.image_link =  request.form.get('image_link')
    artist.facebook_link  =request.form.get('facebook_link')
    artist.website  = request.form.get('website_link')
    #the returned value from FORM is y
    artist.seeking_venue  = True if request.form.get('seeking_venue') == 'y' else False
    artist.seeking_description  = request.form.get('seeking_description')
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  # TODO: populate form with values from venue with ID <venue_id>

  venue= db.session.query(Venue).get(venue_id)
  form.name.data = venue.name
  form.city.data = venue.city
  form.address.data=venue.address
  form.state.data = venue.state
  form.genres.data = venue.genres
  form.phone.data = venue.phone
  form.image_link.data = venue.image_link
  form.website_link.data = venue.website
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = db.session.query(Venue).get(venue_id).all()
  try:
    venue.name = request.form.get('name')
    venue.city = request.form.get('city')
    venue.state  = request.form.get('state')
    venue.address= request.form.get('address')
    venue.genres = request.form.getlist('genres')
    venue.phone=request.form.get('phone')
    venue.image_link =  request.form.get('image_link')
    venue.facebook_link  = request.form.get('facebook_link')
    venue.website  = request.form.get('website_link')
    venue.seeking_talent = True if request.form.get('seeking_talent') == 'y' else False 
    venue.seeking_description  = request.form.get('seeking_description')
    db.session.commit()

  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  form = ArtistForm(request.form)
  if not form.validate():
    return render_template('forms/new_artist.html', form=form)
  error=False
  
  try:
    artist=Artist(
      name=request.form.get('name'),
      city=request.form.get('city'),
     state=request.form.get('state'),
     phone=request.form.get('phone'),
     genres=request.form.getlist('genres'),
     image_link=request.form.get('image_link'),
     facebook_link=request.form.get('facebook_link'),
     website=request.form.get('website_link'),
     seeking_description=request.form.get('seeking_description'), 
     seeking_venue=True if request.form.get('seeking_venue') == 'y' else False ,
    )
    db.session.add(artist)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info()) 
  finally:
    if error:
      flash('An error occurred. Artist ' + request.form['name'] +' could not be listed.')
    else:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')



  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  show=db.session.query(Show).all()
  format=[]

  for sh in show:
    format.append({
    "venue_id": sh.venue_id,
    "venue_name": sh.venue.name,
    "artist_id": sh.artist_id,
    "artist_name": sh.artist.name,
    "artist_image_link": sh.artist.image_link,
    "start_time":format_datetime(str(sh.start_time))
    })


  return render_template('pages/shows.html', shows=format)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error=False
  try:
    show=Show(
      venue_id=request.form.get('venue_id'),
      artist_id=request.form.get('artist_id'),
      start_time=request.form.get('start_time')
    )
    db.session.add(show)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info()) 
  finally:
    if error:
      flash('An error occurred. Show could not be listed.')
    else:
      flash('Show was successfully listed!')
      
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
