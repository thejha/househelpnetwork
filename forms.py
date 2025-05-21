from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, SelectMultipleField, TextAreaField, DateField, FloatField, BooleanField, MultipleFileField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from flask_wtf.file import FileField, FileAllowed, FileSize
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

class AadhaarOTPForm(FlaskForm):
    otp = StringField('OTP', validators=[
        DataRequired(), 
        Length(min=6, max=6, message="OTP must be 6 digits"),
        Regexp('^\d{6}$', message="OTP must be 6 digits")
    ])
    reference_id = HiddenField('Reference ID')
    submit = SubmitField('Verify OTP')

class AadhaarRegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Complete Registration')
    
    # Custom validators for unique email and phone number
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email address is already registered. Please use a different email or login.')
    
    def validate_phone_number(self, phone_number):
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user:
            raise ValidationError('Phone number is already registered. Please use a different phone number.')

class OwnerProfileForm(FlaskForm):
    aadhaar_id = StringField('Aadhaar Number', validators=[
        DataRequired(), 
        Length(min=12, max=12, message="Aadhaar number must be 12 digits"),
        Regexp('^\d{12}$', message="Aadhaar number must be 12 digits")
    ])
    submit = SubmitField('Save Aadhaar')

class HelperProfileForm(FlaskForm):
    name = StringField('Helper Name', validators=[DataRequired(), Length(min=2, max=100)])
    helper_type = SelectField('Helper Type', choices=[('maid', 'Maid')], validators=[DataRequired()])
    
    # Maid specific fields (shown conditionally)
    aadhar_id = StringField('Aadhar ID', validators=[])
    
    # Driver specific fields (shown conditionally)
    driving_license_id = StringField('Driving License ID', validators=[])
    
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[DataRequired()])
    languages = SelectMultipleField('Languages Spoken', choices=[], validators=[DataRequired()], render_kw={"multiple": "multiple", "class": "form-select"})
    
    photo = FileField('Upload Photo (Optional)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG, JPEG and PNG images are allowed'),
        FileSize(max_size=2 * 1024 * 1024, message='File size must be less than 2MB')
    ])
    
    submit = SubmitField('Register Helper')

class HelperAadhaarVerificationForm(FlaskForm):
    aadhaar_id = StringField('Aadhaar Number', validators=[DataRequired(), Length(min=12, max=12)])
    submit = SubmitField('Send OTP')

class CreateHelperForm(FlaskForm):
    name = StringField('Helper Name', validators=[DataRequired(), Length(min=2, max=100)])
    helper_id = StringField('Aadhaar/ID Number', validators=[DataRequired(), Length(min=2, max=50)])
    helper_type = SelectField('Helper Type', choices=[('maid', 'Maid')], validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    gender = SelectField('Gender', choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], validators=[DataRequired()])
    languages = SelectMultipleField('Languages', coerce=str, validators=[])
    aadhar_id = StringField('Aadhaar Number', validators=[Length(min=12, max=12, message="Aadhaar number must be 12 digits")])
    driving_license_id = StringField('Driving License ID', validators=[Length(min=0, max=50)])
    photo = FileField('Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Register Helper')

class SearchHelperForm(FlaskForm):
    search_term = StringField('Search by Aadhaar ID or Name', validators=[DataRequired()])
    submit = SubmitField('Search')

class ContractForm(FlaskForm):
    helper_id = HiddenField('Helper ID')
    helper_type = HiddenField('Helper Type')
    is_full_time = BooleanField('Full Time', default=False)
    
    # Create hour choices for 24-hour format (00:00 to 23:00)
    hour_choices = [(f"{hour:02d}:00", f"{hour:02d}:00") for hour in range(24)]
    
    working_hours_from = SelectField('Working Hours From', 
                                     choices=hour_choices,
                                     default="09:00")
    
    working_hours_to = SelectField('Working Hours To', 
                                  choices=hour_choices,
                                  default="17:00")
    
    tasks = SelectMultipleField('Tasks', choices=[], validators=[DataRequired()], render_kw={"multiple": "multiple"})
    
    start_date = DateField('Start Date', 
                          validators=[DataRequired()], 
                          default=datetime.date.today, 
                          format='%Y-%m-%d')
    
    end_date = DateField('End Date', 
                        validators=[], 
                        default=None, 
                        format='%Y-%m-%d',
                        render_kw={'required': False})
    
    monthly_salary = FloatField('Monthly Salary (₹)', validators=[DataRequired()])
    submit = SubmitField('Create Contract')

class ReviewForm(FlaskForm):
    helper_id = HiddenField('Helper ID')
    contract_id = HiddenField('Contract ID')
    
    # Core values - these are always the same
    punctuality = SelectField('Punctuality', 
                             choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], 
                             coerce=int,
                             validators=[DataRequired()])
    attitude = SelectField('Attitude', 
                          choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], 
                          coerce=int,
                          validators=[DataRequired()])
    hygiene = SelectField('Hygiene', 
                         choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], 
                         coerce=int,
                         validators=[DataRequired()])
    reliability = SelectField('Reliability', 
                            choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], 
                            coerce=int,
                            validators=[DataRequired()])
    communication = SelectField('Communication', 
                            choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], 
                            coerce=int,
                            default=3,
                            validators=[DataRequired()])
    
    # The task ratings will be dynamically added based on the contract tasks
    
    additional_feedback = TextAreaField('Additional Feedback')
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
