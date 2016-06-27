import OracleExperiment
import fio
import numpy
import json
import os
from numpy import average
import codecs
import numpy as np

tmpdir = "../data/tmp/"
RougeHeader = ['R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F',]
RougeHeaderSplit = ['R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F','R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F','R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F',]
RougeNames = ['ROUGE-1','ROUGE-2', 'ROUGE-SUX']

metric='R1-F'
RIndex = RougeHeader.index(metric)
assert(RIndex != -1)

def getRouge(datadir, maxWeek, output):
    sheets = range(0, maxWeek)
    
    body = []
    allbody = []
    
    #Krange = range(1, 25)
    #Krange = range(1, 25)
    Krange = [gK]
    
    for sheet in sheets:
        week = sheet + 1
        dir = datadir + str(week) + '/'
        
        for type in ['q1', 'q2']:
            
            maxS = 0
            maxK = -1
            maxScore = []
            
            Cache = {}
            cachefile = os.path.join(datadir, str(week), 'cache.json')
            print cachefile
            if fio.IsExist(cachefile):
                with open(cachefile, 'r') as fin:
                    Cache = json.load(fin)
            
            allrow = [week]
            
            #Krange = [np.random.randint(1, 25)]
            
            for K in Krange:
            
                summary_file = dir + type + '.%d.summary'%K
                
                print summary_file
                
                if not fio.IsExist(summary_file): 
                    print summary_file
                    continue
                
                
                
                #read TA's summmary
                refs = []
                for i in range(2):
                    reffile = os.path.join(datadir, str(week), type + '.ref.%d' %i)
                    if not fio.IsExist(reffile):
                        print reffile
                        continue
                        
                    lines = fio.ReadFile(reffile)
                    ref = [line.strip() for line in lines]
                    refs.append(ref)
                
                if len(refs) == 0: continue
                  
                lstref = refs[0] + refs[1]
            
                lines = fio.ReadFile(summary_file)
                TmpSum = [line.strip() for line in lines]
            
                cacheKey = OracleExperiment.getKey(lstref, TmpSum)
                if cacheKey in Cache:
                    scores = Cache[cacheKey]
                    print "Hit"
                else:
                    print "Miss"
                    print summary_file
                    scores = OracleExperiment.getRouge_IE256(refs, TmpSum)
                    Cache[cacheKey] = scores
                
                s = float(scores[RIndex])
                
                allrow.append(s)
                
                if s >= maxS:
                    maxS = s
                    maxScore = scores
                    maxK = K
            
            if maxK == -1: continue
                
            row = [week]
            row = row + maxScore + [maxK]
            
            body.append(row)
            
            allrow.append(maxK)
            
            allbody.append(allrow)
        
            try:
                fio.SaveDict2Json(Cache, cachefile)
            except:
                #fio.SaveDict(Cache, cachefile + '.dict')
                pass
        
    header = ['id'] + RougeHeader
    row = ['ave']
    for i in range(1, len(header)):
        scores = [float(xx[i]) for xx in body]
        row.append(numpy.mean(scores))
    body.append(row)
    
    fio.WriteMatrix(output, body, header)
    
    fio.WriteMatrix(output + '.all', allbody, ['week'] + Krange)

def get_LexRankRouge():
    course = 'IE256_2016'
    system = 'QPS_NP'
    
    datadir = "../data/"+course+"/"+system+ '/LexRank/'
    
    posfix = 'LexRank'
    
    #cmd = "python get_summary.py %s %s" % (course, system)
    #print cmd
    #os.system(cmd)
    
    output = '../data/%s/%s/rouge_%s.txt' % (course, system, posfix)
     
    getRouge(datadir, 26, output)
    
    
if __name__ == '__main__':
    
#     get_LexRankRouge()
#     exit(-1)
#     
    import sys
    
    course = sys.argv[1]
    maxWeek = int(sys.argv[2])
    system = sys.argv[3]
    posfix = sys.argv[4]
    gK = int(sys.argv[5])
    
    datadir = "../data/"+course+"/"+system+ '/ClusterARank/'
    output = '../data/%s/%s/rouge_%s.txt' % (course, system, posfix)
    
    getRouge(datadir, maxWeek, output)
                     
    print "done"
