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

import CourseMirror_Survey

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

def extractPhraseFromAnnotation(phrasedir, annotator):
    for doc, lec, annotator in annotation.generate_all_files(annotation.datadir + 'json/', '.json', anotators = annotator, lectures=annotation.Lectures):
        print doc
        
        #load task
        task = annotation.Task()
        task.loadjson(doc)
        
        path = phrasedir + str(lec)+ '/'
        fio.NewPath(path)
        
        for prompt in ['q1', 'q2']:
            filename = path + prompt + '.' + method + '.key'
            
            extracted_phrases = []
            phrase_annotation = task.get_phrase_annotation(prompt)
            for rank in sorted(phrase_annotation):
                phrases = phrase_annotation[rank]
                for phrasedict in phrases:
                    phrase = phrasedict['phrase'].lower()
                    extracted_phrases.append(phrase)
                    
            fio.SaveList(extracted_phrases, filename)

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
    
    if method == 'syntax':
        extractPhrase(excelfile, phrasedir, sennadir, method=method)
    elif method == 'annotator1':
        extractPhraseFromAnnotation(phrasedir, annotation.anotators[:1])
    elif method == 'annotator2':
        extractPhraseFromAnnotation(phrasedir, annotation.anotators[-1:])
    elif method == 'union':
        extractPhraseFromAnnotationUnion(phrasedir, annotation.anotators)
    elif method == 'intersect':
        extractPhraseFromAnnotationIntersect(phrasedir, annotation.anotators)
    print "done"
    