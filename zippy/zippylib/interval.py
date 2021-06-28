#!/usr/bin/env python

__doc__=="""Interval Lists"""
__author__ = "David Brawand"
__license__ = "MIT"
__version__ = "2.5.0"
__maintainer__ = "David Brawand"
__email__ = "dbrawand@nhs.net"
__status__ = "Production"

import sys, os, re, ast
from math import ceil, sqrt
from hashlib import sha1
from collections import Counter
from copy import deepcopy
import networkx as nx

class Interval(object):
    def __init__(self,chrom,chromStart,chromEnd,name=None,reverse=None,sample=None,group=None):
        self.chrom = chrom
        self.chromStart = int(chromStart)
        self.chromEnd = int(chromEnd)
        assert self.chromStart <= self.chromEnd  # make sure its on the forward genomic strand
        self.name = name if name else chrom+':'+str(chromStart)+'-'+str(chromEnd)
        self.strand = 0 if reverse is None else -1 if reverse else 1
        self.sample = sample
        self.subintervals = IntervalList([])
        self._group = group  # the grouping name, used for tiling graph resolution
        return

    def midpoint(self):
        return int(self.chromStart + (self.chromEnd - self.chromStart)/2.0)

    def locus(self):
        '''returns interval of variant'''
        return ( self.chrom, self.chromStart, self.chromEnd )

    def __hash__(self):
        return hash(str(self))

    def __len__(self):
        return self.chromEnd - self.chromStart

    def __eq__(self,other):
        return hash(self) == hash(other)

    def __lt__(self,other):
        return (self.chrom, self.chromStart, self.chromEnd) < (other.chrom, other.chromStart, other.chromEnd)

    def __repr__(self):
        return "<Interval ("+self.name+") "+self.chrom+":"+str(self.chromStart)+'-'+str(self.chromEnd)+ \
            " ["+str(self.strand)+"] len:"+str(len(self))+">"

    def __str__(self):
        return "\t".join(map(str,[self.chrom, self.chromStart, self.chromEnd, self.name]))

    @property
    def group(self):
        return self._group or self.name
    @group.setter
    def group(self,g):
        self._group = g

    def isCombined(self):
        return True if re.match(r'[A-Z0-9]+_\d+\+\d+',self.name) else False

    def tile(self,i,o,suffix=True):  # interval, overlap
        stepping = i-o  # tile stepping
        extendedstart, extendedend = self.chromStart-o, self.chromEnd-stepping
        # get tile spans (and number of exons)
        tilespan = []
        for n,tilestart in enumerate(range(extendedstart, extendedend, stepping)):
            tileend = tilestart+i
            tilespan.append((tilestart,tileend))
        tiles = []
        for n,t in enumerate(tilespan):
            tilenumber = len(tilespan)-n if self.strand < 0 else n+1
            tiles.append(Interval(self.chrom,t[0],t[1],self.name+'_'+str(tilenumber) if suffix else None, self.strand < 0, group=self.group))
        return tiles

    def extend(self,flank):
        self.chromStart = self.chromStart-flank if flank <= self.chromStart else 0
        self.chromEnd = self.chromEnd+flank
        return self

    def overlap(self,other):  # also returnd bookended
        return self.chrom == other.chrom and \
            not (other.chromEnd < self.chromStart or other.chromStart > self.chromEnd)

    def merge(self,other,subintervals=False):
        if self.chrom == other.chrom and self.strand == other.strand:
            self.chromStart = other.chromStart if other.chromStart < self.chromStart else self.chromStart
            self.chromEnd = other.chromEnd if other.chromEnd > self.chromEnd else self.chromEnd
            self.name = self.name if other.name == self.name else self.name + '_' + other.name
            if subintervals and (self.subintervals or other.subintervals):
                self.subintervals += other.subintervals
                self.flattenSubintervals()

    def addSubintervals(self,add):
        for e in add:
            if e.chromStart < self.chromStart:
                self.chromStart = e.chromStart
            if e.chromEnd > self.chromEnd:
                self.chromEnd = e.chromEnd
            self.subintervals.append(e)
        self.subintervals.sort()

    def flattenSubintervals(self):
        if self.subintervals:
            self.subintervals.sort()
            merged = [ self.subintervals[0] ]
            for i in range(1,len(self.subintervals)):
                if merged[-1].overlap(self.subintervals[i]):
                    merged[-1].merge(self.subintervals[i])
                else:
                    merged.append(self.subintervals[i])
            self.subintervals = IntervalList(merged)
    
    def ampliconPath(self,primerPairs,flank):
        # create vertices (primer pairs) and edges (overlaps)import networkx as nx
        G = nx.Graph()
        start, end = None, 'z' # values ensure they are ordered at start and end (None,1,2,3,'z')
        for i, p in enumerate(primerPairs):
            # create edges
            p_target = p.sequencingTarget()
            if p_target:
                # match beginning and end
                if self.chromStart < (p_target[2]-flank) and (p_target[1]+flank) < self.chromStart:
                    G.add_edge(start,p)
                if self.chromEnd < (p_target[2]-flank) and (p_target[1]+flank) < self.chromEnd:
                    G.add_edge(end,p)
                # overlap other amplicons ()
                for j, q in enumerate(primerPairs[i:]):
                    if i == j:
                        continue
                    q_target = q.sequencingTarget()
                    if q_target and p_target[0] == q_target[0] and \
                        (p_target[2]-flank) > (q_target[1]+flank) and \
                            (p_target[1]+flank) < (q_target[2]-flank):
                        # overlaps
                        G.add_edge(p,q)

        '''finds best amplicon path (least nodes, longest length, most overlap, least overlap variation)'''
        def bestPath(graph):
            def orderNodes(node,x):
                if node == start:
                    return start
                elif node == end:
                    return end
                return node.sequencingTarget()[x]
            def stdev(data):
                n = len(data)
                mean = sum(data) / n
                var = sum((x - mean) ** 2 for x in data) / n
                std_dev = sqrt(var)
                return std_dev
            def bestSequence(path):
                ## longest path
                try:
                    path_len = path[-1].sequencingTarget()[2] - path[0].sequencingTarget()[1]
                except:
                    path_len = 0
                ## most overlapping path
                try:
                    ovp = list([path[i].sequencingTarget()[2] - path[i+1].sequencingTarget()[1] for i in range(len(path)-1) ])
                    path_minovp = min(ovp)
                    path_stdovp = stdev(ovp)
                    path_invstdovp = 1/path_stdovp if path_stdovp>0 else None
                except Exception as e:
                    path_minovp = 0
                    path_invstdovp = 0
                return (path_len, path_minovp, path_invstdovp) 

            graph_start = sorted(graph.nodes, key=lambda n: orderNodes(n,1))[0]
            graph_end = sorted(graph.nodes, key=lambda n: orderNodes(n,2))[-1]
            # get least node paths
            paths = list(nx.all_shortest_paths(graph, source=graph_start, target=graph_end))
            # remove start and end nodes
            amp_paths = map(lambda path: filter(lambda x: x is not start and x is not end, path), paths)
            # get longest sequenced
            sorted_paths = sorted(amp_paths, key=bestSequence)
            return sorted_paths[-1]

        # create subgraphs
        subgraphs = [G.subgraph(c).copy() for c in nx.connected_components(G)]
        
        # merge paths and get missedIntervals
        pathPairs = []
        for subgraph in subgraphs:
            # find best path
            path = bestPath(subgraph)
            pathPairs += path

        # create missed
        missedIntervals = self.subtractAll([ Interval(self.chrom, i.sequencingTarget()[1], i.sequencingTarget()[2]) \
            for i in pathPairs ])
        
        # return primer pairs that would match
        return pathPairs, missedIntervals


    def subtractAll(self, others):
        if not others:
            return [ self ]
        c = Counter()
        # change map
        for iv in others:
            if iv.chrom == self.chrom:
                c[max(self.chromStart,iv.chromStart)] += 1
                c[min(self.chromEnd, iv.chromEnd)] -= 1
        # reduce
        start = self.chromStart
        cum = 0
        missed = []
        for pos in sorted(c):
            if pos > start and not cum:
                missed.append((start, pos))
            cum += c[pos]
            if not cum: # start of an uncovered interval
                start = pos
        if pos < self.chromEnd:
            missed.append((pos, self.chromEnd))
        # build intervals
        subtracted = []
        for i, m in enumerate(missed):
            x = deepcopy(self)
            x.chromStart = m[0]
            x.chromEnd = m[1]
            x.name = sha1(' '.join(map(str,[x.chrom,x.chromStart,x.chromEnd]))).hexdigest()
            x.group = self.name
            subtracted.append(x)
        # return remaining interval slices
        return subtracted

'''list of intervals'''
class IntervalList(list):
    def __init__(self,elements,source=None):
        list.__init__(self, elements)
        self.source = source  # source of intervals

    def __str__(self):
        return "<IntervalList (%s) %d elements> " % (self.source, len(self))

    def __repr__(self):
        return "<IntervalList (%s) %d elements> " % (self.source, len(self))
