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
import numpy as np
from AlignPhraseAnnotation import AlignPhraseAnnotation
from crf import CRF
import global_params

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

def compare_length(annotator, output):
    students = set()
    
    lengthes = defaultdict(list)
    body = []
    for doc, lec, annotator in annotation.generate_all_files(annotation.datadir + 'json/', '.json', anotators = annotator, lectures=annotation.Lectures):
        print doc
        
        #load task
        task = annotation.Task()
        task.loadjson(doc)
        
        for prompt in ['q1', 'q2']:
            #for each lecture, prompt
            row = [lec, prompt]
            
            stu = set()
            
            #number of students
            dict = {}
            raw_responses = task.get_raw_response(prompt)
            for response_row in raw_responses[1:]:
                student_id, response = response_row['student_id'], response_row['response']
                student_id = student_id.lower()
                
                if student_id not in dict:
                    dict[student_id] = []
                dict[student_id].append(response)
            
            for stu in dict:
                
                lengthes[prompt].append(len(' '.join(dict[stu]).split()))
    
    import stats_util
    print '%s\t%f\t%f\t%f'%(course, np.mean(lengthes['q1']), np.mean(lengthes['q2']), stats_util.ttest(lengthes['q1'], lengthes['q2'], 2, 2)[-1])
    
def extractStatistics(annotator, output):
    
    students = set()
    
    body = []
    for doc, lec, annotator in annotation.generate_all_files(annotation.datadir + 'json/', '.json', anotators = annotator, lectures=annotation.Lectures):
        print doc
        
        #load task
        task = annotation.Task()
        task.loadjson(doc)
        
        for prompt in ['q1', 'q2']:
            #for each lecture, prompt
            row = [lec, prompt]
            
            stu = set()
            
            #number of students
            wc = 0.0
            dict = {}
            raw_responses = task.get_raw_response(prompt)
            for response_row in raw_responses[1:]:
                student_id, response = response_row['student_id'], response_row['response']
                student_id = student_id.lower()
                
                if student_id not in dict:
                    dict[student_id] = []
                dict[student_id].append(response)
                students.add(student_id)
                stu.add(student_id)
                
                wc += len(response.split())
            
            response_number = len(dict)
            row.append(response_number) #number of responses
            row.append(wc)              #word count
            row.append(wc/response_number) #averaged number of words per response
            
            phrase_summary_dict = task.get_phrase_summary_textdict(prompt)
            extracted_phrases = []
            phrase_annotation = task.get_phrase_annotation(prompt)
            
            stu_h = set()
            ph_c = 0
            for rank in sorted(phrase_annotation):
                phrases = phrase_annotation[rank]
                ph_c += len(phrases)
                for phrasedict in phrases:
                    phrase = phrasedict['phrase'].lower() #phrase
                    extracted_phrases.append(phrase)
                    
                    student_id = phrasedict['student_id'].lower().strip()
                    stu_h.add(student_id)
                    
            row.append(ph_c) #phrase count
            coverage = stu.intersection(stu_h)
            coverage_ratio = len(coverage)*1.0 / len(stu)
            row.append(coverage_ratio)
            
            body.append(row)
    
    #add average
    head = ['lec', 'prompt', 'Response', 'Word', 'Word/Response', 'Highlights', 'Coverage']
    
    row = ['', 'ave']
    for i in range(2, len(head)):
        scores = [float(xx[i]) for xx in body]
        row.append(np.mean(scores))
    body.append(row)
    
    #add std
    row = ['', 'std']
    for i in range(2, len(head)):
        scores = [float(xx[i]) for xx in body]
        row.append(np.std(scores))
    body.append(row)
    
    fio.WriteMatrix(output, body, head)
    
    print(len(students))        
                    
def extractPhraseFromAnnotation(phrasedir, annotator, summarydir=None):
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
            
            if summarydir:
                fio.NewPath(os.path.join(summarydir, str(lec)))
                summary_file = os.path.join(summarydir, str(lec), '%s.summary'%prompt)
            
            body = []   
            
            if summarydir:
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
                
                if summarydir:
                    rank_summary = phrase_summary_dict[rank]
                    max_summary = get_max_phrase_by_ROUGE(rank_summary, rank_phrases, Cache)
                    print max_summary
                    
                    summaries.append(max_summary)
                
            fio.SaveList(extracted_phrases, filename)
            
            fio.WriteMatrix(cluster_output, body, header = None)
            
            if summarydir:
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

def extractPhraseFromCRF(phrasedir, systemdir):
    crf_reader = CRF()
    aligner = AlignPhraseAnnotation()
    
    lectures = annotation.Lectures
    for i, lec in enumerate(lectures):
        path = phrasedir + str(lec)+ '/'
        fio.NewPath(path)
        
        for prompt in ['q1', 'q2']:
            filename = path + prompt + '.' + method + '.key'
            phrases = []
            
            crf_file = os.path.join(systemdir, 'extraction', 'all_output', 'test_%i_%s.out'%(i, prompt))
            for tokens, tags in crf_reader.read_file_generator(crf_file):
                for phrase in aligner.get_phrase(tokens, tags):
                    phrases.append(phrase.lower())
                    
            fio.SaveList(phrases, filename)

def extractPhraseFromCRFWithColor(phrasedir, systemdir):
    crf_reader = CRF()
    aligner = AlignPhraseAnnotation()
    
    lectures = annotation.Lectures
    for i, lec in enumerate(lectures):
        path = phrasedir + str(lec)+ '/'
        fio.NewPath(path)
        
        for prompt in ['q1', 'q2']:
            filename = path + prompt + '.' + method + '.key'
            extracted_phrases = []
            extracted_colors = []
            
            crf_file = os.path.join(systemdir, 'extraction', 'all_output', 'test_%i_%s.out'%(i, prompt))
            for tokens, tags, color0, color1 in crf_reader.read_file_generator_index(crf_file, [0, -1, -4, -3]):
                phrases, phrase_colors = aligner.get_phrase_with_colors(tokens, tags, [color0, color1])
                
                for phrase, phrase_color in zip(phrases, phrase_colors):
                    
                    extracted_phrases.append(phrase.lower())
                    extracted_colors.append(phrase_color)
            
            fio.SaveList(extracted_phrases, filename)
            
            filename = path + prompt + '.' + method + '.key.color'
            fio.SaveDict2Json(extracted_colors, filename)
                
if __name__ == '__main__':
#     course = global_params.g_cid
#     output = "../data/"+course + '/length.txt'
#     compare_length(annotation.anotators[:1], output)
#     exit(-1)
    
    course = sys.argv[1]
    maxWeek = int(sys.argv[2])
    system = sys.argv[3]
    method = sys.argv[4]
    
    sennadir = "../data/"+course+"/senna/"
    excelfile = "../data/CourseMIRROR/reflections.json"
            
    systemdir = "../data/"+course+"/"+system+"/"
    fio.NewPath(systemdir)
    
    phrasedir = "../data/"+course+"/"+system+"/phrase/"
    fio.NewPath(phrasedir)
    
    summarydir = "../data/"+course+"/"+system+"/ClusterARank/"
    if summarydir:
        fio.NewPath(summarydir)

    
#     output = "../data/"+course + '/statistics.txt'
#     extractStatistics(annotation.anotators[:1], output)
#     exit(-1)
    
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
    elif method == 'crf':
        extractPhraseFromCRFWithColor(phrasedir, systemdir)
    
    print "done"
    