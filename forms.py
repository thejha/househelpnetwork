from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, SelectMultipleField, TextAreaField, DateField, FloatField, BooleanField, MultipleFileField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from flask_wtf.file import FileField, FileAllowed
import datetime
from models import User

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    # Custom validators for unique email and phone number
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email address is already registered. Please use a different email or login.')
    
    def validate_phone_number(self, phone_number):
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user:
            raise ValidationError('Phone number is already registered. Please use a different phone number.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class AadhaarVerificationForm(FlaskForm):
    aadhaar_id = StringField('Aadhaar Number', validators=[
        DataRequired(), 
        Length(min=12, max=12, message="Aadhaar number must be 12 digits"),
        Regexp('^\d{12}$', message="Aadhaar number must be 12 digits")
    ])
    submit = SubmitField('Verify Aadhaar')

class AadhaarOTPVerificationForm(FlaskForm):
    otp = StringField('OTP', validators=[
        DataRequired(), 
        Length(min=6, max=6, message="OTP must be 6 digits"),
        Regexp('^\d{6}$', message="OTP must be 6 digits")
    ])
    reference_id = HiddenField('Reference ID')
    submit = SubmitField('Verify OTP')

class OwnerProfileForm(FlaskForm):
    aadhaar_id = StringField('Aadhaar Number', render_kw={'readonly': True})
    name = StringField('Full Name', render_kw={'readonly': True})
    pincode = StringField('Pincode', validators=[DataRequired(), Length(min=6, max=10)])
    state = StringField('State', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    society = StringField('Society/Building Name', validators=[DataRequired()])
    street = StringField('Street', validators=[DataRequired()])
    apartment_number = StringField('Apartment Number', validators=[DataRequired()])
    documents = MultipleFileField('Upload Documents (Utility Bills, etc.)', 
                                validators=[FileAllowed(['jpg', 'png', 'pdf'], 'Images and PDFs only')])
    submit = SubmitField('Save Profile')

class HelperProfileForm(FlaskForm):
    name = StringField('Helper Name', validators=[DataRequired(), Length(min=2, max=100)])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    helper_type = SelectField('Helper Type', choices=[('maid', 'Maid'), ('driver', 'Driver')], validators=[DataRequired()])
    
    # Maid specific fields (shown conditionally)
    aadhar_id = StringField('Aadhar ID', validators=[])
    
    # Driver specific fields (shown conditionally)
    driving_license_id = StringField('Driving License ID', validators=[])
    
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    state = StringField('State', validators=[DataRequired()])
    languages = SelectMultipleField('Languages Spoken', choices=[], validators=[DataRequired()], render_kw={"multiple": "multiple", "class": "form-select"})
    
    photo = FileField('Upload Photo', validators=[FileAllowed(['jpg', 'png'], 'Images only')])
    
    # Document uploads
    aadhar_document = FileField('Upload Aadhar Document', validators=[FileAllowed(['jpg', 'png', 'pdf'], 'Images and PDFs only')])
    driving_license = FileField('Upload Driving License', validators=[FileAllowed(['jpg', 'png', 'pdf'], 'Images and PDFs only')])
    police_verification = FileField('Previous Police Verification Document (Optional)', validators=[FileAllowed(['jpg', 'png', 'pdf'], 'Images and PDFs only')])
    
    submit = SubmitField('Create Helper Profile')

class ContractForm(FlaskForm):
    helper_id = HiddenField('Helper ID')
    tasks = SelectField('Tasks', choices=[], validators=[DataRequired()], render_kw={"multiple": "multiple"})
    start_date = DateField('Start Date', validators=[DataRequired()], default=datetime.date.today)
    end_date = DateField('End Date (Optional)', validators=[], default=None)
    monthly_salary = FloatField('Monthly Salary (₹)', validators=[DataRequired()])
    submit = SubmitField('Create Contract')

class ReviewForm(FlaskForm):
    helper_id = HiddenField('Helper ID')
    tasks_average = SelectField('Overall Task Performance', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], validators=[DataRequired()])
    punctuality = SelectField('Punctuality', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], validators=[DataRequired()])
    attitude = SelectField('Attitude', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], validators=[DataRequired()])
    hygiene = SelectField('Hygiene', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], validators=[DataRequired()])
    communication = SelectField('Communication', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], validators=[DataRequired()])
    reliability = SelectField('Reliability', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], validators=[DataRequired()])
    comments = TextAreaField('Comments', validators=[DataRequired()])
    submit = SubmitField('Submit Review')

class IncidentReportForm(FlaskForm):
    helper_id = HiddenField('Helper ID')
    date = DateField('Incident Date', validators=[DataRequired()], default=datetime.date.today)
    description = TextAreaField('Description of Incident', validators=[DataRequired()])
    fir_number = StringField('FIR Number (if filed)')
    submit = SubmitField('Report Incident')

class OwnerToOwnerConnectForm(FlaskForm):
    helper_id = HiddenField('Helper ID')
    to_owner_contact = StringField('Previous Owner\'s Email/Phone', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    stored_locally = BooleanField('Store this message locally for future reference', default=True)
    submit = SubmitField('Send Message')

class SearchForm(FlaskForm):
    search_type = SelectField('Search By', choices=[
        ('gov_id', 'Government ID'),
        ('phone_number', 'Phone Number')
    ], validators=[DataRequired()])
    search_value = StringField('Enter Value', validators=[DataRequired()])
    submit = SubmitField('Search')

class TaskListForm(FlaskForm):
    name = StringField('Task Name', validators=[DataRequired()])
    submit = SubmitField('Add Task')
