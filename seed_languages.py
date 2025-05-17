"""
Seed script to populate the languages table with major Indian languages.
"""
from app import app, db
from models import Language

def seed_languages():
    """Create language entries for major Indian languages."""
    languages = [
        'Hindi',
        'Bengali',
        'Telugu',
        'Marathi',
        'Tamil',
        'Urdu',
        'Gujarati',
        'Kannada',
        'Odia',
        'Malayalam',
        'Punjabi',
        'Assamese',
        'Maithili',
        'Sanskrit',
        'English',
        'Kashmiri',
        'Nepali',
        'Sindhi',
        'Konkani',
        'Dogri',
        'Manipuri',
        'Bodo'
    ]
    
    with app.app_context():
        # Check if languages already exist to avoid duplicates
        existing_languages = [lang.name for lang in Language.query.all()]
        
        for language in languages:
            if language not in existing_languages:
                language_obj = Language(name=language)
                db.session.add(language_obj)
        
        db.session.commit()
        print(f"Added {len(languages) - len(existing_languages)} new languages to the database.")

if __name__ == "__main__":
    seed_languages()