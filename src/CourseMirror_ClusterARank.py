import sys
import re
import fio
import xml.etree.ElementTree as ET
from collections import defaultdict

import postProcess

import random

import CourseMirror_Survey
import phraseClusteringKmedoid

stopwords = [line.lower().strip() for line in fio.ReadFile("../data/smart_common_words.txt")]
#print "stopwords:", len(stopwords)

noremove = ['nothing', 'none']
for w in noremove:
    if w in stopwords:
        index = stopwords.index(w)
        stopwords.pop(index)

stopwords = stopwords + ['.', '?', '-', ',', '[', ']', '-', ';', '\'', '"', '+', '&', '!', '/', '>', '<', ')', '(', '#', '=']

DateDict = {
            'PHYS0175':
            {1:'1/5/2015',
            2:'1/7/2015',
            3:'1/9/2015',
            4:'1/12/2015',
            5:'1/14/2015',
            6:'1/16/2015',
            7:'1/21/2015',
            8:'1/23/2015',
            9:'1/26/2015',
            10:'1/28/2015',
            11:'1/30/2015',
            12:'2/2/2015',
            13:'2/4/2015',
            14:'2/6/2015',
            15:'2/9/2015',
            16:'2/11/2015',
            17:'2/13/2015',
            18:'2/16/2015',
            19:'2/18/2015',
            20:'2/20/2015',
            21:'2/23/2015',
            22:'2/25/2015',
            23:'2/27/2015',
            24:'3/2/2015',
            25:'3/4/2015',
            26:'3/6/2015',
            27:'3/16/2015',
            28:'3/18/2015',
            29:'3/20/2015',
            30:'3/23/2015',
            31:'3/25/2015',
            32:'3/27/2015',
            33:'3/30/2015',
            34:'4/1/2015',
            35:'4/3/2015',
            36:'4/6/2015',
            37:'4/8/2015',
            38:'4/10/2015',
            39:'4/13/2015',
            40:'4/15/2015',
            41:'4/17/2015',
            },

    'IE256':{
        26:'5/15/2015',
        25:'5/12/2015',
        24:'5/8/2015',
        23:'5/5/2015',
        22:'5/1/2015',
        21:'4/28/2015',
        20:'4/17/2015',
        19:'4/14/2015',
        18:'4/10/2015',
        17:'4/7/2015',
        16:'4/3/2015',
        15:'3/31/2015',
        14:'3/27/2015',
        13:'3/24/2015',
        12:'3/20/2015',
        11:'3/17/2015',
        10:'3/13/2015',
        9:'3/10/2015',
        8:'3/6/2015',
        7:'3/3/2015',
        6:'2/27/2015',
        5:'2/24/2015',
        4:'2/20/2015',
        3:'2/17/2015',
        2:'2/13/2015',
        1:'2/10/2015',
    },
    'CS2001':{
        24:'12/09/2014',
        23:'12/04/2014',
        22:'12/02/2014',
        21:'11/25/2014',
        20:'11/20/2014',
        19:'11/18/2014',
        18:'11/13/2014',
        17:'11/11/2014',
        16:'11/06/2014',
        15:'11/04/2014',
        14:'10/30/2014',
        13:'10/28/2014',
        12:'10/23/2014',
        11:'10/21/2014',
        10:'10/16/2014',
        9:'10/09/2014',
        8:'10/07/2014',
        7:'10/02/2014',
        6:'09/30/2014',
        5:'09/25/2014',
        4:'09/23/2014',
        3:'09/18/2014',
        2:'09/16/2014',
        1:'09/11/2014',
    }
}

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
                            
def getShallowSummary(excelfile, folder, sennadatadir, clusterdir, K=30, method=None, ratio=None, np=None, lex='lexrank'):
    #K is the number of words per points
    sheets = range(0,maxWeek)
    
    for i, sheet in enumerate(sheets):
        week = i + 1
        
        for type in ['q1', 'q2', 'q3', 'q4']:
            print excelfile, sheet, type
            
            student_summaryList = CourseMirror_Survey.getStudentResponseList(excelfile, course, week, type, withSource=True)
            
            ids = [summary[1] for summary in student_summaryList]
            summaries = [summary[0] for summary in student_summaryList] 
                            
            path = folder + str(week)+ '/'
            fio.NewPath(path)
            filename = path + type + '.summary'
            
            #produce the cluster file on the fly
            sennafile = sennadatadir + "senna." + str(week) + "." + type + '.output'
            if not fio.IsExist(sennafile): continue
            
            output = clusterdir + str(week) +'/' + type + ".cluster.kmedoids." + str(ratio) + "." +method + '.' + np
            weightfile = clusterdir + str(week)+ '/' + type + '.' + np + '.' + method
            #if not fio.IsExist(output):
            phraseClusteringKmedoid.getPhraseClusterAll(sennafile, weightfile, output, ratio, MalformedFlilter=True, source=ids, np=np)
            
            NPCandidates, sources = phraseClusteringKmedoid.getNPs(sennafile, MalformedFlilter=True, source=ids, np=np)
            
            #write the sources
            sourcedict = {}
            
            #for np, id in zip(NPCandidates, sources):
            
            if not fio.IsExist(output): continue
            
            body = fio.ReadMatrix(output, False)
            
            lexfile = clusterdir + str(week)+ '/' + str(type) + "." + np + "."+lex+".dict"
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
            
            #sort the clusters according to the number of phrases
            keys = postProcess.RankCluster(NPs, lexdict, clusterids, sources)
            
                        
            sumarysource = []
            
            total_word = 0
            word_count = 0
            for key in keys:
                #phrase = NPs[key]
                phrase, source = postProcess.getTopRankPhrase(NPs, clusterids, int(key), lexdict, sources)
                if phrase in Summary: continue
                
                word_count = len(phrase.split())
                total_word = total_word + word_count
                #if total_word <= K:
                if len(Summary) + 1 <= K:
                    Summary.append(phrase)
                    sumarysource.append(",".join(source))
            
            fio.SaveList(Summary, filename)
            fio.SaveList(sumarysource, filename + ".source")
            
                        
def ShallowSummary(excelfile, datadir, sennadatadir, clusterdir, K=30, method=None, ratio=None, np=None, lex='lexrank'):
    getShallowSummary(excelfile, datadir, sennadatadir, clusterdir, K, method, ratio, np, lex)

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
            print filename
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
    
    sennadir = "../data/"+course+"/senna/"
    excelfile = "../data/CourseMIRROR/reflections.json"
              
    clusterdir = "../data/"+course+"/np/"
    fio.NewPath(clusterdir)
      
    for np in ['syntax']:
        datadir = "../data/"+course+ '/mead/' + "PhraseMead/"
        GetLexRankScore(datadir, np, clusterdir)
          
    for ratio in ["sqrt"]:
        for method in ['optimumComparerLSATasa']:
            for np in ['syntax']:
                for lex in ['lexrankmax']:
                    datadir = "../data/"+course+ '/mead/'+"ClusterARank/"   
                    fio.DeleteFolder(datadir)
                    ShallowSummary(excelfile, datadir, sennadir, clusterdir, K=5, method=method, ratio=ratio, np=np, lex=lex)
    
                    PrintClusterRankSummary(datadir)
    
    print "done"
    