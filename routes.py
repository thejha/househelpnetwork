import os
import uuid
import datetime
import time
from functools import wraps
from flask import render_template, url_for, flash, redirect, request, jsonify, session, send_from_directory, current_app
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from extensions import db, bcrypt
from models import User, OwnerProfile, OwnerDocument, HelperProfile, HelperDocument, TaskList, Contract, Review, IncidentReport, OwnerToOwnerConnect, PincodeMapping, Language, OwnerHelperAssociation, HelperVerificationLog, AadhaarAPILog, ReviewTaskRating
from forms import (RegistrationForm, LoginForm, OwnerProfileForm, HelperProfileForm, ContractForm, ReviewForm, 
                   IncidentReportForm, OwnerToOwnerConnectForm, SearchForm, TaskListForm,
                   AadhaarVerificationForm, AadhaarOTPVerificationForm, AadhaarOTPForm, AadhaarRegistrationForm,
                   HelperAadhaarVerificationForm, CreateHelperForm, SearchHelperForm)
from utils import save_file, get_unique_id, send_notification
from aadhaar_api import generate_aadhaar_otp, verify_aadhaar_otp
from sqlalchemy import desc, func

def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("You don't have permission to access this page.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def register_routes(app):
    # Add route to serve uploaded files
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER']), filename)
    
    # Home route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('owner_dashboard'))
        return render_template('index.html', 
                              title='HouseHelpNetwork - India\'s First Peer-Verified Household Help Platform')
    
    # Authentication routes
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        # Redirect to Aadhaar-based registration
        flash('Our registration process now starts with Aadhaar verification for enhanced security. Please verify your Aadhaar to register.', 'info')
        return redirect(url_for('register_with_aadhaar'))
    
    @app.route('/register-with-aadhaar', methods=['GET', 'POST'])
    def register_with_aadhaar():
        """Step 1: User enters Aadhaar number to start registration"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        # Clear any existing Aadhaar session data when starting a new registration
        session.pop('aadhaar_data', None)
        session.pop('aadhaar_id', None)
        session.pop('aadhaar_reference_id', None)
        session.pop('registration_flow', None)
        
        # Ensure we have a session ID for tracking
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        form = AadhaarVerificationForm()
        if form.validate_on_submit():
            aadhaar_id = form.aadhaar_id.data
            
            # Check if Aadhaar is already registered
            existing_profile = OwnerProfile.query.filter_by(aadhaar_id=aadhaar_id).first()
            if existing_profile:
                form.aadhaar_id.errors.append('This Aadhaar number is already registered. Please use a different Aadhaar number or contact support if you believe this is an error.')
                return render_template('register_aadhaar.html', form=form)
            
            # Call Aadhaar API to generate OTP
            response = generate_aadhaar_otp(aadhaar_id)
            
            if response["success"]:
                # Store reference_id in session for OTP verification
                session['aadhaar_reference_id'] = response["reference_id"]
                session['aadhaar_id'] = aadhaar_id
                session['registration_flow'] = True  # Mark that we're in registration flow
                session.modified = True  # Force session update
                
                app.logger.info(f"OTP sent for Aadhaar verification: {aadhaar_id}, Reference ID: {response['reference_id']}")
                app.logger.debug(f"Session data after OTP generation: aadhaar_id={session.get('aadhaar_id')}, reference_id={session.get('aadhaar_reference_id')}")
                
                flash(f'OTP sent to your registered mobile number. {response["message"]}', 'success')
                return redirect(url_for('aadhaar_register_otp'))
            else:
                flash(f'Failed to send OTP: {response["message"]}', 'danger')
        
        return render_template('register_aadhaar.html', form=form)
    
    @app.route('/register-aadhaar-otp', methods=['GET', 'POST'])
    def aadhaar_register_otp():
        """Step 2: User enters OTP received on mobile to verify Aadhaar"""
        # Check if we have a reference_id in the session
        if 'aadhaar_reference_id' not in session or 'aadhaar_id' not in session:
            flash('Please start the registration process again.', 'warning')
            return redirect(url_for('register_with_aadhaar'))
        
        aadhaar_id = session.get('aadhaar_id')
        reference_id = session.get('aadhaar_reference_id')
        
        # Log the current session state
        app.logger.info(f"OTP verification for Aadhaar: {aadhaar_id}, Reference ID: {reference_id}")
        
        form = AadhaarOTPForm()
        form.reference_id.data = reference_id  # Pre-populate reference ID
        
        if form.validate_on_submit():
            otp = form.otp.data
            
            # Call Sandbox API to verify OTP
            response = verify_aadhaar_otp(reference_id, otp)
            
            # Check if response contains the expected data
            if not response:
                app.logger.error("OTP verification returned empty response")
                flash('An error occurred during verification. Please try again.', 'danger')
                return render_template('verify_aadhaar_registration.html', form=form, reference_id=reference_id)
            
            # Extract error message if verification failed
            error_msg = response.get("message", "Unknown error") if not response.get("success") else ""
            
            # Handle verification result
            if response["success"]:
                # Store Aadhaar data in session for registration completion
                user_details = response.get("user_details", {})
                
                # Double-check if this Aadhaar ID is already registered
                existing_profile = OwnerProfile.query.filter_by(aadhaar_id=aadhaar_id).first()
                if existing_profile:
                    flash('This Aadhaar number is already registered. Please use a different Aadhaar number or contact support.', 'danger')
                    return redirect(url_for('register_with_aadhaar'))
                
                # Store the user details in the session
                session['aadhaar_data'] = user_details
                # Ensure aadhaar_id is still in the session
                session['aadhaar_id'] = aadhaar_id
                session.modified = True  # Force session update
                
                # Log the Aadhaar data being used
                app.logger.info(f"Aadhaar verification successful for ID: {aadhaar_id}")
                app.logger.debug(f"Aadhaar user details: {user_details.get('name')}, {user_details.get('gender')}, {user_details.get('date_of_birth')}")
                app.logger.debug(f"Session data: aadhaar_id={session.get('aadhaar_id')}, has_aadhaar_data={bool(session.get('aadhaar_data'))}")
                
                flash('Aadhaar verification successful! Please complete your registration.', 'success')
                return redirect(url_for('complete_aadhaar_registration'))
            else:
                # Handle specific error types
                error_type = response.get("error_type", "UNKNOWN")
                should_regenerate = response.get("should_regenerate_otp", False)
                
                if should_regenerate:
                    # Clear the reference ID to force regeneration
                    session.pop('aadhaar_reference_id', None)
                    
                    if error_type in ["OTP_EXPIRED", "MAX_ATTEMPTS", "INVALID_REFERENCE"]:
                        flash(f'Verification failed: {error_msg} Please request a new OTP.', 'danger')
                        return redirect(url_for('register_with_aadhaar'))
                    else:
                        flash(f'Verification failed: {error_msg} Please check your Aadhaar number and try again.', 'danger')
                        return redirect(url_for('register_with_aadhaar'))
                else:
                    # User can try again with the same OTP flow
                    flash(f'Failed to verify OTP: {error_msg}. Please try again.', 'danger')
        
        reference_id = session.get('aadhaar_reference_id', '')
        return render_template('verify_aadhaar_registration.html', form=form, reference_id=reference_id)
        
    @app.route('/complete-registration', methods=['GET', 'POST'])
    def complete_aadhaar_registration():
        """Step 3: After successful Aadhaar verification, user completes registration with email and password"""
        # Check if we have Aadhaar data in the session
        if 'aadhaar_data' not in session or 'aadhaar_id' not in session:
            flash('Please start the registration process again.', 'warning')
            return redirect(url_for('register_with_aadhaar'))
        
        aadhaar_data = session.get('aadhaar_data')
        aadhaar_id = session.get('aadhaar_id')
        
        # Validate that we have the necessary data
        if not aadhaar_data or not aadhaar_id:
            app.logger.error(f"Missing critical data: aadhaar_data={bool(aadhaar_data)}, aadhaar_id={bool(aadhaar_id)}")
            flash('Registration data incomplete. Please try again.', 'danger')
            return redirect(url_for('register_with_aadhaar'))
        
        # Add a debug log to verify the data
        app.logger.info(f"Completing registration for Aadhaar ID: {aadhaar_id}")
        app.logger.debug(f"Using Aadhaar data: {aadhaar_data.get('name')}, {aadhaar_data.get('gender')}, DOB: {aadhaar_data.get('date_of_birth')}")
        app.logger.debug(f"Session data before user creation: aadhaar_id={session.get('aadhaar_id')}, aadhaar_data keys={session.get('aadhaar_data', {}).keys()}")
        
        # Double-check again if this Aadhaar ID is already registered
        existing_profile = OwnerProfile.query.filter_by(aadhaar_id=aadhaar_id).first()
        if existing_profile:
            # Clear any session data to prevent reuse
            session.pop('aadhaar_data', None)
            session.pop('aadhaar_id', None)
            session.pop('aadhaar_reference_id', None)
            session.pop('registration_flow', None)
            
            flash('This Aadhaar number is already registered. Please use a different Aadhaar number or contact support.', 'danger')
            return redirect(url_for('register_with_aadhaar'))
        
        form = AadhaarRegistrationForm()
        
        # Pre-populate the phone number from Aadhaar data if available
        if request.method == 'GET' and aadhaar_data.get('phone'):
            form.phone_number.data = aadhaar_data.get('phone')
        
        if form.validate_on_submit():
            try:
                # Create a new user
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                
                # Get address data from Aadhaar
                address_dict = aadhaar_data.get("address", {})
                full_address = aadhaar_data.get("full_address", "")
                
                # Create user
                user = User(
                    name=aadhaar_data.get("name", ""),
                    email=form.email.data,
                    phone_number=form.phone_number.data,
                    password_hash=hashed_password,
                    role='owner'  # Default role is owner
                )
                
                db.session.add(user)
                db.session.flush()  # Get the user ID without committing
                
                # Create owner profile with Aadhaar details
                owner_profile = OwnerProfile(
                    owner_id=user.id,
                    aadhaar_id=aadhaar_id,
                    aadhaar_verified=True,
                    aadhaar_verified_at=datetime.datetime.utcnow(),
                    aadhaar_name=aadhaar_data.get("name", ""),
                    aadhaar_gender=aadhaar_data.get("gender", ""),
                    aadhaar_dob=aadhaar_data.get("date_of_birth", ""),
                    aadhaar_address=full_address,
                    aadhaar_photo=aadhaar_data.get("photo", ""),
                    # Detailed address components
                    address_house=address_dict.get("house", ""),
                    address_landmark=address_dict.get("landmark", ""),
                    address_vtc=address_dict.get("vtc", ""),
                    address_district=address_dict.get("district", ""),
                    address_state=address_dict.get("state", ""),
                    address_pincode=str(address_dict.get("pincode", "")),
                    address_country=address_dict.get("country", "India"),
                    address_post_office=address_dict.get("post_office", ""),
                    address_street=address_dict.get("street", ""),
                    address_subdistrict=address_dict.get("subdistrict", ""),
                    # Original fields
                    pincode=str(address_dict.get("pincode", "")),
                    state=address_dict.get("state", ""),
                    city=address_dict.get("district", address_dict.get("vtc", "")),
                    society=address_dict.get("landmark", ""),
                    street=address_dict.get("street", ""),
                    apartment_number=address_dict.get("house", ""),
                    verification_status='Verified'  # Auto-verify users with Aadhaar
                )
                
                db.session.add(owner_profile)
                
                # Log before commit for debugging
                app.logger.info(f"About to commit new user with ID: {user.id} and Aadhaar ID: {aadhaar_id}")
                
                db.session.commit()
                
                # Log successful registration
                app.logger.info(f"Successfully registered user with ID: {user.id} and Aadhaar ID: {aadhaar_id}")
                
                # Clear session data
                session.pop('aadhaar_data', None)
                session.pop('aadhaar_id', None)
                session.pop('aadhaar_reference_id', None)
                session.pop('registration_flow', None)
                
                # Log in the user automatically after registration
                login_user(user)
                
                flash('Your account has been created with verified Aadhaar details! Welcome to HouseHelpNetwork.', 'success')
                return redirect(url_for('owner_dashboard'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error creating user: {str(e)}")
                app.logger.exception("Full exception details:")
                flash(f'An error occurred while creating your account. Please try again.', 'danger')
        
        return render_template('complete_registration.html', form=form, aadhaar_data=aadhaar_data)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('owner_dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            
            if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember.data)
                
                # Check if user has completed their profile
                if not user.owner_profile:
                    flash('Please complete your profile first.', 'info')
                    return redirect(url_for('aadhaar_verification'))
                
                next_page = request.args.get('next')
                flash('Login successful!', 'success')
                if next_page:
                    return redirect(next_page)
                else:
                    # Redirect to dashboard instead of index
                    return redirect(url_for('owner_dashboard'))
            else:
                flash('Login unsuccessful. Please check email and password.', 'danger')
        
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    def logout():
        # Clear all Aadhaar-related session data
        session.pop('aadhaar_data', None)
        session.pop('aadhaar_id', None)
        session.pop('aadhaar_reference_id', None)
        session.pop('registration_flow', None)
        
        # Also clear helper verification session data if exists
        session.pop('helper_aadhaar_reference_id', None)
        session.pop('helper_aadhaar_id', None)
        session.pop('helper_id', None)
        
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    # Aadhaar Verification Routes
    @app.route('/aadhaar-verification', methods=['GET', 'POST'])
    @login_required
    def aadhaar_verification():
        # Check if profile already exists and verified
        owner_profile = OwnerProfile.query.filter_by(owner_id=current_user.id).first()
        if owner_profile and owner_profile.aadhaar_verified:
            flash('Your Aadhaar is already verified.', 'info')
            return redirect(url_for('profile'))
        
        form = AadhaarVerificationForm()
        if form.validate_on_submit():
            aadhaar_id = form.aadhaar_id.data
            
            # Call Aadhaar API to generate OTP
            response = generate_aadhaar_otp(aadhaar_id)
            
            if response["success"]:
                # Store reference_id in session for OTP verification
                session['aadhaar_reference_id'] = response["reference_id"]
                session['aadhaar_id'] = aadhaar_id
                
                flash(f'OTP sent to your registered mobile number. {response["message"]}', 'success')
                return redirect(url_for('verify_sandbox_otp'))
            else:
                flash(f'Failed to send OTP: {response["message"]}', 'danger')
        
        return render_template('aadhaar_verification.html', form=form)
    
    @app.route('/verify-sandbox-otp', methods=['GET', 'POST'])
    @login_required
    def verify_sandbox_otp():
        # Check if we have a reference_id in the session
        if 'aadhaar_reference_id' not in session or 'aadhaar_id' not in session:
            flash('Please start the Aadhaar verification process again.', 'warning')
            return redirect(url_for('profile'))
        
        form = AadhaarOTPForm()
        
        if form.validate_on_submit():
            otp = form.otp.data
            reference_id = form.reference_id.data or session['aadhaar_reference_id']
            
            # Call Sandbox API to verify OTP
            response = verify_aadhaar_otp(reference_id, otp)
            
            if response["success"]:
                # Create or update owner profile with Aadhaar details
                owner_profile = OwnerProfile.query.filter_by(owner_id=current_user.id).first()
                user_details = response.get("user_details", {})
                address_dict = user_details.get("address", {})
                
                # Format the complete address as a string for storage
                full_address = user_details.get("full_address", "")
                
                # If profile doesn't exist, create a new one
                if not owner_profile:
                    owner_profile = OwnerProfile(
                        owner_id=current_user.id,
                        aadhaar_id=session['aadhaar_id'],
                        aadhaar_verified=True,
                        aadhaar_verified_at=datetime.datetime.utcnow(),
                        aadhaar_name=user_details.get("name", ""),
                        aadhaar_gender=user_details.get("gender", ""),
                        aadhaar_dob=user_details.get("date_of_birth", ""),
                        aadhaar_address=full_address,
                        aadhaar_photo=user_details.get("photo", ""),
                        # Detailed address components
                        address_house=address_dict.get("house", ""),
                        address_landmark=address_dict.get("landmark", ""),
                        address_vtc=address_dict.get("vtc", ""),
                        address_district=address_dict.get("district", ""),
                        address_state=address_dict.get("state", ""),
                        address_pincode=str(address_dict.get("pincode", "")),
                        address_country=address_dict.get("country", "India"),
                        address_post_office=address_dict.get("post_office", ""),
                        address_street=address_dict.get("street", ""),
                        address_subdistrict=address_dict.get("subdistrict", ""),
                        # Original fields
                        pincode=str(address_dict.get("pincode", "")),
                        state=address_dict.get("state", ""),
                        city=address_dict.get("district", address_dict.get("vtc", "")),
                        society=address_dict.get("landmark", ""),
                        street=address_dict.get("street", ""),
                        apartment_number=address_dict.get("house", ""),
                        verification_status='Verified'  # Auto-verify users with Aadhaar
                    )
                    db.session.add(owner_profile)
                else:
                    # Update existing profile with Aadhaar details
                    owner_profile.aadhaar_id = session['aadhaar_id']
                    owner_profile.aadhaar_verified = True
                    owner_profile.aadhaar_verified_at = datetime.datetime.utcnow()
                    owner_profile.aadhaar_name = user_details.get("name", "")
                    owner_profile.aadhaar_gender = user_details.get("gender", "")
                    owner_profile.aadhaar_dob = user_details.get("date_of_birth", "")
                    owner_profile.aadhaar_address = full_address
                    owner_profile.aadhaar_photo = user_details.get("photo", "")
                    
                    # Update detailed address components
                    owner_profile.address_house = address_dict.get("house", "")
                    owner_profile.address_landmark = address_dict.get("landmark", "")
                    owner_profile.address_vtc = address_dict.get("vtc", "")
                    owner_profile.address_district = address_dict.get("district", "")
                    owner_profile.address_state = address_dict.get("state", "")
                    owner_profile.address_pincode = str(address_dict.get("pincode", ""))
                    owner_profile.address_country = address_dict.get("country", "India")
                    owner_profile.address_post_office = address_dict.get("post_office", "")
                    owner_profile.address_street = address_dict.get("street", "")
                    owner_profile.address_subdistrict = address_dict.get("subdistrict", "")
                    
                    # Update original fields
                    owner_profile.verification_status = 'Verified'  # Auto-verify users with Aadhaar
                    owner_profile.pincode = str(address_dict.get("pincode", owner_profile.pincode))
                    owner_profile.state = address_dict.get("state", owner_profile.state)
                    owner_profile.city = address_dict.get("district", address_dict.get("vtc", owner_profile.city))
                    owner_profile.society = address_dict.get("landmark", owner_profile.society)
                    owner_profile.street = address_dict.get("street", owner_profile.street)
                    owner_profile.apartment_number = address_dict.get("house", owner_profile.apartment_number)
                
                # Update user's name if it came from Aadhaar
                if user_details.get("name") and user_details["name"] != current_user.name:
                    current_user.name = user_details["name"]
                
                db.session.commit()
                
                # Store Aadhaar data in session for display
                session['aadhaar_data'] = user_details
                
                # Clear session data after use
                aadhaar_id = session.pop('aadhaar_id', None)
                session.pop('aadhaar_reference_id', None)
                
                flash('Aadhaar verification successful!', 'success')
                return redirect(url_for('aadhaar_details', aadhaar_id=aadhaar_id))
            else:
                flash(f'Failed to verify OTP: {response["message"]}', 'danger')
        
        reference_id = session.get('aadhaar_reference_id', '')
        return render_template('verify_aadhaar.html', form=form, reference_id=reference_id)
        
    @app.route('/aadhaar-details/<aadhaar_id>')
    @login_required
    def aadhaar_details(aadhaar_id):
        # Check if we have Aadhaar data in the session
        aadhaar_data = session.get('aadhaar_data')
        if not aadhaar_data:
            flash('No Aadhaar data found. Please verify your Aadhaar again.', 'warning')
            return redirect(url_for('profile'))
        
        # Clear Aadhaar data from session after displaying
        session.pop('aadhaar_data', None)
        
        return render_template('aadhaar_details.html', aadhaar_data=aadhaar_data, aadhaar_number=aadhaar_id)
    
    # Profile routes
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        # Check if we already have an owner profile
        owner_profile = OwnerProfile.query.filter_by(owner_id=current_user.id).first()
        form = OwnerProfileForm()
        
        if form.validate_on_submit():
            aadhaar_id = form.aadhaar_id.data
            # Generate OTP via Sandbox API
            response = generate_aadhaar_otp(aadhaar_id)
            
            if response["success"]:
                # Store reference_id in session for OTP verification
                session['aadhaar_id'] = aadhaar_id
                session['aadhaar_reference_id'] = response["reference_id"]
                
                flash(f'OTP sent to your registered mobile number. {response["message"]}', 'success')
                return redirect(url_for('verify_sandbox_otp'))
            else:
                flash(f'Failed to verify Aadhaar: {response["message"]}', 'danger')
        
        elif request.method == 'GET' and owner_profile:
            # Pre-populate form with existing Aadhaar data
            form.aadhaar_id.data = owner_profile.aadhaar_id
        
        # Get list of documents if profile exists
        documents = []
        if owner_profile:
            documents = OwnerDocument.query.filter_by(owner_profile_id=owner_profile.id).all()
        
        return render_template('profile.html', form=form, owner_profile=owner_profile, documents=documents)
    
    # Helper Management Routes
    @app.route('/create-helper', methods=['GET', 'POST'])
    @login_required
    def create_helper():
        """Create a new helper profile or associate an existing one"""
        form = CreateHelperForm()
        
        try:
            # Fill the form with available languages
            languages = Language.query.all()
            if not languages:
                # Add default languages if none exist
                default_languages = ["English", "Hindi", "Bengali", "Tamil", "Telugu", "Marathi"]
                for lang_name in default_languages:
                    db.session.add(Language(name=lang_name))
                db.session.commit()
                languages = Language.query.all()
            
            form.languages.choices = [(str(lang.id), lang.name) for lang in languages]
        except Exception as e:
            print(f"Error loading languages: {str(e)}")
            app.logger.error(f"Error loading languages: {str(e)}")
            form.languages.choices = [('1', 'English')]  # Default fallback
        
        # Debug request
        if request.method == 'POST':
            print("Form submitted with POST method")
            print(f"Form data: {request.form}")
            print(f"Photo data present: {form.photo.data is not None}")
            print(f"helper_id: {form.helper_id.data}")
            print(f"Form valid: {form.validate()}")
            
            if not form.validate():
                print("Form validation errors:")
                for field, errors in form.errors.items():
                    print(f"Field {field}: {errors}")
                # Detailed field validation info
                print(f"helper_id field data: {form.helper_id.data}")
                print(f"helper_id field valid: {form.helper_id.validate(form)}")
        
        if form.validate_on_submit():
            helper_id = form.helper_id.data
            
            # Check if helper already exists
            existing_helper = HelperProfile.query.filter_by(helper_id=helper_id).first()
            
            if existing_helper:
                # Associate the current owner with this helper if not already associated
                existing_association = OwnerHelperAssociation.query.filter_by(
                    owner_id=current_user.id, 
                    helper_profile_id=existing_helper.id
                ).first()
                
                if existing_association:
                    flash('You are already associated with this helper.', 'info')
                else:
                    # Create new association (not as primary owner)
                    association = OwnerHelperAssociation(
                        owner_id=current_user.id,
                        helper_profile_id=existing_helper.id,
                        is_primary_owner=False
                    )
                    db.session.add(association)
                    db.session.commit()
                    flash('You have been associated with this existing helper.', 'success')
                
                return redirect(url_for('helper_detail', helper_id=helper_id))
            
            # Process photo upload
            photo_url = None
            if form.photo.data:
                try:
                    filename = secure_filename(f"{helper_id}_{int(time.time())}.jpg")
                    filepath = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'helper_photos', filename)
                    form.photo.data.save(filepath)
                    photo_url = url_for('static', filename=f"uploads/helper_photos/{filename}")
                except Exception as e:
                    flash(f'Error uploading photo: {str(e)}', 'danger')
            
            # Process languages
            language_str = ""
            try:
                language_names = []
                language_ids = request.form.getlist('languages')
                if language_ids:
                    for lang_id in language_ids:
                        language_obj = Language.query.get(int(lang_id))
                        if language_obj:
                            language_names.append(language_obj.name)
                    language_str = ", ".join(language_names)
                else:
                    language_str = "Not specified"
            except Exception as e:
                app.logger.error(f"Error processing languages: {str(e)}")
                language_str = "Error processing languages"
            
            # Create helper profile with minimal information
            try:
                helper = HelperProfile(
                    name=form.name.data,
                    helper_id=helper_id,
                    helper_type=form.helper_type.data,
                    phone_number=form.phone_number.data,
                    photo_url=photo_url,
                    languages=language_str,
                    created_by=current_user.id,
                    gender=form.gender.data,
                    verification_status='Unverified'
                )
                
                db.session.add(helper)
                db.session.commit()
                
                # Create the owner-helper association with this user as primary owner
                association = OwnerHelperAssociation(
                    owner_id=current_user.id,
                    helper_profile_id=helper.id,
                    is_primary_owner=True
                )
                db.session.add(association)
                db.session.commit()
                
                flash('Helper profile created successfully! You can now verify their Aadhaar details.', 'success')
                # Redirect to a helper verification page in the future
                return redirect(url_for('helper_detail', helper_id=helper.helper_id))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error creating helper: {str(e)}")
                flash(f'An error occurred while creating the helper: {str(e)}', 'danger')
        
        return render_template('create_helper.html', form=form)
    
    @app.route('/helpers/<helper_id>')
    @login_required
    def helper_detail(helper_id):
        """View details of a helper"""
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first_or_404()
        
        # Check if the current user is associated with this helper
        association = OwnerHelperAssociation.query.filter_by(
            helper_profile_id=helper.id,
            owner_id=current_user.id
        ).first()
        
        if not association and current_user.role != 'admin':
            flash('You can only view helpers that are associated with your account.', 'danger')
            return redirect(url_for('owner_dashboard'))
        
        # Get verification logs for this helper
        verification_logs = HelperVerificationLog.query.filter_by(
            helper_profile_id=helper.id
        ).order_by(HelperVerificationLog.verification_timestamp.desc()).all()
        
        # Check if current user is the primary owner
        is_primary_owner = association.is_primary_owner if association else False
        
        # Get all owners of this helper
        owner_associations = OwnerHelperAssociation.query.filter_by(
            helper_profile_id=helper.id
        ).all()
        owner_ids = [assoc.owner_id for assoc in owner_associations]
        owners = User.query.filter(User.id.in_(owner_ids)).all() if owner_ids else []
        
        # Get current date for age calculation
        now = datetime.datetime.now()
        
        # Explicitly query for reviews to avoid relationship loading issues
        reviews = Review.query.filter_by(helper_profile_id=helper.id).order_by(Review.timestamp.desc()).all()
        
        # Calculate average rating
        avg_rating = 0
        if reviews:
            total_rating = sum(review.overall_rating for review in reviews)
            avg_rating = total_rating / len(reviews)
        
        # Prepare recent reviews (take up to 3)
        recent_reviews = reviews[:3] if reviews else []
        
        return render_template('helper_detail.html', 
                              helper=helper, 
                              verification_logs=verification_logs,
                              is_primary_owner=is_primary_owner,
                              owners=owners,
                              now=now,
                              reviews=reviews,
                              recent_reviews=recent_reviews,
                              avg_rating=avg_rating)
    
    @app.route('/contracts/create/<helper_id>', methods=['GET', 'POST'])
    @login_required
    def create_contract(helper_id):
        """Create a new contract with a helper"""
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first_or_404()
        
        # Check if the current user is associated with this helper
        association = OwnerHelperAssociation.query.filter_by(
            helper_profile_id=helper.id,
            owner_id=current_user.id
        ).first()
        
        if not association:
            flash('You can only create contracts with helpers that are associated with your account.', 'danger')
            return redirect(url_for('owner_dashboard'))
        
        # Create contract form
        form = ContractForm()
        form.helper_id.data = helper.helper_id
        form.helper_type.data = helper.helper_type
        
        # Set default start date to today
        form.start_date.data = datetime.date.today()
        
        # Load tasks from database for the select field based on helper type
        tasks = TaskList.query.filter_by(helper_type=helper.helper_type).all()
        
        # Define separator used to distinguish categories in task labels
        category_separator = " - "
        
        # Organize tasks by category
        categorized_tasks = {}
        for task in tasks:
            if task.category not in categorized_tasks:
                categorized_tasks[task.category] = []
            
            # Only include sub-tasks as selectable options
            # Main tasks should only serve as category headers and not be selectable
            if not task.is_main_task:
                # Add category prefix for proper categorization in UI
                choice_label = f"{task.category}{category_separator}{task.name}"
                categorized_tasks[task.category].append((str(task.id), choice_label))
        
        # Flatten the choices list
        all_choices = []
        for category, choices in categorized_tasks.items():
            all_choices.extend(choices)
            
        form.tasks.choices = all_choices
        
        # Debug information for form validation
        app.logger.info(f"Form submitted: {request.form}")
        app.logger.info(f"Form validation result: {form.validate()}")
        if form.errors:
            app.logger.info(f"Form errors: {form.errors}")
        
        # Process form even if validation fails for certain fields
        if request.method == 'POST':
            try:
                # Create a unique contract ID
                contract_id = f"CT{int(time.time())}{current_user.id}{helper.id}"
                
                # Get selected tasks as comma-separated list
                selected_tasks = request.form.getlist('tasks')
                tasks_str = ','.join(selected_tasks)
                
                # Get start_date value from request
                start_date_str = request.form.get('start_date', '')
                start_date = None
                if start_date_str and start_date_str.strip():
                    try:
                        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Invalid start date format. Please use YYYY-MM-DD format.', 'danger')
                        return render_template('contract.html', form=form, helper=helper, category_separator=category_separator)
                else:
                    flash('Start date is required.', 'danger')
                    return render_template('contract.html', form=form, helper=helper, category_separator=category_separator)
                
                # Get end_date value from request
                end_date_str = request.form.get('end_date', '')
                end_date = None
                if end_date_str and end_date_str.strip():
                    try:
                        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        # If invalid date format, leave as None
                        pass
                
                # Create contract
                contract = Contract(
                    contract_id=contract_id,
                    helper_profile_id=helper.id,
                    owner_id=current_user.id,
                    tasks=tasks_str,
                    is_full_time=form.is_full_time.data,
                    working_hours_from=None if form.is_full_time.data else form.working_hours_from.data,
                    working_hours_to=None if form.is_full_time.data else form.working_hours_to.data,
                    start_date=start_date,  # Use directly parsed value
                    end_date=end_date,  # Use directly parsed value
                    monthly_salary=form.monthly_salary.data
                )
                
                db.session.add(contract)
                db.session.commit()
                
                flash('Contract created successfully!', 'success')
                return redirect(url_for('owner_dashboard'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error creating contract: {str(e)}")
                flash(f'An error occurred while creating the contract: {str(e)}', 'danger')
        
        return render_template('contract.html', form=form, helper=helper, category_separator=category_separator)
    
    @app.route('/helpers/<helper_id>/associate', methods=['GET', 'POST'])
    @login_required
    def associate_helper(helper_id):
        """Associate an existing helper with the current user"""
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first_or_404()
        
        # Check if already associated
        existing_association = OwnerHelperAssociation.query.filter_by(
            owner_id=current_user.id,
            helper_profile_id=helper.id
        ).first()
        
        if existing_association:
            flash('You are already associated with this helper.', 'info')
            return redirect(url_for('helper_detail', helper_id=helper_id))
        
        # Create new association (not as primary owner)
        association = OwnerHelperAssociation(
            owner_id=current_user.id,
            helper_profile_id=helper.id,
            is_primary_owner=False
        )
        db.session.add(association)
        db.session.commit()
        
        flash('You have been associated with this helper.', 'success')
        return redirect(url_for('helper_detail', helper_id=helper_id))
    
    @app.route('/search-helper', methods=['GET', 'POST'])
    @login_required
    def search_helper():
        """Search for a helper by Aadhaar ID or name to associate with"""
        form = SearchHelperForm()
        
        if form.validate_on_submit():
            search_term = form.search_term.data
            
            # Search by Aadhaar ID (exact match) or name (partial match)
            helpers = HelperProfile.query.filter(
                (HelperProfile.helper_id == search_term) |
                (HelperProfile.name.ilike(f'%{search_term}%'))
            ).all()
            
            return render_template('search_helper_results.html', helpers=helpers, search_term=search_term)
            
        return render_template('search_helper.html', form=form)
    
    # Admin routes
    @app.route('/admin/dashboard')
    @login_required
    @admin_required
    def admin_dashboard():
        # Get statistics for the admin dashboard
        total_users = User.query.count()
        total_helpers = HelperProfile.query.count()
        total_contracts = Contract.query.count()
        total_reviews = Review.query.count()
        
        # Get recent activities
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_helpers = HelperProfile.query.order_by(HelperProfile.created_at.desc()).limit(5).all()
        recent_contracts = Contract.query.order_by(Contract.created_at.desc()).limit(5).all()
        recent_reviews = Review.query.order_by(Review.timestamp.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                              total_users=total_users,
                              total_helpers=total_helpers,
                              total_contracts=total_contracts,
                              total_reviews=total_reviews,
                              recent_users=recent_users,
                              recent_helpers=recent_helpers,
                              recent_contracts=recent_contracts,
                              recent_reviews=recent_reviews)
    
    @app.route('/admin/analytics')
    @login_required
    @admin_required
    def admin_analytics():
        """View analytics dashboard for helpers performance"""
        # Check if analytics images exist
        import os
        analytics_dir = os.path.join(app.static_folder, 'analytics')
        os.makedirs(analytics_dir, exist_ok=True)
        
        distribution_img = 'analytics/helper_type_distribution.png'
        city_img = 'analytics/helper_city_distribution.png'
        ratings_img = 'analytics/ratings_by_helper_type.png'
        
        # Get top helpers by overall rating
        top_helpers = db.session.query(
            HelperProfile,
            func.avg(Review.overall_rating).label('avg_rating'),
            func.count(Review.id).label('review_count')
        ).join(Review, HelperProfile.id == Review.helper_profile_id)\
         .group_by(HelperProfile.id)\
         .having(func.count(Review.id) > 0)\
         .order_by(desc('avg_rating'))\
         .limit(10).all()
        
        # Get top helpers by city
        top_helpers_by_city = {}
        cities = db.session.query(HelperProfile.city).filter(HelperProfile.city != None).distinct().all()
        
        for city_result in cities:
            city = city_result[0]
            if not city:
                continue
                
            city_top = db.session.query(
                HelperProfile,
                func.avg(Review.overall_rating).label('avg_rating'),
                func.count(Review.id).label('review_count')
            ).join(Review, HelperProfile.id == Review.helper_profile_id)\
             .filter(HelperProfile.city == city)\
             .group_by(HelperProfile.id)\
             .having(func.count(Review.id) > 0)\
             .order_by(desc('avg_rating'))\
             .limit(3).all()
             
            if city_top:
                top_helpers_by_city[city] = city_top
        
        # Get top cleaning helpers
        top_cleaning = db.session.query(
            HelperProfile,
            func.avg(Review.hygiene).label('avg_hygiene'),
            func.avg(Review.overall_rating).label('avg_rating'),
            func.count(Review.id).label('review_count')
        ).join(Review, HelperProfile.id == Review.helper_profile_id)\
         .filter(HelperProfile.helper_type == 'maid')\
         .group_by(HelperProfile.id)\
         .having(func.count(Review.id) > 0)\
         .order_by(desc('avg_hygiene'))\
         .limit(5).all()
        
        return render_template('admin/analytics.html',
                              top_helpers=top_helpers,
                              top_helpers_by_city=top_helpers_by_city,
                              top_cleaning=top_cleaning,
                              distribution_img=distribution_img,
                              city_img=city_img,
                              ratings_img=ratings_img)
                              
    @app.route('/admin/run-analytics')
    @login_required
    @admin_required
    def run_analytics():
        """Run the analytics script to update visualizations and data"""
        try:
            from generate_analytics import generate_helper_analytics
            generate_helper_analytics()
            flash('Analytics data and visualizations have been updated successfully.', 'success')
        except Exception as e:
            app.logger.error(f"Error running analytics: {str(e)}")
            flash(f'An error occurred while generating analytics: {str(e)}', 'danger')
            
        return redirect(url_for('admin_analytics'))
    
    @app.route('/admin/tasks', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def manage_tasks():
        form = TaskListForm()
        
        if form.validate_on_submit():
            # Check if task already exists
            existing_task = TaskList.query.filter_by(name=form.name.data).first()
            
            if existing_task:
                flash('This task already exists!', 'danger')
            else:
                # Create new task
                task = TaskList(name=form.name.data)
                db.session.add(task)
                db.session.commit()
                
                flash('Task added successfully!', 'success')
            
            return redirect(url_for('manage_tasks'))
        
        # Get all tasks
        tasks = TaskList.query.all()
        
        return render_template('admin/manage_tasks.html', form=form, tasks=tasks)
    
    @app.route('/admin/tasks/delete/<int:task_id>', methods=['POST'])
    @login_required
    @admin_required
    def delete_task(task_id):
        task = TaskList.query.get_or_404(task_id)
        
        db.session.delete(task)
        db.session.commit()
        
        flash('Task deleted successfully!', 'success')
        return redirect(url_for('manage_tasks'))
    
    @app.route('/admin/pincodes/search', methods=['GET'])
    @login_required
    @admin_required
    def search_pincodes():
        """Search for pincodes. Admin-only route."""
        search_term = request.args.get('term', '')
        if not search_term:
            return jsonify({'success': False, 'message': 'No search term provided'})
        
        # Search for matching pincodes
        pincodes = PincodeMapping.query.filter(PincodeMapping.pincode.contains(search_term)).all()
        
        if not pincodes:
            return jsonify({'success': False, 'message': 'No matching pincodes found'})
        
        # Format results
        results = []
        for pincode in pincodes:
            results.append({
                'id': pincode.id,
                'pincode': pincode.pincode,
                'state': pincode.state,
                'city': pincode.city,
                'society': pincode.society
            })
        
        return jsonify({'success': True, 'results': results})
        
    @app.route('/pincodes/lookup', methods=['GET'])
    def lookup_pincode():
        """Lookup a pincode. Public route that can be accessed by any logged-in user."""
        pincode = request.args.get('pincode', '')
        if not pincode:
            return jsonify({'success': False, 'message': 'No pincode provided'})
        
        # Search for exact pincode match
        pincode_data = PincodeMapping.query.filter(PincodeMapping.pincode == pincode).first()
        
        if not pincode_data:
            return jsonify({'success': False, 'message': 'Pincode not found'})
        
        # Return pincode data
        result = {
            'pincode': pincode_data.pincode,
            'state': pincode_data.state,
            'city': pincode_data.city,
            'society': pincode_data.society
        }
        
        return jsonify({'success': True, 'result': result})
    
    @app.route('/admin/pincodes', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def manage_pincodes():
        """Admin interface for managing pincode mappings."""
        from flask_wtf import FlaskForm
        from flask_wtf.file import FileField, FileAllowed
        from wtforms import StringField, SubmitField
        from wtforms.validators import DataRequired, Length
        import csv
        import io
        
        # Form for adding new pincode mappings
        class PincodeForm(FlaskForm):
            pincode = StringField('Pincode', validators=[DataRequired(), Length(min=6, max=10)])
            city = StringField('City', validators=[DataRequired()])
            state = StringField('State', validators=[DataRequired()])
            society = StringField('Society/Building Name', validators=[DataRequired()])
            submit = SubmitField('Add Pincode')
        
        # Form for bulk upload
        class BulkUploadForm(FlaskForm):
            csv_file = FileField('CSV File', validators=[
                DataRequired(),
                FileAllowed(['csv'], 'CSV files only!')
            ])
            submit = SubmitField('Upload Pincodes')
        
        form = PincodeForm()
        bulk_form = BulkUploadForm()
        
        # Process single pincode form submission
        if form.validate_on_submit():
            # Check if submit button from the single pincode form was clicked
            if 'submit' in request.form:
                # Check if pincode already exists
                existing_pincode = PincodeMapping.query.filter_by(pincode=form.pincode.data).first()
                if existing_pincode:
                    flash('Pincode already exists. Please update the existing one instead.', 'warning')
                else:
                    try:
                        # Add new pincode mapping
                        pincode_mapping = PincodeMapping(
                            pincode=form.pincode.data,
                            city=form.city.data,
                            state=form.state.data,
                            society=form.society.data
                        )
                        db.session.add(pincode_mapping)
                        db.session.commit()
                        flash('Pincode mapping added successfully!', 'success')
                    except Exception as e:
                        db.session.rollback()
                        app.logger.error(f"Error adding pincode: {str(e)}")
                        flash(f'Error adding pincode: {str(e)}', 'danger')
                    
                return redirect(url_for('manage_pincodes'))
        
        # Process bulk upload form submission
        if bulk_form.validate_on_submit() and 'csv_file' in request.files:
            csv_file = request.files['csv_file']
            if csv_file:
                # Read CSV file
                csv_file_stream = io.StringIO(csv_file.stream.read().decode("UTF-8"), newline=None)
                csv_reader = csv.reader(csv_file_stream)
                
                # Skip header row if exists
                header = next(csv_reader, None)
                expected_headers = ['pincode', 'state', 'city', 'society']
                
                # Prepare counters for reporting
                total_rows = 0
                added_rows = 0
                skipped_rows = 0
                error_rows = 0
                
                try:
                    # Process each row and add to database
                    for row in csv_reader:
                        total_rows += 1
                        
                        # Skip empty rows
                        if not row or len(row) < 4:
                            skipped_rows += 1
                            continue
                        
                        pincode, state, city, society = row[0], row[1], row[2], row[3]
                        
                        # Skip if any required field is empty
                        if not pincode or not state or not city or not society:
                            skipped_rows += 1
                            continue
                        
                        # Check if pincode already exists
                        existing_pincode = PincodeMapping.query.filter_by(pincode=pincode).first()
                        if existing_pincode:
                            skipped_rows += 1
                            continue
                        
                        try:
                            # Add new pincode mapping
                            pincode_mapping = PincodeMapping(
                                pincode=pincode,
                                city=city,
                                state=state,
                                society=society
                            )
                            db.session.add(pincode_mapping)
                            added_rows += 1
                        except Exception as e:
                            error_rows += 1
                            app.logger.error(f"Error adding pincode {pincode}: {str(e)}")
                    
                    # Commit all changes
                    db.session.commit()
                    flash(f'Bulk upload complete! Added {added_rows} pincodes, skipped {skipped_rows}, errors {error_rows}.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error processing CSV file: {str(e)}', 'danger')
                
                return redirect(url_for('manage_pincodes'))
        
        # Get last 5 pincode mappings by default
        pincodes = PincodeMapping.query.order_by(PincodeMapping.id.desc()).limit(5).all()
        
        return render_template('admin/manage_pincodes.html', 
                               form=form, 
                               bulk_form=bulk_form, 
                               pincodes=pincodes, 
                               title='Manage Pincodes')
    
    @app.route('/admin/pincodes/delete/<int:pincode_id>', methods=['POST'])
    @login_required
    @admin_required
    def delete_pincode(pincode_id):
        """Delete a pincode mapping."""
        pincode = PincodeMapping.query.get_or_404(pincode_id)
        
        db.session.delete(pincode)
        db.session.commit()
        
        flash('Pincode mapping deleted successfully!', 'success')
        return redirect(url_for('manage_pincodes'))
        
    @app.route('/admin/verify-users')
    @login_required
    @admin_required
    def verify_users():
        # Only get profiles that need manual verification (not already verified via Aadhaar)
        pending_profiles = OwnerProfile.query.filter_by(verification_status='Pending').all()
        
        profiles_with_users = []
        for profile in pending_profiles:
            user = User.query.get(profile.owner_id)
            documents = OwnerDocument.query.filter_by(owner_profile_id=profile.id).all()
            
            profiles_with_users.append({
                'profile': profile,
                'user': user,
                'documents': documents
            })
        
        return render_template('admin/verify_users.html', profiles=profiles_with_users)
    
    @app.route('/admin/verify/<int:profile_id>/<status>', methods=['POST'])
    @login_required
    @admin_required
    def update_verification(profile_id, status):
        profile = OwnerProfile.query.get_or_404(profile_id)
        
        if status not in ['Verified', 'Rejected']:
            flash('Invalid verification status!', 'danger')
            return redirect(url_for('verify_users'))
        
        profile.verification_status = status
        db.session.commit()
        
        # Get the owner and send notification
        owner = User.query.get(profile.owner_id)
        send_notification(
            to=owner.email,
            subject=f'HouseHelpNetwork: Profile {status}',
            message=f'Your profile has been {status.lower()}.'
        )
        
        flash(f'Profile {status.lower()} successfully!', 'success')
        return redirect(url_for('verify_users'))

    # Owner Dashboard route
    @app.route('/dashboard')
    @login_required
    def owner_dashboard():
        """Dashboard for owners showing their helpers and contracts"""
        # Get helpers associated with this user (including those created by others)
        associations = OwnerHelperAssociation.query.filter_by(owner_id=current_user.id).all()
        helper_ids = [assoc.helper_profile_id for assoc in associations]
        helpers = HelperProfile.query.filter(HelperProfile.id.in_(helper_ids)).all() if helper_ids else []
        helpers_count = len(helpers)
        
        # Get contracts for this user
        contracts = Contract.query.filter_by(owner_id=current_user.id).all()
        
        # Sort contracts: active contracts first, then terminated contracts
        sorted_contracts = sorted(contracts, key=lambda c: (c.is_terminated, -c.created_at.timestamp()))
        
        return render_template('owner_dashboard.html', 
                              helpers=helpers,
                              helpers_count=helpers_count,
                              contracts=sorted_contracts)

    @app.route('/helpers/<helper_id>/verify', methods=['GET', 'POST'])
    @login_required
    def verify_helper_aadhaar(helper_id):
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first_or_404()
        
        # Check if the current user is associated with this helper
        association = OwnerHelperAssociation.query.filter_by(
            helper_profile_id=helper.id,
            owner_id=current_user.id
        ).first()
        
        if not association:
            flash('You can only verify helpers that are associated with your account.', 'danger')
            return redirect(url_for('owner_dashboard'))
        
        # Check if helper is already verified - now just display a notice but continue
        if helper.verification_status == 'Verified':
            flash('This helper is already verified. Re-verification will update existing data.', 'info')
        
        form = HelperAadhaarVerificationForm()
        
        # If helper_type is maid, pre-populate the form with the Aadhaar ID
        if helper.helper_type == 'maid' and request.method == 'GET':
            form.aadhaar_id.data = helper.helper_id
        
        if form.validate_on_submit():
            aadhaar_id = form.aadhaar_id.data
            
            # Check if helper_id and input Aadhaar match for maid type
            if helper.helper_type == 'maid' and helper.helper_id != aadhaar_id:
                flash('The Aadhaar number does not match the one used during registration.', 'danger')
                return redirect(url_for('verify_helper_aadhaar', helper_id=helper_id))
            
            # Call Aadhaar API to generate OTP
            response = generate_aadhaar_otp(aadhaar_id)
            
            if response["success"]:
                # Store reference_id in session for OTP verification
                session['helper_aadhaar_reference_id'] = response["reference_id"]
                session['helper_aadhaar_id'] = aadhaar_id
                session['helper_id'] = helper_id
                
                flash(f'OTP sent to the registered mobile number. {response["message"]}', 'success')
                return redirect(url_for('verify_helper_aadhaar_otp', helper_id=helper_id))
            else:
                flash(f'Failed to send OTP: {response["message"]}', 'danger')
        
        return render_template('verify_helper.html', form=form, helper=helper)
    
    @app.route('/helpers/<helper_id>/verify-otp', methods=['GET', 'POST'])
    @login_required
    def verify_helper_aadhaar_otp(helper_id):
        # Check if we have necessary session data
        if 'helper_aadhaar_reference_id' not in session or 'helper_aadhaar_id' not in session or 'helper_id' not in session:
            flash('Please start the verification process again.', 'warning')
            return redirect(url_for('verify_helper_aadhaar', helper_id=helper_id))
        
        # Check if the helper_id in URL matches the one in session
        if helper_id != session['helper_id']:
            flash('Invalid verification request.', 'danger')
            return redirect(url_for('owner_dashboard'))
        
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first_or_404()
        
        # Check if the current user is associated with this helper
        association = OwnerHelperAssociation.query.filter_by(
            helper_profile_id=helper.id,
            owner_id=current_user.id
        ).first()
        
        if not association:
            flash('You can only verify helpers that are associated with your account.', 'danger')
            return redirect(url_for('owner_dashboard'))
        
        form = AadhaarOTPForm()
        
        if form.validate_on_submit():
            otp = form.otp.data
            reference_id = form.reference_id.data or session['helper_aadhaar_reference_id']
            aadhaar_id = session.get('helper_aadhaar_id')
            
            # Call Sandbox API to verify OTP
            response = verify_aadhaar_otp(reference_id, otp, user_id=current_user.id)
            
            if response["success"]:
                user_details = response.get("user_details", {})
                address_dict = user_details.get("address", {})
                
                # Store the transaction_id and timestamp from the response
                transaction_id = response.get("transaction_id", "")
                timestamp = response.get("timestamp")
                
                # Format the complete address as a string for storage
                full_address = user_details.get("full_address", "")
                
                # Update helper profile with Aadhaar details
                helper.verification_status = 'Verified'
                helper.aadhaar_verified = True
                helper.aadhaar_verified_at = datetime.datetime.utcnow()
                
                # Update personal details from Aadhaar
                helper.name = user_details.get("name", helper.name)
                helper.gender = user_details.get("gender", helper.gender)
                helper.aadhaar_dob = user_details.get("date_of_birth", "")
                helper.aadhaar_address = full_address
                helper.aadhaar_photo = user_details.get("photo", "")
                
                # Update detailed address components
                helper.address_house = address_dict.get("house", "")
                helper.address_landmark = address_dict.get("landmark", "")
                helper.address_vtc = address_dict.get("vtc", "")
                helper.address_district = address_dict.get("district", "")
                helper.address_state = address_dict.get("state", "")
                helper.address_pincode = str(address_dict.get("pincode", ""))
                helper.address_country = address_dict.get("country", "India")
                helper.address_post_office = address_dict.get("post_office", "")
                helper.address_street = address_dict.get("street", "")
                helper.address_subdistrict = address_dict.get("subdistrict", "")
                
                # Update original fields
                helper.state = address_dict.get("state", helper.state)
                helper.city = address_dict.get("district", address_dict.get("vtc", helper.city))
                helper.society = address_dict.get("landmark", helper.society)
                helper.street = address_dict.get("street", helper.street)
                helper.apartment_number = address_dict.get("house", helper.apartment_number)
                
                # Create a verification log entry with all the verification data
                verification_log = HelperVerificationLog(
                    helper_profile_id=helper.id,
                    verified_by=current_user.id,
                    verification_result='Valid',
                    transaction_id=transaction_id,
                    verification_data={
                        "timestamp": timestamp,
                        "transaction_id": transaction_id,
                        "data": user_details
                    }
                )
                db.session.add(verification_log)
                
                db.session.commit()
                
                # Clear session data
                session.pop('helper_aadhaar_reference_id', None)
                session.pop('helper_aadhaar_id', None)
                session.pop('helper_id', None)
                
                # Check if this was a re-verification
                is_reverification = HelperVerificationLog.query.filter_by(helper_profile_id=helper.id).count() > 1
                if is_reverification:
                    flash('Helper re-verified successfully! The profile has been updated with the latest Aadhaar information.', 'success')
                else:
                    flash('Helper verified successfully!', 'success')
                    
                return redirect(url_for('helper_detail', helper_id=helper_id))
            else:
                error_type = response.get("error_type", "UNKNOWN")
                error_msg = response.get("message", "Unknown error")
                retry_recommended = response.get("retry_recommended", False)
                should_regenerate = response.get("should_regenerate_otp", False)
                
                # Handle different error scenarios
                if should_regenerate:
                    # Clear the reference ID to force regeneration
                    session.pop('helper_aadhaar_reference_id', None)
                    
                    if error_type in ["OTP_EXPIRED", "MAX_ATTEMPTS", "INVALID_REFERENCE"]:
                        flash(f'Verification failed: {error_msg} Please request a new OTP.', 'danger')
                        return redirect(url_for('verify_helper_aadhaar', helper_id=helper_id))
                    else:
                        flash(f'Verification failed: {error_msg} Please check the Aadhaar number and try again.', 'danger')
                        return redirect(url_for('verify_helper_aadhaar', helper_id=helper_id))
                else:
                    # User can try again with the same OTP flow
                    flash(f'Failed to verify OTP: {error_msg}. Please try again.', 'danger')
        
        reference_id = session.get('helper_aadhaar_reference_id', '')
        return render_template('verify_helper_otp.html', form=form, reference_id=reference_id, helper=helper)

    @app.route('/contracts/<contract_id>')
    @login_required
    def contract_detail(contract_id):
        """View details of a contract"""
        contract = Contract.query.filter_by(contract_id=contract_id).first_or_404()
        
        # Check if the current user is the owner of this contract
        if contract.owner_id != current_user.id and current_user.role != 'admin':
            flash('You can only view contracts that you created.', 'danger')
            return redirect(url_for('owner_dashboard'))
        
        # Get helper details
        helper = HelperProfile.query.get(contract.helper_profile_id)
        
        # Get task details
        task_ids = contract.tasks.split(',') if contract.tasks else []
        tasks = TaskList.query.filter(TaskList.id.in_(task_ids)).all() if task_ids else []
        
        # Organize tasks by category
        tasks_by_category = {}
        for task in tasks:
            if task.category not in tasks_by_category:
                tasks_by_category[task.category] = []
            tasks_by_category[task.category].append(task)
        
        return render_template('contract_detail.html', 
                              contract=contract, 
                              helper=helper,
                              tasks_by_category=tasks_by_category)

    @app.route('/contracts/<contract_id>/terminate', methods=['GET', 'POST'])
    @login_required
    def terminate_contract(contract_id):
        """Terminate an existing contract"""
        contract = Contract.query.filter_by(contract_id=contract_id).first_or_404()
        
        # Check if the current user is the owner of this contract
        if contract.owner_id != current_user.id:
            flash('You can only terminate contracts that you created.', 'danger')
            return redirect(url_for('contract_detail', contract_id=contract_id))
        
        # Check if contract is already terminated
        if contract.is_terminated:
            flash('This contract has already been terminated.', 'info')
            return redirect(url_for('contract_detail', contract_id=contract_id))
        
        if request.method == 'POST':
            termination_reason = request.form.get('termination_reason', '')
            
            # Update contract
            contract.is_terminated = True
            contract.termination_reason = termination_reason
            
            try:
                db.session.commit()
                flash('Contract terminated successfully.', 'success')
                return redirect(url_for('owner_dashboard'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error terminating contract: {str(e)}")
                flash(f'An error occurred while terminating the contract: {str(e)}', 'danger')
        
        return render_template('terminate_contract.html', contract=contract)

    @app.route('/admin/aadhaar-logs')
    @login_required
    @admin_required
    def admin_aadhaar_logs():
        """Admin view to see all Aadhaar API interactions for debugging and audit purposes"""
        from sqlalchemy import desc
        from flask import request
        
        # Get query parameters for filtering
        request_type = request.args.get('type')
        status = request.args.get('status')
        aadhaar_id = request.args.get('aadhaar_id')
        reference_id = request.args.get('reference_id')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Build query
        query = AadhaarAPILog.query
        
        # Apply filters
        if request_type:
            query = query.filter(AadhaarAPILog.request_type == request_type)
        
        if status:
            success = (status == 'success')
            query = query.filter(AadhaarAPILog.success == success)
            
        if aadhaar_id:
            query = query.filter(AadhaarAPILog.aadhaar_id == aadhaar_id)
            
        if reference_id:
            query = query.filter(AadhaarAPILog.reference_id == reference_id)
            
        if from_date:
            try:
                from_date_obj = datetime.datetime.strptime(from_date, '%Y-%m-%d')
                query = query.filter(AadhaarAPILog.created_at >= from_date_obj)
            except ValueError:
                pass
                
        if to_date:
            try:
                to_date_obj = datetime.datetime.strptime(to_date, '%Y-%m-%d')
                to_date_obj = to_date_obj + datetime.timedelta(days=1)  # Include the entire day
                query = query.filter(AadhaarAPILog.created_at <= to_date_obj)
            except ValueError:
                pass
        
        # Order by most recent first
        query = query.order_by(desc(AadhaarAPILog.created_at))
        
        # Paginate results
        logs_pagination = query.paginate(page=page, per_page=per_page)
        
        # Get statistics
        total_logs = AadhaarAPILog.query.count()
        success_logs = AadhaarAPILog.query.filter_by(success=True).count()
        failure_logs = total_logs - success_logs
        success_rate = (success_logs / total_logs * 100) if total_logs > 0 else 0
        
        # Count by request type
        generate_otp_count = AadhaarAPILog.query.filter_by(request_type='generate_otp').count()
        verify_otp_count = AadhaarAPILog.query.filter_by(request_type='verify_otp').count()
        token_count = AadhaarAPILog.query.filter_by(request_type='token').count()
        
        return render_template(
            'admin/aadhaar_logs.html',
            logs=logs_pagination.items,
            pagination=logs_pagination,
            total_logs=total_logs,
            success_logs=success_logs,
            failure_logs=failure_logs,
            success_rate=success_rate,
            generate_otp_count=generate_otp_count,
            verify_otp_count=verify_otp_count,
            token_count=token_count,
            request_type=request_type,
            status=status,
            aadhaar_id=aadhaar_id,
            reference_id=reference_id,
            from_date=from_date,
            to_date=to_date
        )
    
    @app.route('/admin/aadhaar-logs/<int:log_id>')
    @login_required
    @admin_required
    def aadhaar_log_detail(log_id):
        """View detailed information about a specific Aadhaar API log entry"""
        log = AadhaarAPILog.query.get_or_404(log_id)
        
        # Get user details if available
        user = None
        if log.user_id:
            user = User.query.get(log.user_id)
            
        # Get related logs (same session_id)
        related_logs = []
        if log.session_id:
            related_logs = AadhaarAPILog.query.filter(
                AadhaarAPILog.session_id == log.session_id,
                AadhaarAPILog.id != log.id
            ).order_by(AadhaarAPILog.created_at).all()
        
        return render_template(
            'admin/aadhaar_log_detail.html',
            log=log,
            user=user,
            related_logs=related_logs
        )

    @app.route('/contracts/<contract_id>/review', methods=['GET', 'POST'])
    @login_required
    def submit_review(contract_id):
        """Submit a review for a contract"""
        # Get the contract and verify ownership
        contract = Contract.query.filter_by(contract_id=contract_id).first_or_404()
        
        # Check if the current user is the owner of this contract
        if contract.owner_id != current_user.id:
            flash('You can only review contracts that you created.', 'danger')
            return redirect(url_for('owner_dashboard'))
        
        # Check if contract is active
        if contract.is_terminated:
            flash('You cannot review a terminated contract.', 'warning')
            return redirect(url_for('contract_detail', contract_id=contract_id))
        
        # Get the helper profile
        helper = HelperProfile.query.get(contract.helper_profile_id)
        
        # Check if the user has already submitted 4 reviews this month for this contract
        current_month = datetime.date.today().replace(day=1)
        next_month = (current_month.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        
        reviews_this_month = Review.query.filter(
            Review.owner_id == current_user.id,
            Review.contract_id == contract.id,
            Review.review_date >= current_month,
            Review.review_date < next_month
        ).count()
        
        if reviews_this_month >= 4:
            flash('You have already submitted the maximum of 4 reviews for this helper this month.', 'warning')
            return redirect(url_for('contract_detail', contract_id=contract_id))
            
        # Check if a review has already been submitted today for this helper
        today = datetime.date.today()
        existing_review_today = Review.query.filter(
            Review.owner_id == current_user.id,
            Review.helper_profile_id == helper.id,
            Review.review_date == today
        ).first()
        
        if existing_review_today:
            flash('You have already provided feedback for this helper today. Please submit your next review tomorrow to share updated feedback.', 'info')
            return redirect(url_for('contract_detail', contract_id=contract_id))
        
        # Get tasks for this contract
        task_ids = contract.tasks.split(',') if contract.tasks else []
        tasks = TaskList.query.filter(TaskList.id.in_(task_ids)).all() if task_ids else []
        
        # Create form
        form = ReviewForm()
        form.helper_id.data = helper.helper_id
        form.contract_id.data = contract.contract_id
        
        # Process form submission
        if form.validate_on_submit():
            try:
                # Generate unique review ID
                review_id = f"REV-{datetime.datetime.now().strftime('%Y%m%d')}-{helper.helper_id[-4:]}-{current_user.id}"
                
                # Create review
                review = Review(
                    review_id=review_id,
                    helper_profile_id=helper.id,
                    owner_id=current_user.id,
                    contract_id=contract.id,
                    punctuality=float(form.punctuality.data),
                    attitude=float(form.attitude.data),
                    hygiene=float(form.hygiene.data),
                    reliability=float(form.reliability.data),
                    communication=float(form.communication.data),  # Use the value from the form
                    tasks_average=3.0,  # Default value, will be updated after we process task ratings
                    additional_feedback=form.additional_feedback.data,
                    comments=form.additional_feedback.data,  # Duplicate to maintain compatibility
                    review_date=datetime.date.today()
                )
                
                db.session.add(review)
                db.session.flush()  # To get the review ID for task ratings
                
                # Add task ratings and calculate tasks_average
                task_ratings = []
                task_rating_sum = 0
                
                for task in tasks:
                    # Get the rating from the form
                    task_field_name = f'task_{task.id}'
                    if task_field_name in request.form:
                        rating = int(request.form[task_field_name])
                        task_rating_sum += rating
                        
                        # Create task rating
                        task_rating = ReviewTaskRating(
                            review_id=review.id,
                            task_id=task.id,
                            rating=rating
                        )
                        db.session.add(task_rating)
                        task_ratings.append(task_rating)
                
                # Update tasks_average if we have task ratings
                if task_ratings:
                    review.tasks_average = task_rating_sum / len(task_ratings)
                
                db.session.commit()
                flash('Review submitted successfully!', 'success')
                return redirect(url_for('contract_detail', contract_id=contract_id))
                
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error submitting review: {str(e)}")
                flash(f'An error occurred while submitting the review: {str(e)}', 'danger')
        
        return render_template('review.html', 
                              form=form, 
                              helper=helper, 
                              contract=contract,
                              tasks=tasks)
    
    @app.route('/helper/<helper_id>/reviews')
    @login_required
    def helper_reviews(helper_id):
        """View all reviews for a helper"""
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first_or_404()
        
        # Check if the current user is associated with this helper
        association = OwnerHelperAssociation.query.filter_by(
            helper_profile_id=helper.id,
            owner_id=current_user.id
        ).first()
        
        if not association and current_user.role != 'admin':
            flash('You can only view reviews for helpers that are associated with your account.', 'danger')
            return redirect(url_for('owner_dashboard'))
        
        # Get all reviews for this helper
        reviews = Review.query.filter_by(helper_profile_id=helper.id).order_by(Review.timestamp.desc()).all()
        
        # Calculate average ratings
        avg_ratings = {
            'punctuality': 0,
            'attitude': 0,
            'hygiene': 0,
            'reliability': 0,
            'communication': 0,
            'overall': 0
        }
        
        if reviews:
            avg_ratings['punctuality'] = sum(r.punctuality for r in reviews) / len(reviews)
            avg_ratings['attitude'] = sum(r.attitude for r in reviews) / len(reviews)
            avg_ratings['hygiene'] = sum(r.hygiene for r in reviews) / len(reviews)
            avg_ratings['reliability'] = sum(r.reliability for r in reviews) / len(reviews)
            avg_ratings['communication'] = sum(r.communication for r in reviews) / len(reviews)
            avg_ratings['overall'] = sum(r.overall_rating for r in reviews) / len(reviews)
        
        return render_template('helper_reviews.html', 
                              helper=helper, 
                              reviews=reviews,
                              avg_ratings=avg_ratings)
