from scipy.stats import ttest_rel as ttest #paired t-test
import stats_util
import fio
import os
import numpy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import annotation

def get_ttest_pvalues(body1, body2, index):
    p_values = []
    for k in index:
        X = [float(row[k]) for row in body1]
        Y = [float(row[k]) for row in body2]
        _, p = stats_util.ttest(X, Y, tail=2, type=1)
        
        p_values.append(p)
    
    return p_values

def get_pvalues(input1, input2, index):
    head, body1 = fio.ReadMatrix(input1, hasHead=True)
    head, body2 = fio.ReadMatrix(input2, hasHead=True)
    
    p_values = get_ttest_pvalues(body1[:-1], body2[:-1], index)
    return p_values

def gather_rouge(output):
    
    courses = ['IE256', 'IE256_2016', 'CS0445']
    
    rouges = [('LexRank', 'QPS_NP', 'rouge_LexRank'),
               ('PhraseSum', 'QPS_NP', 'rouge_crf_optimumComparerLSATasa'),
               ('SequenceSum', 'QPS_combine_coling', 'rouge_crf_optimumComparerLSATasa'),
               ('SimSum', 'QPS_combine_coling', 'rouge_crf_svm'),
               ('CDSum', 'QPS_combine_coling', 'rouge_crf_ct.svm.default'),
               ]
    
    baseline1 = ('PhraseSum', 'QPS_NP', 'rouge_crf_optimumComparerLSATasa')
    baseline2 = ('SequenceSum', 'QPS_combine_coling', 'rouge_crf_optimumComparerLSATasa')
    
    Header = ['course', 'name', 'R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F',]
    
    ROUGE_Head = ['id', 'R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F']
    
    ROUGE_index = [ROUGE_Head.index(name) for name in ROUGE_Head if name != 'id']
    
    xbody = []
    for course in courses:
        for name, model, method in rouges:
            datadir = '../data/%s/'%course
            
            filename = os.path.join(datadir, model, "%s.txt"%method)
            if not fio.IsExist(filename): continue
            
            baseline1_name = os.path.join(datadir, baseline1[1], "%s.txt"%baseline1[2])
            baseline2_name = os.path.join(datadir, baseline2[1], "%s.txt"%baseline2[2])
            
            if name in ['LexRank', 'SequenceSum', 'SimSum', 'CDSum']:
                pvalues1 = get_pvalues(filename, baseline1_name, ROUGE_index)
            else:
                pvalues1 = [1]*len(ROUGE_index)
            
            if name in ['SimSum', 'CDSum']:
                pvalues2 = get_pvalues(filename, baseline2_name, ROUGE_index)
            else:
                pvalues2 = [1]*len(ROUGE_index)
                
            
            head, body = fio.ReadMatrix(filename, hasHead=True)
            
            row = [course, name]
            row += ['%.3f%s%s'%(float(x),'*' if pvalues1[i] < 0.05 else '', '+' if pvalues2[i] < 0.05 else '') for i, x in enumerate(body[-1][1:])]
            
            xbody.append(row)
    
    fio.WriteMatrix(output, xbody, Header)
    

def split_rouge(filename, prefix, N=2):
    head, body = fio.ReadMatrix(filename, hasHead=True)
    
    newbodies = [[] for i in range(N)]
    
    for i, row in enumerate(body[:-1]):
        newbodies[i%N].append(row)
    
    #compute the new average
    for k in range(len(newbodies)):
        row = ['ave']
        for i in range(1, len(head)):
            scores = [float(xx[i]) for xx in newbodies[k]]
            row.append(numpy.mean(scores))
        newbodies[k].append(row)
    
    for i, newbody in enumerate(newbodies):
        fio.WriteMatrix('%s_q%d.txt'%(prefix,i+1), newbody, head)
    
def gather_rouge_split_by_prompt(output):
    courses = ['IE256', 'IE256_2016', 'CS0445']
    
    rouges = [('LexRank', 'QPS_NP', 'rouge_LexRank'),
               ('PhraseSum', 'QPS_NP', 'rouge_crf_optimumComparerLSATasa'),
               ('SequenceSum', 'QPS_combine_coling', 'rouge_crf_optimumComparerLSATasa'),
               ('SimSum', 'QPS_combine_coling', 'rouge_crf_svm'),
               ('CDSum', 'QPS_combine_coling', 'rouge_crf_ct.svm.default'),
               ]
    
    baseline1 = ('PhraseSum', 'QPS_NP', 'rouge_crf_optimumComparerLSATasa')
    baseline2 = ('SequenceSum', 'QPS_combine_coling', 'rouge_crf_optimumComparerLSATasa')
    
    Header = ['course', 'name', 'R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F',]
    
    ROUGE_Head = ['id', 'R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F']
    
    ROUGE_index = [ROUGE_Head.index(name) for name in ROUGE_Head if name != 'id']
    
    #split the rouge
    for course in courses:
            for name, model, method in rouges:
                datadir = '../data/%s/'%course
                
                prefix = os.path.join(datadir, model, "%s"%method)
                filename = os.path.join(datadir, model, "%s.txt"%method)
                
                if not fio.IsExist(filename): continue
                
                split_rouge(filename, prefix)
                
    xbody = []
    for prompt in ['q1', 'q2']:
        for course in courses:
            for name, model, method in rouges:
                datadir = '../data/%s/'%course
                 
                filename = os.path.join(datadir, model, "%s_%s.txt"%(method,prompt))
                if not fio.IsExist(filename): continue
                 
                baseline1_name = os.path.join(datadir, baseline1[1], "%s_%s.txt"%(baseline1[2],prompt))
                baseline2_name = os.path.join(datadir, baseline2[1], "%s_%s.txt"%(baseline2[2],prompt))
                 
                if name in ['LexRank', 'SequenceSum', 'SimSum', 'CDSum']:
                    pvalues1 = get_pvalues(filename, baseline1_name, ROUGE_index)
                else:
                    pvalues1 = [1]*len(ROUGE_index)
                 
                if name in ['SimSum', 'CDSum']:
                    pvalues2 = get_pvalues(filename, baseline2_name, ROUGE_index)
                else:
                    pvalues2 = [1]*len(ROUGE_index)
                     
                 
                head, body = fio.ReadMatrix(filename, hasHead=True)
                 
                row = [course, name]
                row += ['%.3f%s%s'%(float(x),'*' if pvalues1[i] < 0.05 else '', '+' if pvalues2[i] < 0.05 else '') for i, x in enumerate(body[-1][1:])]
                 
                xbody.append(row)
         
        fio.WriteMatrix(output, xbody, Header)

def save_pdf(output):
    pp = PdfPages(output)
    plt.savefig(pp, format='pdf')
    pp.close()

def get_X_Y(input, index):
    head, body = fio.ReadMatrix(input, hasHead=True)
    
    X = [int(row[0]) for row in body[:-1]] #week
    Y = [float(row[index]) for row in body[:-1]] #rouge
    
    return X, Y
    
def plot_rouge_by_time():
    
    for metric in ['R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F']:
        for prompt in ['q1', 'q2']:
            courses = ['IE256', 'IE256_2016', 'CS0445']
            
            rouges = [#('LexRank', 'QPS_NP', 'rouge_LexRank'),
                       ('PhraseSum', 'QPS_NP', 'rouge_crf_optimumComparerLSATasa'),
                       ('SequenceSum', 'QPS_combine_coling', 'rouge_crf_optimumComparerLSATasa'),
                       #('SimSum', 'QPS_combine_coling', 'rouge_crf_svm'),
                       #('CDSum', 'QPS_combine_coling', 'rouge_crf_ct.svm.default'),
                       ]
            
            baseline1 = ('PhraseSum', 'QPS_NP', 'rouge_crf_optimumComparerLSATasa')
            baseline2 = ('SequenceSum', 'QPS_combine_coling', 'rouge_crf_optimumComparerLSATasa')
            
            Header = ['course', 'name', 'R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F',]
            
            ROUGE_Head = ['id', 'R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F']
            
            ROUGE_index = [ROUGE_Head.index(name) for name in ROUGE_Head if name != 'id']
            
            metric_index = ROUGE_Head.index(metric)
            
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.set_xlabel('week', fontsize=12)
            ax.set_ylabel('Rouge', fontsize=12)
            
            plt.title('%s %s'%(metric,annotation.prompt_name[prompt]))
            plt.grid(True)
            
            colors = ['#d8b365', "#f5f5f5", "#5ab4ac"]
                
            for cid, course in enumerate(courses):
                #c = colors[cid]
                for name, model, method in rouges:
                    datadir = '../data/%s/'%course
                     
                    filename = os.path.join(datadir, model, "%s_%s.txt"%(method,prompt))
                    if not fio.IsExist(filename): continue
                     
                    X, Y = get_X_Y(filename, metric_index)
                    
                    #plt.plot(X, Y, label=metric, marker='D', color="b", alpha=0.6, )
                    plt.plot(X, Y, label='%s_%s'%(course, name), alpha=0.6, linewidth=2)
            
            #legend = plt.legend(loc='right center', shadow=True, fontsize='x-large')
            legend = plt.legend(loc='upper right', shadow=True, fontsize='small')
            
            
            pp = PdfPages('../data/%s_%s.pdf'%(metric,prompt))
            plt.savefig(pp, format='pdf')
            pp.close()
    
if __name__ == '__main__':
    
    #output = '../data/result.rouge.split.txt'
    #gather_rouge_split_by_prompt(output)
    
    plot_rouge_by_time()
    