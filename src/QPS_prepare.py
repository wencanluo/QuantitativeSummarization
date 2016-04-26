import sys
import re
import fio
import xml.etree.ElementTree as ET
from collections import defaultdict
import random
import NLTKWrapper
import SennaParser
import porter

import CourseMirror_Survey

from CourseMirror_Survey import stopwords, punctuations

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

def extractPhraseFromAnnotation():
    pass

if __name__ == '__main__':
    course = sys.argv[1]
    maxWeek = int(sys.argv[2])
    system = sys.argv[3]
    method = sys.argv[4]
    
    sennadir = "../data/"+course+"/senna/"
    excelfile = "../data/CourseMIRROR/reflections.json"
            
    phrasedir = "../data/"+course+"/"+system+"/phrase/"
    
    fio.NewPath(phrasedir)
    extractPhrase(excelfile, phrasedir, sennadir, method=method)
       
    print "done"
    