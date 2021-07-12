from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash

from flask_sqlalchemy import SQLAlchemy

from os import urandom

import sys
import json
import requests


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
db = SQLAlchemy(app)

app.secret_key = urandom(24)


class City(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(40), unique=True, nullable=False)
    temp = db.Column(db.Integer)
    description = db.Column(db.String(40))

    def __repr__(self):
        return "<City name: %r >" % self.name


def get_city_data(url, api_key, city_name):

    params = {'q': city_name, 'appid': api_key}

    city_data = json.loads(requests.get(url, params=params).content.decode())

    if city_data['cod'] == '404':
        return None

    return {'city': city_name, 'temp': int(city_data['main']['temp']) - 273,
            'weather': city_data['weather'][0]['description']}


@app.route('/delete/<city_name>', methods=['POST'])
def delete_city(city_name):
    city = City.query.filter_by(name=city_name).first()
    db.session.delete(city)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/add', methods=['POST', 'GET'])
def add_city():
    city_name = request.form['city_name']
    url = "http://api.openweathermap.org/data/2.5/weather"
    key = "19dd2152041d2eea64e7a3cf9e5d6a3a"

    city_data = get_city_data(url, key, city_name)

    if city_data is None:
        flash("The city doesn't exist!")
    elif City.query.filter_by(name=city_name).first() is not None:
        flash("The city has already been added to the list!")
    else:
        db.session.add(City(name=city_data['city'], temp=city_data['temp'],
                            description=city_data['weather']))
        db.session.commit()

    return redirect(url_for('index'))


@app.route('/')
def index():

    context = {}

    if City.query.all():

        for city in City.query.all():
            context[city.name] = {'city': city.name, 'temp': city.temp, 'weather': city.description}

    return render_template('index.html', context=context)


# don't change the following way to run flask:
if __name__ == '__main__':
    db.create_all()

    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()

