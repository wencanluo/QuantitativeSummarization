import fio
import sys
import annotation
import os
import numpy
from collections import defaultdict
import global_params

phrase_exe = '.key'
color_exe  = '.key.color'
sum_exe = '.summary'
sum_count_exe = '.summary.no'
ref_exe = '.ref'

class EvalStudent:
    def __init__(self, key_prefix, sum_prefix, N):
        '''
        N is number of annotators
        '''
        
        self.key_prefix = key_prefix
        self.sum_prefix = sum_prefix
        self.N = N
        
        #load phrase color map
        phrasefile = key_prefix + phrase_exe
        phrases = fio.LoadList(phrasefile)
        
        colorfile = key_prefix + color_exe
        color_map = fio.LoadDictJson(colorfile)
        
        phrase_color_map = self.combine_phrase_color(phrases, color_map)
        
        #get phrase summary color map
        sumfile = sum_prefix + sum_exe
        summaries = fio.LoadList(sumfile)
        
        self.summary_color = self.get_summary_color(summaries, phrase_color_map)
        
        #get summary count
        sumcountfile =  sum_prefix + sum_count_exe
        self.summary_no = [int(x) for x in fio.LoadList(sumcountfile)]
        
        assert(len(self.summary_color) == len(self.summary_no))
        
        #load human_summary color map
        self.ref_color = []
        
        for i in range(N):
            d = {}
            ref_sumcolor_file = '%s%s.%d.color'%(sum_prefix, ref_exe, i)
            ref_sumno_file = '%s%s.%d.no'%(sum_prefix, ref_exe, i)
            
            for color, no in zip(fio.LoadList(ref_sumcolor_file), fio.LoadList(ref_sumno_file)):
                d[int(color)] = int(no)
            
            self.ref_color.append(d)
        
    def combine_phrase_color(self, phrases, color_map):
        phrase_color_map = {}
        
        assert(len(phrases) == len(color_map))
        
        for phrase, color_list in zip(phrases, color_map):
            if phrase not in phrase_color_map:
                phrase_color_map[phrase] = [[] for i in range(self.N)]
            
            for i,colors in enumerate(color_list):
                phrase_color_map[phrase][i] = phrase_color_map[phrase][i] + colors
        
        return phrase_color_map
        
    def get_summary_color(self, summaries, phrase_color_map):
        return [phrase_color_map[phrase] if phrase in phrase_color_map else [] for phrase in summaries]
            
    def score_no(self):
        
        ave = []
        
        #average by annotators
        scores = []
        
        try:
            for i in range(self.N):
                tp = 0.0
                
                color_count = defaultdict(int)
                for summary_color, summary_no in zip(self.summary_color, self.summary_no):
                    colors = summary_color[i]
                    
                    for color in set(colors):
                        #if color == -1: continue
                        
                        color_count[color] += summary_no
                        
                #precision
                #number of phrases matches the human color
                for color in color_count:
                    if color == -1: continue
                    
                    tp += min(self.ref_color[i][color], color_count[color])
                
                total_p = numpy.sum(color_count.values())
                if total_p == 0:
                    precision = 0.0
                else:
                    precision = tp  / total_p
                #precision = tp  / numpy.sum(self.summary_no)
                        
                #recall
                total_r = numpy.sum(self.ref_color[i].values())
                recall = tp / total_r
                
                #number of color in human summary extracted
                if (precision+recall) == 0:
                    f_measure = 0
                else:
                    f_measure = 2*precision*recall/(precision+recall)
            
                scores.append([precision, recall, f_measure])
            
            ave = numpy.mean(scores, 0)
        
        except Exception as e:
            print e
            print total_p, total_r
            print self.key_prefix
            
        return list(ave) 

def evaluate_student_number(phrasedir, summarydir, output):
    body = []
    
    lectures = annotation.Lectures
    for i, lec in enumerate(lectures):
        
        for prompt in ['q1', 'q2']:
            key_prefix = os.path.join(phrasedir, str(lec), '%s.%s'%(prompt, method))
            sum_prefix = os.path.join(summarydir, str(lec), '%s'%(prompt))
            
            evalator = EvalStudent(key_prefix, sum_prefix, len(annotation.anotators))
            
            scores = evalator.score_no()
            
            row = [lec] + scores
            
            body.append(row)
    
    head = ['week', 'precision', 'recall', 'f-measure']
    row = ['ave']
    for i in range(1, len(head)):
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
#         course = 'IE256_2016'
        course = global_params.g_cid
        maxWeek = 29
        system = 'QPS_combine'
#         system = 'QPS_NP'
        method = 'crf'
    
    phrasedir = "../data/"+course+"/"+system+"/phrase/"
    summarydir = "../data/"+course+"/"+system+ '/ClusterARank/'
    
    output =  os.path.join("../data/"+course+"/"+system, 'eva_student_%s.txt'%method)
    
    evaluate_student_number(phrasedir, summarydir, output)