# Import the dependencies.
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Set up Flask
app = Flask(__name__)

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
@app.route('/')
def home():
    return (
        f"SurfsUp!<br>"
        f"Available Routes:<br>"
        f"/api/v1.0/precipitation<br>"
        f"/api/v1.0/stations<br>"
        f"/api/v1.0/tobs<br>"
        f"/api/v1.0/&lt;start&gt;<br>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;<br>"
    )


#################################################
# Flask Routes
#################################################

# Route to get the last 12 months of precipitation data
@app.route('/api/v1.0/precipitation')
def precipitation():
    # Get the most recent date
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
    most_recent_date = datetime.strptime(most_recent_date, "%Y-%m-%d")
    date_12_months_ago = most_recent_date - timedelta(days=365)

    # Query precipitation data for the last 12 months
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= date_12_months_ago).\
        order_by(Measurement.date).all()

    # Convert the results into a dictionary
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}

    # Return as JSON
    return jsonify(precipitation_dict)

# Route to get a list of stations
@app.route('/api/v1.0/stations')
def stations():
    # Query list of stations
    stations_data = session.query(Station.station).all()

    # Convert to list of station IDs
    stations_list = [station[0] for station in stations_data]

    # Return as JSON
    return jsonify(stations_list)

# Route to get temperature observations for the most active station in the last 12 months
@app.route('/api/v1.0/tobs')
def tobs():
    # Get the most active station (already performed in previous analysis)
    most_active_station = session.query(Measurement.station, func.count(Measurement.station).label('station_count'))\
        .group_by(Measurement.station)\
        .order_by(func.count(Measurement.station).desc()).first()[0]

    # Get the most recent date
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
    most_recent_date = datetime.strptime(most_recent_date, "%Y-%m-%d")
    date_12_months_ago = most_recent_date - timedelta(days=365)

    # Query temperature observations for the most active station over the last 12 months
    tobs_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= date_12_months_ago).\
        filter(Measurement.station == most_active_station).\
        order_by(Measurement.date).all()

    # Convert results to list of temperatures
    tobs_list = [{'date': date, 'temperature': tobs} for date, tobs in tobs_data]

    # Return as JSON
    return jsonify(tobs_list)

# Route to get temperature stats (TMIN, TAVG, TMAX) for a given start date
@app.route('/api/v1.0/<start>')
def start_stats(start):
    # Try to parse the date in the correct format
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid start date format, use YYYY-MM-DD"}), 400

    # Query TMIN, TAVG, and TMAX for the specified start date
    stats = session.query(
        func.min(Measurement.tobs).label('min_temp'),
        func.avg(Measurement.tobs).label('avg_temp'),
        func.max(Measurement.tobs).label('max_temp')
    ).filter(Measurement.date >= start_date).all()

    # Convert to dictionary and return as JSON
    result = {
        'start_date': start,
        'TMIN': stats[0].min_temp,
        'TAVG': stats[0].avg_temp,
        'TMAX': stats[0].max_temp
    }

    return jsonify(result)

# Route to get temperature stats for a date range
@app.route('/api/v1.0/<start>/<end>')
def start_end_stats(start, end):
    # Try to parse the start and end dates
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

    # Query TMIN, TAVG, and TMAX for the specified date range
    stats = session.query(
        func.min(Measurement.tobs).label('min_temp'),
        func.avg(Measurement.tobs).label('avg_temp'),
        func.max(Measurement.tobs).label('max_temp')
    ).filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()

    # Convert to dictionary and return as JSON
    result = {
        'start_date': start,
        'end_date': end,
        'TMIN': stats[0].min_temp,
        'TAVG': stats[0].avg_temp,
        'TMAX': stats[0].max_temp
    }

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)