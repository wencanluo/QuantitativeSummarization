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

from AlignPhraseAnnotation import AlignPhraseAnnotation
from crf_feature_extractor import CRF_Extractor
from crf import CRF

def extractPhraseFeatureFromAnnotation(extractiondir, annotators, id):
    
    crf_feature_extractor = CRF_Extractor()
    
    for docs in annotation.generate_all_files_by_annotators(annotation.datadir + 'json/', '.json', anotators = annotators, lectures=annotation.Lectures):
        
        doc0, lec0, annotator0 = docs[0]
        doc1, lec1, annotator1 = docs[1]
        
        assert(lec0 == lec1)
        lec = lec0
        
        #load tasks
        task0 = annotation.Task()
        task0.loadjson(doc0)
        
        task1 = annotation.Task()
        task1.loadjson(doc1)
        
        path = extractiondir + str(lec)+ '/'
        fio.NewPath(path)
        
        for prompt in ['q1', 'q2']:
            filename = path + prompt + '.feature.crf'
            print filename
            
            fout = codecs.open(filename, "w", "utf-8")
            
            extracted_phrases = []
            phrase_annotation0 = task0.get_phrase_annotation(prompt)
            phrase_annotation1 = task1.get_phrase_annotation(prompt)
            
            aligner = AlignPhraseAnnotation(task0, task1, prompt)
            aligner.align()
            
            for d in aligner.responses:
                tokens = [token.lower() for token in d['response']]
                tags = d['tags'][id]
                
                n_tokens = []
                n_tags = []
                
                for token, tag in zip(tokens, tags):
                    if len(token) == 0: continue
                    
                    n_tokens.append(token)
                    n_tags.append(tag)
                
                if len(n_tokens) == 0: continue
                
                tokens = n_tokens
                tags = n_tags
                
                body = crf_feature_extractor.extract_crf_features(tokens, tags)
                
                for row in body:
                    fout.write(' '.join(row))
                    fout.write('\n')
                fout.write('\n')
            
            fout.close()

def combine_files(feature_dir, lectures, output):
    
    fout = codecs.open(output, "w", "utf-8")
    
    for lec in lectures:
        for q in ['q1', 'q2']:
            filename = os.path.join(feature_dir, str(lec), '%s.feature.crf'%q)
            
            for line in codecs.open(filename, 'r', 'utf-8').readlines():
                fout.write(line)
            
    fout.close()
            
def train_leave_one_lecture_out():
    wapiti_home = '../../../tool/wapiti-1.5.0/'
    training_set_file = '../data/IE256/QPS_A1/extraction/14/q1.feature.crf'
    pattern_file = '../data/IE256/QPS_A1/model/ngram53.pattern.txt'
    model_dir = '../data/IE256/QPS_A1/model/cv/'
    fio.NewPath(model_dir)
    
    feature_dir = '../data/IE256/QPS_A1/extraction/'
    feature_cv_dir = '../data/IE256/QPS_A1/extraction/cv/'
    fio.NewPath(feature_cv_dir)
    
    outputdir = '../data/IE256/QPS_A1/extraction/cv_output/'
    fio.NewPath(outputdir)
    
    lectures = annotation.Lectures
    
    for i, lec in enumerate(lectures):
        train = [x for x in lectures if x != lec]
        test = [lec]
        
        train_filename = os.path.join(feature_cv_dir, 'train_%d.feature.crf'%i)
        test_filename = os.path.join(feature_cv_dir, 'test_%d.feature.crf'%i)
        model_file = os.path.join(model_dir, '%d.model'%i)
        output_file = os.path.join(outputdir, 'test_%d.out'%i)
        
        print train_filename
        print test_filename
        print model_file
        print output_file
        
        combine_files(feature_dir, train, train_filename)
        combine_files(feature_dir, test, test_filename)
        
        crf = CRF(wapiti_home)
        crf.train(train_filename, pattern_file, model_file)
        crf.predict(test_filename, model_file, output_file)
        
    print lectures
    
if __name__ == '__main__':
    course = sys.argv[1]
    maxWeek = int(sys.argv[2])
    system = sys.argv[3]
    method = sys.argv[4]
    
    excelfile = "../data/CourseMIRROR/reflections.json"
            
    extractiondir = "../data/"+course+"/"+system+"/extraction/"
    fio.NewPath(extractiondir)
    
#     if method == 'annotator1':
#         extractPhraseFeatureFromAnnotation(extractiondir, annotation.anotators, 1)
#     elif method == 'annotator2':
#         extractPhraseFeatureFromAnnotation(extractiondir, annotation.anotators, 2)
#     elif method == 'union':
#         extractPhraseFromAnnotationUnion(phrasedir, annotation.anotators)
#     elif method == 'intersect':
#         extractPhraseFromAnnotationIntersect(phrasedir, annotation.anotators)
#     print "done"
#     
    train_leave_one_lecture_out()