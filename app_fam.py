# Import libraries
from flask import Flask, g, render_template, request, session, redirect, url_for
from flask_httpauth import HTTPBasicAuth  # Used by API
from flask_pymongo import PyMongo # Needed for all MongoDB operations except deleting files
from datetime import timedelta, datetime
import re, os, sys, platform
from mgt.config import *
from mgt.passmanage import *
from mgt.emailalert import *

# Configuration files
config_folder = "config"
config_name = "settings"
config_file = os.path.join(config_folder, config_name + ".cfg")
users_name = "users"
users_file = os.path.join(config_folder, users_name + ".cfg")
orgs_name = "orgs"
orgs_file = os.path.join(config_folder, orgs_name + ".cfg")
log_folder = "logs"
log_name = "app_fam"
log_file = os.path.join(log_folder, log_name + ".log")

# Read configuration
configuration = dict({})
def config_load():
    global configuration
    configuration = read_cfg(config_file)
config_load()

# Users tracking
users_exist = False # Assumes no users exist

# Read users
users = list([])
def users_load():
    global users
    users = read_users(users_file)
users_load()

# Read organizations
orgs = list([])
def orgs_load():
    global orgs
    orgs = read_orgs(orgs_file)
orgs_load()

# Create log folder if it does not already exist
if not os.path.exists(log_folder):
    os.mkdir(log_folder)

# Setup logging
logger = setup_log(log_file, configuration['logfilesettings'][0],
                   configuration['logfilesettings'][1], configuration['logfilesettings'][2])

# Starting up
logger.info('****====****====****====****====****====**** App Starting ****====****====****====****====****====****')

# Config values write out to log
if configuration['error']:
    print("Unable to set config variables")
    logger.info('Problem reading ' + config_file + ', check your configuration file!')
else:  # Config settings out to the log
    print("Configuration files read")
    logger.info('Log file settings: ')
    logger.info('            Bytes: ' + str(configuration['logfilesettings'][0]))
    logger.info('          Backups: ' + str(configuration['logfilesettings'][1]))
    # Add logging level display to log
    loglevel = "Not set"
    if (configuration['logfilesettings'][2] == 10):
        loglevel = "DEBUG"
    elif (configuration['logfilesettings'][2] == 20):
        loglevel = "INFO"
    elif (configuration['logfilesettings'][2] == 30):
        loglevel = "WARNING"
    elif (configuration['logfilesettings'][2] == 40):
        loglevel = "ERROR"
    elif (configuration['logfilesettings'][2] == 50):
        loglevel = "CRITICAL"
    logger.info('            Level: ' + str(configuration['logfilesettings'][2]) + " (" + loglevel + ")")
    logger.info('  Email is set to: ' + configuration['email'])
    logger.info('   SMTP is set to: ' + configuration['smtp'])
    logger.info('   Team is set to: ' + configuration['team'])
    logger.info('   Logo is set to: ' + configuration['logo'])
    logger.info(' Logo size is set: ' + str(configuration['logosize'][0]) + ', ' + str(configuration['logosize'][1]))
    logger.info('   DB collections: ')
    for collection in configuration['dbcoll']:
        logger.info('                   ' + collection)

# Orgs write out to log
if len(orgs) > 1:
    print ("Organization records read")
    logger.info('       Orgs found: ')
    for org_record in orgs:
        # Write organization to the log
        logger.info('                   ' + org_record['name'])
else:
    configuration['error'] = True
    print ("Unable to find any organizations")
    logger.info('Problem reading ' + orgs_file + ', check your organizations file!')

# Users write out to log
if len(users) >= 1:
    print ("User records read")
    logger.info('      Users found: ')
    for user_record in users:
        # Find the organization name
        org_name = "None"
        for user_org in orgs:
            if user_org['_index'] == user_record['org']:
                org_name = user_org['name']
        # Write user and their organization to the log
        logger.info('                   ' + user_record['namelast'] + ', ' + user_record['namefirst'] + ' (' + user_record['login'] + ') - ' + org_name)
else:
    users_exist = False
    print ("Unable to find any users")
    logger.info('Problem reading ' + users_file + ', check your users file!')

# Application create
fam_app = Flask(__name__)

# Add secret key since session requires it
fam_app.secret_key = 'another secret thing here hah'
logger.debug('DEBUG: Flask secret set')
# Set the length of time someone stays logged in
fam_app.permanent_session_lifetime = timedelta(hours=1)
logger.debug('DEBUG: User session set to 1 hour')

# Authorization used for API
auth = HTTPBasicAuth()
logger.debug('DEBUG: HTTP authorization created for credential handling')

# File upload settings
fam_app.config['MAX_CONTENT_PATH'] = 50000000 # 50000000 equals 50MB

db_connection_error = True # Default to an error

# Create connection to database
db_inst = PyMongo(fam_app, uri=configuration['dbconn'])

# Test and log connection
def db_test():
    global db_connection_error
    # MongoDB object, db_conn_type of mongodb for non-Atlas hosted
    if configuration['error'] == False:
        # Remove password for the log
        db_conn_host, db_conn_type, db_conn_remaining = str(configuration['dbconn']).split(":")
        db_conn_end = str(db_conn_remaining).split("@")[1]
        db_conn_log = db_conn_host + ":" + db_conn_type + ':[password]@' + db_conn_end
        try:
            # Test connection, will bomb if above connection did not work
            test_query = int(db_inst.db["not_real_collection"].count_documents({'not_real_record': "nothing_here"}))
            db_connection_error = False # Database connected if made it here
            logger.info('  Connected to DB: ' + db_conn_log)
        except:
            db_connection_error = True # Flag an error if we cannot connect to the database
            print("Database failed to connect!")
            logger.info('   Failed conn DB: ' + db_conn_log)
    else:
        # Configuration error, do not attempt to connect to database
        db_connection_error = True
        print("Database not connected because of problem opening " + config_file + ".")
        logger.info('Database not connected because of problem opening ' + config_file)
db_test()

# Login
def login(login_name, login_password):  # Password ignored
    logger.debug('DEBUG: Login function started')
    if "None" not in str(login_name):
        # Setup user session
        user_session = {"_index": 0, "login": login_name}
        logger.debug('DEBUG: Session set to login ' + login_name)
    else:
        # Setup guest session
        user_session = {"_index": 999999999999, "login": "guest"}
        logger.debug('DEBUG: Session set to login guest')
    # Update session with user info
    session['user_id'] = int(user_session['_index'])
    session['login'] = login_name
    # Set global variables for user
    g.user = user_session
    logger.debug('DEBUG: Global user variable created')
    # Allow user in, but assume they are guest if None is passed (not secure, just for testing)
    return True

# Setup user session from browser or API
def session_setup():
    logger.debug('DEBUG: Session setup function started')
    # Set the session to be saved by client in browser or API client
    session.permanent = True
    logger.debug('DEBUG: Session set to permanent to be saved by client browser')
    # Reload all configuration files to capture any changes made
    config_load()
    logger.debug('DEBUG: Configuration load function started')
    g.root = configuration['root']
    g.team = configuration['team']
    g.email = configuration['email']
    logger.debug('DEBUG: Global shared variables created')
    # Session setup
    return bool(configuration['error'])  # True if problem with configuration, false otherwise

# Endpoint pre-processing
@fam_app.before_request
def before_request():
    # Setup the session for the user
    failure = session_setup()
    if failure:  # Returns true if there was a problem
        logger.debug('DEBUG: Server error of some kind')
        return render_template('error.html')

# Endpoint root
@fam_app.route('/')
@auth.login_required
def landingpage():
    logger.info(request.remote_addr + ' ==> Landing page (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
    if int(g.org['_index']) == 999999999999: # User is not assigned to an organization
        return render_template('landing.html', pagetitle="You must be assigned to an organization to have access", notnewinstall=users_exist)
    else:
        return render_template('landing.html', pagetitle="Collections", config_data=configuration)

# Collections page listing records
@fam_app.route('/colls')
@auth.login_required
def collspage():
    # Page records to show parameters
    page_start = request.args.get('start', default = 1, type = int)
    if (page_start < 1):
        page_start = 1
    page_records = request.args.get('records', default = g.user['pagerecords'], type = int)
    page_total = 0
    page_dims = dict({'start': page_start, 'records': page_records, 'total': page_total})
    # End-user filter selections
    filter_number = request.args.get('num', default = 999999999999, type = int)
    filter_name = request.args.get('name', default = "", type = str)
    filter_owner = request.args.get('owner', default = 999999999999, type = int)
    filter_org = request.args.get('org', default = 999999999999, type = int)
    # Build filter
    query_filter = dict({})
    if (filter_number != 999999999999):
        query_filter['record_number'] = filter_number
    if (filter_name != ""):
        query_filter['record_name'] = filter_name
    if (filter_owner != 999999999999):
        query_filter['record_user'] = filter_owner
    if (filter_org != 999999999999):
        query_filter['record_org'] = filter_org
    # Page
    page_title = "Records"
    if users_exist == False: # No users exist, will need to prompt to create one
        logger.info(request.remote_addr + ' ==> No users exist yet, prompting to create admin account )')
        return redirect(url_for('loginnewpage'))
    if int(session['user_id']) == 999999999999: # User is a guest
        logger.info(request.remote_addr + ' ==> Collections listing page access error (' + str(g.user['login']) + ')')
        # Put a delay in for denial-of service attacks
        # time.sleep(5)
        return redirect(url_for('loginpage', requestingurl=request.full_path))
    if g.user['admin'] == False and int(g.org['_index']) == 999999999999: # User is not admin or in an org
        logger.info(request.remote_addr + ' ==> Collections page org error for collection ' + filter_name + '(' + str(g.user['login']) + ')')
        return render_template('collections.html', pagetitle="Please have your admin assign you to your organization", org_records=orgs, user_records=users, pagedims=page_dims)
    else: # User is valid and in an organization
        # Collection name argument passed
        data_coll = request.args.get('data', default = "", type = str)
        if (data_coll == ""):
            logger.info(request.remote_addr + ' ==> Collection name not passed (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
            page_title = "You must pass a collection name"
            # Show page error
            return render_template('collections.html', pagetitle=page_title, pagedims=page_dims)
        page_title = "Records for collection: " + str(data_coll)
        # Setup sort
        record_sort = tuple([('record_name', 1)])
        # Create list to collect records
        record_list = []
        # Read all records
        logger.info(request.remote_addr + ' ==> Record listing page (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
        try: # Get the list of records
            if int(filter_number) == 999999999999: # Find all records visible to this user
                if (g.user['admin'] == True): # User is admin, get all records
                    query_run = query_filter
                else: # User is org admin or user, in the page non-org admins will not see links for records they do not own
                    # Override user and organization filter to just the user
                    query_filter['record_org'] = int(g.org['_index'])
                    query_run = query_filter
                # Record count
                page_total = int(db_inst.db[data_coll].count_documents(query_run))
                if (page_start >= page_total):
                    page_start = page_total
                # Query
                record_list = list(db_inst.db[data_coll].find(query_run).sort(record_sort).skip(page_start-1).limit(page_records))
            else: # Find just the record requested
                record_number = filter_number
                page_total = 1
                page_start = 1
                page_title = "Record filtered"
                if (g.user['admin'] == True): # User is admin, get the record no matter who it is tied to
                    record_list.append(dict(db_inst.db[data_coll].find_one({'record_number': int(record_number)})))
                elif (g.user['orgadmin'] == True): # User is org admin, get the record if tied to the user's org
                    record_list.append(dict(db_inst.db[data_coll].find_one({'record_number': int(record_number), 'record_org': int(g.org['_index'])})))
                else: # Get record if it is owned by the user
                    record_list.append(dict(db_inst.db[data_coll].find_one({'record_number': int(record_number), 'record_user': int(g.user['_index'])})))
        except: # Error if failed
            logger.info(request.remote_addr + ' ==> Database error reading records (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
            page_title = "No access to record or it does not exist"
        # Update total number of records and start based on the query
        page_dims['total'] = page_total
        page_dims['start'] = page_start
        if len(record_list) > 0: # Render page with records
            return render_template('collections.html', pagetitle=page_title, recordlist=record_list, org_records=orgs, user_records=users, pagedims=page_dims)
        else: # Render page without records
            page_title = "No Records"
            return render_template('collections.html', pagetitle=page_title, org_records=orgs, user_records=users, pagedims=page_dims)
   
# Collection page listing fields from one record
@fam_app.route('/coll', methods=['GET', 'POST'])
@auth.login_required
def collpage():
    # End-user filter selections
    filter_number = request.args.get('num', default = 999999999999, type = int)
    # Build filter
    query_filter = dict({})
    if (filter_number != 999999999999):
        query_filter['record_number'] = filter_number
    # Page
    page_title = "Record"
    if users_exist == False: # No users exist, will need to prompt to create one
        logger.info(request.remote_addr + ' ==> No users exist yet, prompting to create admin account )')
        return redirect(url_for('loginnewpage'))
    if int(session['user_id']) == 999999999999: # User is a guest
        logger.info(request.remote_addr + ' ==> Collection page access error for ' + filter_number + ' (' + str(g.user['login']) + ')')
        # Prompt to login
        return redirect(url_for('loginpage', requestingurl=request.full_path))
    if g.user['admin'] == False and int(g.org['_index']) == 999999999999: # User is not admin or in an org
        logger.info(request.remote_addr + ' ==> Collection page access error for ' + filter_number + ' (' + str(g.user['login']) + ')')
        page_title = "You must be in an organization to see records"
        # Show page error
        return render_template('collection.html', pagetitle=page_title)
    else:
        # Collection name argument passed
        data_coll = request.args.get('data', default = "", type = str)
        if (data_coll == ""):
            logger.info(request.remote_addr + ' ==> Collection name not passed (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
            page_title = "You must pass a collection name"
            # Show page error
            return render_template('collection.html', pagetitle=page_title)
        if request.method == 'POST':
            # Current time
            nowIs = datetime.now().strftime("_%Y%m%d-%H%M%S%f")
            # Process new record after form is filled out and a POST request happens
            record_new = True
            record_user = 999999999999
            record_org = 999999999999
            try: # Existing record
                record_number = int(request.form['record_number'])
                record_new = False
                record_user = int(request.form['record_user'])
                record_org = int(request.form['record_org'])
            except: # New record
                record_number = int(datetime.now().strftime("%Y%m%d%H%M%S") + str(session['user_id']).zfill(4))
                record_new = True
                record_user = int(g.user['_index'])
                record_org = int(g.org['_index'])
            # Get remaining record fields
            try:
                record_name = request.form['record_name']
            except:
                record_name = "Name error"

            record_message = ""

            record_file_version = "None"
            if 'record_file' in request.files:
                # File object
                record_file = request.files['record_file']
                if record_file:
                    # Name to use to reference the file with time in to avoid duplicates
                    record_file_name, record_file_extension = os.path.splitext(record_file.filename)
                    record_file_clean = re.sub('[^A-Za-z0-9]+', '', record_file_name)
                    if (record_file_clean == ""):
                        record_file_clean = "Doc"
                    record_file_version = record_file_clean + nowIs + record_file_extension
                    document_number = int(datetime.now().strftime("%Y%m%d%H%M%S") + str(session['user_id']).zfill(4))
                    try:
                        # Write file object to database
                        db_inst.save_file(record_file_version, record_file)
                        record_message = "Document added"
                        # Create new document record
                        db_inst.db[data_coll].insert_one({'document_number': document_number, 'document_record': record_number, 'document_file': record_file_version, 'document_name': record_file.filename})
                        logger.info(request.remote_addr + ' ==> Document ' + str(document_number) + ' stored (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                        record_message = "Document stored"
                    except:
                        logger.info(request.remote_addr + ' ==> Database error adding document (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                        record_message = "Document not added, database error"
            document_records = []
            try: # Read document record
                document_records = list(db_inst.db[data_coll].find({'document_record': int(record_number) }))
            except: # Error if failed
                logger.info(request.remote_addr + ' ==> Database error reading document record for confirmation page (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                document_records.append({'document_number': 999999999999, 'document_record': 999999999999, 'document_file': "None"})
                page_title = "Database error reading document record"

            # Write new record info to log
            new_record_details = {
                "record_number": record_number,
                "record_name": record_name,
                "record_user": record_user,
                "record_org": record_org
            }

            if record_new:
                try:
                    # Create new record in database collection
                    db_inst.db[data_coll].insert_one({'record_number': int(record_number), 'record_name': record_name, 'record_user': int(record_user), 'record_org': int(record_org)})
                    record_message = "Record added to collection: " + str(data_coll)
                    logger.info(request.remote_addr + ' ==> New record (' + str(g.user['login']) + ' - ' + str(g.org['name']) + '): ' + str(new_record_details))
                except:
                    logger.info(request.remote_addr + ' ==> Database error adding new record (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                    record_message = "Record not added, database error for collection: " + str(data_coll)
            else:
                if g.user['admin'] == True or int(g.user['_index']) == record_user or (int(g.user['org']) == record_org and g.user['orgadmin'] == True): # User is admin, record owner, or record org admin
                    try:
                        # Modify existing record details in database collection
                        db_inst.db[data_coll].replace_one({'record_number': int(record_number) },{'record_number': int(record_number), 'record_name': record_name, 'record_user': int(record_user), 'record_org': int(record_org)})
                        record_message = "Record modified in collection: " + str(data_coll)
                        logger.info(request.remote_addr + ' ==> Modified record (' + str(g.user['login']) + ' - ' + str(g.org['name']) + '): ' + str(new_record_details))
                    except:
                        logger.info(request.remote_addr + ' ==> Database error modifying record (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                        record_message = "Record not modified, database error for collection: " + str(data_coll)
                else:
                    logger.info(request.remote_addr + ' ==> Denied access to modify record (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                    record_message = "Record not modified error"
                    new_record_details = ({'record_number': 999999999999, 'record_name': "Blocked...", 'record_user': 999999999999, 'record_org': 999999999999})
                    document_records.append({'document_number': 999999999999, 'document_record': 999999999999, 'document_file': "Blocked..."})

            # Confirm new record
            return render_template('collection.html', pagetitle=record_message, recorddetails=new_record_details, recorddocuments=document_records, org_records=orgs, user_records=users)

        else: # GET request
            # Show individual record page
            page_title = "Record"
            if int(filter_number) == 999999999999: # New record
                logger.info(request.remote_addr + ' ==> New record page (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                page_title = "Create a new record in collection: " + str(data_coll)
                return render_template('collection.html', pagetitle=page_title, org_records=orgs, user_records=users)
            else: # Existing record
                record_number = filter_number
                new_record = {}
                try: # Read record
                    new_record = dict(db_inst.db[data_coll].find_one({'record_number': int(record_number) }))
                except: # Error if failed
                    logger.info(request.remote_addr + ' ==> Database error reading record (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                    new_record = ({'record_number': 999999999999, 'record_name': "Name error", 'record_user': 999999999999, 'record_org': 999999999999})
                    page_title = "Database error reading record"
                document_records = []
                if g.user['admin'] == True or int(g.user['_index']) == int(new_record['record_user']) or (int(g.user['org']) == int(new_record['record_org']) and g.user['orgadmin'] == True): # User is admin, record owner, or record org admin
                    try: # Read document record
                        document_records = list(db_inst.db[data_coll].find({'document_record': int(record_number) }))
                    except: # Error if failed
                        logger.info(request.remote_addr + ' ==> Database error reading document record (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                        document_records.append({'document_number': 999999999999, 'document_record': 999999999999, 'document_file': "None"})
                        page_title = "Database error reading document record"
                    logger.info(request.remote_addr + ' ==> Existing record page (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                else: # Denied access to record
                    logger.info(request.remote_addr + ' ==> Denied access to record (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                    new_record = ({'record_number': 999999999999, 'record_name': "Blocked...", 'record_user': 999999999999, 'record_org': 999999999999})
                    document_records.append({'document_number': 999999999999, 'document_record': 999999999999, 'document_file': "Blocked..."})
                    page_title = "Record Access Error"
                return render_template('collection.html', pagetitle=page_title, recordedit=new_record, recorddocuments=document_records, org_records=orgs, user_records=users)

# # Collections record delete page
@fam_app.route('/colldelete', methods=['GET', 'POST'])
@auth.login_required
def colldeletepage():
    # End-user filter selections
    filter_number = request.args.get('num', default = 999999999999, type = int)
    # Build filter
    query_filter = dict({})
    if (filter_number != 999999999999):
        query_filter['record_number'] = filter_number
    record_number = filter_number
    # Page
    page_title = "Delete Record"
    if users_exist == False: # No users exist, will need to prompt to create one
        logger.info(request.remote_addr + ' ==> No users exist yet, prompting to create admin account )')
        return redirect(url_for('loginnewpage'))
    if int(session['user_id']) == 999999999999: # User is a guest
        logger.info(request.remote_addr + ' ==> Collection delete page access error for ' + filter_number + ' (' + str(g.user['login']) + ')')
        # Prompt to login
        return redirect(url_for('loginpage', requestingurl=request.full_path))
    if g.user['admin'] == False and int(g.org['_index']) == 999999999999: # User is not admin or in an org
        logger.info(request.remote_addr + ' ==> Collection delete page access error for ' + filter_number + ' (' + str(g.user['login']) + ')')
        page_title = "You must be in an organization to see records"
        # Show page error
        return render_template('colldel.html', pagetitle=page_title)
    else:
        # Collection name argument passed
        data_coll = request.args.get('data', default = "", type = str)
        if (data_coll == ""):
            logger.info(request.remote_addr + ' ==> Collection name not passed (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
            page_title = "You must pass a collection name"
            # Show page error
            return render_template('colldel.html', pagetitle=page_title)
        if request.method == 'POST':
            # Put a delay in to avoid large numbers of accidental requests
            # time.sleep(2)

            # Look to see if delete button was selected
            if request.form['submit'] == 'deleterecord':
                # Get record details
                try: # Record information
                    del_record = dict(db_inst.db[data_coll].find_one({'record_number': int(record_number) }))
                except: # Error if failed
                    logger.info(request.remote_addr + ' ==> Database error reading record to confirm delete (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                    del_record = ({'record_number': 999999999999, 'record_name': "Name error", 'record_user': 999999999999, 'record_org': 999999999999})
                    page_title = "Database error reading record to confirm for delete page"
                if g.user['admin'] == True or int(g.user['_index']) == int(del_record['record_user']) or (int(g.user['org']) == int(del_record['record_org']) and g.user['orgadmin'] == True): # User is admin, record owner, or record org admin
                    # Get the calling page
                    try:
                        user_returnto = request.form['returnto']
                    except:
                        user_returnto = ""
                    # Delete the opportunity
                    db_inst.db[data_coll].delete_one({'record_number': int(record_number) })
                    # Log the delete
                    logger.info(request.remote_addr + ' ==> Record deleted (' + str(g.user['login']) + ' - ' + str(g.org['name']) + '): ' + str(data_coll) + ': ' + str(record_number))
                    page_title = "Record " + str(record_number) + " Deleted"
                    if len(user_returnto) > 0: # Check to see what page URL was looking for
                        return redirect(user_returnto) # Go to calling page where delete was selected
                    else:
                        return render_template('colldel.html', pagetitle=page_title) # No calling page, just confirm it was deleted
                else:
                    # Log that it was requested but not performed here
                    logger.info(request.remote_addr + ' ==> Record delete denied for (' + str(g.user['login']) + ' - ' + str(g.org['name']) + '): ' + str(data_coll) + ': ' + str(record_number))
                    page_title = "Record " + str(record_number) + " Delete Denied"
                    return render_template('colldel.html', pagetitle=page_title)
            else:
                # Post request unrecognized
                logger.info(request.remote_addr + ' ==> Record delete failed for (' + str(g.user['login']) + ' - ' + str(g.org['name']) + '): ' + str(data_coll) + ': ' + str(record_number))
                page_title = "Record Deleted Incomplete Request for Unknown Reason"
                return render_template('colldel.html', pagetitle=page_title)
        else: # GET request
            # End-user filter selections
            forwardurl = ""
            if 'requestingurl' in request.args: # Pass from URL if supplied
                forwardurl = request.args['requestingurl']
            page_title = "Record Delete"
            if int(filter_number) == 999999999999: # No record passed
                logger.info(request.remote_addr + ' ==> Delete record page for non-existant record (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                page_title = "No Record Passed for Collection " + str(data_coll) + " to Delete"
                return render_template('colldel.html', pagetitle=page_title)
            else: # Existing record
                del_record = {}
                try: # Read record
                    del_record = dict(db_inst.db[data_coll].find_one({'record_number': int(record_number) }))
                except: # Error if failed
                    logger.info(request.remote_addr + ' ==> Database error reading record to be deleted (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                    del_record = ({'record_number': 999999999999, 'record_name': "Name error", 'record_user': 999999999999, 'record_org': 999999999999})
                    page_title = "Database Error Reading Record to be Deleted"
                if g.user['admin'] == True or int(g.user['_index']) == int(del_record['record_user']) or (int(g.user['org']) == int(del_record['record_org']) and g.user['orgadmin'] == True): # User is admin, record owner, or record org admin
                    logger.info(request.remote_addr + ' ==> Existing record page to delete (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                else: # Denied access to record
                    logger.info(request.remote_addr + ' ==> Denied access to record to delete (' + str(g.user['login']) + ' - ' + str(g.org['name']) + ')')
                    del_record = ({'record_number': 999999999999, 'record_name': "Blocked...", 'record_user': 999999999999, 'record_org': 999999999999})
                    page_title = "Record Delete Access Error"
                return render_template('colldel.html', pagetitle=page_title, recorddel=del_record, org_records=orgs, user_records=users, returnto=forwardurl)

# Logs page
@fam_app.route('/status')
@auth.login_required
def statuspage():
    if (int(session['user_id']) == 999999999999) or (session['login'] not in configuration['admin']):
        # User is non-admin
        logger.info(request.remote_addr + ' ==> Status page denied (' + str(g.user['login']) + ')')
        return render_template('error.html')

    running_python = sys.version.split('\n')
    logger.debug('DEBUG: Python version queried')
    running_host = platform.node()
    logger.debug('DEBUG: Host type queried')
    running_os = platform.system()
    logger.debug('DEBUG: Operating System queried')
    running_hardware = platform.machine()
    logger.debug('DEBUG: Server hardware queried')
    try:
        with open(log_file, 'r') as logging_file:
            log_data = logging_file.read()
            logger.debug('DEBUG: Log file read')
    except IOError:
        print('Problem opening ' + log_file + ', check to make sure your log file location is valid.')
        log_data = "Unable to read log file " + log_file
        logger.debug('DEBUG: Log file problem reading it')
    logger.info(request.remote_addr + ' ==> Status page (' + str(g.user['login']) + ')')
    return render_template('status.html', pagetitle="Status",
                           running_python=running_python, running_host=running_host,
                           running_os=running_os, running_hardware=running_hardware,
                           config_data=configuration, log_data=log_data)


# User authorization
@auth.verify_password
def verify(username, password):
    logger.debug('DEBUG: Verify passwerd function started')
    if not (username and password):  # Check to see if user has provided a login
        logger.debug('DEBUG: Username or password not supplied')
        return False
    # The password will change to something we can pull from Password State
    logger.debug('DEBUG: Checking password supplied')
    if (password != "TempPasswordHere"):  # Check password
        return False
    g.user = {}
    logger.debug('DEBUG: Global user variable cleared')
    authorized = login(username, password)
    return authorized


# API for Testing
@fam_app.route('/api', methods=['POST', 'GET'])
@auth.login_required
def api_json():
    response_message = {'status': 400, 'message': 'Authentication problem'}
    autherror = {'response:': response_message}
    logger.debug('DEBUG: Defaulting to error status before determining state for API call')
    if not configuration['error']:
        logger.debug('DEBUG: No configuration error')
        if int(g.user['_index']) == 999999999999:  # User is a guest
            response_message = {'status': 401, 'message': "Authentication is required, provide credentials"}
            logger.info(request.remote_addr + ' ==> API request denied (' + str(g.user['login']) + ')')
            autherror = {'response': response_message}
            logger.debug('DEBUG: Authorization error being returned to user')
            return autherror
        else:  # Process request
            # url_args = request.args  # URL arguments not implemented, reserved for later use
            logger.debug('DEBUG: URL arguments collected but not being used')
            response_message = {'status': 200, 'message': "Successful (" + str(g.user['login']) + ")"}
            data_response = {'response': response_message}
            logger.info(request.remote_addr + ' ==> API request received (' + str(g.user['login']) + ')')
            if request.method == 'POST':  # POST method expected
                logger.debug('DEBUG: Call type is POST')
                content_type = request.headers.get('Content-Type')
                logger.debug('DEBUG: Requesting content type from user')
                if (content_type == 'application/json'):
                    post_json = request.json
                    logger.debug('DEBUG: Content type includes JSON payload')
                    logger.debug('DEBUG: ' + str(post_json))
                    data_error = True
                    try:  # JSON data included
                        print("POST JSON received")
                        logger.info(request.remote_addr + ' ==> API request started (' + str(g.user['login']) + ')')
                        # Pass JSON from request to Test Server
                        data_run = "No data returned"
                        # Maybe pass something to an external app here
                        if not data_error:
                            data_response['data'] = str(data_run)
                        logger.info(request.remote_addr + ' ==> API request completed (' + str(g.user['login']) + ')')
                        response_message = {'status': 202, 'message': "Successful (" + str(g.user['login']) + ")"}
                    except Exception:  # No JSON data included or run failed
                        print("Missing JSON data or run failed")
                        logger.info(request.remote_addr + ' ==> API request missing JSON data or run failed (' +
                                    str(g.user['login']) + ')')
                        response_message = {
                            'status': 406,
                            'message': "Missing JSON data or run failed (" + str(g.user['login']) + ")"
                        }
            else:  # GET method reply with error
                logger.debug('DEBUG: Call type is GET')
                logger.info(request.remote_addr + ' ==> API request failed not POST (' + str(g.user['login']) + ')')
                response_message = {
                    'status': 405,
                    'message': "POST method with JSON data required (" + str(g.user['login']) + ")"
                }
            data_response['response'] = response_message
            logger.debug('DEBUG: Data response being returned to user')
            return data_response
    else:
        logger.info(request.remote_addr + ' ==> API request server configuration error (' + str(g.user['login']) + ')')
        response_message = {'status': 409, 'message': "Server configuration problem"}
        server_error = {'response': response_message}
        logger.debug('DEBUG: Configuration error being returned to user')
        return server_error


# Run in debug mode if started from CLI (http://localhost:5000)
if __name__ == '__main__':
    logger.debug('DEBUG: Main function starting Flask app')
    fam_app.run(debug=True)
