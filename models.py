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
    # Updated relationship without backref
    owner_connects = db.relationship('OwnerToOwnerConnect', 
                                     foreign_keys='OwnerToOwnerConnect.from_owner_id',
                                     lazy=True)
    # New relationship for helper associations
    helper_associations = db.relationship('OwnerHelperAssociation', backref='owner', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class OwnerProfile(db.Model):
    __tablename__ = 'owner_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    aadhaar_id = db.Column(db.String(12), nullable=True)  # 12-digit Aadhaar number
    aadhaar_verified = db.Column(db.Boolean, default=False)  # Whether Aadhaar has been verified
    aadhaar_verified_at = db.Column(db.DateTime, nullable=True)  # When Aadhaar was verified
    aadhaar_name = db.Column(db.String(100), nullable=True)  # Name as per Aadhaar
    aadhaar_gender = db.Column(db.String(10), nullable=True)  # Gender as per Aadhaar
    aadhaar_dob = db.Column(db.String(20), nullable=True)  # DOB as per Aadhaar
    aadhaar_address = db.Column(db.Text, nullable=True)  # Complete address as per Aadhaar
    aadhaar_photo = db.Column(db.Text, nullable=True)  # Base64 encoded photo from Aadhaar
    
    # Detailed address components from Aadhaar
    address_house = db.Column(db.String(100), nullable=True)  # House number/name
    address_landmark = db.Column(db.String(100), nullable=True)  # Landmark
    address_vtc = db.Column(db.String(100), nullable=True)  # Village/Town/City
    address_district = db.Column(db.String(50), nullable=True)  # District
    address_state = db.Column(db.String(50), nullable=True)  # State
    address_pincode = db.Column(db.String(10), nullable=True)  # Pincode
    address_country = db.Column(db.String(50), nullable=True)  # Country
    address_post_office = db.Column(db.String(100), nullable=True)  # Post Office
    address_street = db.Column(db.String(100), nullable=True)  # Street
    address_subdistrict = db.Column(db.String(100), nullable=True)  # Subdistrict
    
    # Original fields (may be populated from Aadhaar data or manually)
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
    helper_id = db.Column(db.String(50), unique=True, nullable=False)  # Aadhaar ID for maids, DL for drivers
    helper_type = db.Column(db.String(20), nullable=False)  # 'maid' or 'driver'
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    languages = db.Column(db.String(200))  # Comma-separated list of languages
    photo_url = db.Column(db.String(200))
    gender = db.Column(db.String(10))  # Add gender column
    state = db.Column(db.String(50))
    city = db.Column(db.String(50))
    society = db.Column(db.String(100))
    street = db.Column(db.String(100))
    apartment_number = db.Column(db.String(50))
    verification_status = db.Column(db.String(20), default='Unverified')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Aadhaar verification fields
    aadhaar_verified = db.Column(db.Boolean, default=False)
    aadhaar_verified_at = db.Column(db.DateTime)
    aadhaar_dob = db.Column(db.String(20))
    aadhaar_address = db.Column(db.Text)
    aadhaar_photo = db.Column(db.Text)  # Base64 encoded photo
    care_of = db.Column(db.String(100))  # Added care_of field
    
    # Detailed address components
    address_house = db.Column(db.String(100))
    address_landmark = db.Column(db.String(100))
    address_vtc = db.Column(db.String(100))
    address_district = db.Column(db.String(100))
    address_state = db.Column(db.String(100))
    address_pincode = db.Column(db.String(10))
    address_country = db.Column(db.String(100))
    address_post_office = db.Column(db.String(100))
    address_street = db.Column(db.String(100))
    address_subdistrict = db.Column(db.String(100))
    
    # Relationships
    documents = db.relationship('HelperDocument', backref='helper_profile', lazy=True)
    contracts = db.relationship('Contract', backref='helper_profile', lazy=True)
    reviews = db.relationship('Review', backref='helper_profile', lazy=True)
    incidents = db.relationship('IncidentReport', backref='helper_profile', lazy=True)
    # Define the relationship without using backref
    connect_requests = db.relationship('OwnerToOwnerConnect', lazy=True)
    
    # New relationships for multi-owner support
    owner_associations = db.relationship('OwnerHelperAssociation', backref='helper_profile', lazy=True)
    verification_logs = db.relationship('HelperVerificationLog', backref='helper_profile', lazy=True)
    
    # Get primary owner
    @property
    def primary_owner(self):
        association = OwnerHelperAssociation.query.filter_by(
            helper_profile_id=self.id, 
            is_primary_owner=True
        ).first()
        if association:
            return User.query.get(association.owner_id)
        return None
    
    # Get all owners
    @property
    def owners(self):
        associations = OwnerHelperAssociation.query.filter_by(helper_profile_id=self.id).all()
        owner_ids = [assoc.owner_id for assoc in associations]
        return User.query.filter(User.id.in_(owner_ids)).all()
    
    def __init__(self, name, helper_id, helper_type, phone_number, languages, created_by, photo_url=None, gender=None, state=None, has_police_verification=False, verification_status='Unverified'):
        self.name = name
        self.helper_id = helper_id
        self.helper_type = helper_type
        self.phone_number = phone_number
        self.languages = languages
        self.created_by = created_by
        self.photo_url = photo_url
        self.gender = gender
        self.state = state
        self.has_police_verification = has_police_verification
        self.verification_status = verification_status
    
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
    category = db.Column(db.String(50), nullable=True)
    helper_type = db.Column(db.String(20), nullable=False, default='maid')  # 'maid' or 'driver'
    is_main_task = db.Column(db.Boolean, default=False)  # True for main tasks, False for subtasks
    parent_id = db.Column(db.Integer, nullable=True)  # For subtasks, references the main task
    
    def __repr__(self):
        return f'<TaskList {self.name}>'

class Contract(db.Model):
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.String(50), unique=True, nullable=False)
    helper_profile_id = db.Column(db.Integer, db.ForeignKey('helper_profiles.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tasks = db.Column(db.String(255), nullable=False)  # Comma-separated task IDs
    is_full_time = db.Column(db.Boolean, default=False)
    working_hours_from = db.Column(db.String(10), nullable=True)
    working_hours_to = db.Column(db.String(10), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # optional if ongoing
    monthly_salary = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    termination_reason = db.Column(db.Text, nullable=True)  # Reason for contract termination
    is_terminated = db.Column(db.Boolean, default=False)  # Flag to track terminated contracts
    
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
    
    # Relationships - removed backref to avoid conflict
    helper_profile = db.relationship('HelperProfile')
    requesting_owner = db.relationship('User', foreign_keys=[from_owner_id])
    
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

# New models for multi-owner support
class OwnerHelperAssociation(db.Model):
    __tablename__ = 'owner_helper_associations'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    helper_profile_id = db.Column(db.Integer, db.ForeignKey('helper_profiles.id'), nullable=False)
    is_primary_owner = db.Column(db.Boolean, default=False)
    added_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('owner_id', 'helper_profile_id', name='uq_owner_helper'),
    )
    
    def __repr__(self):
        return f'<OwnerHelperAssociation owner_id={self.owner_id} helper_id={self.helper_profile_id}>'

class HelperVerificationLog(db.Model):
    __tablename__ = 'helper_verification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    helper_profile_id = db.Column(db.Integer, db.ForeignKey('helper_profiles.id'), nullable=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    verification_timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    verification_result = db.Column(db.String(20), nullable=False)  # 'Valid', 'Invalid', etc.
    transaction_id = db.Column(db.String(100))
    verification_data = db.Column(db.JSON)
    
    # Relationship to the user who performed verification
    verifier = db.relationship('User', backref='verification_logs')
    
    def __repr__(self):
        return f'<HelperVerificationLog {self.id}>'

class AadhaarAPILog(db.Model):
    """Log all Aadhaar API requests and responses for troubleshooting and audit purposes."""
    __tablename__ = 'aadhaar_api_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    aadhaar_id = db.Column(db.String(12), nullable=True)  # Can be null for token requests
    reference_id = db.Column(db.String(100), nullable=True)
    request_type = db.Column(db.String(50), nullable=False)  # 'token', 'generate_otp', 'verify_otp'
    request_payload = db.Column(db.JSON, nullable=True)
    response_payload = db.Column(db.JSON, nullable=True)
    success = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, nullable=True)  # Can be null for anonymous requests
    session_id = db.Column(db.String(100), nullable=True)  # To track related requests
    
    def __repr__(self):
        return f'<AadhaarAPILog {self.id} {self.request_type} success={self.success}>'
