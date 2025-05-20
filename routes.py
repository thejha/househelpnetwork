import os
import uuid
import datetime
from functools import wraps
from flask import render_template, url_for, flash, redirect, request, jsonify, session, send_from_directory
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from extensions import db, bcrypt
from models import User, OwnerProfile, OwnerDocument, HelperProfile, HelperDocument, TaskList, Contract, Review, IncidentReport, OwnerToOwnerConnect, PincodeMapping, Language
from forms import (RegistrationForm, LoginForm, OwnerProfileForm, HelperProfileForm, ContractForm, ReviewForm, 
                   IncidentReportForm, OwnerToOwnerConnectForm, SearchForm, TaskListForm,
                   AadhaarVerificationForm, AadhaarOTPVerificationForm, AadhaarOTPForm, AadhaarRegistrationForm)
from utils import save_file, get_unique_id, send_notification
from aadhaar_api import generate_aadhaar_otp, verify_aadhaar_otp

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
            
        form = AadhaarVerificationForm()
        if form.validate_on_submit():
            aadhaar_id = form.aadhaar_id.data
            
            # Call Aadhaar API to generate OTP
            response = generate_aadhaar_otp(aadhaar_id)
            
            if response["success"]:
                # Store reference_id in session for OTP verification
                session['aadhaar_reference_id'] = response["reference_id"]
                session['aadhaar_id'] = aadhaar_id
                session['registration_flow'] = True  # Mark that we're in registration flow
                
                flash(f'OTP sent to your registered mobile number. {response["message"]}', 'success')
                return redirect(url_for('aadhaar_register_otp'))
            else:
                flash(f'Failed to send OTP: {response["message"]}', 'danger')
        
        return render_template('register_aadhaar.html', form=form)
    
    @app.route('/register-aadhaar-otp', methods=['GET', 'POST'])
    def aadhaar_register_otp():
        """Step 2: User enters OTP received for Aadhaar verification"""
        # Check if we have a reference_id in the session
        if 'aadhaar_reference_id' not in session or 'aadhaar_id' not in session or 'registration_flow' not in session:
            flash('Please start the registration process again.', 'warning')
            return redirect(url_for('register_with_aadhaar'))
        
        form = AadhaarOTPForm()
        
        if form.validate_on_submit():
            otp = form.otp.data
            reference_id = form.reference_id.data or session['aadhaar_reference_id']
            
            # Call Sandbox API to verify OTP
            response = verify_aadhaar_otp(reference_id, otp)
            
            if response["success"]:
                # Store Aadhaar data in session for registration completion
                session['aadhaar_data'] = response.get("user_details", {})
                
                flash('Aadhaar verification successful! Please complete your registration.', 'success')
                return redirect(url_for('complete_aadhaar_registration'))
            else:
                flash(f'Failed to verify OTP: {response["message"]}', 'danger')
        
        reference_id = session.get('aadhaar_reference_id', '')
        return render_template('verify_aadhaar_registration.html', form=form, reference_id=reference_id)
        
    @app.route('/complete-registration', methods=['GET', 'POST'])
    def complete_aadhaar_registration():
        """Step 3: After successful Aadhaar verification, user completes registration with email and password"""
        # Check if we have Aadhaar data in the session
        if 'aadhaar_data' not in session or 'aadhaar_id' not in session or 'registration_flow' not in session:
            flash('Please start the registration process again.', 'warning')
            return redirect(url_for('register_with_aadhaar'))
        
        aadhaar_data = session.get('aadhaar_data')
        aadhaar_id = session.get('aadhaar_id')
        
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
                db.session.commit()
                
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
                flash(f'An error occurred while creating your account: {str(e)}. Please try again.', 'danger')
        
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
    @app.route('/helpers/create', methods=['GET', 'POST'])
    @login_required
    def create_helper():
        form = HelperProfileForm()
        
        # Populate languages from the database
        languages = Language.query.all()
        form.languages.choices = [(str(lang.id), lang.name) for lang in languages]
        
        if form.validate_on_submit():
            # Set helper_id based on helper type
            helper_id = None
            if form.helper_type.data == 'maid':
                helper_id = form.aadhar_id.data
                # Validate Aadhar ID format
                if not helper_id or len(helper_id) != 12 or not helper_id.isdigit():
                    flash('Please enter a valid 12-digit Aadhar ID', 'danger')
                    return render_template('create_helper.html', form=form)
            else:  # Driver
                helper_id = form.driving_license_id.data
                if not helper_id:
                    flash('Please enter a valid Driving License ID', 'danger')
                    return render_template('create_helper.html', form=form)
            
            # Check if helper already exists
            existing_helper = HelperProfile.query.filter_by(helper_id=helper_id).first()
            if existing_helper:
                flash('A helper with this ID already exists!', 'danger')
                return redirect(url_for('create_helper'))
            
            # Save photo if provided
            photo_url = None
            if form.photo.data and form.photo.data.filename:
                photo_url = save_file(form.photo.data, 'helper_photos')
                if not photo_url:
                    flash('Failed to upload photo. Please try again.', 'danger')
                    return render_template('create_helper.html', form=form)
            
            # Get the selected languages
            language_ids = form.languages.data or []  # Handle case when no languages are selected
            language_names = []
            for lang_id in language_ids:
                language_obj = Language.query.get(int(lang_id))
                if language_obj:
                    language_names.append(language_obj.name)
            language_str = ", ".join(language_names)
            
            # Create helper profile with minimal information
            helper = HelperProfile(
                name=form.name.data,
                helper_id=helper_id,
                helper_type=form.helper_type.data,
                phone_number=form.phone_number.data,
                photo_url=photo_url,
                languages=language_str,
                created_by=current_user.id,
                verification_status='Unverified'
            )
            
            db.session.add(helper)
            db.session.commit()
            
            flash('Helper profile created successfully! You can now verify their Aadhaar details.', 'success')
            # Redirect to a helper verification page in the future
            return redirect(url_for('helper_detail', helper_id=helper.helper_id))
        
        return render_template('create_helper.html', form=form)
    
    @app.route('/helpers/<helper_id>')
    @login_required
    def helper_detail(helper_id):
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first_or_404()
        
        # Get documents, contracts, reviews and incident reports
        documents = HelperDocument.query.filter_by(helper_profile_id=helper.id).all()
        contracts = Contract.query.filter_by(helper_profile_id=helper.id).all()
        reviews = Review.query.filter_by(helper_profile_id=helper.id).all()
        incidents = IncidentReport.query.filter_by(helper_profile_id=helper.id).all()
        
        # Calculate average ratings if reviews exist
        avg_ratings = {}
        if reviews:
            avg_ratings = {
                'tasks_average': sum([r.tasks_average for r in reviews]) / len(reviews),
                'punctuality': sum([r.punctuality for r in reviews]) / len(reviews),
                'attitude': sum([r.attitude for r in reviews]) / len(reviews),
                'hygiene': sum([r.hygiene for r in reviews]) / len(reviews),
                'communication': sum([r.communication for r in reviews]) / len(reviews),
                'reliability': sum([r.reliability for r in reviews]) / len(reviews),
                'overall': sum([
                    (r.tasks_average + r.punctuality + r.attitude + r.hygiene + r.communication + r.reliability) / 6
                    for r in reviews
                ]) / len(reviews)
            }
        
        return render_template('helper_detail.html', 
                              helper=helper, 
                              documents=documents,
                              contracts=contracts, 
                              reviews=reviews, 
                              incidents=incidents,
                              avg_ratings=avg_ratings)
    
    @app.route('/contract/create/<helper_id>', methods=['GET', 'POST'])
    @login_required
    def create_contract(helper_id):
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first_or_404()
        
        form = ContractForm()
        
        # Add task choices to form
        tasks = TaskList.query.all()
        form.tasks.choices = [(str(task.id), task.name) for task in tasks]
        
        if form.validate_on_submit():
            # Create a unique contract ID
            contract_id = get_unique_id('contract')
            
            # Parse tasks data
            tasks_str = ','.join(request.form.getlist('tasks'))
            
            # Create contract
            contract = Contract(
                contract_id=contract_id,
                helper_profile_id=helper.id,
                owner_id=current_user.id,
                tasks=tasks_str,
                start_date=form.start_date.data,
                end_date=form.end_date.data if form.end_date.data else None,
                monthly_salary=form.monthly_salary.data
            )
            
            db.session.add(contract)
            db.session.commit()
            
            flash('Contract created successfully!', 'success')
            return redirect(url_for('helper_detail', helper_id=helper.helper_id))
        
        form.helper_id.data = helper_id
        
        return render_template('contract.html', form=form, helper=helper)
    
    @app.route('/review/create/<helper_id>', methods=['GET', 'POST'])
    @login_required
    def create_review(helper_id):
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first_or_404()
        
        form = ReviewForm()
        
        if form.validate_on_submit():
            # Create a unique review ID
            review_id = get_unique_id('review')
            
            # Create review
            review = Review(
                review_id=review_id,
                helper_profile_id=helper.id,
                owner_id=current_user.id,
                tasks_average=float(form.tasks_average.data),
                punctuality=float(form.punctuality.data),
                attitude=float(form.attitude.data),
                hygiene=float(form.hygiene.data),
                communication=float(form.communication.data),
                reliability=float(form.reliability.data),
                comments=form.comments.data
            )
            
            db.session.add(review)
            db.session.commit()
            
            flash('Review submitted successfully!', 'success')
            return redirect(url_for('helper_detail', helper_id=helper.helper_id))
        
        form.helper_id.data = helper_id
        
        return render_template('review.html', form=form, helper=helper)
    
    @app.route('/incident/report/<helper_id>', methods=['GET', 'POST'])
    @login_required
    def report_incident(helper_id):
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first_or_404()
        
        form = IncidentReportForm()
        
        if form.validate_on_submit():
            # Create a unique report ID
            report_id = get_unique_id('incident')
            
            # Create incident report
            incident = IncidentReport(
                report_id=report_id,
                helper_profile_id=helper.id,
                owner_id=current_user.id,
                date=form.date.data,
                description=form.description.data,
                fir_number=form.fir_number.data if form.fir_number.data else None
            )
            
            db.session.add(incident)
            db.session.commit()
            
            flash('Incident reported successfully!', 'success')
            return redirect(url_for('helper_detail', helper_id=helper.helper_id))
        
        form.helper_id.data = helper_id
        
        return render_template('incident.html', form=form, helper=helper)
    
    @app.route('/connect/<helper_id>', methods=['GET', 'POST'])
    @login_required
    def owner_connect(helper_id):
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first_or_404()
        
        form = OwnerToOwnerConnectForm()
        
        if form.validate_on_submit():
            # Create a unique form ID
            form_id = get_unique_id('connect')
            
            # Create owner-to-owner connect request
            connect = OwnerToOwnerConnect(
                form_id=form_id,
                helper_profile_id=helper.id,
                from_owner_id=current_user.id,
                to_owner_contact=form.to_owner_contact.data,
                message=form.message.data,
                stored_locally=form.stored_locally.data
            )
            
            db.session.add(connect)
            db.session.commit()
            
            # Send notification (mock functionality for now)
            send_notification(
                to=form.to_owner_contact.data,
                subject='HouseHelpNetwork: New Connect Request',
                message=f'{current_user.name} wants to connect regarding a helper'
            )
            
            flash('Connection request sent successfully!', 'success')
            return redirect(url_for('helper_detail', helper_id=helper.helper_id))
        
        form.helper_id.data = helper_id
        
        return render_template('owner_connect.html', form=form, helper=helper)
    
    @app.route('/search', methods=['GET', 'POST'])
    @login_required
    def search():
        form = SearchForm()
        helper = None
        
        if form.validate_on_submit() or request.args.get('search_value'):
            search_type = form.search_type.data if form.validate_on_submit() else request.args.get('search_type')
            search_value = form.search_value.data if form.validate_on_submit() else request.args.get('search_value')
            
            if search_type == 'gov_id':
                helper = HelperProfile.query.filter_by(gov_id=search_value).first()
            elif search_type == 'phone_number':
                helper = HelperProfile.query.filter_by(phone_number=search_value).first()
            
            if helper:
                return redirect(url_for('helper_detail', helper_id=helper.helper_id))
            else:
                flash('No helper found with the provided information.', 'info')
        
        return render_template('search.html', form=form, helper=helper)
    
    # Admin routes
    @app.route('/admin/dashboard')
    @login_required
    @admin_required
    def admin_dashboard():
        # Get statistics for the admin dashboard
        total_helpers = HelperProfile.query.count()
        total_owners = User.query.filter_by(role='owner').count()
        pending_verifications = OwnerProfile.query.filter_by(verification_status='Pending').count()
        aadhaar_verified_users = OwnerProfile.query.filter_by(aadhaar_verified=True).count()
        manual_verified_users = OwnerProfile.query.filter(
            OwnerProfile.verification_status == 'Verified',
            OwnerProfile.aadhaar_verified == False
        ).count()
        
        recent_helpers = HelperProfile.query.order_by(HelperProfile.created_at.desc()).limit(5).all()
        recent_reviews = Review.query.order_by(Review.timestamp.desc()).limit(5).all()
        recent_incidents = IncidentReport.query.order_by(IncidentReport.timestamp.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                              total_helpers=total_helpers,
                              total_owners=total_owners,
                              pending_verifications=pending_verifications,
                              aadhaar_verified_users=aadhaar_verified_users,
                              manual_verified_users=manual_verified_users,
                              recent_helpers=recent_helpers,
                              recent_reviews=recent_reviews,
                              recent_incidents=recent_incidents)
    
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
        # Get helpers created by this user
        helpers = HelperProfile.query.filter_by(created_by=current_user.id).all()
        helpers_count = len(helpers)
        
        # Get contracts for this user
        contracts = Contract.query.filter_by(owner_id=current_user.id).all()
        
        return render_template('owner_dashboard.html', 
                              helpers=helpers,
                              helpers_count=helpers_count,
                              contracts=contracts)

    @app.route('/helpers/<helper_id>/verify', methods=['GET', 'POST'])
    @login_required
    def verify_helper_aadhaar(helper_id):
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first_or_404()
        
        # Check if the current user created this helper profile
        if helper.created_by != current_user.id:
            flash('You can only verify helpers that you have added.', 'danger')
            return redirect(url_for('owner_dashboard'))
        
        # Check if helper is already verified
        if helper.verification_status == 'Verified':
            flash('This helper is already verified.', 'info')
            return redirect(url_for('helper_detail', helper_id=helper_id))
        
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
        
        form = AadhaarOTPForm()
        
        if form.validate_on_submit():
            otp = form.otp.data
            reference_id = form.reference_id.data or session['helper_aadhaar_reference_id']
            
            # Call Sandbox API to verify OTP
            response = verify_aadhaar_otp(reference_id, otp)
            
            if response["success"]:
                user_details = response.get("user_details", {})
                address_dict = user_details.get("address", {})
                
                # Update helper profile with Aadhaar details
                helper.verification_status = 'Verified'
                
                # Update other fields with Aadhaar data
                if user_details.get("name"):
                    helper.name = user_details.get("name")
                if user_details.get("gender"):
                    helper.gender = user_details.get("gender")
                if address_dict.get("state"):
                    helper.state = address_dict.get("state")
                
                db.session.commit()
                
                # Clear session data
                session.pop('helper_aadhaar_reference_id', None)
                session.pop('helper_aadhaar_id', None)
                session.pop('helper_id', None)
                
                flash('Helper verified successfully!', 'success')
                return redirect(url_for('helper_detail', helper_id=helper_id))
            else:
                flash(f'Failed to verify OTP: {response["message"]}', 'danger')
        
        reference_id = session.get('helper_aadhaar_reference_id', '')
        return render_template('verify_helper_otp.html', form=form, reference_id=reference_id, helper=helper)
