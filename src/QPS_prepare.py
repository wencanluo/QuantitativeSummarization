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

from AlignPhraseAnnotation import AlignPhraseAnnotation

def isMalformed(phrase):
    N = len(phrase.split())
    if N == 1: #single stop words
        if phrase.lower() in stopwords: return True
        if phrase.isdigit(): return True
            
    if len(phrase) > 0:
        if phrase[0] in punctuations: return True
    
    return False
                    
def getKeyPhrases(student_summaryList, sennafile, method=None, MalformedFlilter=False, save2file=None):
    #read senna file
    sentences = SennaParser.SennaParse(sennafile)
    
    phrases = []
    for s in sentences:
        if method=='syntax':
            NPs = s.getSyntaxNP()
        else:
            NPs = []
        
        for np in NPs:
            if MalformedFlilter:
                if isMalformed(np): 
                    continue
        
            phrases.append(np.lower())
            
    return phrases
                    
def extractPhrase(excelfile, folder, sennadatadir, method):
    sheets = range(0,maxWeek)
    
    for i, sheet in enumerate(sheets):
        week = i + 1
        
        for type in ['q1', 'q2', 'q3', 'q4']:
        #for type in ['POI', 'MP']:
            print excelfile, sheet, type
            student_summaryList = CourseMirror_Survey.getStudentResponseList(excelfile, course, week, type, withSource=False)
            if len(student_summaryList) == 0: continue
            
            path = folder + str(week)+ '/'
            fio.NewPath(path)
            filename = path + type + '.' + method + '.key'
            
            sennafile = sennadatadir + "senna." + str(week) + "." + type + '.output'
            if not fio.IsExist(sennafile): continue
            
            phrases = getKeyPhrases(student_summaryList, sennafile, method=method, MalformedFlilter=True)
            
            fio.SaveList(phrases, filename)

def get_max_phrase_by_ROUGE(human, systems, Cache=None):
    max_rouge = 0
    metric = 'R1-F'
    summary = None
    for system in systems:
        ref = [human]
        TmpSum = [system]
        
        cacheKey = OracleExperiment.getKey(ref, TmpSum)
        if cacheKey in Cache:
            scores = Cache[cacheKey]
            print "Hit"
        else:
            scores = OracleExperiment.getRouge(ref, TmpSum)
            Cache[cacheKey] = scores
        
        score = float(scores[OracleExperiment.RougeHeader.index(metric)]) 
        if score >= max_rouge:
            max_rouge = score
            summary = system
    
    return summary
    
def extractPhraseFromAnnotation(phrasedir, annotator, summarydir):
    for doc, lec, annotator in annotation.generate_all_files(annotation.datadir + 'json/', '.json', anotators = annotator, lectures=annotation.Lectures):
        print doc
        
        #load task
        task = annotation.Task()
        task.loadjson(doc)
        
        path = phrasedir + str(lec)+ '/'
        fio.NewPath(path)
        
        #Add a cache to make it faster
        Cache = {}
        cachefile = phrasedir + str(lec) + '/' + 'cache.json'
        if fio.IsExist(cachefile):
            with open(cachefile, 'r') as fin:
                Cache = json.load(fin)
                
        for prompt in ['q1', 'q2']:
            filename = path + prompt + '.' + method + '.key'
            cluster_output = path + prompt + '.cluster.kmedoids.sqrt.oracle.%s'%method
            summary_file = os.path.join(summarydir, str(lec), '%s.summary'%prompt)
            
            body = []   
            
            summaries = []
            
            phrase_summary_dict = task.get_phrase_summary_textdict(prompt)
            extracted_phrases = []
            phrase_annotation = task.get_phrase_annotation(prompt)
            for rank in sorted(phrase_annotation):
                rank_phrases = []
                phrases = phrase_annotation[rank]
                for phrasedict in phrases:
                    phrase = phrasedict['phrase'].lower()
                    extracted_phrases.append(phrase)
                    rank_phrases.append(phrase)
                    row = [phrase, rank]
                    body.append(row)
                
                rank_summary = phrase_summary_dict[rank]
                max_summary = get_max_phrase_by_ROUGE(rank_summary, rank_phrases, Cache)
                print max_summary
                
                summaries.append(max_summary)
                
            fio.SaveList(extracted_phrases, filename)
            
            fio.WriteMatrix(cluster_output, body, header = None)
            
            fio.SaveList(summaries, summary_file)
            
            with open(cachefile, 'w') as outfile:
                json.dump(Cache, outfile, indent=2)

def extractPhraseFromAnnotationUnion(phrasedir, annotators):
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
        
        path = phrasedir + str(lec)+ '/'
        fio.NewPath(path)
        
        for prompt in ['q1', 'q2']:
            filename = path + prompt + '.' + method + '.key'
            print filename
            
            extracted_phrases = []
            phrase_annotation0 = task0.get_phrase_annotation(prompt)
            phrase_annotation1 = task1.get_phrase_annotation(prompt)
            
            aligner = AlignPhraseAnnotation(task0, task1, prompt)
            aligner.align()
            extracted_phrases = aligner.get_union()
                       
            fio.SaveList(extracted_phrases, filename)

def extractPhraseFromAnnotationIntersect(phrasedir, annotators):
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
        
        path = phrasedir + str(lec)+ '/'
        fio.NewPath(path)
        
        for prompt in ['q1', 'q2']:
            filename = path + prompt + '.' + method + '.key'
            print filename
            
            extracted_phrases = []
            phrase_annotation0 = task0.get_phrase_annotation(prompt)
            phrase_annotation1 = task1.get_phrase_annotation(prompt)
            
            aligner = AlignPhraseAnnotation(task0, task1, prompt)
            aligner.align()
            extracted_phrases = aligner.get_intersect()
                       
            fio.SaveList(extracted_phrases, filename)
                                        
if __name__ == '__main__':
    course = sys.argv[1]
    maxWeek = int(sys.argv[2])
    system = sys.argv[3]
    method = sys.argv[4]
    
    sennadir = "../data/"+course+"/senna/"
    excelfile = "../data/CourseMIRROR/reflections.json"
            
    phrasedir = "../data/"+course+"/"+system+"/phrase/"
    fio.NewPath(phrasedir)
    
    summarydir = "../data/"+course+"/"+system+"/ClusterARank/"
    fio.NewPath(summarydir)
    
    if method == 'syntax':
        extractPhrase(excelfile, phrasedir, sennadir, method=method)
    elif method == 'annotator1':
        extractPhraseFromAnnotation(phrasedir, annotation.anotators[:1], summarydir)
    elif method == 'annotator2':
        extractPhraseFromAnnotation(phrasedir, annotation.anotators[-1:], summarydir)
    elif method == 'union':
        extractPhraseFromAnnotationUnion(phrasedir, annotation.anotators)
    elif method == 'intersect':
        extractPhraseFromAnnotationIntersect(phrasedir, annotation.anotators)
    print "done"
    