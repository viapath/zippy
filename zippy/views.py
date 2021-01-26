#!/usr/local/env python
import sys
import os
import re
import json
import bcrypt
import hashlib
import subprocess
import tempfile
from functools import wraps, reduce
from collections import Counter, defaultdict
from flask import Flask, render_template, request, redirect, send_from_directory, session, flash, url_for
from werkzeug.utils import secure_filename
from . import app
from .zippy import validateAndImport, zippyBatchQuery, zippyPrimerQuery, \
    updateLocation, searchByName, updatePrimerName, updatePrimerPairName, \
    blacklistPair, deletePair, readprimerlocations
from .zippylib import ascii_encode_dict
from .zippylib.primer import Location, checkPrimerFormat
from .zippylib.database import PrimerDB

app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'batch', 'vcf', 'bed', 'csv', 'tsv', 'fasta', 'fa'])
app.secret_key = 'Zippy is the best handpuppet out there'

# read zippy configuration file
try:
    assert os.environ['ZIPPY_CONFIG']
except (KeyError, AssertionError):
    app.config['CONFIG_FILE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zippy.json')
except:
    raise
else:
    print >> sys.stderr, "WARNING: Using CONFIG from ENV (overriding default configuration)"
    app.config['CONFIG_FILE'] = os.environ['ZIPPY_CONFIG']

# configure flask app
with open(app.config['CONFIG_FILE']) as conf:
    config = json.load(conf, object_hook=ascii_encode_dict)
    # read password (bcrypt), override if ENV variable set with a value
    app.config['PASSWORD'] = config['password']
    try:
        assert os.environ['ZIPPY_PASSWORD']
    except (KeyError, AssertionError):
        pass
    except:
        raise
    else:
        print >> sys.stderr, "WARNING: Using Password from ENV (overriding default configuration)"
        hashed_env_password = bcrypt.hashpw(os.environ['ZIPPY_PASSWORD'], bcrypt.gensalt())
        app.config['PASSWORD'] = hashed_env_password
    # read folder locations
    app.config['UPLOAD_FOLDER'] = config['uploads_folder']
    app.config['DOWNLOAD_FOLDER'] = config['results_folder']
    # load database
    db = PrimerDB(config['database'],dump=config['ampliconbed'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

'''API logger'''
def logger(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        # pre execution logger
        db.log(session['logged_in'], func.__name__, str(args), str(kwargs), \
            str(request.form), str(request.files))
        return func(*args, **kwargs)
    return wrap

'''user is logged in'''
def logged_in(s):
    if "logged_in" in s:
        if s['logged_in'] == 'admin':
            return s['logged_in']
        elif db.getUser(s["logged_in"]):
            return s['logged_in']
    return None

''' extremely simple login system for basic audit capabilities'''
def login_required(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if logged_in(session):
            return func(*args, **kwargs)
        else:
            flash('Authentication required!', 'warning')
            return redirect(url_for('login'))
    return wrap

def is_admin(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if logged_in(session) == 'admin':
            return func(*args, **kwargs)
        else:
            error = 'Administrator login required'
            return render_template('login.html', error=error)
    return wrap

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html',designtiers=config['design']['tiers'])

# simple access control (login)
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username'].rstrip().encode('utf-8')
        users = db.getUser(username)
        stored_pw = users[0][1].encode('utf-8') if users else app.config['PASSWORD'] if username == 'admin' else None
        if stored_pw and bcrypt.hashpw(request.form['password'].rstrip().encode('utf-8'), stored_pw) == stored_pw:
            session['logged_in'] = username
            db.log(session['logged_in'], 'login')
            return redirect(url_for('index'))
        else:
            error = 'Please try again.'
    return render_template('login.html', error=error)

@app.route('/user_admin', methods=['GET','POST'])
def user_admin():
    error = None
    if request.method =='POST':
        if 'edit_username' in request.form.keys() and request.form['edit_username'] and\
            'edit_password' in request.form.keys() and request.form['edit_password']:
            # change password or edit user
            if re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$", request.form['edit_password']):
                hashed_password = bcrypt.hashpw(request.form['edit_password'].encode('utf-8'), bcrypt.gensalt())
                db.editUser(request.form['edit_username'], hashed_password)
                # if not admin go back to index after change
                if logged_in(session) != 'admin':
                    return redirect(url_for('index'))
            else:
                error = "Password must be at least 8 characters long, and contain numbers and letters"
        elif 'delete_username' in request.form.keys() and \
            request.form['delete_username'] and logged_in(session) == 'admin':
            # deletes user
            db.editUser(request.form['delete_username'])
    users = db.getUsers() if logged_in(session) == 'admin' else []
    return render_template('user_admin.html', users=users, error=error)

@app.route('/favicon.ico') 
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/logout')
def logout():
    db.log(session['logged_in'], 'logout')
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/batch_result')
def batch_result():
    return render_template('batch_result.html')

@app.route('/batch_result/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/location_updated')
def location_updated(status):
    return render_template('location_updated.html', status)

@app.route('/batch_design/', methods=['POST', 'GET'])
@logger
def batch_design():
    # read form
    uploadFile = request.files['variantTable']
    uploadFile2 = request.files['missedRegions']
    uploadFile3 = request.files['singleGenes']
    tiers = map(int,request.form.getlist('tiers'))
    predesign = request.form.get('predesign')
    design = request.form.get('design')
    outfile = request.form.get('outfile')

    # save files
    uploadedFiles = []
    for uf in [uploadFile, uploadFile2, uploadFile3]:
        if uf and allowed_file(uf.filename):
            uploadedFiles.append(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(uf.filename)))
            uf.save(uploadedFiles[-1])
            print >> sys.stderr, "file saved to %s" % uploadedFiles[-1]

    if uploadedFiles:
        # create output folder
        filehash = hashlib.sha1(''.join([ open(uf).read() for uf in uploadedFiles ])).hexdigest()
        downloadFolder = os.path.join(app.config['DOWNLOAD_FOLDER'], filehash)
        subprocess.check_call(['mkdir', '-p', downloadFolder], shell=False)

        # run Zippy to design primers
        shortName = os.path.splitext(os.path.basename(uploadedFiles[0]))[0]
        downloadFile = os.path.join(downloadFolder, outfile) if outfile else os.path.join(downloadFolder, shortName)
        arrayOfFiles, missedIntervalNames = zippyBatchQuery(config, uploadedFiles, design, downloadFile, db, predesign, tiers)
        arrayOfFiles = list([ f[len(app.config['DOWNLOAD_FOLDER']):].lstrip('/') for f in arrayOfFiles if f.startswith(app.config['DOWNLOAD_FOLDER'])])
        return render_template('batch_result.html', outputFiles=arrayOfFiles, missedIntervals=missedIntervalNames)
    else:
        flash('No appropriate worksheets supplied','warning')
        return redirect(url_for('index'))

@app.route('/adhoc_design/', methods=['POST'])
@logger
def adhoc_design():
    # read form data
    uploadFile = request.files['filePath']
    locus = request.form.get('locus')
    design = request.form.get('design')
    tiers = map(int,request.form.getlist('tiers'))
    gap = request.form.get('gap')
    store = request.form.get('store')
    # if locus or file
    if re.match('\w{1,2}:\d+-\d+',locus) or (uploadFile and allowed_file(uploadFile.filename)):
        # get target
        if uploadFile:
            filename = secure_filename(uploadFile.filename)
            print >> sys.stderr, "Uploaded: ", filename
            target = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploadFile.save(target)
            print >> sys.stderr, "file saved to %s" % target
        else:
            target = locus
        # run Zippy
        primerTable, resultList, missedIntervals = zippyPrimerQuery(config, target, design, None, db, store, tiers, gap)

        print >> sys.stderr, primerTable

        # get missed and render template
        missedIntervalNames = []
        for interval in missedIntervals:
            missedIntervalNames.append(interval.name)
        return render_template('/adhoc_result.html', primerTable=primerTable, resultList=resultList, missedIntervals=missedIntervalNames)
    else:
        flash('No locus of file given for primer design','warning')
        return redirect(url_for('index'))

@app.route('/import_primers/', methods=['POST'])
@logger
def import_primers():
    # read form data
    uploadFile = request.files['filePath']
    primers = request.form.get('primers')
    validate = request.form.get('validate')
    # if Primers given
    if (primers and checkPrimerFormat(primers)) or \
        (uploadFile and allowed_file(uploadFile.filename)):
        # get target
        if uploadFile:
            filename = secure_filename(uploadFile.filename)
            print >> sys.stderr, "Uploaded: ", filename
            target = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploadFile.save(target)
            print >> sys.stderr, "file saved to %s" % target
        elif primers:
            # write file
            with tempfile.NamedTemporaryFile(suffix='.fa', prefix="primers_", delete=False) as fh:
                print >> fh, primers
            print >> sys.stderr, "primers written to %s" % fh.name
            target = fh.name

        # run Zippy
        report_counts, failed_primers = validateAndImport(config, target, validate, db)
        # amend report descriptions
        desc = defaultdict(str, {
            "PASS": "Passed validation",
            "amplicons": "Too many amplicons",
            "criticalsnp": "Polymorphism in 3prime end",
            "mispriming": "Excess primer binding sites",
            "snpcount": "Polymorphism in primers",
            "designrank": "Suboptimal design",
            "taggedthermo": "Tagged primer forms secondary structures or dimers",
            "thermo": "Forms secondary structures or dimers",
            "no_target": " Could not infer target sequence"
        })
        report = []
        for keyword, count in sorted(report_counts.items(), key=lambda x: x[1] * -1):
            report.append([keyword, count, desc[keyword]])
        # get missed and render template
        return render_template('/import_report.html', failed_primers=failed_primers,
            report=report)
    else:
        flash('No primers supplied','warning')
        return redirect(url_for('index'))

@app.route('/update_location/', methods=['POST'])
@logger
def updatePrimerLocation():
    primername = request.form.get('primername')
    vessel = request.form.get('vessel')
    well = request.form.get('well')
    force = request.form.get('force')
    try:
        assert primername
        loc = Location(vessel, well)
    except:
        print >> sys.stderr, 'Please fill in all fields (PrimerName VesselNumber Well)'
        return render_template('location_updated.html', status=None)
    # run zippy and render
    updateStatus = updateLocation(primername, loc, db, force)
    return render_template('location_updated.html', status=updateStatus)

@app.route('/select_pair_to_update/<pairName>')
@logger
def pair_to_update(pairName):
    return render_template('update_pair.html', pairName=pairName)

@app.route('/update_pair_name/<pairName>', methods=['POST'])
@logger
def update_pair_name(pairName):
    newName = request.form.get('name')
    if newName == pairName:
        flash('New name is the same as current', 'warning')
        return render_template('update_pair.html', pairName=pairName)
    if updatePrimerPairName(pairName, newName, db):
        flash('Pair "%s" renamed "%s"' % (pairName, newName), 'success')
    else:
        flash('Pair renaming failed', 'warning')
    return render_template('update_pair.html', pairName=newName)

@app.route('/select_primer_to_update/<primerName>')
@app.route('/select_primer_to_update/<primerName>/<primerLoc>')
@logger
def primer_to_update(primerName, primerLoc="None"):
    primerInfo = primerName + '|' + primerLoc
    return redirect(url_for('updateLocationFromTable', primerInfo=primerInfo))

@app.route('/update_location_from_table/<primerInfo>', methods=['GET','POST'])
@logger
def updateLocationFromTable(primerInfo):
    if request.method == 'POST':
        primerName = primerInfo
        vessel = request.form.get('vessel')
        well = request.form.get('well')
        force = request.form.get('force')
        try:
            assert primerName
            loc = Location(vessel, well)
        except:
            print >> sys.stderr, 'Please fill in all fields (PrimerName VesselNumber Well)'
            return render_template('location_updated.html', status=None)
        # run zippy and render
        updateStatus = updateLocation(primerName, loc, db, force)
        if updateStatus[0] == 'occupied':
            flash('Location already occupied by %s' % (' and '.join(updateStatus[1])), 'warning')
        elif updateStatus[0] == 'success':
            flash('%s location sucessfully set to %s' % (primerName, str(loc)), 'success')
        else:
            flash('%s location update to %s failed' % (primerName, str(loc)), 'warning')
        return render_template('update_location_from_table.html', primerName=primerName, primerLoc=vessel + '-' + well)
    else:
        splitInfo = primerInfo.split('|')
        primerName = splitInfo[0]
        primerLoc = splitInfo[1]
        return render_template('update_location_from_table.html', primerName=primerName, primerLoc=primerLoc)

@app.route('/select_primer_to_rename/<primerName>/<primerLoc>', methods=['POST'])
@logger
def primer_to_rename(primerName, primerLoc):
    newName = request.form.get('name')
    print >> sys.stderr, primerName
    print >> sys.stderr, primerLoc
    print >> sys.stderr, newName
    primerInfo = primerName + '|' + primerLoc + '|' + newName
    print >> sys.stderr, primerInfo
    return redirect(url_for('update_name_of_primer', primerInfo=primerInfo))

@app.route('/update_primer_name/<primerInfo>')
@logger
def update_name_of_primer(primerInfo):
    splitInfo = primerInfo.split('|')
    currentName = splitInfo[0]
    primerLoc = splitInfo[1]
    newName = splitInfo[2]
    if newName == currentName:
        flash('Primer renaming failed - new name is the same as current', 'warning')
        return render_template('update_location_from_table.html', primerName=newName, primerLoc=primerLoc)
    if updatePrimerName(currentName, newName, db):
        flash('Primer "%s" renamed "%s"' % (currentName, newName), 'success')
    else:
        flash('Primer renaming failed', 'warning')
    return render_template('update_location_from_table.html', primerName=newName, primerLoc=primerLoc)

@app.route('/search/', methods=['POST','GET'])
def search():
    if request.method == 'POST':
        session['searchName'] = request.form.get('searchName')
    searchResult = searchByName(session['searchName'], db)
    return render_template('searchname_result.html', searchResult=searchResult, \
        searchName=session['searchName'])

@app.route('/blacklist_pair/<pairname>', methods=['POST'])
@logger
def blacklist_pair(pairname):
    blacklisted = blacklistPair(pairname, db)
    for b in blacklisted:
        flash('%s added to blacklist' % (b,), 'success')
    return redirect(url_for('search'))

@app.route('/delete_pair/<pairname>', methods=['POST'])
@logger
def delete_pair(pairname):
    deleted = deletePair(pairname, db)
    for d in deleted:
        flash('%s deleted' % (d,), 'success')
    return redirect(url_for('search'))

@app.route('/upload_locations/', methods=['POST'])
@logger
def upload_locations():
    if request.method == 'POST':
        locationsheet = request.files['locationsheet']
        if not locationsheet or not locationsheet.filename.endswith('.csv'):
            flash('Not a CSV file. Please try again','warning')
        else:
            filename = secure_filename(locationsheet.filename)
            saveloc = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            locationsheet.save(saveloc)
            updateList = readprimerlocations(saveloc)
            for item in updateList:
                updateStatus = updateLocation(item[0], item[1], db, True) # Force is set to True, will force primers into any occupied locations
                if updateStatus[0] == 'occupied':
                    flash('Location already occupied by %s' % (' and '.join(updateStatus[1])), 'warning')
                elif updateStatus[0] == 'success':
                    flash('%s location sucessfully set to %s' % (item[0], str(item[1])), 'success')
                else:
                    flash('%s location update to %s failed' % (item[0], str(item[1])), 'warning')
            print >> sys.stderr, 'Updated locations using :', updateList
    return redirect(url_for('index'))
