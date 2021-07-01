#!/usr/bin/env python

__doc__=="""
################################################################
# Zippy - Primer database and automated design                 #
# -- Organisation: Viapath Analytics / King's College Hospital #
# -- From: 26/08/2015                                          #
################################################################
"""
__author__ = "David Brawand"
__credits__ = ['David Brawand','Christopher Wall']
__license__ = "MIT"
__version__ = "2.5.0"
__maintainer__ = "David Brawand"
__email__ = "dbrawand@nhs.net"
__status__ = "Production"

import os
import re
import sys
import json
import tempfile
import hashlib
import csv
from zippylib.files import VCF, BED, GenePred, Interval, Data, readTargets, readBatch
from zippylib.primer import Tag, Genome, MultiFasta, Primer3, Primer, PrimerPair, Location, parsePrimerName
from zippylib.reports import Test
from zippylib.database import PrimerDB
from zippylib.interval import IntervalList
from zippylib import ConfigError, Progressbar, banner
from zippylib.reports import Worksheet
from argparse import ArgumentParser
from copy import deepcopy
from collections import defaultdict, Counter
from urllib import unquote
import cPickle as pickle

'''file MD5'''
def fileMD5(fi, block_size=2**20):
    md5 = hashlib.md5()
    with open(fi,'rb') as fh:
        while True:
            data = fh.read(block_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

'''import primer locations from table'''
def importPrimerLocations(inputfile):
    primerlocs = {}
    with open(inputfile) as infh:
        for i,line in enumerate(infh):
            if i == 0:
                header = map(lambda x : x.lower(), line.rstrip().split('\t'))
            else:
                f = map(lambda x: x.strip('"'), line.rstrip().split('\t'))
                l = dict(zip(header,f))
                # store metadata and write fasta
                if 'vessel' in l.keys() and 'well' in l.keys() and \
                    l['vessel'] and l['well'] and l['vessel'] != 'None' and l['well'] != 'None':
                    # store location
                    loc = Location(l['vessel'],l['well'])
                    if l['primername'] in primerlocs.keys():
                        primerlocs[l['primername']].merge(loc)
                    else:
                        primerlocs[l['primername']] = loc
    return primerlocs

'''converts comma seperated variant descriptor to pseudo human readable format'''
def shortHumanReadable(x):
    fields = unquote(x).split(',')
    return '_'.join([ fields[0], hashlib.sha1(','.join(fields[:-1])).hexdigest()[:6].upper() ])

'''generates hash from primer sequences'''
seqhash = lambda x,y: hashlib.sha1(','.join([x,y])).hexdigest()  # sequence pair hashing function

'''reads fasta/tab inputfile, searches genome for targets, decides if valid pairs
    inputfile: FILENAME
    config:    CONFIGURATION DICT
    primer3:   PRIMER3 PRIMERS (disables deep amplicon searching)
    keepall:   KEEP ALL PAIRS (even if they do not yield an amplicon)
'''
def importPrimerPairs(inputfile,config,primer3=True,keepall=False):
    # read table/fasta
    primersets = defaultdict(list)  # pair primersets
    primertags = {}  # primer tags from table
    if not inputfile.split('.')[-1].startswith('fa'):  # ignores duplicate sequence
        # import from table
        primerseqs = {}
        fastafile = 'import_' + fileMD5(inputfile)[:8] + '.fasta'
        with open(fastafile,'w') as outfh:
            with open(inputfile) as infh:
                for i,line in enumerate(infh):
                    if i == 0:
                        minimalHeader = set(['primername','primerset','tag','sequence','vessel','well'])
                        header = map(lambda x : x.lower(), line.rstrip().split('\t'))
                        try:
                            assert not minimalHeader.difference(set(header))
                        except:
                            print >> sys.stderr, 'ERROR: Missing columns (%s)' % ','.join(list(minimalHeader.difference(set(header))))
                            raise Exception('FileHeaderError')
                    else:
                        f = map(lambda x: x.strip('"'), line.rstrip().split('\t'))
                        l = dict(zip(header,f))
                        # remove tag from sequence
                        if l['tag']:
                            try:
                                tagseqs = config['ordersheet']['sequencetags'][l['tag']]['tags']
                            except:
                                pass
                            else:
                                for t in tagseqs:
                                    if l['sequence'].startswith(t):
                                        l['sequence'] = l['sequence'][len(t):]
                                        break
                        # store metadata and write fasta
                        if l['primername'] in primerseqs.keys():
                            try:
                                assert l['sequence'] == primerseqs[l['primername']]
                                assert l['tag'] == primertags[l['primername']]
                            except:
                                print >> sys.stderr, l['primername']
                                print >> sys.stderr, primerseqs[l['primername']]
                                print >> sys.stderr, primertags[l['primername']]
                                raise Exception('ImportFormattingError')
                        else:
                            print >> outfh, '>'+l['primername']
                            print >> outfh, l['sequence']
                        if l['primerset']:
                            primersets[l['primername']].append(l['primerset'])
                        primertags[l['primername']] = l['tag']
                        primerseqs[l['primername']] = l['sequence']
        primerfile = MultiFasta(fastafile)
    else:
        primerfile = MultiFasta(inputfile)
        # set default tags for import
        for r in primerfile.references:
            primertags[r] = config['import']['tag']
    print >> sys.stderr, "Placing primers on genome..."

    # amend tag sequences
    primer_tags_seqs = {}
    for primername, tag in primertags.items():
        m = re.match(r'(.*_(fwd|rev))(\|\S+)?', primername, re.IGNORECASE)
        if m:
            if m.group(2).lower() == 'fwd':
                primer_tags_seqs[m.group(1)] = Tag(tag, config['ordersheet']['sequencetags'][tag]['tags'][0])
            elif m.group(2).lower() == 'rev':
                primer_tags_seqs[m.group(1)] = Tag(tag, config['ordersheet']['sequencetags'][tag]['tags'][1])
        else:
            primer_tags_seqs[primername] = Tag(tag)

    # Align primers to genome
    primers = primerfile.createPrimers(config['design']['bowtieindex'], \
        delete=False, tags=primer_tags_seqs, \
        tmThreshold=config['design']['mispriming']['minimaltm'], \
        endMatch=config['design']['mispriming']['identity3prime'])  # places in genome

    # pair primers (by name or by primerset) MAKE COPIES!!!!
    pairs = {}
    for p in primers:
        setnames = primersets[p.name] \
            if p.name in primersets.keys() and len(primersets[p.name])>0 \
            else [ parsePrimerName(p.name)[0] ]
        for setname in setnames:
            try:
                pairs[setname]
            except KeyError:
                try:
                    pairs[setname] = PrimerPair([None,None],name=setname)
                except:
                    print >> sys.stderr, '>>',primersets[p.name], '|', p.name, '|', setnames, '<'
                    raise
            except:
                raise
            # get primer orientation (might be wrong if guesses from name, will correct after)
            ## this basically just makes sure primers get paired (one fwd, one reverse)
            reverse = p.targetposition.reverse if p.targetposition else parsePrimerName(p.name)[1] < 0
            try:
                if reverse and pairs[setname][1] is None:
                    pairs[setname][1] = deepcopy(p)
                else:
                    if pairs[setname][0] is None:
                        pairs[setname][0] = deepcopy(p)
                    else:
                        assert pairs[setname][1] is None
                        pairs[setname][1] = deepcopy(p)
            except:
                print >> sys.stderr, "ERROR: Primer pair strand conflict?"
                print >> sys.stderr, "PRIMER0", pairs[setname][0]
                print >> sys.stderr, "PRIMER1", pairs[setname][1]
                print >> sys.stderr, "REVERSE", reverse
                print >> sys.stderr, "SETNAME", setname
                print >> sys.stderr, "PRIMER", p.name, parsePrimerName(p.name)
                print >> sys.stderr, "PAIRS", pairs[setname]
                raise

    # check if any unpaired primers
    for k,v in pairs.items():
        if not all(v):
            print >> sys.stderr, "WARNING: primer set %s is incomplete and skipped" % k
            del pairs[k]
    # prune ranks in primer3 mode (renames pair)
    if primer3:
        for p in pairs.values():
            assert p[0].targetposition and p[1].targetposition  # make sure target postiions are set
            p.pruneRanks()
        validPairs = pairs.values()
    else:
        # guess target if not set
        validPairs = []
        print >> sys.stderr, 'Identifying correct amplicons for unplaced primer pairs...'
        for p in pairs.values():
            if not p[0].targetposition or not p[1].targetposition:
                # find primer pair amplicons of the maximum import size
                amplicons = p.amplicons(config['import']['ampliconsize'],autoreverse=True)
                if amplicons:
                    shortest = sorted(amplicons,key=lambda x: len(x[2]))[0]  # sort amplicons by size
                    if len(amplicons)>1:
                        print >> sys.stderr, 'WARNING: multiple amplicons for {}. Assuming shortest ({}bp) is correct.'.format(p.name,str(len(shortest[2])))
                    p[0].targetposition = shortest[0]  # m
                    p[1].targetposition = shortest[1]  # n
                    validPairs.append(p)
                elif primer3:
                    # if primer comes from primer3, then do not attempt deep amplicon search
                    print >> sys.stderr, 'WARNING: Primer set {} does not produce a well-sized, unique amplicon ({},{})'.format(p.name,len(p[0].loci),len(p[1].loci))
                else:
                    # try to find amplicon by sequence matching (locus+-ampliconsize)
                    #   if no amplicons from genome mapping with sufficient Tm
                    # --------------------------------------------------------
                    
                    # get new loci (one round)
                    refGenome = Genome(config['design']['genome'])
                    newLoci = [[],[]]
                    for mapped, query in [[0,1],[1,0]]:
                        for l in p[mapped].loci:
                            newLoci[query] += refGenome.primerMatch(l,p[query].seq,config['import']['ampliconsize'])

                    # add new loci
                    if newLoci[0] or newLoci[1]:
                        for i,loc in enumerate(newLoci):
                            p[i].loci += loc
                            p[i].loci = list(set(p[i].loci))  # remove redundancy
                    elif keepall:
                        validPairs.append(p)
                        continue
                    else:
                        print >> sys.stderr, 'WARNING: {} is not specific and not imported ({},{})'.format(p.name,len(p[0].loci),len(p[1].loci))
                        continue
                    
                    # infer new amplicons and store
                    amplicons = p.amplicons(config['import']['ampliconsize'],autoreverse=True)
                    if amplicons:
                        p[0].targetposition = amplicons[0][0]  # m
                        p[1].targetposition = amplicons[0][1]  # n
                        validPairs.append(p)
                    elif keepall:
                        validPairs.append(p)
                    else:
                        print >> sys.stderr, '\n'.join([ "-> "+str(l) for l in p[0].loci])
                        print >> sys.stderr, '\n'.join([ "<- "+str(l) for l in p[1].loci])
                        print >> sys.stderr, 'WARNING: Primer set {} has no valid amplicons ({},{})'.format(p.name,len(p[0].loci),len(p[1].loci))
            else:
                validPairs.append(p)
    return validPairs


'''checks (mispriming, amplicons, snpcheck) primerpairs and generates simple report'''
def checkPrimerPairs(pairs, db, config):
    pairs_passed = defaultdict(list)  # found/designed primer pairs (from database or design)

    # create report (primername -> result) and result array
    report = defaultdict(list)
    passed_primer_pairs, failed_primer_pairs = [], []

    #  load blacklist
    blacklist = db.blacklist() if db else []
    try:
        blacklist += pickle.load(open(config['blacklistcache'],'rb'))
    except:
        print >> sys.stderr, 'Could not read blacklist cache, check permissions'
        print >> sys.stderr, os.getcwd(), config['blacklistcache']
    
    # filter primer pairs
    progress = Progressbar(len(pairs),'Validating')
    for i, pair in enumerate(pairs):
        sys.stderr.write('\r'+progress.show(i))

        # check blacklist (will skip further checks)
        if pair.uniqueid() in blacklist:
            report[pair.name].append("blacklisted")
        # check targets (will skip further checks)
        elif not all([pair[0].checkTarget(), pair[1].checkTarget()]):
            report[pair.name].append("no_target")
        else:
            # run SNPcheck
            for p in pair:
                p.snpCheckPrimer(config['snpcheck']['common'], config['snpcheck']['maf'])
            # check designlimits (use import amplicon length limit)
            check_params = {'amplicons': [config['import']['ampliconsize'],True] }
            report[pair.name] += pair.check(config['designlimits'],check_params)
        # add passed primers
        if not report[pair.name]:
            passed_primer_pairs.append(pair)
        else:
            failed_primer_pairs.append(pair)
    sys.stderr.write('\r'+progress.show(len(pairs))+'\n')

    return passed_primer_pairs, failed_primer_pairs, report


'''get primers from intervals using new graph based heuristic'''
def getPrimers(intervals, db, design, config, tiers=[0], rename=None, compatible=False, graph=True):
    # create interval dict (missed)
    ivmissed = defaultdict(list)
    # create result dict (primers)
    ivpairs = defaultdict(list)  # found/designed primer pairs (from database or design)

    # load blacklist
    blacklist = db.blacklist() if db else []
    try:
        blacklist += pickle.load(open(config['blacklistcache'],'rb'))
    except:
        print >> sys.stderr, 'Could not read blacklist cache, check permissions'
        print >> sys.stderr, os.getcwd(), config['blacklistcache']

    # build gap primers and hash valid pairs
    if compatible:
        assert len(intervals)==2
        # get compatible pairs (no SNPcheck, just hash seqs)
        compatible = set()
        # build gap sequence
        gap = Interval(intervals[0].chrom, intervals[0].chromEnd, intervals[1].chromStart)
        # design primers
        progress = Progressbar(len(tiers),'Building compatibility list')
        for tier in tiers:
            sys.stderr.write('\r'+progress.show(tier))
            # get sequence
            maxFlank = max([ max(x) for x in config['design']['primer3'][tier]['PRIMER_PRODUCT_SIZE_RANGE'] ])
            p3 = Primer3(config['design']['genome'], gap.locus(), maxFlank)
            # alter configuration for gap pcr
            cfg = deepcopy(config['design']['primer3'][tier])
            # redefine PRIMER_PRODUCT_SIZE_RANGE
            cfg['PRIMER_PRODUCT_SIZE_RANGE'] = [ [x[0]+len(gap), x[1]+len(gap) ] for x in cfg['PRIMER_PRODUCT_SIZE_RANGE']]
            # redefine primer count (Get 2x more for compatibiliy pairs as they are cheap to design)
            cfg['PRIMER_NUM_RETURN'] *= 2
            p3.design('gap-PCR', cfg)
            if p3.pairs:
                for p in p3.pairs:
                    compatible.add(seqhash(p[0].seq, p[1].seq))
        sys.stderr.write('\r'+progress.show(len(tiers))+'\n')

    # primer searching in database by default (tier0)
    if db:
        progress = Progressbar(len(intervals),'Querying database')
        for i, iv in enumerate(intervals):
            sys.stderr.write('\r'+progress.show(i))
            pp = db.query(iv, True, **config['ordersheet'])
            primerpairs, missed = iv.ampliconPath(pp, config['tiling']['flank'])
            # print '\n', iv.group, '>>', [ m.name for m in missed ] 
            ivpairs[iv] = primerpairs
            if missed:
                ivmissed[iv] = missed
        sys.stderr.write('\r'+progress.show(len(intervals))+'\n')
        # print query count
        print >> sys.stderr, 'Found primers for {:d} out of {:d} intervals in database'.format(len([ iv for iv in intervals if ivpairs[iv]]), len(intervals))

    # designing
    if design:
        for tier in tiers:
            # skip step if no missing intervals left
            if not any(ivmissed.values()):
                break
            # get missed intervals
            print >> sys.stderr, "\n*** Round #{} ({} intervals) ***".format(tier+1, len(ivmissed))
            
            # determine design slice (interval+max amplicon length)
            try:
                designIntervalOversize = max([ max(x) for x in config['design']['primer3'][tier]['PRIMER_PRODUCT_SIZE_RANGE'] ])
            except:
                print >> sys.stderr, "WARNING: could not determine maximum amplicon size, default setting applied"
                designIntervalOversize = 2000
            
            # design missing intervals with Primer3
            designedPairs = defaultdict(list)
            progress = Progressbar(len(ivmissed),'Designing primers')
            subinterval_mappings = {}
            for i,iv in enumerate(ivmissed.keys()):
                sys.stderr.write('\r'+progress.show(i))
                for miv in ivmissed[iv]:
                    # tile interval (determine design intervals)
                    divs = [ miv ]
                    if len(miv)>config['tiling']['maxlen'] and not iv.isCombined():
                        divs = miv.tile(config['tiling']['splitlen'], config['tiling']['overlap'])
                    # design
                    for div in divs:
                        subinterval_mappings[div.name] = iv
                        p3 = Primer3(config['design']['genome'], div.locus(), designIntervalOversize)
                        p3.design(div.name, config['design']['primer3'][tier])
                        if p3.pairs:
                            designedPairs[iv] += p3.pairs
            sys.stderr.write('\r'+progress.show(len(ivmissed))+'\n')

            # processing and importing
            if designedPairs:
                # get all previously designed primer ids (to filter out duplicates)
                existing_primers = set()
                for pairs in ivpairs.values():
                    for pair in pairs:
                        existing_primers.add(pair.uniqueid())

                ## import designed primer pairs (place on genome and get amplicons)
                with tempfile.NamedTemporaryFile(suffix='.fa',prefix="primers_",delete=False) as fh:
                    for iv in designedPairs.keys():
                        for pairnumber, pair in enumerate(designedPairs[iv]):
                            strand = ['rev','fwd'] if iv.strand < 0 else ['fwd','rev'] 
                            for i, primer in enumerate(pair):
                                print >> fh, primer.fasta('_'.join([ pair.name, strand[i] ]))
                pairs = importPrimerPairs(fh.name, config, primer3=True)
                os.unlink(fh.name)  # remove fasta file

                ## Remove non-specific and blacklisted primer pairs
                specificPrimerPairs = []
                blacklisted = 0
                for i, pair in enumerate(pairs):
                    if pair.uniqueid() in blacklist:
                        blacklisted += 1
                    elif all([pair[0].checkTarget(), pair[1].checkTarget()]):
                        specificPrimerPairs.append(pair)
                if blacklisted:
                    sys.stderr.write('Removed '+str(blacklisted)+' blacklisted primer pairs\n')
                if len(pairs) != len(specificPrimerPairs):
                    sys.stderr.write('Removed '+str(len(pairs)-len(specificPrimerPairs))+' non-specific primer pairs\n')
                pairs = specificPrimerPairs

                # dedup primer pair
                # SNPcheck
                # meet designlimit or blacklist
                # bin primers for selection and SNPcheck
                primer_bins = defaultdict(list)
                progress = Progressbar(len(pairs),'SNPcheck')
                failCount = 0
                for i,pair in enumerate(pairs):
                    sys.stderr.write('\r'+progress.show(i))
                    if pair.uniqueid() not in existing_primers:
                        for j, primer in enumerate(pair):
                            # SNPcheck
                            primer.snpCheckPrimer(config['snpcheck']['common'],
                                config['snpcheck']['maf'])
                        # check designlimits
                        if not pair.check(config['designlimits']):
                            # rename (for variant based naming which is too rich)
                            if rename:
                                pair.rename(rename)
                            # save primer pair to bin
                            existing_primers.add(pair.uniqueid())
                            primer_bins[pair.name].append(pair)
                        else:
                            # add to blacklist if design limits fail
                            blacklist.append(pair.uniqueid())
                            failCount += 1
                sys.stderr.write('\r'+progress.show(len(pairs))+'\n')
                if failCount:
                    print >> sys.stderr, 'INFO: {:2d} pairs violated design limits and were blacklisted ({} total)'.format(failCount,str(len(blacklist)))

                for primer_bin, pairs in primer_bins.items():
                    # get corresponding interval
                    iv = subinterval_mappings.get(primer_bin)
                    # get best pair(s)
                    bestPairs = []
                    for i, p in enumerate(sorted(pairs)):
                        if i == config['report']['pairs']:
                            break  # only report number of primer pairs requested
                        # log primer design (0 if from database)
                        if p.designrank() >= 0:
                            p.log(config['logfile'])
                        # save to primer table
                        bestPairs.append(p)
                    # pick best path
                    path, missed = iv.ampliconPath(ivpairs[iv] + bestPairs, config['tiling']['flank'])
                    ivmissed[iv] = missed
                    ivpairs[iv] = path

                print >> sys.stderr, 'Design status:', [ len(ivmissed[iv]) for iv in intervals ], '->', [ len(ivpairs[iv]) for iv in intervals ]

    print >> sys.stderr, '\n'

    # save blacklist cache
    if design:
        try:
            pickle.dump(list(set(blacklist)),open(config['blacklistcache'],'wb'))
        except:
            print >> sys.stderr, 'Could not write to blacklist cache, check permissions'
            print >> sys.stderr, os.getcwd(), config['blacklistcache']

    # print primer pair count and build database table
    print >> sys.stderr, '-'*45
    print >> sys.stderr, '| {:<16} | {:6} | {:4} | {:<6} |'.format('INTERVAL', 'LENGTH', 'AMPS', 'STATUS')
    print >> sys.stderr, '-'*45
    for iv,p in sorted(ivpairs.items(), key=lambda x: x[0].name):
        print >> sys.stderr, '| {:<16} | {:6} | {:4} | {:<6} |'.format(\
            unquote(iv.name), len(iv), len(p), "FAIL" if not ivpairs[iv] and ivmissed[iv] else \
                "PART" if ivmissed[iv] else "OK")
    print >> sys.stderr, '-'*45


    # select primer pairs
    primerTable = []  # primer table (text)
    primerVariants = defaultdict(list)  # primerpair -> intervalnames/variants dict
    missedIntervals = []  # list of missed intervals/variants
    if compatible:
        # make pairs and exclude all pairings not in compatibility list score by geometric mean of 1based rank
        rankedPairs = []
        for l, left in enumerate(sorted(ivpairs[intervals[0]])):
            for r, rite in enumerate(sorted(ivpairs[intervals[1]])):
                if seqhash(left[0].seq, rite[1].seq) in compatible:
                    rankedPairs.append((((l+1)*(r+1)) ** (1.0/2), max(l, r), left, rite))
        if rankedPairs:
            rankedPairs.sort()  # sort ranked paired primerpairs
            primerTable.append([unquote(intervals[0].name)] + str(rankedPairs[0][2]).split('\t'))
            primerTable.append([unquote(intervals[1].name)] + str(rankedPairs[0][3]).split('\t'))
            primerVariants[rankedPairs[0][2]].append(intervals[0])
            primerVariants[rankedPairs[0][3]].append(intervals[1])
            # add gap interval
            gapInterval = Interval(intervals[0].chrom, intervals[0].chromStart, intervals[1].chromEnd)
            gapPrimerPair = PrimerPair([rankedPairs[0][2][0], rankedPairs[0][3][1]], name='gap_'+gapInterval.name )
            primerTable.append([unquote(gapInterval.name)] + str(gapPrimerPair).split('\t'))
        else:
            missedIntervals = intervals
    else:
        # select by best pairs independently (always print database primers)
        for iv in sorted(intervals):
            # store missed intervals (identify slices)
            if ivmissed[iv]:
                for miv in ivmissed[iv]:
                    if iv!=miv:
                        miv.name = '{}|{}:{}-{}'.format(miv.group, miv.chrom, miv.chromStart, miv.chromEnd)
                    missedIntervals.append(miv)

            #renaming logic (increments and offsets)
            slice_number_offset = 0
            for i, pair in enumerate(sorted(ivpairs[iv])):
                # rename
                slice_number = i+1 if not pair.reverse else len(ivpairs[iv])-i
                if len(ivpairs[iv])>1 and pair.designrank() >= 0:
                    # rename if necessary
                    newname = '_'.join(map(str,[iv.group,slice_number+slice_number_offset]))
                    while newname in [ x.name for x in ivpairs[iv] if x.designrank() < 0 ]:
                        slice_number_offset += 1
                        newname = '_'.join(map(str,[iv.group,slice_number+slice_number_offset]))
                    pair.rename(newname)
                    # log primer design (0 if from database)
                    pair.log(config['logfile'])
                # save result (with interval names)
                primerVariants[pair].append(iv)
                # save to primer table
                primerTable.append([unquote(iv.name)] + str(pair).split('\t'))
    # update primer pairs with covered variants
    for pp, v in primerVariants.items():
        pp.variants = v
    return primerTable, primerVariants.keys(), missedIntervals

# ==============================================================================
# === convenience functions for webservice =====================================
# ==============================================================================

# query database / design primer for VCF,BED,GenePred or interval
def zippyPrimerQuery(config, targets, design=True, outfile=None, db=None, store=False, tiers=[0], gap=None):
    intervals = readTargets(targets, config)  # get intervals from file or commandline
    if gap:  # gap PCR primers
        try:
            assert len(intervals)==1
            intervals += readTargets(gap, config)  # get interval of second breakpoint
            assert len(set([i.chrom for i in intervals] ))
        except AssertionError:
            print >> sys.stderr, "ERROR: gap-PCR primers can only be designed for a single pair of breakpoint intervals on the same chromosome!"
        except:
            raise
    primerTable, resultList, missedIntervals = getPrimers(intervals,db,design,config,tiers,compatible=True if gap else False)
    ## print primerTable
    if outfile:
        with open(outfile,'w') as fh:
            print >> fh, '\n'.join([ '\t'.join(map(str,l)) for l in primerTable ])
            print >> fh, '\n'.join([ '\t'.join([mi.name,'NA']+['']*12) for mi in missedIntervals ])
    else:
        print >> sys.stdout, '\n'.join([ '\t'.join(map(str,l)) for l in primerTable ])
    ## print and store primer pairs
    if store and db and design:
        db.addPairs(resultList, config['conditions'])  # store pairs in database (assume they are correctly designed as mispriming is ignored and capped at 1000)
        print >> sys.stderr, "Primer designs stored in database"
    return primerTable, resultList, missedIntervals

# batch query primer database and create confirmation worksheet
def zippyBatchQuery(config, targets, design=True, outfile=None, db=None, predesign=False, tiers=[0]):
    # read targets from first file and additional files
    if not isinstance(targets,list):
        targets = [ targets ]
    # load query files
    print >> sys.stderr, 'Reading batch file {}...'.format(targets[0])
    sampleVariants, genes, fullgenes = readBatch(targets[0], config, database=db)
    for t in range(1,len(targets)): # read additional files
        print >> sys.stderr, 'Reading additional file {}...'.format(targets[t])
        sv, g, f = readBatch(targets[t], config, database=db)
        # amend target regions
        for k,v in sv.items():
            if k in sampleVariants.keys():
                sampleVariants[k] += v
            else:
                sampleVariants[k] = v
        genes = list(set(genes) | set(g))
        fullgenes = list(set(fullgenes) | set(f))

    print >> sys.stderr, '\n'.join([ '{:<20} - {:>2d}'.format(sample,len(variants)) \
        for sample,variants in sorted(sampleVariants.items(),key=lambda x: x[0]) ])

    # predesign
    if predesign and db and genes:
        # check what variants are not covered
        variants = [v for pv in sampleVariants.values() for v in pv]  # get all variants in batch
        selectedgeneexons = list(set(genes) - set(fullgenes))
        # get variants with no overlapping amplicon -> get variants which need new primer designs
        intervals = IntervalList([], source='GenePred')
        # get variants that need a new primer design 
        designVariants = []
        for var in variants:
            pp = db.query(var,True)
            _, missed = var.ampliconPath(pp, flank=config['tiling']['flank'])
            if missed:
                designVariants.append(var)
        if designVariants:
            print >> sys.stderr, "Designing exon primers for {} variants..".format(str(len(designVariants)))
            with open(config['design']['annotation']) as fh:
                for iv in GenePred(fh,getgenes=selectedgeneexons,**config['tiling']):  # get intervals from file or commandline
                    found = False
                    for dv in designVariants:
                        if not found and iv.overlap(dv):
                            intervals.append(iv)
                            found = True
                        if found: break
                    if found: break
        # add full genes
        if fullgenes:
            with open(config['design']['annotation']) as fh:
                intervals += GenePred(fh,getgenes=fullgenes,**config['tiling'])
        # predesign and store
        if intervals:
            primerTable, resultList, missedIntervals = getPrimers(intervals,db,predesign,config,tiers)
            if db:
                db.addPairs(resultList, config['conditions'])  # store pairs in database (assume they are correctly designed as mispriming is ignored and capped at 1000)
        # reload query files
        print >> sys.stderr, 'Updating query table...'
        sampleVariants = readBatch(targets[0], config, database=db)[0]
        for t in range(1,len(targets)): # read additional files
            sv = readBatch(targets[t], config, database=db)[0]
            # amend target regions
            for k,v in sv.items():
                if k in sampleVariants.keys():
                    sampleVariants[k] += v
                else:
                    sampleVariants[k] = v

    # for each sample design
    primerTableConcat = []
    allMissedIntervals = {}
    missedIntervalNames = []
    tests = [] # all tests
    tests_long = []
    tests_std = []
    for sample, intervals in sorted(sampleVariants.items(),key=lambda x: x[0]):
        print >> sys.stderr, "Getting primers for {} variants in sample {}".format(len(intervals),sample)
        # get/design primers
        #print >> sys.stderr, intervals
        primerTable, resultList, missedIntervals = getPrimers(intervals,db,design,config,tiers,rename=shortHumanReadable)
        if missedIntervals:
            allMissedIntervals[sample] = missedIntervals
            missedIntervalNames += [ i.name for i in missedIntervals ]
        # store result list
        primerTableConcat += [ [sample]+l for l in primerTable ]
        # store primers
        if db:
            db.addPairs(resultList, config['conditions'])  # store pairs in database (assume they are correctly designed as mispriming is ignored and capped at 1000)
        # Build Tests
        for primerpair in resultList:
            tests.append(Test(primerpair,sample))
            # print(resultList)
            if primerpair.cond == 'LB':
                tests_long.append(Test(primerpair,sample))
            elif primerpair.cond == 'STD':
                tests_std.append(Test(primerpair,sample))
            else:
                print('failed to add {} to a batch'.format(primerpair))

    ## print primerTable
    writtenFiles = []
    if not outfile:
        print >> sys.stdout, '\n'.join([ '\t'.join(l) for l in primerTableConcat ])
    else:
        worksheetName = '' if os.path.basename(targets[0]).startswith(os.path.basename(outfile)) else os.path.basename(outfile)
        # output data
        writtenFiles.append(outfile+'.txt')
        print >> sys.stderr, "Writing results to {}...".format(writtenFiles[-1])
        with open(writtenFiles[-1],'w') as fh:
            print >> fh, '\n'.join([ '\t'.join(l) for l in primerTableConcat ])
        # Primer Test Worksheet
        primerTests = [ t for t in tests if not any(t.primerpairobject.locations()) ]
        if primerTests:
            writtenFiles.append(outfile+'.primertest.pdf')
            print >> sys.stderr, "Writing Test Worksheet to {}...".format(writtenFiles[-1])
            ws = Worksheet(primerTests,name="Primer Test PCR")  # load worksheet
            ws.addControls(control='Normal')  # add positive controls
            ws.fillPlates(size=config['report']['platesize'],randomize=True,\
                includeSamples=False, includeControls=True)  # only include controls
            ws.createWorkSheet(writtenFiles[-1], primertest=True, worklist=worksheetName, **config['report'])
            # robot csv
            writtenFiles.append(outfile+'.primertest.csv')
            print >> sys.stderr, "Writing Test CSV to {}...".format(writtenFiles[-1])
            ws.robotCsv(writtenFiles[-1], sep=',')
            # order list
            writtenFiles.append(outfile+'.ordersheet.csv')
            print >> sys.stderr, "Writing primer order list to {}...".format(writtenFiles[-1])
            ws.orderCsv(writtenFiles[-1], config=config['ordersheet'])
        # Batch PCR worksheets long
        if tests_long:
            writtenFiles.append(outfile+'_long.pdf')
            print >> sys.stderr, "Writing long batch worksheet to {}...".format(writtenFiles[-1])
            ws_long = Worksheet(tests_long,name='Variant Confirmations')  # load worksheet
            ws_long.addControls()  # add controls
            ws_long.fillPlates(size=config['report']['platesize'],randomize=True)
            ws_long.createWorkSheet(writtenFiles[-1], worklist=worksheetName+'_LONG', **config['l_report'])
            ws_long.tubeLabels()
            # robot csv
            writtenFiles.append(outfile+'_long.csv')
            print >> sys.stderr, "Writing long batch robot CSV to {}...".format(writtenFiles[-1])
            ws_long.robotCsv(writtenFiles[-1], sep=',')
            # tube Labels
            writtenFiles.append(outfile+'_long.tubelabels.txt')
            print >> sys.stderr, "Writing long batch tube labels to {}...".format(writtenFiles[-1])
            ws_long.tubeLabels(writtenFiles[-1],tags=config['ordersheet']['sequencetags'])
            # Batch PCR worksheet std
        if tests_std:
            writtenFiles.append(outfile+'.pdf')
            print >> sys.stderr, "Writing worksheet to {}...".format(writtenFiles[-1])
            ws_std = Worksheet(tests_std,name='Variant Confirmations')
            ws_std.addControls()
            ws_std.fillPlates(size=config['report']['platesize'],randomize=True)
            ws_std.createWorkSheet(writtenFiles[-1], worklist=worksheetName, **config['report'])
            # validate primer tube labels (checks for hash substring collisions)
            ws_std.tubeLabels()
            # robot csv
            writtenFiles.append(outfile+'.csv')
            print >> sys.stderr, "Writing robot CSV to {}...".format(writtenFiles[-1])
            ws_std.robotCsv(writtenFiles[-1], sep=',')
            # writtenFiles.append(outfile+'.long.csv')
            # print >> sys.stderr, "Writing long batch robot CSV to {}...".format(writtenFiles[-1])
            # ws_long.robotCsv(writtenFiles[-1], sep=',')
            # tube labels
            writtenFiles.append(outfile+'.tubelabels.txt')
            print >> sys.stderr, "Writing tube labels to {}...".format(writtenFiles[-1])
            ws_std.tubeLabels(writtenFiles[-1],tags=config['ordersheet']['sequencetags'])
            #writtenFiles.append(outfile+'.long.tubelabels.txt')
            #print >> sys.stderr, "Writing long batch tube labels to {}...".format(writtenFiles[-1])
            #ws_long.tubeLabels(writtenFiles[-1],tags=config['ordersheet']['sequencetags'])
        # write missed intervals
        missedIntervalNames = []
        if allMissedIntervals:
            writtenFiles.append(outfile+'.failed.txt')
            print >> sys.stderr, "Writing failed designs {}...".format(writtenFiles[-1])
            with open(writtenFiles[-1],'w') as fh:
                print >> fh, '\t'.join(['sample','variant'])
                for sample, missed in sorted(allMissedIntervals.items()):
                    print >> fh, '\n'.join([ '\t'.join([sample,unquote(i.name)]) for i in missed ])
    return writtenFiles, sorted(list(set(missedIntervalNames)))

def validateAndImport(config, target, validate, store, db):
    pairs = importPrimerPairs(target, config, primer3=False, keepall=validate)  # import and locate primer pairs
    if validate:
        print >> sys.stderr, "Validating {} primer pairs...".format(len(pairs))
        pairs, failed_pairs, report = checkPrimerPairs(pairs, db, config)
        # print report
        failed_pair_count = len(failed_pairs)
        if failed_pair_count:
            print >> sys.stderr, 'INFO: {:d} pairs violated design limits, yield no amplicon, or are blacklisted (of {:d} total)'.format(failed_pair_count,len(pairs))
            for primer_name, fails in report.items():
                result = 'PASS' if not fails else ', '.join(fails)
                print >> sys.stderr, "{:<40} {}".format(primer_name,result)
        # create summry stat 
        report_counts = Counter()
        for p,r in report.items():
            for t in r:
                report_counts[t] +=1
        report_counts['PASS'] = len(pairs)
        # store primers
        if store:
            db.addPairs(pairs, config['conditions'])
        # return stat and failed pairs
        return report_counts, failed_pairs
    # no validation
    if store:
        db.addPairs(pairs, config['conditions'])  # store pairs in database (assume they are correctly designed as mispriming is ignored and capped at 1000)
        sys.stderr.write('Added {} primer pairs to database without validation\n'.format(len(pairs)))
    else:
        sys.stderr.write('Nothing to do :(\n')
    return {}, []

# update storage location for primer
def updateLocation(primername, location, database, force=False):
    occupied = database.getLocation(location)
    if not occupied or force:
        if database.storePrimer(primername,location,force):
            print >> sys.stderr, '%s location sucessfully set to %s' % (primername, str(location))
            return ('success', location)
        else:
            print >> sys.stderr, 'WARNING: %s location update to %s failed' % (primername, str(location))
            return ('fail', location)
    else:
        print >> sys.stderr, 'Location already occupied by %s' % (' and '.join(occupied))
        return ('occupied', occupied)

# search primer pair by name substring matching
def searchByName(searchName, db):
    primersInDB = db.query(searchName)
    print >> sys.stderr, 'Found {} primer pairs with string "{}"'.format(len(primersInDB),searchName)
    return primersInDB

# update name of primer in database
def updatePrimerName(primerName, newName, db):
    nameUpdate = db.updateName(primerName, newName)
    if nameUpdate:
        print >> sys.stderr, 'Primer %s renamed %s' % (primerName, newName)
        return nameUpdate
    else:
        print >> sys.stderr, 'Primer renaming failed'
        return nameUpdate

# update name of primer pair in database
def updatePrimerPairName(pairName, newName, db):
    nameUpdate = db.updatePairName(pairName, newName)
    if nameUpdate:
        print >> sys.stderr, 'Pair %s renamed %s' % (pairName, newName)
        return nameUpdate
    else:
        print >> sys.stderr, 'Pair renaming failed'
        return nameUpdate

# blacklist primer pair in database
def blacklistPair(pairname, db):
    blacklisted = db.blacklist(pairname)
    print >> sys.stderr, '%s added to blacklist' % (blacklisted,)
    return blacklisted

# just delete primer pair in database (skip addition to blacklist)
def deletePair(pairname, db):
    deleted = db.blacklist(pairname,True)
    print >> sys.stderr, '%s has been deleted' % (deleted,)
    return deleted

def readprimerlocations(locationfile):
    header = []
    updateList = []
    with open(locationfile) as csvfile:
        readfile = csv.reader(csvfile, delimiter=',')
        for line in readfile:
            if not header:
                header = line
            elif len(line)<3:
                pass  # empty line (CR/LF)
            else:
                try:
                    row = dict(zip(header,line))
                    updateList.append([row['PrimerName'], Location(row['Box'].strip('Bbox'), row['Well'])])
                except:
                    raise
                    raise Exception('InputFormatError')
    return updateList

# ==============================================================================
# === CLI ======================================================================
# ==============================================================================
def main():
    from zippylib import ascii_encode_dict
    from zippylib import banner

    print >> sys.stderr, banner(__version__)

    parser = ArgumentParser(prog="zippy.py", description= 'Zippy - Primer design and database')
    parser.add_argument('--version', action='version', version='%(prog)s '+__version__+'('+__status__+')',\
        help="Displays version")

    #   configuration files
    global_group = parser.add_argument_group('Global options')
    global_group.add_argument("-c", dest="config", default='zippy.json',metavar="JSON_FILE", \
        help="configuration file [zippy.json]")
    global_group.add_argument("--tiers", dest="tiers", default='0,1,2', \
        help="Allowed design tiers (0,1,...,n)")

    # run modes
    subparsers = parser.add_subparsers(help='Help for subcommand')

    ## add primers
    parser_add = subparsers.add_parser('add', help='Add previously designed primers to database')
    parser_add.add_argument("primers", default=None, metavar="FASTA/TAB", \
        help="Primers or locations to add to database")
    parser_add.add_argument("--check", dest="check", default=False, action="store_true", \
        help="Check primers against designlimits")
    parser_add.add_argument("--dryrun", dest="store", default=True, action="store_false", \
        help="Dry run (does not store primers)")
    parser_add.add_argument("-F", dest="outfile", default=None, type=str, \
        help="Output failed imports to file")
    parser_add.set_defaults(which='add')

    ## retrieve
    parser_retrieve = subparsers.add_parser('get', help='Get/design primers')
    parser_retrieve.add_argument("targets", default=None, metavar="VCF/BED/Interval/GenePred", \
        help="File with intervals of interest or CHR:START-END (mandatory for gap-PCR)")
    parser_retrieve.add_argument("--design", dest="design", default=False, action="store_true", \
        help="Design primers if not in database")
    parser_retrieve.add_argument("--gap", dest="gap", default=None, metavar="CHR:START-END", \
        help="Second break point for gap-PCR")
    parser_retrieve.add_argument("--tiers", dest="tiers", default='0,1,2', \
        help="Allowed design tiers (0,1,...,n)")
    parser_retrieve.add_argument("--nostore", dest="store", default=True, action='store_false', \
        help="Do not store result in database")
    parser_retrieve.add_argument("--outfile", dest="outfile", default='', type=str, \
        help="Output file name")
    parser_retrieve.set_defaults(which='get')

    ## query database for primers by name
    parser_query = subparsers.add_parser('query', help='Query database for primers with specified sub-string in name')
    parser_query.add_argument("subString", default=None, metavar="Sub-string within name", \
        help="String found within primer name")
    parser_query.set_defaults(which='query')

    ## batch
    parser_batch = subparsers.add_parser('batch', help='Batch design primers for sample list')
    parser_batch.add_argument("targets", default=None, metavar="FILE1,FILE2,...", \
        help="SNPpy result table(s) ")
    parser_batch.add_argument("--predesign", dest="predesign", default=False, action="store_true", \
        help="Design primers for all genes in batch")
    parser_batch.add_argument("--nodesign", dest="design", default=True, action="store_false", \
        help="Skip primer design if not in database")
    parser_batch.add_argument("--tiers", dest="tiers", default='0,1,2', \
        help="Allowed design tiers (0,1,...,n)")
    parser_batch.add_argument("--outfile", dest="outfile", default='', type=str, \
        help="Create worksheet PDF, order and robot CSV")
    parser_batch.set_defaults(which='batch')

    ## update
    parser_update = subparsers.add_parser('update', help='Update status and location of primers')
    parser_update.add_argument('-l', dest="location", nargs=3, \
        help="Update storage location of primer pair (primerid vessel well)")
    parser_update.add_argument('-t', dest="locationtable", \
        help="Batch update storage locations from TSV (primerid vessel well)")
    parser_update.add_argument("--force", dest="force", default=False, action='store_true', \
        help="Force Location update (resets existing)")
    parser_update.add_argument('-b', dest="blacklist", type=str, \
        help="Blacklist primer")
    parser_update.set_defaults(which='update')

    ## dump specific datasets from database
    parser_dump = subparsers.add_parser('dump', help='Data dump')
    parser_dump.add_argument("--amplicons", dest="amplicons", default='', type=str, \
        help="Retrieve amplicons of given size (eg. 10-1000)")
    parser_dump.add_argument("--ordersheet", dest="ordersheet", default=False, action="store_true", \
        help="IDT order sheet (primer pairs with no status marker)")
    parser_dump.add_argument("--locations", dest="locations", default=False, action="store_true", \
        help="Primer locations")
    parser_dump.add_argument("--redundancies", dest="redundancies", default=False, action="store_true", \
        help="Primers with same sequence and tag")
    parser_dump.add_argument("--table", dest="table", default=False, action="store_true", \
        help="Primer pair table with locations")
    parser_dump.add_argument("--outfile", dest="outfile", default='', type=str, \
        help="Output file name")
    parser_dump.set_defaults(which='dump')

    options = parser.parse_args()

    # read config and open database
    with open(options.config) as conf:
        config = json.load(conf, object_hook=ascii_encode_dict)
    here = config['primerbed'] if 'primerbed' in config.keys() and config['primerbed'] else None
    db = PrimerDB(config['database'],dump=here)

    if options.which=='add':  # read primers and add to database
        # import primer pairs
        if options.primers.split('.')[-1].startswith('fa'):
            report, failed_pairs = validateAndImport(config, options.primers, options.check, options.store, db)
            if failed_pairs:
                if options.outfile is None:
                    print >> sys.stderr, "FAILED IMPORTS"
                    for primerpair in failed_pairs:
                        print >> sys.stderr, primerpair.display()
                else:
                    with open(options.outfile, 'w') as fh:
                        for primerpair in failed_pairs:
                            print >> fh, primerpair.display('# ')
                            print >> fh, primerpair.fasta()
            print >> sys.stderr, report

        # store locations if table
        if not options.primers.split('.')[-1].startswith('fa'):  # assume table format
            locations = importPrimerLocations(options.primers)
            print >> sys.stderr, "Setting Primer locations..."
            db.addLocations(*locations.items())
            sys.stderr.write('Added {} locations for imported primers\n'.format(len(locations)))
    elif options.which=='dump':  # data dump fucntions (`for bulk downloads`)
        if options.amplicons:
            try:
                l = options.amplicons.split('-')
                assert len(l)==2
                amplen = map(int,l)
            except (AssertionError, ValueError):
                raise ConfigError('must give amplicon size to retrieve')
            except:
                raise
            else:
                # get amplicons amplen
                data,colnames = db.dump('amplicons', size=amplen)
        elif options.ordersheet:
            data,colnames = db.dump('ordersheet', **config['ordersheet'])
        elif options.locations:
            data,colnames = db.dump('locations')
        elif options.table:
            data,colnames = db.dump('table')
        elif options.redundancies:
            data,colnames = db.getRedundantPrimers()
        else:
            print >> sys.stderr, "What to dump stranger?"
            sys.exit(1)
        # format data output
        if options.outfile:
            dump = Data(data,colnames)
            dump.writefile(options.outfile)  # sets format by file extension
        else:
            print '\t'.join(colnames)
            for row in data:
                print '\t'.join(map(str,row))
    elif options.which=='update':  #update location primer pairs are stored
        if options.location:
            primer, vessel, well = options.location
            updateLocation(primer, Location(vessel, well), db, options.force)
        if options.locationtable:
            updateList = readprimerlocations(options.locationtable)
            for item in updateList:  # [ Primer, Location ]
                updateLocation(item[0], item[1], db, options.force)
        if options.blacklist:
            print >> sys.stderr, 'BLACKLISTED PAIRS: {}'.format(','.join(db.blacklist(options.blacklist)))
            print >> sys.stderr, 'REMOVED ORPHANS:   {}'.format(','.join(db.removeOrphans()))
    elif options.which=='get':  # get primers for targets (BED/VCF or interval)
        zippyPrimerQuery(config, options.targets, options.design, options.outfile, \
            db, options.store, map(int,options.tiers.split(',')), options.gap)
    elif options.which=='batch':
        zippyBatchQuery(config, options.targets.split(','), options.design, options.outfile, \
            db, options.predesign, map(int,options.tiers.split(',')))
    elif options.which=='query':
        searchByName(options.subString, db)

if __name__=="__main__":
    main()
