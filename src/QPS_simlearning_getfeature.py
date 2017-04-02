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

from similarity import Similarity

import global_params

sim_exe = '.feature.sim'

def extractPhrasePaireFeature(phrasedir):
    for lec in annotation.Lectures:
        path = phrasedir + str(lec)+ '/'
        fio.NewPath(path)
        
        for prompt in ['q1', 'q2']:
            prefix = os.path.join(path, '%s.%s.'%(prompt, method))
            filename = path + prompt + sim_exe
            print filename
            
            featureset = []
            
            feature_extractor = Similarity(prefix)
            
            phrasefile = os.path.join(path, "%s.%s.key"%(prompt, method))
            
            phrases = fio.LoadList(phrasefile)
            
            for p1 in phrases:
                for p2 in phrases:
                    featureset.append((feature_extractor.get_features(p1, p2), 0.0, {'p1':p1, 'p2':p2}))
            
            fio.SaveDict2Json(featureset, filename)
            
            feature_extractor.save()
            
def extractPhrasePaireFromAnnotation(phrasedir, annotators, id):
    for doc, lec, annotator in annotation.generate_all_files(annotation.datadir + 'json/', '.json', anotators = annotators, lectures=annotation.Lectures):
        print doc
        
        #load task
        task = annotation.Task()
        task.loadjson(doc)
        
        path = phrasedir + str(lec)+ '/'
        fio.NewPath(path)
        
        for prompt in ['q1', 'q2']:
            prefix = os.path.join(path, '%s.%s.'%(prompt, method))
            filename = path + prompt + sim_exe
            print filename
            
            featureset = []
            
            feature_extractor = Similarity(prefix)
            
            phrase_annotation = task.get_phrase_annotation(prompt)
            
            #positive examples
            for rank1 in sorted(phrase_annotation):
                for rank2 in sorted(phrase_annotation):
                    if rank1 == rank2:
                        score = 1.0
                    else:
                        score = 0.0
                                
                    phrases1 = phrase_annotation[rank1]
                    phrases2 = phrase_annotation[rank2]
                    for phrasedict1 in phrases1:
                        p1 = phrasedict1['phrase'].lower().strip()
                        
                        for phrasedict2 in phrases2:
                            p2 = phrasedict2['phrase'].lower().strip()
                            
                            featureset.append((feature_extractor.get_features(p1, p2), score, {'p1':p1, 'p2':p2}))
            
            fio.SaveDict2Json(featureset, filename)
            
            feature_extractor.save()
        
if __name__ == '__main__':

    #Step3: extract features
#     for system, method in [
# #                             ('QPS_NP', 'syntax'),
# #                             ('QPS_NP', 'crf'),
# #                             ('QPS_A1', 'crf'),
# #                             ('QPS_A2', 'crf'),
# #                             ('QPS_union', 'crf'),
# #                             ('QPS_intersect', 'crf'),
#                             ('QPS_combine', 'crf'),
#                            ]:
#         phrasedir = "../data/"+course+"/"+system+"/phrase/"
#                   
#         extractPhrasePaireFeature(phrasedir)
#            
#         model_dir = "../data/"+course+"/simlearning/svm"
#         fio.NewPath(model_dir)
#            
#         predict_leave_one_lecture_out(model_dir, phrasedir, modelname='svm')
#             
# #         model_dir = "../data/"+course+"/simlearning/"
# #         predict_leave_one_lecture_out(model_dir, phrasedir, modelname='svr')
#             
# # #           
#     exit(-1)
    
    #Step 1: get sim feature for oracle 1, and oracle 2
    debug = False
     
    course = sys.argv[1]
    maxWeek = int(sys.argv[2])
    system = sys.argv[3]
    method = sys.argv[4]
     
    excelfile = "../data/CourseMIRROR/reflections.json"
             
    phrasedir = "../data/"+course+"/"+system+"/phrase/"
    fio.NewPath(phrasedir)
     
    class_index_dict_file = '../data/%s/class_dict.json' %course
     
    if method == 'annotator1':
        extractPhrasePaireFromAnnotation(phrasedir, annotation.anotators[0:1], 0)        
    elif method == 'annotator2':
        extractPhrasePaireFromAnnotation(phrasedir, annotation.anotators[-1:], 1)
      
     
#     correlation_analysis_noduplicate()
#     model_dir = "../data/"+course+"/simlearning/"
#     train_leave_one_lecture_out(model_dir)
#     extractPhrasePaireFeature(phrasedir)
    
    print "done"
    