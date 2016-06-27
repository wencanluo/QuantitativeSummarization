import sys
import re
import fio
import xml.etree.ElementTree as ET
from collections import defaultdict

import postProcess
import random
import CourseMirror_Survey
import phraseClusteringKmedoid
import os

stopwords = [line.lower().strip() for line in fio.ReadFile("../data/smart_common_words.txt")]
#print "stopwords:", len(stopwords)

noremove = ['nothing', 'none']
for w in noremove:
    if w in stopwords:
        index = stopwords.index(w)
        stopwords.pop(index)

stopwords = stopwords + ['.', '?', '-', ',', '[', ']', '-', ';', '\'', '"', '+', '&', '!', '/', '>', '<', ')', '(', '#', '=']

def getTopRankPhrase(NPs, clusterids, cid, lexdict, sources):
    #get cluster NP, and scores
    dict = {}
    
    s = []
    
    for NP, id, source in zip(NPs, clusterids, sources):
        if int(id) == cid:
            dict[NP] = lexdict[NP.lower()]
            s.append(source)
    
    keys = sorted(dict, key=dict.get, reverse =True)
    
    source = set(s)
    return keys[0], source
                            
def getShallowSummary(excelfile, folder, clusterdir, K=30, method=None, similarity=None, ratio=None, lex='lexrank'):
    #K is the number of words per points
    sheets = range(0,maxWeek)
    
    for i, sheet in enumerate(sheets):
        week = i + 1
        
        for type in ['q1', 'q2', 'q3', 'q4']:
            
            path = folder + str(week)+ '/'
            fio.NewPath(path)
            filename = path + type + '.%d.summary'%ratio
            
            #produce the cluster file on the fly
            phrasefile = os.path.join(clusterdir, str(week), type + '.' + method + '.key')
            if not fio.IsExist(phrasefile): continue
            
            print excelfile, sheet, type
            
            cluster_output = clusterdir + str(week) +'/' + type + ".cluster.kmedoids." + str(ratio) + "." +similarity + '.' + method
            print cluster_output
            
            weightfile = clusterdir + str(week)+ '/' + type + '.' + method + '.' + similarity
            print weightfile
            
            if not fio.IsExist(cluster_output):
            #if True:
                print "clustering"
                phraseClusteringKmedoid.getPhraseClusterPhrase(phrasefile, weightfile, cluster_output, ratio, method=method)
            if not fio.IsExist(cluster_output): continue
            body = fio.ReadMatrix(cluster_output, False)
            
            NPCandidates = fio.ReadFile(phrasefile)
            
            lexfile = clusterdir + str(week)+ '/' + str(type) + "." + method + "."+lex+".dict"
            lexdict = fio.LoadDict(lexfile, 'float')
            
            NPs = [row[0] for row in body]
            clusterids = [row[1] for row in body]
            
            #assert(NPCandidates == NPs)
            if NPCandidates != NPs: 
                print NPCandidates
                print NPs
            
            cluster = {}
            for row in body:
                cluster[row[0]] = int(row[1])
            
            Summary = []
            
            #sort the clusters according to the number of response
            keys = postProcess.RankClusterNoSource(NPs, lexdict, clusterids)
            
            total_word = 0
            word_count = 0
            for key in keys:
                #phrase = NPs[key]
                phrase = postProcess.getTopRankPhraseNoSource(NPs, clusterids, int(key), lexdict)
                if phrase in Summary: continue
                
                word_count = len(phrase.split())
                total_word = total_word + word_count
                #if total_word <= K:
                if len(Summary) + 1 <= K:
                    Summary.append(phrase)
                    
            fio.SaveList(Summary, filename)
                        
def ShallowSummary(excelfile, datadir, clusterdir, K=30, method=None, similarity=None, ratio=None, lex='lexrank'):
    getShallowSummary(excelfile, datadir, clusterdir, K, method, similarity, ratio, lex)

def GetLexRankScore(datadir, np, outputdir):
    sheets = range(0, maxWeek)
    
    for type in ['q1', 'q2', 'q3', 'q4']:
        for sheet in sheets:
            week = sheet + 1
            
            DID = str(week) + '_' + type
            
            phrases = []
            scores = []
    
            #read Docsent
            path = datadir + str(week)+ '/'
            path = path + type + '/'
            path = path + 'docsent/'
            filename = path + DID + '.docsent'
            #print filename
            if not fio.IsExist(filename): continue
            
            tree = ET.parse(filename)
            root = tree.getroot()
            
            for child in root:
                phrases.append(child.text)
            
            #read feature
            path = datadir + str(week)+ '/'
            path = path + type + '/'
            path = path + 'feature/'
            filename = path + type + '.LexRank.sentfeature'
            
            if fio.IsExist(filename):
                tree = ET.parse(filename)
                root = tree.getroot()
                
                for child in root:
                    feature = child[0]
                    #print feature.tag, feature.attrib, feature.attrib['V']
                    #print child.tag, child.attrib
                    scores.append(feature.attrib['V'])
            else:
                for phrase in phrases:
                    scores.append("0")
                
            #write
            assert(len(phrases) == len(scores))
            
            dict = {}
            for phrase, score in zip(phrases, scores):
                dict[phrase.lower()] = score
            
            output = outputdir + str(week)+ '/' + str(type) + "." + np + ".lexrank.dict"
            fio.NewPath(outputdir + str(week)+ '/')
            fio.SaveDict(dict, output, SortbyValueflag=True)
            
            dict = {}
            for phrase, score in zip(phrases, scores):
                if phrase.lower() in dict:
                    dict[phrase.lower()] = max(score, dict[phrase.lower()])
                else:
                    dict[phrase.lower()] = score
            
            output = outputdir + str(week)+ '/' + str(type) + "." + np + ".lexrankmax.dict"
            fio.SaveDict(dict, output, SortbyValueflag=True)

def getDate(lectures, cid, lecture):
    for dict in lectures['results']:
        if dict['cid'] != cid: continue
        if dict['number'] == lecture:
            return dict['date']
    
    return ""

def PrintClusterRankSummary(datadir):
    sheets = range(0,maxWeek)
    
    lectures = fio.LoadDictJson('../data/CourseMIRROR/lectures.json')
    
    head = ['week', 'data', 'Point of Interest', "Muddiest Point"]
    body = []
    
    for i, sheet in enumerate(sheets):        
        row = []
        week = i + 1
        
        row.append(week)
        row.append(getDate(lectures, course, week))
        
        for type in ['q1', 'q2', 'q3', 'q4']:
            path = datadir + str(i+1)+ '/'
            summaryfile = path + type + '.summary'
            if not fio.IsExist(summaryfile): continue
            
            summaries = [line.strip() for line in fio.ReadFile(summaryfile)]
            
            sourcefile = path + type + '.summary.source'
            sources = [line.split(',') for line in fio.ReadFile(sourcefile)]
            
            combinedSummary = []
            for j, (summary, source) in enumerate(zip(summaries, sources)):
                summary = summary.replace('"', '\'')
                combinedSummary.append(str(j+1) + ") " + summary + " [" + str(len(source)) + "]")
            
            row.append('"' + chr(10).join(combinedSummary)+ '"') 
        
        body.append(row)
    fio.WriteMatrix(datadir + "summary.txt", body, head)
                        
if __name__ == '__main__':
    
    
    
    course = sys.argv[1]
    maxWeek = int(sys.argv[2])
    system = sys.argv[3]
    method = sys.argv[4]
    similarity = sys.argv[5] 
    K = int(sys.argv[6])
    
    excelfile = "../data/CourseMIRROR/reflections.json"
              
    clusterdir = "../data/"+course+"/"+system+"/phrase/"
    fio.NewPath(clusterdir)
      
    datadir = "../data/"+course+"/"+system+"/PhraseMead/"
    GetLexRankScore(datadir, method, clusterdir)
          
    for ratio in [K]:
        for lex in ['lexrankmax']:
            datadir = "../data/"+course+"/"+system+ '/ClusterARank/'   
            #fio.DeleteFolder(datadir)
            ShallowSummary(excelfile, datadir, clusterdir, K=5, method = method, similarity=similarity, ratio=ratio, lex=lex)

                #PrintClusterRankSummary(datadir)
    
    print "done"
    