import sys
import re
import fio
import xml.etree.ElementTree as ET
from collections import defaultdict
import random
import NLTKWrapper
import SennaParser
import porter
import annotation
import os
import CourseMirror_Survey
import OracleExperiment
import json
from CourseMirror_Survey import stopwords, punctuations
import codecs
from nltk.tag import SennaPSGTagger
import pickle
import numpy as np

import pickle

import file_util

from AlignPhraseAnnotation import AlignPhraseAnnotation

from similarity import Similarity

import global_params
import cmd
from OSLOM_wrapper import OSLOM

sim_exe = '.feature.sim'
net_exe = '.net.dat'

def writegraph_leave_one_lecture_out_lsa(model_dir, phrasedir, modelname='lsa'):    
    lectures = annotation.Lectures
    
    for i, lec in enumerate(lectures):
        test = [lec]
        
        path = os.path.join(phrasedir, str(lec))
        
        for q in ['q1', 'q2']:
            #write the output
            phrasefile = os.path.join(path, "%s.%s.key"%(q, method))
            phrases = fio.LoadList(phrasefile)
            
            if modelname == 'lsa':
                similarties_results = os.path.join(path, "%s.%s.optimumComparerLSATasa"%(q, method))
            elif modelname == 'svm':
                similarties_results = os.path.join(path, "%s.%s.svm"%(q, method))
            
            simhead, simbody = fio.ReadMatrix(similarties_results, hasHead=True)
            
            assert(len(simhead) == len(phrases))
            
            body = []
            for i, p1 in enumerate(phrases):
                for j, p2 in enumerate(phrases):
                    if j <= i: 
                        continue #undirect graph
                    
                    score = simbody[i][j]
                    
                    score = float(score) if score != 'NaN' else 0.0
                    
                    #if score == 0.0: score = 0.000001
                    #if score < 0.5: continue
                    if score == 0.0: continue
                    
                    #row = [i, j, '%f'%score]
                    row = [i, j]
                    
                    body.append(row)
            
            output = os.path.join(path, "%s.%s.%s%s"%(q, method,modelname,net_exe))
            fio.WriteMatrix(output, body)
            
def writegraph_leave_one_lecture_out(model_dir, phrasedir, modelname='svr', traincourse=None):   
    from sklearn import svm
    from sklearn.metrics import mean_squared_error, precision_recall_fscore_support, accuracy_score
    import QPS_simlearning
 
    sim_extractor = Similarity()
    allfeatures = sorted(sim_extractor.features.keys())
    
    features = allfeatures
    
    name = '_'.join(features)
    
    lectures = annotation.Lectures
    
    for i, lec in enumerate(lectures):
        test = [lec]
        
        print test
        model_file = os.path.join(model_dir, '%d_%s.model'%(lec, name))
        #model_file = os.path.join(model_dir, '%s_%s.model'%('IE256_2016', name))
        
        with open(model_file, 'rb') as handle:
            clf = pickle.load(handle)
        
        path = os.path.join(phrasedir, str(lec))
        
        for q in ['q1', 'q2']:
            test_X, test_Y = QPS_simlearning.combine_files_test(phrasedir, test, features, prompts=[q])
            predict_Y = clf.predict(test_X)
            
            #write the output
            phrasefile = os.path.join(path, "%s.%s.key"%(q, method))
            phrases = fio.LoadList(phrasefile)
            
            assert(len(predict_Y) == len(phrases)*len(phrases))
            
            k = 0
            body = []
            for i, p1 in enumerate(phrases):
                for j, p2 in enumerate(phrases):
                    if j <= i: 
                        k += 1
                        continue #undirect graph
                    
                    if modelname == 'svm':
                        if predict_Y[k] == 1.0:
                            #row = [i,j, '%.1f'%predict_Y[k]]
                            row = [i,j]
                            body.append(row)
                    else:
                        row = [i,j, '%.2f'%predict_Y[k]]
                        body.append(row)
                        
                    k += 1
            
            output = os.path.join(path, "%s.%s.%s%s"%(q, method,modelname,net_exe))
            fio.WriteMatrix(output, body)
            
def solvegraph_leave_one_lecture_out(phrasedir, modelname='svr'):    
    lectures = annotation.Lectures
    
    oslom = OSLOM(oslom_parms)
    
    if modelname=='svm':
        weighted = False
        undirect = True
    elif modelname=='lsa':
        weighted = False
        undirect = True
    else: #svr, lsa
        weighted = True
        undirect = True
                
    for i, lec in enumerate(lectures):
        path = os.path.join(phrasedir, str(lec))
        
        for q in ['q1', 'q2']:
            #write the output
            phrasefile = os.path.join(path, "%s.%s.key"%(q, method))
            phrases = fio.LoadList(phrasefile)
            
            netgraphfile = os.path.join(path, "%s.%s.%s%s"%(q, method,modelname,net_exe))
            
            oslom.solve_graph(netgraphfile, undirect, weighted)

def write_communite_to_clusters(communites, phrases, output):
    body = []
    
    dict = {}
    for i, community in enumerate(communites):
        for node in community:
            row = [phrases[node], i+1]
            body.append(row)
            dict[node] = 1
    
#     k = len(communites)
#     #write phrases that are not in any communities
#     for i in range(len(phrases)):
#         if i in dict: continue
#         
#         row = [phrases[i], k]
#         k += 1
#         body.append(row)
        
    fio.WriteMatrix(output, body, None)
        
def readgraph_leave_one_lecture_out(phrasedir, modelname='svr'):    
    lectures = annotation.Lectures
    
    oslom = OSLOM()
    
    if modelname=='svr':
        weighted = True
        undirect = True
    else:
        weighted = False
        undirect = True
                
    for i, lec in enumerate(lectures):
        path = os.path.join(phrasedir, str(lec))
        
        for q in ['q1', 'q2']:
            #write the output
            phrasefile = os.path.join(path, "%s.%s.key"%(q, method))
            phrases = fio.LoadList(phrasefile)
            
            netgraphfile = os.path.join(path, "%s.%s.%s%s_oslo_files"%(q, method,modelname,net_exe), 'tp')
            
            if not fio.IsExist(netgraphfile):#no communities
                print netgraphfile
                communites = [[x] for x in range(len(phrases))]
            else:
                communites = oslom.readgraph_partitions(netgraphfile)
                
                #if len(communites) == 1:#break it
                #    communites = [[x] for x in range(len(phrases))]
            
            name = 'ct.%s.%s'%(modelname, 'default')
            output = os.path.join(path, "%s.cluster.kmedoids.sqrt.%s.%s" % (q, name, method))
            write_communite_to_clusters(communites, phrases, output)
            
            print "%d\t%s\t%d"%(lec, q, len(communites))
            
if __name__ == '__main__':
    course = global_params.g_cid
    
    oslom_parms = sys.argv[1]
    
    if oslom_parms == '0':
        oslom_parms = ''
    elif oslom_parms == '1':
        #oslom_parms = '-t 1.0 -singlet -r 30'# -cp 0.1
        oslom_parms = '-t 1.0 -seed 0 -singlet -r 30'# -cp 0.1
        #oslom_parms = '-t 1.0'# -cp 0.1
    elif oslom_parms == '2':
        oslom_parms = '-t 0.9 -infomap 3'# -cp 0.1
    elif oslom_parms == '3':
        oslom_parms = '-t 0.9 -infomap 3 -copra 2'# -cp 0.1
    elif oslom_parms == '4': #default
        oslom_parms = '-t 1.0 -r 30 -infomap 5 -copra 5'# -cp 0.1
    
    for modelname in ['svm', 'lsa']:#'svm', 'svr',
    #for modelname in ['lsa']:#'svm', 'svr',  
    #for modelname in ['svr', 'svm']:    #'svm', 
        for system, method in [
#                                 ('QPS_A1_N', 'crf'),
#                                 ('QPS_A2_N', 'crf'),
#                                 ('QPS_NP', 'syntax'),
#                                 ('QPS_union', 'crf'),
#                                 ('QPS_intersect', 'crf'),
                                ('QPS_combine', 'crf'),
                            ]:
            phrasedir = "../data/"+course+"/"+system+"/phrase/"
            
            #extractPhrasePaireFeature(phrasedir)
            
            model_dir = "../data/"+course+"/simlearning/svm/"
             
            writegraph_leave_one_lecture_out_lsa(model_dir, phrasedir, modelname=modelname)
                 
#             solvegraph_leave_one_lecture_out(phrasedir, modelname=modelname)
# #             
#             readgraph_leave_one_lecture_out(phrasedir, modelname=modelname)
        