from app import app
from models import Language, db

with app.app_context():
    # Check if languages exist
    languages = Language.query.all()
    if languages:
        print(f"Found {len(languages)} languages in the database:")
        for lang in languages:
            print(f"- {lang.id}: {lang.name}")
    else:
        print("No languages found in the database. Adding common languages...")
        # Add common languages
        common_languages = [
            "English", "Hindi", "Bengali", "Tamil", "Telugu", 
            "Marathi", "Gujarati", "Kannada", "Malayalam", "Punjabi",
            "Urdu", "Odia"
        ]
        for lang_name in common_languages:
            lang = Language(name=lang_name)
            db.session.add(lang)
        
        db.session.commit()
        print(f"Added {len(common_languages)} languages to the database")
        
        # Verify languages were added
        languages = Language.query.all()
        print("Languages in database now:")
        for lang in languages:
            print(f"- {lang.id}: {lang.name}") 