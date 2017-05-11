import OracleExperiment
import fio
import numpy
import json
import os
from numpy import average
import codecs
import global_params

tmpdir = "../data/tmp/"
RougeHeader = ['R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F',]
RougeHeaderSplit = ['R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F','R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F','R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F',]
RougeNames = ['ROUGE-1','ROUGE-2', 'ROUGE-SUX']

def getRouge(datadir, maxWeek, output):
    print datadir
    
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
            except Exception as e:
                #fio.SaveDict(Cache, cachefile + '.dict')
                print e
        
    header = ['id'] + RougeHeader
    row = ['ave']
    for i in range(1, len(header)):
        scores = [float(xx[i]) for xx in body]
        row.append(numpy.mean(scores))
    body.append(row)
    
    fio.WriteMatrix(output, body, header)

def get_LexRankRouge():
    course = global_params.g_cid
    system = 'QPS_NP'
    
    datadir = "../data/"+course+"/"+system+ '/LexRank/'
    
    posfix = 'LexRank'
    
    #cmd = "python get_summary.py %s %s" % (course, system)
    #print cmd
    #os.system(cmd)
    
    output = '../data/%s/%s/rouge_%s.txt' % (course, system, posfix)
     
    getRouge(datadir, 29, output)
    

def gather_rouge():
    
    Allbody = []
    for cid in [
                'IE256',
                'IE256_2016',
                'CS0445',
                ]:
                
        ilpdir = "../data/%s/"%cid
        baseline_rougefile = os.path.join(ilpdir, 'rouge_np.txt')
        if not fio.IsExist(baseline_rougefile): continue
        
        basehead, basebody = fio.ReadMatrix(baseline_rougefile, hasHead=True)
        row = [cid, '', 'PhrasSum'] + ['%.3f'%float(x) for x in basebody[-1][1:-3]]
        Allbody.append(row)
        
        for A in ['1',
                  '2',
                  ]:
            
            for model in ['optimumComparerLSATasa', 
                          'oracle', 
                          'oracle_selection']:
                
                modeldir = os.path.join(ilpdir, 'oracle_annotator_%s'%A)
                model_rouge_file = os.path.join(modeldir, 'rouge_annotator%s_%s.txt'%(A, model))
                head, body = fio.ReadMatrix(model_rouge_file, hasHead=True)
                
                if model == 'optimumComparerLSATasa':
                    basehead1, basebody1 = fio.ReadMatrix(model_rouge_file, hasHead=True)
                elif model == 'oracle':
                    basehead2, basebody2 = fio.ReadMatrix(model_rouge_file, hasHead=True)
                
                row = [cid, 'A%s'%A, model] + ['%.3f'%float(x) for x in body[-1][1:-3]]
                
                print cid, model
                print model_rouge_file
                print baseline_rougefile
                #get p values
                from stats_util import get_ttest_pvalues
                pvalues = get_ttest_pvalues(basebody[1:-1], body[1:-1], range(1,len(head)-3))
                
                if model == 'optimumComparerLSATasa':
                    k = 3
                    for p in pvalues:
                        if p < 0.05:
                            row[k] = row[k]+'$^*$'
                        k+=1
                elif model == 'oracle':
                    pvalues1 = get_ttest_pvalues(basebody1[1:-1], body[1:-1], range(1,len(head)-3))
                    
                    k = 3
                    for p1, p2 in zip(pvalues, pvalues1):
                        if p1 < 0.05 and p2 < 0.05:
                            row[k] = row[k]+'$^{*\dag}$'
                        elif p1 < 0.05:
                            row[k] = row[k]+'$^*$'
                        elif p2 < 0.05:
                            row[k] = row[k]+'$^\dag$'
                        k+=1
                    
                elif model == 'oracle_selection':
                    pvalues1 = get_ttest_pvalues(basebody1[1:-1], body[1:-1], range(1,len(head)-3))
                    pvalues2 = get_ttest_pvalues(basebody2[1:-1], body[1:-1], range(1,len(head)-3))
                    
                    k = 3
                    for p1, p2, p3 in zip(pvalues, pvalues1, pvalues2):
                        if p1 >= 0.05 and p2 >= 0.05 and p3>=0.05:
                            k+=1
                            continue
                        
                        row[k] = row[k]+'$^{'
                        
                        if p1 < 0.05:
                            row[k] = row[k]+'*'
                        if p2 < 0.05:
                            row[k] = row[k]+'\dag'
                            
                        if p3 < 0.05:
                            row[k] = row[k]+'\circ'
                        
                        row[k] = row[k]+'}$'
                        k+=1
                
                Allbody.append(row)

    output = '../data/rouge_oracle_all_gather.txt'
    fio.Write2Latex(output, Allbody, [''] + head)

            
if __name__ == '__main__':
    
#     gather_rouge()
#     exit(-1)
#     get_LexRankRouge()
#     exit(-1)
#     
    import sys
    
    course = sys.argv[1]
    maxWeek = int(sys.argv[2])
    system = sys.argv[3]
    posfix = sys.argv[4]
    
    datadir = "../data/"+course+"/"+system+ '/ClusterARank/'
    output = '../data/%s/%s/rouge_%s.txt' % (course, system, posfix)
    
    print output
    
    getRouge(datadir, maxWeek, output)
                     
    print "done"
