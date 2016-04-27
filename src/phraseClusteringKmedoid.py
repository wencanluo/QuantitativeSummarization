import sys
import re
import fio
import xml.etree.ElementTree as ET
from collections import defaultdict
import random
import NLTKWrapper
import SennaParser
import porter
import math
import copy
import numpy

import ClusterWrapper
import SennaParser

from CourseMirror_Survey import stopwords, punctuations

def isMalformed(phrase):
    N = len(phrase.split())
    if N == 1: #single stop words
        if phrase.lower() in stopwords: return True
        if phrase.isdigit(): return True
            
    if len(phrase) > 0:
        if phrase[0] in punctuations: return True
    
    return False

def MalformedNPFlilter(NPs):
    newNPs = []
    for NP in NPs:
        if isMalformed(NP): continue
        newNPs.append(NP)
    return newNPs
                        
def getNPs(sennafile, MalformedFlilter=False, source = None, np=None):
    np_phrase = []
    sources = []
    
    #read senna file
    sentences = SennaParser.SennaParse(sennafile)
    
    if len(source) != len(sentences):
        print len(source), len(sentences), sennafile
        
    #get NP phrases
    for i, s in enumerate(sentences):
        if np=='syntax':
            NPs = s.getSyntaxNP()
        elif np == 'chunk':
            NPs = s.getNPrases()
        elif np == 'sentence':
            NPs = s.getSentence()
        elif np.startswith('syntax_'):
            NPs = s.getSyntaxPhrases(np[len('syntax_'):])
        else:
            NPs = s.getSyntaxNP()
            
        for NP in NPs:
            NP = NP.lower()
            
            if MalformedFlilter:
                if isMalformed(NP): 
                    #print NP
                    continue
            
            np_phrase.append(NP)
            
            if source != None:
                sources.append(source[i])
    
    if source != None:
        return np_phrase, sources
    
    return np_phrase



def Similarity2Distance(similarity):
    #http://scikit-learn.org/stable/modules/generated/sklearn.cluster.SpectralClustering.html#sklearn.cluster.SpectralClustering
    distance = copy.deepcopy(similarity)
    
    #change the similarity to distance
    for i, row in enumerate(distance):
        for j, col in enumerate(row):
            if distance[i][j] == "NaN":
                distance[i][j] = 1.0
            else:
                try:
                    if float(distance[i][j]) < 0:
                        print "<0", i, j, distance[i][j]
                        distance[i][j] = 0
                    if float(distance[i][j]) > 100:
                        print ">100", i, j, distance[i][j]
                        distance[i][j] = 100
                    distance[i][j] = 1.0 / math.pow(math.e, float(distance[i][j]))
                except OverflowError as e:
                    print e
                    exit()
    return distance

def getPhraseClusterPhrase(phrasefile, weightfile, output, ratio=None, method=None):
    NPCandidates = fio.ReadFile(phrasefile)
    if len(NPCandidates) == 0: return
    
    NPs, matrix = fio.ReadMatrix(weightfile, hasHead = True)
    
    #change the similarity to distance
    matrix = Similarity2Distance(matrix)

    index = {}
    for i, NP in enumerate(NPs):
        index[NP] = i
    
    newMatrix = []
    
    for NP1 in NPCandidates:
        if NP1 not in index: continue
        
        i = index[NP1]
        
        row = []
        for NP2 in NPCandidates:
            if NP2 not in index:
                print NP2, weightfile, method
                continue
            
            j = index[NP2]
            row.append(matrix[i][j])
            
        newMatrix.append(row)
    
    V = len(NPCandidates)
    if ratio == "sqrt":
        K = int(math.sqrt(V))
    elif float(ratio) > 1:
        K = int(ratio)
    else:
        K = int(ratio*V)
    
    if K < 1: K=1
    
    clusterid = ClusterWrapper.KMedoidCluster(newMatrix, K)
    
    body = []   
    for NP, id in zip(NPCandidates, clusterid):
        row = []
        row.append(NP)
        row.append(id)
        body.append(row)    
    
    fio.WriteMatrix(output, body, header = None)
    
def getPhraseClusterAll(sennafile, weightfile, output, ratio=None, MalformedFlilter=False, source=None, np=None):
    NPCandidates, sources = getNPs(sennafile, MalformedFlilter, source=source, np=np)
    
    if len(NPCandidates) == 0: return
    
    NPs, matrix = fio.ReadMatrix(weightfile, hasHead = True)
    
    #change the similarity to distance
    matrix = Similarity2Distance(matrix)

    index = {}
    for i, NP in enumerate(NPs):
        index[NP] = i
    
    newMatrix = []
    
    for NP1 in NPCandidates:
        assert(NP1 in index)
        i = index[NP1]
        
        row = []
        for NP2 in NPCandidates:
            if NP2 not in index:
                print NP2, weightfile, np
            j = index[NP2]
            row.append(matrix[i][j])
            
        newMatrix.append(row)
    
    V = len(NPCandidates)
    if ratio == "sqrt":
        K = int(math.sqrt(V))
    elif float(ratio) > 1:
        K = int(ratio)
    else:
        K = int(ratio*V)
    
    if K < 1: K=1
    
    clusterid = ClusterWrapper.KMedoidCluster(newMatrix, K)
    
    body = []   
    for NP, id in zip(NPCandidates, clusterid):
        row = []
        row.append(NP)
        row.append(id)
        body.append(row)    
    
    fio.WriteMatrix(output, body, header = None)
    
def getPhraseCluster(phrasedir, method='lexicalOverlapComparer', ratio=None):
    sheets = range(0,12)
    
    for sheet in sheets:
        week = sheet + 1
        for type in ['POI', 'MP', 'LP']:
            weightfilename = phrasedir + str(week)+ '/' + type + '.' + method
            print weightfilename
            
            NPs, matrix = fio.ReadMatrix(weightfilename, hasHead = True)
            
            #change the similarity to method
            for i, row in enumerate(matrix):
                for j, col in enumerate(row):
                    matrix[i][j] = 1 - float(matrix[i][j]) if matrix[i][j] != "NaN" else 0
            
            V = len(NPs)
            if ratio == None:
                K = int(math.sqrt(V))
            else:
                K = int(ratio*V)
            
            K=10    
            clusterid = ClusterWrapper.KMedoidCluster(matrix, K)
            
#             sorted_lists = sorted(zip(NPs, clusterid), key=lambda x: x[1])
#             NPs, clusterid = [[x[i] for x in sorted_lists] for i in range(2)]
            
            dict = defaultdict(int)
            for id in clusterid:
                dict[id] = dict[id] + 1
             
            body = []   
            for NP, id in zip(NPs, clusterid):
                row = []
                row.append(NP)
                row.append(id)
                #row.append(dict[id])
                
                body.append(row)
            
            if ratio == None:    
                file = phrasedir + '/' + str(week) +'/' + type + ".cluster.kmedoids." + "sqrt" + "." +method
            else:
                file = phrasedir + '/' + str(week) +'/' + type + ".cluster.kmedoids." + str(ratio) + "." +method
            fio.WriteMatrix(file, body, header = None)
            
                
if __name__ == '__main__':
    pass
    
 