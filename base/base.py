# -*- encoding: utf-8 -*-
from datetime import datetime
from tokenize import Floatnumber, Number

from esipy import EsiApp
from esipy import EsiClient
from esipy import EsiSecurity

from flask import Flask
from flask import render_template
from flask import request
from flask import session

from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import current_user

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

import config
import logging
import time
import urllib.parse

#import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

# logger stuff
logger = logging.getLogger(__name__)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)
logger.addHandler(console)

# init app and load conf
app = Flask(__name__)
app.config.from_object(config)
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")

# init db
db = SQLAlchemy(app)
migrate = Migrate(app, db)
engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=True)
Base = declarative_base()
Base.metadata.create_all(engine)

# init flask login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# -----------------------------------------------------------------------
# Database models
# -----------------------------------------------------------------------
class User(db.Model, UserMixin):
    # our ID is the character ID from EVE API
    character_id = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=False
    )
    character_owner_hash = db.Column(db.String(255))
    character_name = db.Column(db.String(200))

    # SSO Token stuff
    access_token = db.Column(db.String(4096))
    access_token_expires = db.Column(db.DateTime())
    refresh_token = db.Column(db.String(100))

    def get_id(self):
        """ Required for flask-login """
        return self.character_id

    def get_sso_data(self):
        """ Little "helper" function to get formated data for esipy security
        """
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_in': (
                self.access_token_expires - datetime.utcnow()
            ).total_seconds()
        }

    def update_token(self, token_response):
        """ helper function to update token data from SSO response """
        self.access_token = token_response['access_token']
        self.access_token_expires = datetime.fromtimestamp(
            time.time() + token_response['expires_in'],
        )
        if 'refresh_token' in token_response:
            self.refresh_token = token_response['refresh_token']

class Characters(Base):
    __tablename__ = 'characters'
    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    birthday = Column(String(32))
    corporation_id = Column(Integer)
    alliance_id = Column(Integer)
    security_status = Column(Integer)
    description = Column(Text)
    def __repr__(self):
        return "<Characters(id='%s', name='%s', birthday='%s', corporation_id='%s, alliance_id='%s, security_status='%s, description='%s)>" % (
            self.id, self.name, self.birthday, self.corporation_id, self.alliance_id, self.security_status, self.description)

class Skills(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True)
    skills = Column(Text)
    total_sp = Column(String(64))
    unallocated_sp = Column(String(64))
    def __repr__(self):
        return "<Skills(id='%s', skills='%s', total_sp='%s', unallocated_sp='%s')>" % (
            self.id, self.skills, self.total_sp, self.unallocated_sp)

class CharacterStatus(Base):
    __tablename__ = 'characterstatus'
    id = Column(Integer, primary_key=True)
    online = Column(String(8))
    location = Column(String(64))
    fleet = Column(String(8))
    docked = Column(String(64))
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    def __repr__(self):
        return "<CharacterStatus(id='%s', online='%s', location='%s', fleet='%s', docked='%s', last_updated='%s')>" % (
            self.id, self.online, self.location, self.fleet, self.docked, self.last_updated)

# -----------------------------------------------------------------------
# Create Database tables
# -----------------------------------------------------------------------
Base.metadata.create_all(engine)

# -----------------------------------------------------------------------
# Flask Login requirements
# -----------------------------------------------------------------------
@login_manager.user_loader
def load_user(character_id):
    """ Required user loader for Flask-Login """
    return User.query.get(character_id)

# -----------------------------------------------------------------------
# ESIPY Init
# -----------------------------------------------------------------------
# create the app
esiapp = EsiApp().get_latest_swagger

# init the security object
esisecurity = EsiSecurity(
    redirect_uri=config.ESI_CALLBACK,
    client_id=config.ESI_CLIENT_ID,
    secret_key=config.ESI_SECRET_KEY,
    headers={'User-Agent': config.ESI_USER_AGENT}
)

# init the client
esiclient = EsiClient(
    security=esisecurity,
    cache=None,
    headers={'User-Agent': config.ESI_USER_AGENT}
)

# -----------------------------------------------------------------------
# Configure global variables
# -----------------------------------------------------------------------
# Configure Fleet Roles
dps = ('Vindicator','Kronos','Golem','Armageddon','Hyperion','Tempest','Dominix','Dominix Navy Issue','Bhaalgorn','Raven Navy Issue','Barghest','Rattlesnake')
sniper = ('Nightmare','Paladin','Vargur','Machariel')
logi = ('Scimitar','Basilsk','Loki')
support = ('Nestor','Claymore','Vulture','Proteus')
transport = ('Crane','Viator','Bowhead')

# -----------------------------------------------------------------------
# Index Redirect to Main
# -----------------------------------------------------------------------
@app.route('/')
def index():
    server_status = None
    current_character = None
    current_corporation = None

    # EVE Online Server Status
    op = esiapp.op['get_status']()
    server_status = esiclient.request(op)

    if current_user.is_authenticated:
        esisecurity.update_token(current_user.get_sso_data())
        
        op = esiapp.op['get_characters_character_id'](
        character_id=current_user.character_id
        )
        current_character = esiclient.request(op)
        op = esiapp.op['get_corporations_corporation_id'](
            corporation_id=current_character.data.corporation_id
        )
        current_corporation = esiclient.request(op)
    
    return render_template('main_redirect.html', **{
        'server_status': server_status,
        'current_character': current_character,
        'current_corporation': current_corporation
    })

# -----------------------------------------------------------------------
# Main Routes
# -----------------------------------------------------------------------
@app.route('/main')
def main():
    server_status = None
    online = None
    current_character = None
    location = None
    location_solar_name = None
    current_corporation = None

    # EVE Online Server Status
    op = esiapp.op['get_status']()
    server_status = esiclient.request(op)

    if current_user.is_authenticated:
        esisecurity.update_token(current_user.get_sso_data())

        # Pilot status and location
        op = esiapp.op['get_characters_character_id_online'](
            character_id=current_user.character_id
        )
        online = esiclient.request(op)
        op = esiapp.op['get_characters_character_id_location'](
            character_id=current_user.character_id
        )
        location = esiclient.request(op)
        op = esiapp.op['get_universe_systems_system_id'](
            system_id=location.data.solar_system_id
        )
        location_solar_name = esiclient.request(op)
        op = esiapp.op['get_characters_character_id'](
            character_id=current_user.character_id
        )
        current_character = esiclient.request(op)

        # Pilot corporation
        op = esiapp.op['get_corporations_corporation_id'](
            corporation_id=current_character.data.corporation_id
        )
        current_corporation = esiclient.request(op)
        current_corp_url = urllib.parse.quote(current_corporation.data.url, safe='/:')
        

        # Incursions status
        op = esiapp.op['get_incursions']()
        incursions = esiclient.request(op)


    return render_template('main.html', **{
        'server_status': server_status,
        'online': online,
        'current_character': current_character,
        'current_corporation': current_corporation,
        'current_corp_url': current_corp_url,
        'location': location,
        'location_solar_name': location_solar_name,
    })

# -----------------------------------------------------------------------
# Implant Routes
# -----------------------------------------------------------------------
@app.route('/redir_implants')
def redir_implants():
    server_status = None
    current_character = None
    current_corporation = None

    # EVE Online Server Status
    op = esiapp.op['get_status']()
    server_status = esiclient.request(op)

    if current_user.is_authenticated:
        esisecurity.update_token(current_user.get_sso_data())
        
        op = esiapp.op['get_characters_character_id'](
        character_id=current_user.character_id
        )
        current_character = esiclient.request(op)
        op = esiapp.op['get_corporations_corporation_id'](
            corporation_id=current_character.data.corporation_id
        )
        current_corporation = esiclient.request(op)
    
    return render_template('implants_redirect.html', **{
        'server_status': server_status,
        'current_character': current_character,
        'current_corporation': current_corporation
    })

@app.route('/implants')
def implants():
    server_status = None
    online = None
    current_character = None
    location = None
    location_solar_name = None
    dock = None
    dock_status = None
    current_corporation = None
    current_corp_url = None
    fleet = None
    implant_names = []
    implant_ids = []
    implant_set_bonus = None
    ship = None
    ship_type = None
    ship_class = None
    fleet_id = None
    incursions = None

    # EVE Online Server Status
    op = esiapp.op['get_status']()
    server_status = esiclient.request(op)

    if current_user.is_authenticated:
        esisecurity.update_token(current_user.get_sso_data())

        # Pilot status and location
        op = esiapp.op['get_characters_character_id_online'](
            character_id=current_user.character_id
        )
        online = esiclient.request(op)
        op = esiapp.op['get_characters_character_id_location'](
            character_id=current_user.character_id
        )
        location = esiclient.request(op)
        op = esiapp.op['get_universe_systems_system_id'](
            system_id=location.data.solar_system_id
        )
        location_solar_name = esiclient.request(op)
        op = esiapp.op['get_characters_character_id'](
            character_id=current_user.character_id
        )
        current_character = esiclient.request(op)

        # Pilot corporation
        op = esiapp.op['get_corporations_corporation_id'](
            corporation_id=current_character.data.corporation_id
        )
        current_corporation = esiclient.request(op)
        current_corp_url = urllib.parse.quote(current_corporation.data.url, safe='/:')
        
        # Clone implants
        op = esiapp.op['get_characters_character_id_implants'](
            character_id=current_user.character_id
        )
        implants = esiclient.request(op)

        # Determine the Implant Set and relevant bonus totals

        
        # Query API for the Implant name
        ascendancy_high = ['33516','33525']
        for slot in range(10):
            try:
                op = esiapp.op['get_universe_types_type_id'](
                    type_id=implants.data[slot]
                    )
                implant_names.append(esiclient.request(op))
                implant_id = {'data': {'id': implants.data[slot] }}
                implant_ids.append(implant_id)
            except IndexError:
                implant_name = {'data': {'name': '< EMPTY SLOT >'}}
                implant_names.append(implant_name)
                implant_id = {'data': {'id': '0' }}
                implant_ids.append(implant_id)


        # Implant Bonus check
        # - Ascendancy
        # - Saviour
        bonus_check_status = "continue"
        while bonus_check_status == "continue":

            implant_set_bonus = "Shit"
            bonus_check_status = "stop"

        # Skill Hardwiring - Slot: 6 - 10
        # - Hybrid
        # - Laser
        # - Projectile
        # - Logistics
        # - muppet

        # Ship and Fittings
        op = esiapp.op['get_characters_character_id_ship'](
            character_id=current_user.character_id
        )
        ship = esiclient.request(op)
        op = esiapp.op['get_universe_types_type_id'](
            type_id=ship.data.ship_type_id
        )
        ship_type = esiclient.request(op)
        op = esiapp.op['get_universe_groups_group_id'](
            group_id=ship_type.data.group_id
        )
        ship_class = esiclient.request(op)

        # Incursions status
        op = esiapp.op['get_incursions']()
        incursions = esiclient.request(op)

        # Fleet
        op = esiapp.op['get_characters_character_id_fleet'](
            character_id=current_user.character_id
        )
        fleet = esiclient.request(op)

        if 'fleet_id' in fleet.data:
            fleet_id = fleet.data.fleet_id
        else:
            fleet_id = ''
        
        if 'structure_id' in location.data:
            op = esiapp.op['get_universe_structures_structure_id'](
            structure_id=location.data.structure_id
            )
            dock = esiclient.request(op)
            dock_status = dock.data.name
        elif 'station_id' in location.data:
            op = esiapp.op['get_universe_stations_station_id'](
            station_id=location.data.station_id
            )
            dock = esiclient.request(op)            
            dock_status = dock.data.name
        else:
            dock_status = "No"

        #if 'fleet_id' in fleet.data:
        #    ## Fleet boss only
        #    op = esiapp.op['get_fleets_fleet_id'](
        #        fleet_id=fleet.data.fleet_id
        #    )
        #    fleet_details = esiclient.request(op)
        #    op = esiapp.op['get_fleets_fleet_id_members'](
        #        fleet_id=fleet.data.fleet_id
        #    )
        #    fleet_members = esiclient.request(op)
        def write_characters_db():
            ## Save to database
            # Create a SQLAlchemy session object with ORM
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            Session.configure(bind=engine)
            session = Session()
            # Append or Create the Characters table entry
            character = Characters(
                id=current_user.character_id, 
                name=current_user.character_name,
                birthday=current_character.data.birthday,
                corporation_id=current_character.data.corporation_id,
                security_status=current_character.data.security_status,
                description=current_character.data.description)
            session.merge(character)
            # Commit current changes to the database
            session.commit()

        def write_characterstatus_db():
            ## Save to database
            # Create a SQLAlchemy session object with ORM
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            Session.configure(bind=engine)
            session = Session()
            # Append or Create the CharacterStatus table entry
            characterstatus = CharacterStatus(
                id=current_user.character_id, 
                online=online.data.online,
                location=location_solar_name.data.name,
                fleet=fleet_id,
                docked=dock_status)
            session.merge(characterstatus)
            # Commit current changes to the database
            session.commit()
        write_characters_db()
        write_characterstatus_db()

    return render_template('implants.html', **{
        'server_status': server_status,
        'dps': dps,
        'sniper': sniper,
        'logi': logi,
        'support': support,
        'transport': transport,
        'online': online,
        'dock': dock,
        'dock_status': dock_status,
        'current_character': current_character,
        'current_corporation': current_corporation,
        'current_corp_url': current_corp_url,
        'location': location,
        'location_solar_name': location_solar_name,
        'fleet': fleet,
        'fleet_id': fleet_id,
        'implant_names': implant_names,
        'implant_ids': implant_ids,
        'implant_set_bonus': implant_set_bonus,
        'ship': ship,
        'ship_type': ship_type,
        'ship_class': ship_class,
    })

# -----------------------------------------------------------------------
# Pilot Routes
# -----------------------------------------------------------------------
@app.route('/redir_skills')
def redir_skills():
    server_status = None
    current_character = None
    current_corporation = None

    # EVE Online Server Status
    op = esiapp.op['get_status']()
    server_status = esiclient.request(op)

    if current_user.is_authenticated:
        esisecurity.update_token(current_user.get_sso_data())
        
        op = esiapp.op['get_characters_character_id'](
        character_id=current_user.character_id
        )
        current_character = esiclient.request(op)
        op = esiapp.op['get_corporations_corporation_id'](
            corporation_id=current_character.data.corporation_id
        )
        current_corporation = esiclient.request(op)
    
    return render_template('skills_redirect.html', **{
        'server_status': server_status,
        'current_character': current_character,
        'current_corporation': current_corporation
    })

@app.route('/skills')
def skills():
    server_status = None
    current_character = None
    current_corporation = None
    implant_names = []
    implant_ids = []
    implant_set_bonus = None
    skills = None
    skillqueue = None
    skillqueue_total = None
    skillqueue_0_name = None
    skillqueue_1_name = None
    skillqueue_2_name = None
    skillqueue_3_name = None
    skillqueue_4_name = None
    skillqueue_5_name = None
    skillqueue_0_level = None
    skillqueue_1_level = None
    skillqueue_2_level = None
    skillqueue_3_level = None
    skillqueue_4_level = None
    skillqueue_5_level = None
    incursions = None

    # EVE Online Server Status
    op = esiapp.op['get_status']()
    server_status = esiclient.request(op)

    if current_user.is_authenticated:
        esisecurity.update_token(current_user.get_sso_data())

        # Pilot status and location
        op = esiapp.op['get_characters_character_id'](
            character_id=current_user.character_id
        )
        current_character = esiclient.request(op)

        # Pilot corporation
        op = esiapp.op['get_corporations_corporation_id'](
            corporation_id=current_character.data.corporation_id
        )
        current_corporation = esiclient.request(op)
        
        # Clone implants
        op = esiapp.op['get_characters_character_id_implants'](
            character_id=current_user.character_id
        )
        implants = esiclient.request(op)

        # Determine the Implant Set and relevant bonus totals

        
        # Query API for the Implant name
        ascendancy_high = ['33516','33525']
        for slot in range(10):
            try:
                op = esiapp.op['get_universe_types_type_id'](
                    type_id=implants.data[slot]
                    )
                implant_names.append(esiclient.request(op))
                implant_id = {'data': {'id': implants.data[slot] }}
                implant_ids.append(implant_id)
            except IndexError:
                implant_name = {'data': {'name': '< EMPTY SLOT >'}}
                implant_names.append(implant_name)
                implant_id = {'data': {'id': '0' }}
                implant_ids.append(implant_id)


        # Implant Bonus check
        # - Ascendancy
        # - Saviour
        bonus_check_status = "continue"
        while bonus_check_status == "continue":

            implant_set_bonus = "Shit"
            bonus_check_status = "stop"

        # Skill Hardwiring - Slot: 6 - 10
        # - Hybrid
        # - Laser
        # - Projectile
        # - Logistics
        # - muppet

        # Pilot Skills
        op = esiapp.op['get_characters_character_id_skills'](
            character_id=current_user.character_id
        )
        skills = esiclient.request(op)

        ## Skill Queue
        op = esiapp.op['get_characters_character_id_skillqueue'](
            character_id=current_user.character_id
        )
        skillqueue = esiclient.request(op)
        skillqueue_total = len(skillqueue.data)

        if 1 < skillqueue_total:
            skillqueue_0 = skillqueue.data[0].skill_id
            op = esiapp.op['get_universe_types_type_id'](
            type_id=skillqueue_0
            )
            skill_lookup = esiclient.request(op)
            skillqueue_0_level = skillqueue.data[0].finished_level
            skillqueue_0_name = skill_lookup.data.name
        else:
            skillqueue_1_name = "  < empty >"
            skillqueue_1_level = ""
        if 1 < skillqueue_total:
            skillqueue_1 = skillqueue.data[1].skill_id
            op = esiapp.op['get_universe_types_type_id'](
            type_id=skillqueue_1
            )
            skill_lookup = esiclient.request(op)
            skillqueue_1_level = skillqueue.data[1].finished_level
            skillqueue_1_name = skill_lookup.data.name
        else:
            skillqueue_1_name = "  < empty >"
            skillqueue_1_level = ""
        
        if 2 < skillqueue_total:
            skillqueue_2 = skillqueue.data[2].skill_id
            op = esiapp.op['get_universe_types_type_id'](
            type_id=skillqueue_2
            )
            skill_lookup = esiclient.request(op)
            skillqueue_2_level = skillqueue.data[2].finished_level
            skillqueue_2_name = skill_lookup.data.name
        else:
            skillqueue_2_name = "  < empty >"
            skillqueue_2_level = ""
        
        if 3 < skillqueue_total:
            skillqueue_3 = skillqueue.data[3].skill_id
            op = esiapp.op['get_universe_types_type_id'](
            type_id=skillqueue_3
            )
            skill_lookup = esiclient.request(op)
            skillqueue_3_level = skillqueue.data[3].finished_level
            skillqueue_3_name = skill_lookup.data.name
        else:
            skillqueue_3_name = "  < empty >"
            skillqueue_3_level = ""

        if 4 < skillqueue_total:
            skillqueue_4 = skillqueue.data[4].skill_id
            op = esiapp.op['get_universe_types_type_id'](
            type_id=skillqueue_4
            )
            skill_lookup = esiclient.request(op)
            skillqueue_4_level = skillqueue.data[4].finished_level
            skillqueue_4_name = skill_lookup.data.name
        else:
            skillqueue_4_name = "  < empty >"
            skillqueue_4_level = ""
        if 5 < skillqueue_total:
            skillqueue_5 = skillqueue.data[5].skill_id
            op = esiapp.op['get_universe_types_type_id'](
            type_id=skillqueue_5
            )
            skill_lookup = esiclient.request(op)
            skillqueue_5_level = skillqueue.data[5].finished_level
            skillqueue_5_name = skill_lookup.data.name
        else:
            skillqueue_5_name = "  < empty >"
            skillqueue_5_level = ""

        def write_characters_db():
            ## Save to database
            # Create a SQLAlchemy session object with ORM
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            Session.configure(bind=engine)
            session = Session()
            # Append or Create the Characters table entry
            character = Characters(
                id=current_user.character_id, 
                name=current_user.character_name,
                birthday=current_character.data.birthday,
                corporation_id=current_character.data.corporation_id,
                security_status=current_character.data.security_status,
                description=current_character.data.description)
            session.merge(character)
            # Commit current changes to the database
            session.commit()

        def write_skills_db():
            ## Save to database
            # Create a SQLAlchemy session object with ORM
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            Session.configure(bind=engine)
            session = Session()
            # Append or Create the Skills table entry
            skill = Skills(
                id=current_user.character_id, 
                skills=skills.data.skills,
                total_sp=skills.data.total_sp,
                unallocated_sp=skills.data.unallocated_sp)
            session.merge(skill)
            # Commit current changes to the database
            session.commit()

        write_characters_db()
        write_skills_db()

    return render_template('skills.html', **{
        'server_status': server_status,
        'current_character': current_character,
        'current_corporation': current_corporation,
        'skills': skills,
        'skillqueue': skillqueue,
        'skillqueue_total': skillqueue_total,
        'skillqueue_0_name': skillqueue_0_name,
        'skillqueue_1_name': skillqueue_1_name,
        'skillqueue_2_name': skillqueue_2_name,
        'skillqueue_3_name': skillqueue_3_name,
        'skillqueue_4_name': skillqueue_4_name,
        'skillqueue_5_name': skillqueue_5_name,
        'skillqueue_0_level': skillqueue_0_level,
        'skillqueue_1_level': skillqueue_1_level,
        'skillqueue_2_level': skillqueue_2_level,
        'skillqueue_3_level': skillqueue_3_level,
        'skillqueue_4_level': skillqueue_4_level,
        'skillqueue_5_level': skillqueue_5_level,
        'incursions': incursions,
    })

# -----------------------------------------------------------------------
# Pilot Routes
# -----------------------------------------------------------------------
@app.route('/redir_pilot')
def redir_pilot():
    server_status = None
    current_character = None
    current_corporation = None

    # EVE Online Server Status
    op = esiapp.op['get_status']()
    server_status = esiclient.request(op)

    if current_user.is_authenticated:
        esisecurity.update_token(current_user.get_sso_data())
        
        op = esiapp.op['get_characters_character_id'](
        character_id=current_user.character_id
        )
        current_character = esiclient.request(op)
        op = esiapp.op['get_corporations_corporation_id'](
            corporation_id=current_character.data.corporation_id
        )
        current_corporation = esiclient.request(op)
    
    return render_template('pilot_redirect.html', **{
        'server_status': server_status,
        'current_character': current_character,
        'current_corporation': current_corporation
    })

@app.route('/pilot')
def pilot():
    server_status = None
    online = None
    current_character = None
    location = None
    location_solar_name = None
    dock = None
    dock_status = None
    current_corporation = None
    current_corp_url = None
    fleet = None
    implant_names = []
    implant_ids = []
    implant_set_bonus = None
    ship = None
    ship_type = None
    ship_class = None
    skills = None
    skillqueue = None
    skillqueue_total = None
    skillqueue_0_name = None
    skillqueue_1_name = None
    skillqueue_2_name = None
    skillqueue_3_name = None
    skillqueue_4_name = None
    skillqueue_5_name = None
    skillqueue_0_level = None
    skillqueue_1_level = None
    skillqueue_2_level = None
    skillqueue_3_level = None
    skillqueue_4_level = None
    skillqueue_5_level = None
    fleet_id = None
    incursions = None

    # EVE Online Server Status
    op = esiapp.op['get_status']()
    server_status = esiclient.request(op)

    if current_user.is_authenticated:
        esisecurity.update_token(current_user.get_sso_data())

        # Pilot status and location
        op = esiapp.op['get_characters_character_id_online'](
            character_id=current_user.character_id
        )
        online = esiclient.request(op)
        op = esiapp.op['get_characters_character_id_location'](
            character_id=current_user.character_id
        )
        location = esiclient.request(op)
        op = esiapp.op['get_universe_systems_system_id'](
            system_id=location.data.solar_system_id
        )
        location_solar_name = esiclient.request(op)
        op = esiapp.op['get_characters_character_id'](
            character_id=current_user.character_id
        )
        current_character = esiclient.request(op)

        # Pilot corporation
        op = esiapp.op['get_corporations_corporation_id'](
            corporation_id=current_character.data.corporation_id
        )
        current_corporation = esiclient.request(op)
        current_corp_url = urllib.parse.quote(current_corporation.data.url, safe='/:')
        
        # Clone implants
        op = esiapp.op['get_characters_character_id_implants'](
            character_id=current_user.character_id
        )
        implants = esiclient.request(op)

        # Determine the Implant Set and relevant bonus totals

        
        # Query API for the Implant name
        ascendancy_high = ['33516','33525']
        for slot in range(10):
            try:
                op = esiapp.op['get_universe_types_type_id'](
                    type_id=implants.data[slot]
                    )
                implant_names.append(esiclient.request(op))
                implant_id = {'data': {'id': implants.data[slot] }}
                implant_ids.append(implant_id)
            except IndexError:
                implant_name = {'data': {'name': '< EMPTY SLOT >'}}
                implant_names.append(implant_name)
                implant_id = {'data': {'id': '0' }}
                implant_ids.append(implant_id)


        # Implant Bonus check
        # - Ascendancy
        # - Saviour
        bonus_check_status = "continue"
        while bonus_check_status == "continue":

            implant_set_bonus = "Shit"
            bonus_check_status = "stop"

        # Skill Hardwiring - Slot: 6 - 10
        # - Hybrid
        # - Laser
        # - Projectile
        # - Logistics
        # - muppet

        # Ship and Fittings
        op = esiapp.op['get_characters_character_id_ship'](
            character_id=current_user.character_id
        )
        ship = esiclient.request(op)
        op = esiapp.op['get_universe_types_type_id'](
            type_id=ship.data.ship_type_id
        )
        ship_type = esiclient.request(op)
        op = esiapp.op['get_universe_groups_group_id'](
            group_id=ship_type.data.group_id
        )
        ship_class = esiclient.request(op)

        # Pilot Skills
        op = esiapp.op['get_characters_character_id_skills'](
            character_id=current_user.character_id
        )
        skills = esiclient.request(op)

        ## Skill Queue
        op = esiapp.op['get_characters_character_id_skillqueue'](
            character_id=current_user.character_id
        )
        skillqueue = esiclient.request(op)
        skillqueue_total = len(skillqueue.data)

        if 1 < skillqueue_total:
            skillqueue_0 = skillqueue.data[0].skill_id
            op = esiapp.op['get_universe_types_type_id'](
            type_id=skillqueue_0
            )
            skill_lookup = esiclient.request(op)
            skillqueue_0_level = skillqueue.data[0].finished_level
            skillqueue_0_name = skill_lookup.data.name
        else:
            skillqueue_1_name = "  < empty >"
            skillqueue_1_level = ""
        if 1 < skillqueue_total:
            skillqueue_1 = skillqueue.data[1].skill_id
            op = esiapp.op['get_universe_types_type_id'](
            type_id=skillqueue_1
            )
            skill_lookup = esiclient.request(op)
            skillqueue_1_level = skillqueue.data[1].finished_level
            skillqueue_1_name = skill_lookup.data.name
        else:
            skillqueue_1_name = "  < empty >"
            skillqueue_1_level = ""
        
        if 2 < skillqueue_total:
            skillqueue_2 = skillqueue.data[2].skill_id
            op = esiapp.op['get_universe_types_type_id'](
            type_id=skillqueue_2
            )
            skill_lookup = esiclient.request(op)
            skillqueue_2_level = skillqueue.data[2].finished_level
            skillqueue_2_name = skill_lookup.data.name
        else:
            skillqueue_2_name = "  < empty >"
            skillqueue_2_level = ""
        
        if 3 < skillqueue_total:
            skillqueue_3 = skillqueue.data[3].skill_id
            op = esiapp.op['get_universe_types_type_id'](
            type_id=skillqueue_3
            )
            skill_lookup = esiclient.request(op)
            skillqueue_3_level = skillqueue.data[3].finished_level
            skillqueue_3_name = skill_lookup.data.name
        else:
            skillqueue_3_name = "  < empty >"
            skillqueue_3_level = ""

        if 4 < skillqueue_total:
            skillqueue_4 = skillqueue.data[4].skill_id
            op = esiapp.op['get_universe_types_type_id'](
            type_id=skillqueue_4
            )
            skill_lookup = esiclient.request(op)
            skillqueue_4_level = skillqueue.data[4].finished_level
            skillqueue_4_name = skill_lookup.data.name
        else:
            skillqueue_4_name = "  < empty >"
            skillqueue_4_level = ""
        if 5 < skillqueue_total:
            skillqueue_5 = skillqueue.data[5].skill_id
            op = esiapp.op['get_universe_types_type_id'](
            type_id=skillqueue_5
            )
            skill_lookup = esiclient.request(op)
            skillqueue_5_level = skillqueue.data[5].finished_level
            skillqueue_5_name = skill_lookup.data.name
        else:
            skillqueue_5_name = "  < empty >"
            skillqueue_5_level = ""

        # Incursions status
        op = esiapp.op['get_incursions']()
        incursions = esiclient.request(op)

        # Fleet
        op = esiapp.op['get_characters_character_id_fleet'](
            character_id=current_user.character_id
        )
        fleet = esiclient.request(op)

        if 'fleet_id' in fleet.data:
            fleet_id = fleet.data.fleet_id
        else:
            fleet_id = ''
        
        if 'structure_id' in location.data:
            op = esiapp.op['get_universe_structures_structure_id'](
            structure_id=location.data.structure_id
            )
            dock = esiclient.request(op)
            dock_status = dock.data.name
        elif 'station_id' in location.data:
            op = esiapp.op['get_universe_stations_station_id'](
            station_id=location.data.station_id
            )
            dock = esiclient.request(op)            
            dock_status = dock.data.name
        else:
            dock_status = "No"

        #if 'fleet_id' in fleet.data:
        #    ## Fleet boss only
        #    op = esiapp.op['get_fleets_fleet_id'](
        #        fleet_id=fleet.data.fleet_id
        #    )
        #    fleet_details = esiclient.request(op)
        #    op = esiapp.op['get_fleets_fleet_id_members'](
        #        fleet_id=fleet.data.fleet_id
        #    )
        #    fleet_members = esiclient.request(op)
        def write_characters_db():
            ## Save to database
            # Create a SQLAlchemy session object with ORM
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            Session.configure(bind=engine)
            session = Session()
            # Append or Create the Characters table entry
            character = Characters(
                id=current_user.character_id, 
                name=current_user.character_name,
                birthday=current_character.data.birthday,
                corporation_id=current_character.data.corporation_id,
                security_status=current_character.data.security_status,
                description=current_character.data.description)
            session.merge(character)
            # Commit current changes to the database
            session.commit()

        def write_skills_db():
            ## Save to database
            # Create a SQLAlchemy session object with ORM
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            Session.configure(bind=engine)
            session = Session()
            # Append or Create the Skills table entry
            skill = Skills(
                id=current_user.character_id, 
                skills=skills.data.skills,
                total_sp=skills.data.total_sp,
                unallocated_sp=skills.data.unallocated_sp)
            session.merge(skill)
            # Append or Create the CharacterStatus table entry
            characterstatus = CharacterStatus(
                id=current_user.character_id, 
                online=online.data.online,
                location=location_solar_name.data.name,
                fleet=fleet_id,
                docked=dock_status)
            session.merge(characterstatus)
            # Commit current changes to the database
            session.commit()

        def write_characterstatus_db():
            ## Save to database
            # Create a SQLAlchemy session object with ORM
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            Session.configure(bind=engine)
            session = Session()
            # Append or Create the CharacterStatus table entry
            characterstatus = CharacterStatus(
                id=current_user.character_id, 
                online=online.data.online,
                location=location_solar_name.data.name,
                fleet=fleet_id,
                docked=dock_status)
            session.merge(characterstatus)
            # Commit current changes to the database
            session.commit()
        write_characters_db()
        write_skills_db()
        write_characterstatus_db()

    return render_template('pilot.html', **{
        'server_status': server_status,
        'dps': dps,
        'sniper': sniper,
        'logi': logi,
        'support': support,
        'transport': transport,
        'online': online,
        'dock': dock,
        'dock_status': dock_status,
        'current_character': current_character,
        'current_corporation': current_corporation,
        'current_corp_url': current_corp_url,
        'location': location,
        'location_solar_name': location_solar_name,
        'fleet': fleet,
        'fleet_id': fleet_id,
        'implant_names': implant_names,
        'implant_ids': implant_ids,
        'implant_set_bonus': implant_set_bonus,
        'ship': ship,
        'ship_type': ship_type,
        'ship_class': ship_class,
        'skills': skills,
        'skillqueue': skillqueue,
        'skillqueue_total': skillqueue_total,
        'skillqueue_0_name': skillqueue_0_name,
        'skillqueue_1_name': skillqueue_1_name,
        'skillqueue_2_name': skillqueue_2_name,
        'skillqueue_3_name': skillqueue_3_name,
        'skillqueue_4_name': skillqueue_4_name,
        'skillqueue_5_name': skillqueue_5_name,
        'skillqueue_0_level': skillqueue_0_level,
        'skillqueue_1_level': skillqueue_1_level,
        'skillqueue_2_level': skillqueue_2_level,
        'skillqueue_3_level': skillqueue_3_level,
        'skillqueue_4_level': skillqueue_4_level,
        'skillqueue_5_level': skillqueue_5_level,
        'incursions': incursions,
    })

@app.route("/shit")
def shit():
    site_input = "No input was specified.<br><strong>usage:</strong> /shit/some command here"
    return "💩💩💩<br>" + site_input + "<br>💩💩💩"
@app.route("/shit/<site_input>")
def shitty_command(site_input):
    return "💩💩💩<br>" + site_input + "<br>💩💩💩"

if __name__ == '__main__':
    app.run(port=config.PORT, host=config.HOST)
    