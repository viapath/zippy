#!/usr/local/env python
from __future__ import print_function

import sys
import os
import re
import json
import bcrypt
import hashlib
import subprocess
from functools import wraps
from flask import Flask, render_template, request, redirect, send_from_directory, session, flash, url_for
from celery import Celery
from werkzeug.utils import secure_filename
from . import app, config
from .zippy import zippyBatchQuery, zippyPrimerQuery, updateLocation, searchByName, updatePrimerName, updatePrimerPairName, blacklistPair, deletePair, readprimerlocations, __version__
from .zippylib.primer import Location, ChromosomeNotFoundError
from .zippylib.database import PrimerDB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def login_required(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if session.get('logged_in', False):
            return func(*args, **kwargs)
        else:
            flash('Authentication required!', 'warning')
            return redirect(url_for('login'))
    return wrap


@app.errorhandler(ChromosomeNotFoundError)
def handle_chromosome_not_found(err):
    message=("<h1>Chromosome {0!r} not found</h1>.<p>The available chromosomes are {1}.</p>"+
        "<p>Hit the back button and try again</p>").format(err.args[0], err.args[1])
    return (message, 404)


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html',designtiers=config['design']['tiers'], version=__version__)


# simple access control (login)
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        #it used bcrypt.hashpw(request.form['password'].rstrip().encode('utf-8'), app.config['PASSWORD']) in the original viapath/zippy package, but this didn't work
        if request.form['password'].rstrip() == app.config['PASSWORD']:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = 'Wrong password. Please try again.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/no_file')
def no_file():
    return render_template('no_file.html')


@app.route('/file_uploaded')
def file_uploaded():
    return render_template('file_uploaded.html')


@app.route('/file_uploaded/<path:filename>')
def download_file(filename):
    return send_from_directory(os.getcwd(), filename, as_attachment=True)


@app.route('/adhoc_result')
def adhoc_result(primerTable, resultList, missedIntervals):
    return render_template('file_uploaded.html', primerTable, resultList, missedIntervals)


@app.route('/location_updated')
def location_updated(status):
    return render_template('location_updated.html', status)


@app.route('/upload/', methods=['POST', 'GET'])
def upload():
    # read form
    uploadFile = request.files['variantTable']
    uploadFile2 = request.files['missedRegions']
    uploadFile3 = request.files['singleGenes']
    tiers = list(map(int, request.form.getlist('tiers')))
    predesign = request.form.get('predesign')
    design = request.form.get('design')
    outfile = request.form.get('outfile')

    # save files
    uploadedFiles = []
    for uf in [uploadFile, uploadFile2, uploadFile3]:
        if uf and allowed_file(uf.filename):
            uploadedFiles.append(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(uf.filename)))
            uf.save(uploadedFiles[-1])
            print("file saved to %s" % uploadedFiles[-1], file=sys.stderr)

    if uploadedFiles:
        # open config file and database
        with open(app.config['CONFIG_FILE']) as conf:
            config = json.load(conf)
            db = PrimerDB(config['database'], dump=config['ampliconbed'])

        # create output folder
        filehash = hashlib.sha1(b''.join([open(uf,"rb").read() for uf in uploadedFiles])).hexdigest()
        downloadFolder = os.path.join(app.config['DOWNLOAD_FOLDER'], filehash)
        subprocess.check_call(['mkdir', '-p', downloadFolder], shell=False)

        # run Zippy to design primers
        shortName = os.path.splitext(os.path.basename(uploadedFiles[0]))[0]
        downloadFile = os.path.join(downloadFolder, outfile) if outfile else os.path.join(downloadFolder, shortName)
        arrayOfFiles, missedIntervalNames, flash_messages = zippyBatchQuery(config, uploadedFiles, design, downloadFile, db, predesign, tiers)
        for flash_message in flash_messages:
            flash(*flash_message)
        return render_template('file_uploaded.html', outputFiles=arrayOfFiles, missedIntervals=missedIntervalNames)
    else:
        print("file for upload not supplied or file-type not allowed")
        return redirect('/no_file')


@app.route('/test/', methods=['POST', 'GET'])
def testpage():
    # read form data
    #return "teste"
    try:
        assert 0,'tp'
    except MemoryError as exc:
        import traceback
        return str(traceback.format_exc())


@app.route('/save_comments/', methods=['POST'])
def search_by_name_comments_save():
    db = PrimerDB(config['database'], dump=config['ampliconbed'])
    try:
        db.updatePrimerPairsComments(request.form)
    except:
        flash("ERROR when saving the comments", "error")
    else:
        flash("The comments were saved", "success")
    return redirect('/index')
    #return "Comments saved SN"


@app.route('/adhoc_design/', methods=['POST'])
def adhocdesign():
    # read form data
    #return '2cad'
    #return "dde {0}".format(str(request.files.items()))
    uploadFile = request.files['filePath']
    locus = request.form.get('locus').strip()
    design = request.form.get('design')
    tiers = list(map(int,request.form.getlist('tiers')))
    gap = request.form.get('gap')
    store = request.form.get('store')

    print('tiers', tiers, file=sys.stderr)
    print('locus', locus, file=sys.stderr)
    print('gap', gap, file=sys.stderr)
    # if locus:
    rematch = re.match('\w{1,6}:\d+[-:]\d+',locus)
    if rematch or (uploadFile and allowed_file(uploadFile.filename)):
        # get target
        if uploadFile:
            filename = secure_filename(uploadFile.filename)
            print ("Uploaded: ", filename, file=sys.stderr)
            try:
                target = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            except Exception as exc:
                import traceback
                return str(traceback.format_exc())
            uploadFile.save(target)
            print("file saved to %s" % target, file=sys.stderr)
            if len(locus)>0:
                args=(target,locus)
            else:
                args=target
        else:
            args = locus
        # read config
        with open(app.config['CONFIG_FILE']) as conf:
            config = json.load(conf)
            db = PrimerDB(config['database'],dump=config['ampliconbed'])
        # run Zippy
        """import cProfile
        profiler = cProfile.Profile()
        profiler.runcall(zippyPrimerQuery, config, args, design, None, db, store, tiers, gap)
        profiler.print_stats()
        assert 0"""
        #print("parguments", config, args, design, None, db, store, tiers, gap)
        primerTable, resultList, missedIntervals, flash_messages = zippyPrimerQuery(config, args, design, None, db, store, tiers, gap)

        for flash_message in flash_messages:
            flash(*flash_message)

        # get missed and render template
        missedIntervalNames = []
        for interval in missedIntervals:
            missedIntervalNames.append(interval.name)
        return render_template('/adhoc_result.html', primerTable=primerTable, resultList=resultList, missedIntervals=missedIntervalNames)
    else:
        print ("no locus or file given", file=sys.stderr)
        return render_template('/adhoc_result.html', primerTable=[], resultList=[], missedIntervals=[])


@app.route('/update_location/', methods=['POST'])
def updatePrimerLocation():
    primername = request.form.get('primername')
    vessel = request.form.get('vessel')
    well = request.form.get('well')
    force = request.form.get('force')
    try:
        assert primername
        loc = Location(vessel, well)
    except:
        print ('Please fill in all fields (PrimerName VesselNumber Well)', file=sys.stderr)
        return render_template('location_updated.html', status=None)
    # read config
    with open(app.config['CONFIG_FILE']) as conf:
        config = json.load(conf)
        db = PrimerDB(config['database'],dump=config['ampliconbed'])
    # run zippy and render
    updateStatus = updateLocation(primername, loc, db, force)
    return render_template('location_updated.html', status=updateStatus)


@app.route('/select_pair_to_update/<pairName>')
def pair_to_update(pairName):
    return render_template('update_pair.html', pairName=pairName)


@app.route('/update_pair_name/<pairName>', methods=['POST'])
def update_pair_name(pairName):
    newName = request.form.get('name')
    if newName == pairName:
        flash('New name is the same as current', 'warning')
        return render_template('update_pair.html', pairName=pairName)
    with open(app.config['CONFIG_FILE']) as conf:
        config = json.load(conf)
        db = PrimerDB(config['database'],dump=config['ampliconbed'])
        if updatePrimerPairName(pairName, newName, db):
            flash('Pair "%s" renamed "%s"' % (pairName, newName), 'success')
        else:
            flash('Pair renaming failed', 'warning')
    return render_template('update_pair.html', pairName=newName)


@app.route('/select_primer_to_update/<primerName>/<primerLoc>')
def primer_to_update(primerName, primerLoc):
    primerInfo = primerName + '|' + primerLoc
    return redirect('/update_location_from_table/%s' % (primerInfo))


@app.route('/update_location_from_table/<primerInfo>', methods=['GET','POST'])
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
            print ('Please fill in all fields (PrimerName VesselNumber Well)', file=sys.stderr)
            return render_template('location_updated.html', status=None)
        with open(app.config['CONFIG_FILE']) as conf:
            config = json.load(conf)
            db = PrimerDB(config['database'], dump=config['ampliconbed'])
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
def primer_to_rename(primerName, primerLoc):
    newName = request.form.get('name')
    print(primerName, file=sys.stderr)
    print(primerLoc, file=sys.stderr)
    print(newName, file=sys.stderr)
    primerInfo = primerName + '|' + primerLoc + '|' + newName
    print(primerInfo, file=sys.stderr)
    return redirect('/update_primer_name/%s' % (primerInfo))


@app.route('/update_primer_name/<primerInfo>')
def update_name_of_primer(primerInfo):
    splitInfo = primerInfo.split('|')
    currentName = splitInfo[0]
    primerLoc = splitInfo[1]
    newName = splitInfo[2]
    if newName == currentName:
        flash('Primer renaming failed - new name is the same as current', 'warning')
        return render_template('update_location_from_table.html', primerName=newName, primerLoc=primerLoc)
    with open(app.config['CONFIG_FILE']) as conf:
        config = json.load(conf)
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        if updatePrimerName(currentName, newName, db):
            flash('Primer "%s" renamed "%s"' % (currentName, newName), 'success')
        else:
            flash('Primer renaming failed', 'warning')
    return render_template('update_location_from_table.html', primerName=newName, primerLoc=primerLoc)


@app.route('/specify_searchname/', methods=['POST'])
def searchName():
    searchName = request.form.get('searchName')
    session['searchName'] = searchName
    return redirect('/search_by_name/')


@app.route('/search_by_name/')
def search_by_name():
    searchName = session['searchName']
    with open(app.config['CONFIG_FILE']) as conf:
        config = json.load(conf)
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        searchResult = searchByName(searchName, db)
    return render_template('searchname_result.html', searchResult=searchResult, searchName=searchName)


@app.route('/blacklist_pair/<pairname>', methods=['POST'])
def blacklist_pair(pairname):
    print ('This is the pairname: ' + pairname, file=sys.stderr)
    with open(app.config['CONFIG_FILE']) as conf:
        config = json.load(conf)
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        blacklisted = blacklistPair(pairname, db)
        for b in blacklisted:
            flash('%s added to blacklist' % (b,), 'success')
    return redirect('/search_by_name/')


@app.route('/delete_pair/<pairname>', methods=['POST'])
def delete_pair(pairname):
    print ('This is the pairname: ' + pairname, file=sys.stderr)
    with open(app.config['CONFIG_FILE']) as conf:
        config = json.load(conf)
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        deleted = deletePair(pairname, db)
        for d in deleted:
            flash('%s deleted' % (d,), 'success')
    return redirect('/search_by_name/')


@app.route('/upload_batch_locations/', methods=['POST'])
def upload_samplesheet():
    if request.method == 'POST':
        locationsheet = request.files['locationsheet']
        if not locationsheet or not locationsheet.filename.endswith('.csv'):
            flash('Not a CSV file. Please try again', 'warning')
        else:
            filename = secure_filename(locationsheet.filename)
            saveloc = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            locationsheet.save(saveloc)
            updateList = readprimerlocations(saveloc)
            with open(app.config['CONFIG_FILE']) as conf:
                config = json.load(conf)
                db = PrimerDB(config['database'], dump=config['ampliconbed'])
                for item in updateList:
                    updateStatus = updateLocation(item[0], item[1], db, True)  # Force is set to True, will force primers into any occupied locations
                    if updateStatus[0] == 'occupied':
                        flash('Location already occupied by %s' % (' and '.join(updateStatus[1])), 'warning')
                    elif updateStatus[0] == 'success':
                        flash('%s location sucessfully set to %s' % (item[0], str(item[1])), 'success')
                    else:
                        flash('%s location update to %s failed' % (item[0], str(item[1])), 'warning')
            print ('Updated locations using :', updateList, file=sys.stderr)
    return redirect('/index')
