# import Flask
import datetime as dt
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

# Set up database
engine = create_engine("sqlite:///Hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect = True)
dir(Base.classes)

Station = Base.classes.station
Measurements = Base.classes.measurements

# Create session
session = Session(engine)
# Create an app, being sure to pass __name__
app = Flask(__name__)

# Define home route
@app.route("/")
def home():
    """list all available routes"""
    return(
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

# Precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():

    """Query data"""
    precip_data = session.query(Measurements.date, Measurements.prcp).all()
    
    """Convert the query results to a dictionary using date as the key and prcp as the value"""
    precip_list = []
    for date, prcp in precip_data:
        precip_dict = {}
        precip_dict["date"] = date
        precip_dict["prcp"] = prcp
        precip_list.append(precip_dict) 

    return jsonify(precip_list)

# Station route
@app.route("/api/v1.0/stations")
def about():
    """Return a JSON list of stations from the dataset."""
    station_list = session.query(Station.station, Station.name).all()
    return jsonify(station_list)

# Query the dates and temperature observations of the most active station for the previous year of data.
@app.route("/api/v1.0/tobs")
def tobs():
    # Find the most recent date in the data set.
    most_recent_date = session.query(Measurements.date).order_by(Measurements.date.desc()).first()
    # Calculate the previous year date
    one_year_ago = dt.date(2017, 8, 23) - dt.timedelta(days=365)
    # List the stations and the counts in descending order.
    station_rank = session.query(Measurements.station, func.count(Measurements.station)).group_by(Measurements.station).order_by(func.count(Measurement.station).desc()).all()
    most_active_station = station_rank[0][0]

    # Query the last 12 months of temperature observation data for the most active station

    sel = [Measurements.date, Measurements.tobs]

    station_temps = session.query(*sel).\
            filter(Measurements.date >= one_year_ago, Measurements.station == most_active_station).\
            group_by(Measurements.date).\
            order_by(Measurements.date).all()

     # Return a dictionary with the date as key and the daily temperature observation as value
    observation_dates = []
    temperature_observations = []

    for date, observation in station_temps:
        observation_dates.append(date)
        temperature_observations.append(observation)
    
    most_active_tobs_dict = dict(zip(observation_dates, temperature_observations))

    return jsonify(most_active_tobs_dict)   
    

# Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a given start or start-end range.
# When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than or equal to the start date.
@app.route("/api/v1.0/<start>")
def startDate(date):
    temp_results = session.query(func.min(Measurements.tobs), func.avg(Measurements.tobs), func.max(Measurements.tobs)).filter(Measurements.date >= date).all()
    return jsonify(temp_results)

@app.route("/api/v1.0/<start>/<end>")
def start_end(start,end):
    temp_results2 = session.query(func.min(Measurements.tobs), func.avg(Measurements.tobs), func.max(Measurements.tobs)).filter(Measurements.date >= start).filter(Measurements.date <= end).all()
    return jsonify(temp_results2)

# Close session
session.close()


if __name__ == "__main__":
    app.run(debug=True)
