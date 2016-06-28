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

from sklearn import svm
from sklearn.metrics import mean_squared_error, precision_recall_fscore_support, accuracy_score
import pickle

import file_util

from AlignPhraseAnnotation import AlignPhraseAnnotation

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

def combine_files_test(phrasedir, lectures, features=None, prompts=['q1', 'q2']):
    X = []
    Y = []
    
    if features == None:
        sim_extractor = Similarity()
        features = sorted(sim_extractor.features.keys())

    for i, lec in enumerate(lectures):
        for q in prompts:
            
            for phrasedir in [phrasedir]:
                path = phrasedir + str(lec)+ '/'
                
                filename = os.path.join(path, q + sim_exe)
                
                data = fio.LoadDictJson(filename)
                
                for fdict, score, _ in data:
                    row = []
                    
                    for name in features:
                        x = fdict[name]
                        if str(x) == 'nan':
                            x = 0.0
                        row.append(x)
                    
                    X.append(row)
                    Y.append(score)
                        
    return X, Y
           
def combine_files(lectures, features=None, prompts=['q1', 'q2']):
    phrasedir1 = '../data/%s/oracle_annotator_1/phrase/'%course
    phrasedir2 = '../data/%s/oracle_annotator_2/phrase/'%course
    
    X = []
    Y = []
    
    if features == None:
        sim_extractor = Similarity()
        features = sorted(sim_extractor.features.keys())

    for i, lec in enumerate(lectures):
        for q in prompts:
            
            for phrasedir in [phrasedir1, phrasedir2]:
                path = phrasedir + str(lec)+ '/'
                
                filename = os.path.join(path, q + sim_exe)
                
                data = fio.LoadDictJson(filename)
                
                for fdict, score, _ in data:
                    row = []
                    
                    for name in features:
                        x = fdict[name]
                        if str(x) == 'nan':
                            x = 0.0
                        row.append(x)
                    
                    X.append(row)
                    Y.append(score)
                        
    return X, Y

def correlation_analysis():
    phrasedir1 = '../data/%s/oracle_annotator_1/phrase/'%course
    phrasedir2 = '../data/%s/oracle_annotator_2/phrase/'%course
    
    outdir = '../data/%s/simlearning/'
    fio.NewPath(outdir)
    
    sim_extractor = Similarity()
    
    features = sorted(sim_extractor.features.keys())
    head = features + ['score']
    body = []
    lectures = annotation.Lectures
    
    for i, lec in enumerate(lectures):
        for q in ['q1', 'q2']:
            
            outfile = os.path.join(outdir, str(lec), '%s%s'%(q, sim_exe))
            
            for phrasedir in [phrasedir1, phrasedir2]:
                path = phrasedir + str(lec)+ '/'
                
                filename = os.path.join(path, q + sim_exe)
                
                data = fio.LoadDictJson(filename)
                
                for fdict, score, _ in data:
                    row = []
                    
                    for name in features:
                        x = fdict[name]
                        
                        if str(x) == 'nan':
                            x = 0.0
                        
                        row.append(x)
                    row.append(score)
                    
                    body.append(row)
    
    out_correlation = os.path.join(outdir, 'data.txt')
    fio.WriteMatrix(out_correlation, body, head)

def correlation_analysis_noduplicate():
    phrasedir1 = '../data/%s/oracle_annotator_1/phrase/'%course
    phrasedir2 = '../data/%s/oracle_annotator_2/phrase/'%course
    
    outdir = '../data/%s/simlearning/'%course
    fio.NewPath(outdir)
    
    sim_extractor = Similarity()
    
    features = sorted(sim_extractor.features.keys())
    head = features + ['score']
    body = []
    lectures = annotation.Lectures
    
    for i, lec in enumerate(lectures):
        for q in ['q1', 'q2']:
            
            outfile = os.path.join(outdir, str(lec), '%s%s'%(q, sim_exe))
            
            for phrasedir in [phrasedir1, phrasedir2]:
                path = phrasedir + str(lec)+ '/'
                
                filename = os.path.join(path, q + sim_exe)
                
                data = fio.LoadDictJson(filename)
                
                for fdict, score, pd in data:
                    if pd['p1'] == pd['p2']: 
                        print pd['p1']
                        continue
                    
                    row = []
                    
                    for name in features:
                        x = fdict[name]
                        
                        if str(x) == 'nan':
                            x = 0.0
                        
                        row.append(x)
                    row.append(score)
                    
                    body.append(row)
    
    out_correlation = os.path.join(outdir, 'data.txt')
    fio.WriteMatrix(out_correlation, body, head)
    
def train_leave_one_lecture_out(model_dir, name='simlearn_cv'):
#     model_dir = '../data/IE256/%s/model/%s/'%(system, name)
#     fio.NewPath(model_dir)
#      
#     outputdir = '../data/IE256/%s/extraction/%s_output/'%(system, name)
#     fio.NewPath(outputdir)
    
    sim_extractor = Similarity()
    allfeatures = sorted(sim_extractor.features.keys())
    
    if True:
        k = len(allfeatures)
    #for k in range(len(allfeatures)+1):
        #features = allfeatures#['WordEmbedding']
        
        if k == len(allfeatures):#use all features
            features = allfeatures
        else:
            features = [allfeatures[k]]
        
        name = '_'.join(features)
        
        lectures = annotation.Lectures
        
        dict = defaultdict(int)
        
        MSE = []
        for i, lec in enumerate(lectures):
            train = [x for x in lectures if x != lec]
            test = [lec]
            
            print train
            print test
            
            model_file = os.path.join(model_dir, '%d_%s.model'%(lec, name))
            
            if fio.IsExist(model_file):
                with open(model_file, 'rb') as handle:
                    clf = pickle.load(handle)
            else:
                train_X, train_Y = combine_files(train, features)
                clf = svm.SVR()
                clf.fit(train_X, train_Y)
                
                with open(model_file, 'wb') as handle:
                    pickle.dump(clf, handle)
            
            for q in ['q1', 'q2']:
                test_X, test_Y = combine_files(test, features, prompts=[q])
                predict_Y = clf.predict(test_X)
                
                mse = mean_squared_error(test_Y, predict_Y)
                
                MSE.append([lec, q, mse])
        
        output = '../data/%s/simlearning.cv.%s.txt'%(course, name)
        
        fio.WriteMatrix(output, MSE, header=['lec', 'prompt', 'MSE'])

def train_leave_one_lecture_out_svm(model_dir, name='simlearn_cv'):
#     model_dir = '../data/IE256/%s/model/%s/'%(system, name)
#     fio.NewPath(model_dir)
#      
#     outputdir = '../data/IE256/%s/extraction/%s_output/'%(system, name)
#     fio.NewPath(outputdir)
    
    sim_extractor = Similarity()
    allfeatures = sorted(sim_extractor.features.keys())
    
    #for k in range(len(allfeatures)+1):
    if True:
        k = len(allfeatures)
        
        #features = allfeatures#['WordEmbedding']
        
        if k == len(allfeatures):#use all features
            features = allfeatures
        else:
            features = [allfeatures[k]]
            #features = allfeatures[0:k] + allfeatures[k+1:]
        
        name = '_'.join(features)
        
        lectures = annotation.Lectures
        
        dict = defaultdict(int)
        
        MSE = []
        for i, lec in enumerate(lectures):
            train = [x for x in lectures if x != lec]
            test = [lec]
            
            print train
            print test
            
            model_file = os.path.join(model_dir, '%d_%s.model'%(lec, name))
            
            if fio.IsExist(model_file):
                with open(model_file, 'rb') as handle:
                    clf = pickle.load(handle)
            else:
                train_X, train_Y = combine_files(train, features)
                clf = svm.SVC()
                clf.fit(train_X, train_Y)
                
                with open(model_file, 'wb') as handle:
                    pickle.dump(clf, handle)
            
            for q in ['q1', 'q2']:
                test_X, test_Y = combine_files(test, features, prompts=[q])
                predict_Y = clf.predict(test_X)
                
                prf = precision_recall_fscore_support(test_Y, predict_Y, average='weighted')
                
                accuracy = accuracy_score(test_Y, predict_Y)
                
                MSE.append([lec, q, accuracy] + [prf[0], prf[1], prf[2]])
        
        output = '../data/%s/simlearning.cv.svm.%s.txt'%(course, name)
        
        fio.WriteMatrix(output, MSE, header=['lec', 'prompt', 'accuracy', 'precision', 'recall', 'f-score'])

def predict_leave_one_lecture_out(model_dir, phrasedir, modelname='svr'):    
    sim_extractor = Similarity()
    allfeatures = sorted(sim_extractor.features.keys())
    
    features = allfeatures
    
    name = '_'.join(features)
    
    lectures = annotation.Lectures
    
    for i, lec in enumerate(lectures):
        test = [lec]
        
        print test
        model_file = os.path.join(model_dir, '%d_%s.model'%(lec, name))
        
        with open(model_file, 'rb') as handle:
            clf = pickle.load(handle)
        
        path = os.path.join(phrasedir, str(lec))
        
        for q in ['q1', 'q2']:
            test_X, test_Y = combine_files_test(phrasedir, test, features, prompts=[q])
            predict_Y = clf.predict(test_X)
            
            #write the output
            phrasefile = os.path.join(path, "%s.%s.key"%(q, method))
            phrases = fio.LoadList(phrasefile)
            
            assert(len(predict_Y) == len(phrases)*len(phrases))
            
            k = 0
            body = []
            for p1 in phrases:
                row = []
                for p2 in phrases:
                    row.append(predict_Y[k])
                    k += 1
                body.append(row)
            
            output = os.path.join(path, "%s.%s.%s"%(q, method,modelname))
            fio.WriteMatrix(output, body, phrases)
            
def gather_performance(output):
    sim_extractor = Similarity()
    allfeatures = sorted(sim_extractor.features.keys())
    
    allbody = []
    for k in range(len(allfeatures)+1):
        #features = allfeatures#['WordEmbedding']
        
        if k == len(allfeatures):#use all features
            features = allfeatures
        else:
            features = [allfeatures[k]]
            #features = allfeatures[0:k] + allfeatures[k+1:]
        
        name = '_'.join(features)
        
        resultfile = '../data/%s/simlearning.cv.svm.%s.txt'%(course, name)
        
        head, body = fio.ReadMatrix(resultfile, hasHead=True)
        
        #get the average
        allhead = ['name'] + head[2:]
        average = [name]
        for i in range(2, len(head)):#start from the third one
            values = [float(row[i]) for row in body]
            average.append(np.mean(values))
        
        allbody.append(average)
    
    fio.WriteMatrix(output, allbody, allhead)

def check_stopword():
    from CourseMirror_Survey import stopwords
    
    vocab = fio.LoadDictJson(global_params.vocab)
    
    for word, count in vocab.items():
        if count < 5: continue
        
        if word in stopwords:
            print word, '\t', count
    
        
if __name__ == '__main__':
#     check_stopword()
#     exit(-1)
    
    course = "IE256_2016"
#     
#     model_dir = "../data/"+course+"/simlearning/svm/"
#     fio.NewPath(model_dir)
#     train_leave_one_lecture_out_svm(model_dir)
#      
# #     model_dir = "../data/"+course+"/simlearning/"
# # #     fio.NewPath(model_dir)
# #     train_leave_one_lecture_out(model_dir)
#      
#         
# #     all_performance = "../data/"+course+"/simlearning/svm/out.txt"
# #     gather_performance(all_performance)
#        
#     exit(-1)
#     
# #     #print getSennaPSGtags("I think the main topic of this course is interesting".split())
    for system, method in [
#                             ('QPS_NP', 'syntax'),
#                               ('QPS_NP', 'crf'),
#                             ('QPS_A1', 'crf'),
#                             ('QPS_A2', 'crf'),
#                             ('QPS_union', 'crf'),
#                             ('QPS_intersect', 'crf'),
#                             ('QPS_combine', 'crf'),
                           ]:
        phrasedir = "../data/"+course+"/"+system+"/phrase/"
                
        extractPhrasePaireFeature(phrasedir)
         
        model_dir = "../data/"+course+"/simlearning/svm"
        fio.NewPath(model_dir)
         
        predict_leave_one_lecture_out(model_dir, phrasedir, modelname='svm')
          
#         model_dir = "../data/"+course+"/simlearning/"
#         predict_leave_one_lecture_out(model_dir, phrasedir, modelname='svr')
          
# #           
    exit(-1)
     
    debug = False
    
    course = sys.argv[1]
    maxWeek = int(sys.argv[2])
    system = sys.argv[3]
    method = sys.argv[4]
    
    excelfile = "../data/CourseMIRROR/reflections.json"
            
    phrasedir = "../data/"+course+"/"+system+"/phrase/"
    fio.NewPath(phrasedir)
    
    class_index_dict_file = '../data/%s/class_dict.json' %course
    
#     if method == 'annotator1':
#         extractPhrasePaireFromAnnotation(phrasedir, annotation.anotators[0:1], 0)        
#     elif method == 'annotator2':
#         extractPhrasePaireFromAnnotation(phrasedir, annotation.anotators[-1:], 1)
#      
    #correlation_analysis()
#     correlation_analysis_noduplicate()
    
    model_dir = "../data/"+course+"/simlearning/"
    train_leave_one_lecture_out(model_dir)
    
#     extractPhrasePaireFeature(phrasedir)
    
    print "done"
    