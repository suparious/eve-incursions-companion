

@app.route('/character/save')
def character_save():
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
         # Append or Create the Skills table entry
        skill = Skills(
            id=current_user.character_id, 
            skills=skills.data.skills,
            total_sp=skills.data.total_sp,
            unallocated_sp=skills.data.unallocated_sp)
        session.merge(skill)
        # Commit current changes to the database
        session.commit()