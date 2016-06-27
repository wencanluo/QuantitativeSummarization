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

import file_util

from AlignPhraseAnnotation import AlignPhraseAnnotation
from crf_feature_extractor import CRF_Extractor
from crf import CRF
import global_params

def getSennaPSGtags(tokens):
    tagger = SennaPSGTagger(global_params.sennadir)
    psgtags = [tag for _, tag in tagger.tag(tokens)]
    
    tags = ['O']*len(tokens)
    
    NP = []
		
    stack = []
    tmp = []
    
    hasNP = False
    for k, (token, tag) in enumerate(zip(tokens, psgtags)):
        Added = False
        
        for i, ch in enumerate(tag):
            if ch == '(':
                if not hasNP: continue
                stack.append(ch)
            elif ch == ')':
                if not hasNP: continue
                
                stack.pop()
                if len(stack) == 0: #empty, the NP is done
                    if not Added: 
                        tmp.append(token)
                        Added = True
                        tags[k] = 'I'
                        
                    NP.append(" ".join(tmp))
                    tmp = []
                    hasNP = False
            else:
                if hasNP: 
                    if not Added: #add the word only once
                        tmp.append(token)
                        Added = True
                        tags[k] = 'I'
                    continue
                
                if tag[i-1:].startswith('(NP'):
                    hasNP = True
                    stack.append('(')
                    tmp.append(token)
                    tags[k] = 'B'
                    
                    Added = True
    
    return tags

def extractPhraseFromSyntax(extractiondir, annotators):
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
                tags = d['tags'][0]
                
                n_tokens = []
                n_tags = []
                
                for token, tag in zip(tokens, tags):
                    if len(token) == 0: continue
                    
                    n_tokens.append(token)
                    n_tags.append(tag)
                
                if len(n_tokens) == 0: continue
                
                tokens = n_tokens
                tags = n_tags
                
                body = []

                words = tokens
                N = len(tokens)
                
                #first row: the word token
                for word in words:
                    row = []
                    row.append(word)
                    body.append(row)
                
                #last row:
                tags = [tag for tag in tags]
                
                for i, tag in enumerate(tags):
                    body[i].append(tag)
                    
                #extract the NP tags
                psg_tags = getSennaPSGtags(tokens)
                for i, tag in enumerate(psg_tags):
                    body[i].append(tag)
   
                for row in body:
                    fout.write(' '.join(row))
                    fout.write('\n')
                fout.write('\n')
            
            fout.close()
           
        if debug:
            break

def extractPhraseFeatureFromAnnotation(extractiondir, annotators, id, empty='N'):
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
            
            crf_feature_extractor = CRF_Extractor()
            
            #add sentences to the extrator for global feature extraction
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
                
                crf_feature_extractor.add_sentence((tokens, tags))
            
            for tokens, tags in crf_feature_extractor.sentences:
                if empty == 'Y':
                    flag = True
                    for tag in tags:
                        if tag != 'O': flag = False
                    if flag: continue
                
                body = crf_feature_extractor.extract_crf_features(tokens, tags, prompt)
                
                for row in body:
                    fout.write(' '.join(row))
                    fout.write('\n')
                fout.write('\n')
            
            fout.close()

def extractVocab(annotators, output):
    vocab = defaultdict(int)
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
        
        for prompt in ['q1', 'q2']:
            phrase_annotation0 = task0.get_phrase_annotation(prompt)
            phrase_annotation1 = task1.get_phrase_annotation(prompt)
            
            aligner = AlignPhraseAnnotation(task0, task1, prompt)
            aligner.align()
            
            #add sentences to the extrator for global feature extraction
            for d in aligner.responses:
                tokens = [token.lower() for token in d['response']]
                
                for token in tokens:
                    vocab[token] += 1
    fio.SaveDict2Json(vocab, output)
            
def extractPhraseFeatureFromUnion(extractiondir, annotators, empty='N'):
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
            
            crf_feature_extractor = CRF_Extractor()
            
            #add sentences to the extrator for global feature extraction
            for d in aligner.responses:
                tokens = [token.lower() for token in d['response']]
                tags = aligner.union_tag(d['tags'][0], d['tags'][1])
                
                n_tokens = []
                n_tags = []
                
                for token, tag in zip(tokens, tags):
                    if len(token) == 0: continue
                    
                    n_tokens.append(token)
                    n_tags.append(tag)
                
                if len(n_tokens) == 0: continue
                
                tokens = n_tokens
                tags = n_tags
                
                crf_feature_extractor.add_sentence((tokens, tags))
            
            for tokens, tags in crf_feature_extractor.sentences:
                if empty == 'Y':
                    flag = True
                    for tag in tags:
                        if tag != 'O': flag = False
                    if flag: continue
                
                body = crf_feature_extractor.extract_crf_features(tokens, tags, prompt)
                
                for row in body:
                    fout.write(' '.join(row))
                    fout.write('\n')
                fout.write('\n')
            
            fout.close()

def extractPhraseFeatureFromIntersect(extractiondir, annotators, empty='N'):
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
            
            crf_feature_extractor = CRF_Extractor()
            
            #add sentences to the extrator for global feature extraction
            for d in aligner.responses:
                tokens = [token.lower() for token in d['response']]
                tags = aligner.interset_tag(d['tags'][0], d['tags'][1])
                
                n_tokens = []
                n_tags = []
                
                for token, tag in zip(tokens, tags):
                    if len(token) == 0: continue
                    
                    n_tokens.append(token)
                    n_tags.append(tag)
                
                if len(n_tokens) == 0: continue
                
                tokens = n_tokens
                tags = n_tags
                
                crf_feature_extractor.add_sentence((tokens, tags))
            
            for tokens, tags in crf_feature_extractor.sentences:
                if empty == 'Y':
                    flag = True
                    for tag in tags:
                        if tag != 'O': flag = False
                    if flag: continue
                
                body = crf_feature_extractor.extract_crf_features(tokens, tags, prompt)
                
                for row in body:
                    fout.write(' '.join(row))
                    fout.write('\n')
                fout.write('\n')
            
            fout.close()

def extractPhraseFeatureFromCombine(extractiondir, annotators, empty='N'):
    for docs in annotation.generate_all_files_by_annotators(annotation.datadir + 'json/', '.json', anotators = annotators, lectures=annotation.Lectures):
        
        doc0, lec0, annotator0 = docs[0]
        doc1, lec1, annotator1 = docs[1]
        
        assert(lec0 == lec1)
        lec = lec0
        
        #print lec
        
        #if lec != 17: continue
        
        #load tasks
        task0 = annotation.Task()
        task0.loadjson(doc0)
        
        task1 = annotation.Task()
        task1.loadjson(doc1)
        
        path = extractiondir + str(lec)+ '/'
        fio.NewPath(path)
        
        for prompt in ['q1', 'q2']:
            
            #if prompt != 'q2': continue
            
            filename = path + prompt + '.feature.crf'
            print filename
            
            fout = codecs.open(filename, "w", "utf-8")
            
            extracted_phrases = []
            phrase_annotation0 = task0.get_phrase_annotation(prompt)
            phrase_annotation1 = task1.get_phrase_annotation(prompt)
            
            aligner = AlignPhraseAnnotation(task0, task1, prompt)
            aligner.align()
            
            crf_feature_extractor = CRF_Extractor()
            
            #add sentences to the extrator for global feature extraction
            for d in aligner.responses:
                tokens = [token.lower() for token in d['response']]
                colors = d['colors']
                
                if d['tags'][0] == d['tags'][1]:
                    combinetags = [d['tags'][0]]
                else:
                    combinetags = [d['tags'][0], d['tags'][1]]
                
                for tags in combinetags:
                    n_tokens = []
                    n_tags = []
                    
                    for token, tag in zip(tokens, tags):
                        if len(token) == 0: continue
                        
                        n_tokens.append(token)
                        n_tags.append(tag)
                    
                    if len(n_tokens) == 0: continue
                    
                    tokens = n_tokens
                    tags = n_tags
                    
                    crf_feature_extractor.add_sentence((tokens, tags, colors))
            
            for tokens, tags, colors in crf_feature_extractor.sentences:
                if empty == 'Y':
                    flag = True
                    for tag in tags:
                        if tag != 'O': flag = False
                    if flag: continue
                
                body = crf_feature_extractor.extract_crf_features(tokens, tags, prompt, colors)
                
                for row in body:
                    fout.write(' '.join(row))
                    fout.write('\n')
                fout.write('\n')
            
            fout.close()
            
def combine_files(feature_dir, lectures, output, prompts=['q1', 'q2']):
    
    fout = codecs.open(output, "w", "utf-8")
    
    for lec in lectures:
        for q in prompts:
            filename = os.path.join(feature_dir, str(lec), '%s.feature.crf'%q)
            
            for i, line in enumerate(codecs.open(filename, 'r', 'utf-8').readlines()):
                if len(line.strip()) != 0 and len(line.split()) != 8:
                    print filename
                    print i, line
                    if debug: break
                    
                fout.write(line)
        if debug: break
            
    fout.close()
            
def train_leave_one_lecture_out(name='cv'):
    wapiti_home = '../../../tool/wapiti-1.5.0/'
    
    pattern_file = '../data/%s.pattern.txt'%name
    model_dir = '../data/%s/%s/model/%s/'%(course, system, name)
    fio.NewPath(model_dir)
    
    feature_dir = '../data/%s/%s/extraction/'%(course, system)
    feature_cv_dir = '../data/%s/%s/extraction/%s/'%(course, system, name)
    fio.NewPath(feature_cv_dir)
    
    outputdir = '../data/%s/%s/extraction/%s_output/'%(course, system, name)
    fio.NewPath(outputdir)
    
    lectures = annotation.Lectures
    
    dict = defaultdict(int)
    
    for i, lec in enumerate(lectures):
        train = [x for x in lectures if x != lec]
        test = [lec]
        
        train_filename = os.path.join(feature_cv_dir, 'train_%d.feature.crf'%i)
        
        model_file = os.path.join(model_dir, '%d.model'%i)
        
        print train_filename
        print model_file
        
        crf = CRF(wapiti_home)
        if not fio.IsExist(model_file):
        #if True:
            combine_files(feature_dir, train, train_filename)
            crf.train(train_filename, pattern_file, model_file)
        
        for q in ['q1', 'q2']:
            
            test_filename = os.path.join(feature_cv_dir, 'test_%d_%s.feature.crf'%(i, q))
            output_file = os.path.join(outputdir, 'test_%d_%s.out'%(i, q))
            
            dict['test_%d_%s'%(i, q)] = 1
            
            if empty == 'Y':
                test_filename_old = test_filename.replace('_Y', '_N')
                cmd = 'cp %s %s'%(test_filename_old, test_filename)
                os.system(cmd)
            else:
                combine_files(feature_dir, test, test_filename, prompts=[q])
                #pass
            
            crf.predict(test_filename, model_file, output_file)
        
        if debug: break
    
    file_util.save_dict2json(dict, class_index_dict_file)

def train_leave_one_lecture_out_NP(name='cv'):
    feature_dir = '../data/%s/%s/extraction/'%(course, system)
    
    outputdir = '../data/%s/%s/extraction/%s_output/'%(course, system, name)
    fio.NewPath(outputdir)
    
    lectures = annotation.Lectures
    
    dict = defaultdict(int)
    
    for i, lec in enumerate(lectures):
        train = [x for x in lectures if x != lec]
        test = [lec]
        
        for q in ['q1', 'q2']:
            
            output_file = os.path.join(outputdir, 'test_%d_%s.out'%(i, q))
            
            dict['test_%d_%s'%(i, q)] = 1
            
            combine_files(feature_dir, test, output_file, prompts=[q])
            
        
        if debug: break
    
    file_util.save_dict2json(dict, class_index_dict_file)
    
if __name__ == '__main__':
    #exit(-1)
    
    #print getSennaPSGtags("I think the main topic of this course is interesting".split())
    #exit(-1)
    
    debug = False
    
    course = sys.argv[1]
    maxWeek = int(sys.argv[2])
    system = sys.argv[3]
    method = sys.argv[4]
    empty = sys.argv[5]
    
    excelfile = "../data/CourseMIRROR/reflections.json"
    
    #extractVocab(annotation.anotators, '../data/%s/vocab.json'%course)
    
    extractiondir = "../data/"+course+"/"+system+"/extraction/"
    fio.NewPath(extractiondir)
    
    class_index_dict_file = '../data/%s/class_dict.json'%course
    
    if method == 'NP':
        extractPhraseFromSyntax(extractiondir, annotation.anotators)
        train_leave_one_lecture_out_NP('all')
         
    elif method == 'annotator1':
        extractPhraseFeatureFromAnnotation(extractiondir, annotation.anotators, 0, empty)   
    elif method == 'annotator2':
        extractPhraseFeatureFromAnnotation(extractiondir, annotation.anotators, 1, empty)
    elif method == 'union':
        extractPhraseFeatureFromUnion(extractiondir, annotation.anotators, empty)
    elif method == 'intersect':
        extractPhraseFeatureFromIntersect(extractiondir, annotation.anotators, empty)
    elif method == 'combine':
        extractPhraseFeatureFromCombine(extractiondir, annotation.anotators, empty)
    print "done"
     
#     if method != 'NP':
#         train_leave_one_lecture_out('all')