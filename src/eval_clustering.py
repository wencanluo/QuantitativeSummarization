import fio
import sys
import annotation
import os
import numpy
from collections import defaultdict, Counter


phrase_exe = '.key'
color_exe  = '.key.color'
sum_exe = '.summary'
sum_count_exe = '.summary.no'
ref_exe = '.ref'

cdcluster = 'ct.svm.default'
lsacluster = 'optimumComparerLSATasa'

class EvalCluster:
    def __init__(self, key_prefix, cluster_file, N):
        '''
        N is number of annotators
        '''
        
        self.key_prefix = key_prefix
        self.cluster_file = cluster_file
        self.N = N
        
        #load phrase color map
        phrasefile = key_prefix + phrase_exe
        phrases = fio.LoadList(phrasefile)
        self.phrases = phrases
        
        colorfile = key_prefix + color_exe
        color_map = fio.LoadDictJson(colorfile)
        
        phrase_color_map = self.combine_phrase_color(phrases, color_map)
        
        #get phrase summary color map
        sumfile = cluster_file
        body = fio.ReadMatrix(cluster_file, False)
        clusterphrases = [row[0] for row in body]
        clusterids = [row[1] for row in body]
            
        self.cluster_color = self.get_summary_color(clusterphrases, clusterids, phrase_color_map)
        
        
    def combine_phrase_color(self, phrases, color_map):
        phrase_color_map = {}
        
        assert(len(phrases) == len(color_map))
        
        for phrase, color_list in zip(phrases, color_map):
            if phrase not in phrase_color_map:
                phrase_color_map[phrase] = [[] for i in range(self.N)]
            
            for i,colors in enumerate(color_list):
                phrase_color_map[phrase][i] = phrase_color_map[phrase][i] + colors
        
        return phrase_color_map
        
    def get_summary_color(self, clusterphrases, clusterids, phrase_color_map):
        dict = {}
        
        for phrase, id in zip(clusterphrases, clusterids):
            if id not in dict:
                dict[id] = []
            
            if phrase in phrase_color_map:
                dict[id].append(phrase_color_map[phrase])
            else:
                dict[id].append([])
        return dict
            
    def score_no(self):
        
        ave = []
        
        #average by annotators
        scores = []
        
        try:
            for i in range(self.N):
                tp = 0.0
                
                agreement = 0.0
                total = 0
                
                #for each cluster
                for id in self.cluster_color:
                    #get the majority
                    total += len(self.cluster_color[id])
                    
                    cluster_color_list = []
                    for phrase_colors in self.cluster_color[id]:
                        colors = phrase_colors[i]
                        
                        counter = Counter(colors)
                        phrase_color_sorted = sorted(counter, key=counter.get, reverse=True)
                        phrase_color = phrase_color_sorted[0]
                        
                        cluster_color_list.append(phrase_color)
                    
                    #count the agreement
                    counter = Counter(cluster_color_list)
                    cluster_color_sorted = sorted(counter, key=counter.get, reverse=True)
                    cluster_color = cluster_color_sorted[0]
                    
                    #count the ratio
                    agreement += counter[cluster_color]
                
                scores.append([agreement/total, len(self.cluster_color), len(self.cluster_color) + (len(self.phrases) - total)])
            
            ave = numpy.mean(scores, 0)
        
        except Exception as e:
            print e
            print self.key_prefix
            
        return list(ave) 

def evaluate_cluster(phrasedir, output):
    body = []
    
    head = ['ext', 'week', 'agreement', 'size']
    
    for ext in [cdcluster, lsacluster]:
        lectures = annotation.Lectures
        for i, lec in enumerate(lectures):
            
            for prompt in ['q1', 'q2']:
                key_prefix = os.path.join(phrasedir, str(lec), '%s.%s'%(prompt, method))
                cluster_file = os.path.join(phrasedir, str(lec), '%s.cluster.kmedoids.sqrt.%s.%s'%(prompt,ext,method))
                
                evalator = EvalCluster(key_prefix, cluster_file, len(annotation.anotators))
                
                scores = evalator.score_no()
                
                row = [ext, lec] + scores
                
                body.append(row)
    
        row = ['-', 'ave']
        for i in range(2, len(head)):
            scores = [float(xx[i]) for xx in body]
            row.append(numpy.mean(scores))
        body.append(row)
    
    fio.WriteMatrix(output, body, head)

if __name__ == '__main__':
    debug = True
    
    if not debug:
        course = sys.argv[1]
        maxWeek = int(sys.argv[2])
        system = sys.argv[3]
        method = sys.argv[4]
    else:
        #course = 'IE256_2016'
        #course = 'IE256'
        course = 'CS0445'
        maxWeek = 29
        system = 'QPS_combine'
        #system = 'QPS_NP'
        method = 'crf'
    
    phrasedir = "../data/"+course+"/"+system+"/phrase/"
    
    output =  os.path.join("../data/"+course+"/"+system, 'eva_cluster_%s.txt'%method)
    
    evaluate_cluster(phrasedir, output)