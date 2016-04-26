import sys
import re
import xml.etree.ElementTree as ET
import numpy
from collections import defaultdict
import json
                    
def getTopRankPhraseNoSource(NPs, clusterids, cid, lexdict):
    #get cluster NP, and scores
    dict = {}
    
    for NP, id in zip(NPs, clusterids):
        if int(id) == cid:
            dict[NP] = lexdict[NP.lower()]
            
    keys = sorted(dict, key=dict.get, reverse =True)
    
    return keys[0]
                    
def getTopRankPhrase(NPs, clusterids, cid, lexdict, sources):
    #get cluster NP, and scores
    dict = {}
    
    s = []
    
    for NP, id, source in zip(NPs, clusterids, sources):
        if int(id) == cid:
            dict[NP] = lexdict[NP.lower()]
            s.append(source)
    
    keys = sorted(dict, key=dict.get, reverse =True)
    
    source = set(s)
    return keys[0], source

def RankCluster2(NPs, lexdict, clusterids, sources):
    sdict = {}
    for id, source in zip(clusterids, sources):
        if id not in sdict:
            sdict[id] = set([])
        sdict[id].add(source)
    
    sizedict = {}
    for key in sdict:
        sizedict[key] = len(sdict[key])
    
    print "sizedict"        
    #fio.PrintDict(sizedict)
    
    keys = sorted(sizedict, key=sizedict.get, reverse =True)
    
    return keys

def RankClusterNoSource(NPs, lexdict, clusterids):
    sizedict = defaultdict(int)
    for id in clusterids:
        sizedict[id] += 1

    #get lex scores for clusters
    highestlexdict = {}
    for key in sizedict:
        phrase = getTopRankPhraseNoSource(NPs, clusterids, int(key), lexdict)
        highestlexdict[key] = lexdict[phrase.lower()]
    
    print "highestlexdict" 
    #fio.PrintDict(highestlexdict)
        
    
    print "sizedict"        
    #fio.PrintDict(sizedict)
    
    tkeys = sorted(sizedict, key=sizedict.get, reverse =True)
    
    #break the tires
    keys = []
    N = len(tkeys)
    i = 0
    while i < len(tkeys):
        tkey = []
        j = i
        while (j < N):
            if sizedict[tkeys[j]] == sizedict[tkeys[i]]:
                tkey.append(tkeys[j])
                j = j + 1
            else:
                break
        if j==i:
            i = i + 1
        else:
            i = j
        
        print i
        
        if len(tkey) == 1:
            keys = keys + tkey
        else:
            #sort them
            tdict = {}
            for key in tkey:
                tdict[key] = highestlexdict[key]
            tkey = sorted(tdict, key=tdict.get, reverse =True)
            keys = keys + tkey
        
    assert(len(keys) == len(tkeys))
    
    print keys
    return keys

def RankCluster(NPs, lexdict, clusterids, sources):
    sdict = {}
    for id, source in zip(clusterids, sources):
        if id not in sdict:
            sdict[id] = set([])
        sdict[id].add(source)
    
    sizedict = {}
    for key in sdict:
        sizedict[key] = len(sdict[key])

    #get lex scores for clusters
    highestlexdict = {}
    for key in sdict:
        phrase, source = getTopRankPhrase(NPs, clusterids, int(key), lexdict, sources)
        highestlexdict[key] = lexdict[phrase]
    
    print "highestlexdict" 
    #fio.PrintDict(highestlexdict)
        
    
    print "sizedict"        
    #fio.PrintDict(sizedict)
    
    tkeys = sorted(sizedict, key=sizedict.get, reverse =True)
    
    #break the tires
    keys = []
    N = len(tkeys)
    i = 0
    while i < len(tkeys):
        tkey = []
        j = i
        while (j < N):
            if sizedict[tkeys[j]] == sizedict[tkeys[i]]:
                tkey.append(tkeys[j])
                j = j + 1
            else:
                break
        if j==i:
            i = i + 1
        else:
            i = j
        
        print i
        
        if len(tkey) == 1:
            keys = keys + tkey
        else:
            #sort them
            tdict = {}
            for key in tkey:
                tdict[key] = highestlexdict[key]
            tkey = sorted(tdict, key=tdict.get, reverse =True)
            keys = keys + tkey
        
    assert(len(keys) == len(tkeys))
    
    print keys
    return keys
                                 
if __name__ == '__main__':
    pass