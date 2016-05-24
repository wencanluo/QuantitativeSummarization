import OracleExperiment
import fio
import numpy
import json
import os
from numpy import average
import codecs

tmpdir = "../data/tmp/"
RougeHeader = ['R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F',]
RougeHeaderSplit = ['R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F','R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F','R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F',]
RougeNames = ['ROUGE-1','ROUGE-2', 'ROUGE-SUX']

def getRouge(datadir, maxWeek, output):
    sheets = range(0, maxWeek)
    
    body = []
    
    for sheet in sheets:
        week = sheet + 1
        dir = datadir + str(week) + '/'
        
        for type in ['q1', 'q2']:
            summary_file = dir + type + "." + 'summary'
            print summary_file
            
            if not fio.IsExist(summary_file): 
                print summary_file
                continue
            
            Cache = {}
            cachefile = os.path.join(datadir, str(week), 'cache.json')
            print cachefile
            if fio.IsExist(cachefile):
                with open(cachefile, 'r') as fin:
                    Cache = json.load(fin)
            
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
            
            row = [week]
            row = row + scores
            
            body.append(row)
        
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
    
if __name__ == '__main__':
    import sys
    
    course = sys.argv[1]
    maxWeek = int(sys.argv[2])
    system = sys.argv[3]
    posfix = sys.argv[4]
    
    datadir = "../data/"+course+"/"+system+ '/ClusterARank/'
    output = '../data/%s/%s/rouge_%s.txt' % (course, system, posfix)
    
    getRouge(datadir, maxWeek, output)
                     
    print "done"
