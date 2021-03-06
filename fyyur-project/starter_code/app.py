#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask import wtf
from flask_wtf import Form
from forms import *
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    artists = db.relationship('Artist', secondary=Shows, backref=db.backref('venue', lazy=True))


    

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    

    

Shows = db.Table('Shows',
                  db.Column("id", db.Integer, primary_key=True),
                  db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), nullable=False),
                  db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), nullable=False),
                  db.Column('start_time', db.DateTime, default=datetime.utcnow()))

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

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
  data = []
  locations = Venue.query.distinct(Venue.city, Venue.state).all()
  for venue in locations:
    upcoming_shows = len(Venue.query.join(Shows).filter(Shows.start_time > datetime.utcnow(), Shows.venue_id == venue.id).all())

  for venue_data in Venue.query.filter_by(city=venue.city, state=venue).all():
    data.append({
      "city": venue.city,
      "state": venue.state,
      "venues": [{
        "id": venue_data.id,
        "name": venue_data.name,
        "num_upcoming_shows": upcoming_shows
      }]
    })
  
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  search_term = request.form.get("search_term", "")
  partial_search_response = Venue.query.filter(Venue.name.like("%{search_term}%")).all()
  data = []
  for venue in partial_search_response:
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(Venue.query.join(Shows).filter(Shows.start_time > datetime.utcnow(), Shows.venue_id == venue.id).all())
    })
  
  response = {
    "count": len(partial_search_response),
    "data": data
  }
  

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  
  venue = Venue.query.filter_by(id=venue_id).first()
  data = None
  artist_up_show = []
  artist_past_show = []
  shows = db.session.query(Shows).filter(Shows.venue_id == venue.id).all()

  for show in shows:
    artist = Artist.query.filter_by(id=show.artist_id).first()
    start_time = format_datetime(str(show.start_time))
    artist_show = {
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artists_image_link": artist.image_link,
      "start_time": start_time
    }

    if show.start_time >= datetime.utcnow():
      artist_up_show.append(artist_show)
    elif show.start_time < datetime.utcnow():
      artist_past_show.append(artist_show)
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "upcoming_shows": artist_up_show,
    "past_shows": artist_past_show,
    "past_shows_count": len(artist_past_show)
  }


  data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    image_url = request.form['image_url']
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    genres  = request.form.getlist('genres')
    image_link = request.form['image_link']
    seeking_talent = true if 'seeking_talent' in request.form else False
    seeking_description = request.form['seeking_description']

    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, image_url=image_url, facebook_link=facebook_link, website=website, genres=genres, image_link=image_link, seeking_talent=seeking_talent, seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash("An error occurred. Venue " + name + "could not be listed.")
  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')




  

 
  flash('Venue ' + request.form['name'] + ' was successfully listed!')
  
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  
  
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  
  data = db.session.query(Artist).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  
  search_term = request.form.get('search_term', '')
  partial_search_response = db.session.query(Artist).filter(Artist.name.like("%{search_term}%")).all()
  data = []
  for artist in partial_search_response:
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(Artist.query.join(Shows).filter(Shows.start_time > datetime.utcnow(), Shows.venue_id == artist.id).all())
    })
  
  response = {
    "count": len(partial_search_response),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  
 
  shows = db.session.query(Shows).filter(Shows.artist_id == artist_id).all() 
  data = None
  artist = Artist.query.filter_by(id = artist_id).first()
  past_shows = []

  for show in shows:
    past_shows.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time


    })

    upcoming_shows = db.session.query(Shows).join(Venue).filter(Shows.artist_id == artist_id).filter(Shows.start_time > datetime.utcnow())
    coming_shows = []

    for show in upcoming_shows:
      coming_shows.append({
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time
      })

    
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "address": artist.address,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_talent": artist.seeking_talent,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "upcoming_shows": coming_shows,
    "past_shows": past_shows,
    "past_shows_count": len(past_shows)
  }

  
  
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter_by(id=artist_id).first()
  
  form.name.data = artist.name
  form.genres.data = artist.genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link

 
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  
  form = ArtistForm()
  artist = Artist.query.filter_by(id=artist_id).first()

  artist.name = form.name.data
  artist.genres = form.genres.data
  artist.city = form.city.data
  artist.state = form.state.data
  artist.phone = form.phone.data
  artist.website = form.website.data
  artist.facebook_link = form.facebook_link.data

  db.session.add(artist)
  db.session.commit()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).first()

  form.name.data = venue.name
  form.genres.data = venue.genres
  form.address.data = venue.address
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.website = venue.website
  form.facebook_link = venue.facebook_link
  form.seeking_talent = venue.seeking_talent
  form.seeking_description = venue.seeking_description
  form.image_link = venue.image_link

  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).first()

  venue.name = form.name.data
  venue.genres = form.genres.data
  venue.address = form.address.data
  venue.city = form.city.data
  venue.state = form.state.data
  venue.phone = form.phone.data
  venue.website = form.website.data
  venue.facebook_link = form.facebook_link.data
  venue.seeking_talent = form.seeking_talent.data
  venue.seeking_description = form.seeking_description.data
  venue.image_link = form.image_link.data

  db.session.add(venue)
  db.commit()




  
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
 

  error = False


  artist_form = ArtistForm()
  name = artist_form.name.data
  city = artist_form.city.data
  phone = artist_form.phone.data
  state = artist_form.state.data
  genres = artist_form.genres.data
  facebook_link = artist_form.facebook_link.data
  image_url = artist_form.image_url.data
  website_link = artist_form.website_link.data
  seeking_venue = artist_form.seeking_venue.data
  seeking_description = artist_form.seeking_description.data

  artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_url=image_url, website_link=website_link, seeking_venue=seeking_venue, seeking_description=seeking_description)

  try:
    db.session.add(artist)
    db.session.commit()
    
  except:
    error = True
    db.session.rollback()
  
  finally:
    db.session.close()
  
  if error:
    flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
  
  if not error:
    flash('Artist ' + artist.name + ' was successfully listed!')




 
  return render_template('pages/home.html')




#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  

  data = []
  
  show_query = db.session.query(Shows).all()

  for show in show_query:
    
    data.append({
      "venue_id": show.id,
      "venue_name": show.name,
      "artist_id": Artist.name,
      "artist_image_link": Artist.image_link,
      "start_time": show.start_time
    })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  
  error = False
  show_form = ShowForm()

  try:
    artist_id = show_form.artist_id.data
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    show = Shows.insert().values(artist_id=artist_id, venue_id=venue_id, start_time=start_time)

    db.session.add(show)
    db.session.commit()
  
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  
  finally:
    db.session.close()
  
  if error:
    flash('An error occurred. Show could not be listed.')
  
  if not error:
    flash('Show was successfully listed!')


 
  flash('Show was successfully listed!')
  
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
