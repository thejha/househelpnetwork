import datetime
from flask_login import UserMixin
from extensions import db, login_manager

# Define the user loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='owner')  # 'owner' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    owner_profile = db.relationship('OwnerProfile', backref='user', uselist=False)
    reviews = db.relationship('Review', backref='owner', lazy=True)
    incident_reports = db.relationship('IncidentReport', backref='owner', lazy=True)
    owner_connects = db.relationship('OwnerToOwnerConnect', 
                                     foreign_keys='OwnerToOwnerConnect.from_owner_id',
                                     backref='requesting_owner')

    def __repr__(self):
        return f'<User {self.email}>'

class OwnerProfile(db.Model):
    __tablename__ = 'owner_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    aadhaar_id = db.Column(db.String(12), nullable=True)  # 12-digit Aadhaar number
    aadhaar_verified = db.Column(db.Boolean, default=False)  # Whether Aadhaar has been verified
    aadhaar_verified_at = db.Column(db.DateTime, nullable=True)  # When Aadhaar was verified
    pincode = db.Column(db.String(10), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    society = db.Column(db.String(100), nullable=False)
    street = db.Column(db.String(100), nullable=False)
    apartment_number = db.Column(db.String(20), nullable=False)
    verification_status = db.Column(db.String(20), default='Pending')  # Pending, Verified, Rejected
    
    # Relationships
    documents = db.relationship('OwnerDocument', backref='owner_profile', lazy=True)
    
    def __repr__(self):
        return f'<OwnerProfile {self.owner_id}>'

class OwnerDocument(db.Model):
    __tablename__ = 'owner_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_profile_id = db.Column(db.Integer, db.ForeignKey('owner_profiles.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., Aadhar, utility_bill
    url = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return f'<OwnerDocument {self.type}>'

class HelperProfile(db.Model):
    __tablename__ = 'helper_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Helper name
    helper_id = db.Column(db.String(50), unique=True, nullable=False)  # unique ID (Aadhar or DL based on type)
    helper_type = db.Column(db.String(20), nullable=False)  # 'maid' or 'driver'
    gender = db.Column(db.String(10), nullable=False)  # 'male' or 'female'
    phone_number = db.Column(db.String(20), nullable=False)
    photo_url = db.Column(db.String(255), nullable=True)
    state = db.Column(db.String(50), nullable=False)
    languages = db.Column(db.String(255), nullable=False)  # Comma-separated values or references to Language
    has_police_verification = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    documents = db.relationship('HelperDocument', backref='helper_profile', lazy=True)
    contracts = db.relationship('Contract', backref='helper_profile', lazy=True)
    reviews = db.relationship('Review', backref='helper_profile', lazy=True)
    incident_reports = db.relationship('IncidentReport', backref='helper_profile', lazy=True)
    
    def __init__(self, name, helper_id, helper_type, gender, phone_number, state, languages, created_by, photo_url=None, has_police_verification=False):
        self.name = name
        self.helper_id = helper_id
        self.helper_type = helper_type
        self.gender = gender
        self.phone_number = phone_number
        self.state = state
        self.languages = languages
        self.created_by = created_by
        self.photo_url = photo_url
        self.has_police_verification = has_police_verification
    
    def __repr__(self):
        return f'<HelperProfile {self.helper_id}>'

class HelperDocument(db.Model):
    __tablename__ = 'helper_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    helper_profile_id = db.Column(db.Integer, db.ForeignKey('helper_profiles.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., Aadhar, driving_license, police_verification
    url = db.Column(db.String(255), nullable=False)
    
    def __init__(self, helper_profile_id, type, url):
        self.helper_profile_id = helper_profile_id
        self.type = type
        self.url = url
    
    def __repr__(self):
        return f'<HelperDocument {self.type}>'

class TaskList(db.Model):
    __tablename__ = 'task_list'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    
    def __repr__(self):
        return f'<TaskList {self.name}>'

class Contract(db.Model):
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.String(50), unique=True, nullable=False)
    helper_profile_id = db.Column(db.Integer, db.ForeignKey('helper_profiles.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tasks = db.Column(db.String(255), nullable=False)  # Comma-separated task IDs
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # optional if ongoing
    monthly_salary = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationship
    owner = db.relationship('User', backref='contracts')
    
    def __repr__(self):
        return f'<Contract {self.contract_id}>'

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.String(50), unique=True, nullable=False)
    helper_profile_id = db.Column(db.Integer, db.ForeignKey('helper_profiles.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tasks_average = db.Column(db.Float, nullable=False)
    punctuality = db.Column(db.Float, nullable=False)
    attitude = db.Column(db.Float, nullable=False)
    hygiene = db.Column(db.Float, nullable=False)
    communication = db.Column(db.Float, nullable=False)
    reliability = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<Review {self.review_id}>'

class IncidentReport(db.Model):
    __tablename__ = 'incident_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(50), unique=True, nullable=False)
    helper_profile_id = db.Column(db.Integer, db.ForeignKey('helper_profiles.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    fir_number = db.Column(db.String(50), nullable=True)  # optional
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<IncidentReport {self.report_id}>'

class OwnerToOwnerConnect(db.Model):
    __tablename__ = 'owner_to_owner_connects'
    
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.String(50), unique=True, nullable=False)
    helper_profile_id = db.Column(db.Integer, db.ForeignKey('helper_profiles.id'), nullable=False)
    from_owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_owner_contact = db.Column(db.String(120), nullable=False)  # Email or phone
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    stored_locally = db.Column(db.Boolean, default=True)
    
    # Relationships
    helper_profile = db.relationship('HelperProfile', backref='connect_requests')
    
    def __repr__(self):
        return f'<OwnerToOwnerConnect {self.form_id}>'

class Language(db.Model):
    __tablename__ = 'languages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return f'<Language {self.name}>'

class PincodeMapping(db.Model):
    __tablename__ = 'pincode_mapping'
    
    id = db.Column(db.Integer, primary_key=True)
    pincode = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    society = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<PincodeMapping {self.pincode}>'
