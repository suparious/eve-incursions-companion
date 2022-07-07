import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
import config

engine = create_engine('mysql+pymysql://fleet_demo:Jfk_67-45@data:3306/fleet', echo=True)
Base = declarative_base()



# -----------------------------------------------------------------------
# Database models
# -----------------------------------------------------------------------
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    fullname = Column(String(64))
    nickname = Column(String(64))
    def __repr__(self):
       return "<User(name='%s', fullname='%s', nickname='%s')>" % (
                            self.name, self.fullname, self.nickname)

class Characters(Base):
    __tablename__ = 'characters'
    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    birthday = Column(String(32))
    gender = Column(String(12))
    race_id = Column(Integer)
    faction_id = Column(Integer)
    alliance_id = Column(Integer)
    bloodline_id = Column(Integer)
    corporation_id = Column(Integer)
    security_status = Column(Integer)
    description = Column(Text)
    def __repr__(self):
        return "<Characters(name='%s', title='%s', birthday='%s', gender='%s, race_id='%s, faction_id='%s, alliance_id='%s, bloodline_id='%s, corporation_id='%s, security_status='%s, description='%s)>" % (
            self.name, self.title, self.birthday, self.gender, self.race_id, self.faction_id, self.alliance_id, self.bloodline_id, self.corporation_id, self.security_status, self.description)

class Skills(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True)
    skills = Column(String(64))
    total_sp = Column(String(64))
    unallocated_sp = Column(String(64))
    def __repr__(self):
       return "<Skills(user_id='%s', skills='%s', total_sp='%s', unallocated_sp='%s')>" % (self.user_id, self.skills, self.total_sp, self.unallocated_sp)


Base.metadata.create_all(engine)

ed_user = User(name='ed', fullname='Ed Jones', nickname='edsnickname')
ed_user.name
ed_user.nickname
str(ed_user.id)

from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()

session.add(ed_user)
our_user = session.query(User).filter_by(name='ed').first() 
our_user
ed_user is our_user

session.add_all([
    User(name='wendy', fullname='Wendy Williams', nickname='windy'),
    User(name='mary', fullname='Mary Contrary', nickname='mary'),
    User(name='fred', fullname='Fred Flintstone', nickname='freddy')])

ed_user.nickname = 'eddie'

session.dirty
session.new
session.commit()

ed_user.id 

for instance in session.query(User).order_by(User.id):
    print(instance.name, instance.fullname)

for name, fullname in session.query(User.name, User.fullname):
    print(name, fullname)

for row in session.query(User.name.label('name_label')).all():
   print(row.name_label)

for row in session.query(User, User.name).all():
   print(row.User, row.name)


from sqlalchemy.orm import aliased
user_alias = aliased(User, name='user_alias')

for row in session.query(user_alias, user_alias.name).all():
   print(row.user_alias)

for u in session.query(User).order_by(User.id)[1:3]:
   print(u)

for name, in session.query(User.name).\
            filter_by(fullname='Ed Jones'):
   print(name)

for name, in session.query(User.name).\
            filter(User.fullname=='Ed Jones'):
   print(name)

for user in session.query(User).\
         filter(User.name=='ed').\
         filter(User.fullname=='Ed Jones'):
   print(user)

for user in session.query(User).\
         filter(User.name!='ed'):
   print(user)

for user in session.query(User).\
         filter(User.name.like('%ed%')):
   print(user)

for user in session.query(User).\
         filter(User.name.in_(['ed', 'wendy', 'jack'])):
   print(user)