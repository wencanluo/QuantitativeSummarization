import annotation
import os
import fio
import NLTKWrapper
import numpy
import sys
import global_params

def get_phrase_reference_summary_phrase_no(outputs = None):
    
    Numbers = []
    
    counts = []
    for doc, lec, annotator in annotation.generate_all_files(annotation.datadir + 'json/', '.json', anotators = annotation.anotators[:1], lectures=annotation.Lectures):
        print doc
        
        task = annotation.Task()
        task.loadjson(doc)
        
        sub_tasks = task.get_tasks()
        
        for sub_task in sub_tasks:
            if sub_task["task_name"] == "Phrase":
                if sub_task['prompt'] == 0: #POI
                    type = 'q1'
                else: 
                    type = 'q2'
                
                student_numbers = [row[2].strip() for row in sub_task["summary"][1:]]
                Numbers += [int(x) for x in student_numbers]
                    
    fio.SaveDict2Json(Numbers, '../data/%s_supporters.txt'%global_params.g_cid)
        
def get_phrase_reference_summary_phrase(outputs = None):
    
    for output in outputs:
        fio.NewPath(output)
        
        counts = []
        for doc, lec, annotator in annotation.generate_all_files(annotation.datadir + 'json/', '.json', anotators = annotation.anotators, lectures=annotation.Lectures):
            print doc
            
            task = annotation.Task()
            task.loadjson(doc)
            
            sub_tasks = task.get_tasks()
            
            for sub_task in sub_tasks:
                if sub_task["task_name"] == "Phrase":
                    if sub_task['prompt'] == 0: #POI
                        type = 'q1'
                    else: 
                        type = 'q2'
                    
                    summary_filename = os.path.join(output, str(lec), type+'.ref.' + str(annotation.anotator_dict[annotator])) 
                    #summary_filename = os.path.join(output, str(lec), type+'.ref.summary') 
                    
                    print summary_filename
                    
                    summaries = [row[1] for row in sub_task["summary"][1:]]
                    colors = [row[0].strip()[1] for row in sub_task["summary"][1:]]
                    student_numbers = [row[2].strip() for row in sub_task["summary"][1:]]
                    
                    count = 0
                    for summary in summaries:
                        count += len(NLTKWrapper.wordtokenizer(summary))
                    
                    counts.append(count)
                    fio.SaveList(summaries, summary_filename)
                    
                    color_filename = os.path.join(output, str(lec), '%s.ref.%s.color'%(type, str(annotation.anotator_dict[annotator])))
                    fio.SaveList(colors, color_filename)
                    
                    no_filename = os.path.join(output, str(lec), '%s.ref.%s.no'%(type, str(annotation.anotator_dict[annotator])))
                    fio.SaveList(student_numbers, no_filename)
        
        print counts
        print numpy.mean(counts)
        print numpy.median(counts)
    
def plot_reference_summary_no_distribution():
    import collections
    C = {}
        
    M = 0
    for cid in ['Engineer', 'IE256', 'IE256_2016', 'CS0445']:
        support_file = '../data/%s_supporters.txt'%cid
        supports = fio.LoadDictJson(support_file)
        
        M = max(M, max(supports))
        C[cid] = collections.Counter(supports)
    
    for cid in ['Engineer', 'IE256', 'IE256_2016', 'CS0445']:
        del C[cid][0]
        
    A = {}
    
    for i in range(1, M+1):
        for cid in ['Engineer', 'IE256', 'IE256_2016', 'CS0445']:
            if cid not in A:
                A[cid] = collections.defaultdict(float)
                
            r = C[cid][i]*1.0/sum(C[cid].values()) if i in C[cid] else 0
            A[cid][i] += r + A[cid][i-1]
    
    for i in range(1, M+1):
        for cid in ['Engineer', 'IE256', 'IE256_2016', 'CS0445']:
            print A[cid][i], '\t',
        print
         
    
if __name__ == '__main__':
#     get_phrase_reference_summary_phrase_no()
#     plot_reference_summary_no_distribution()
#     exit(-1)
    
    course = sys.argv[1]
    system = sys.argv[2]
    
    mead_datadir = "../data/%s/%s/"%(course,system)
    
    outputs =  [
                #mead_datadir + 'Mead',
                #mead_datadir + 'PhraseMead',
                #mead_datadir + 'PhraseMeadMMR',
                #mead_datadir + 'PhraseLexRank',
                #mead_datadir + 'PhraseLexRankMMR',
                #mead_datadir + 'keyphrase',
                mead_datadir + 'ClusterARank',
#                 mead_datadir + 'LexRank',
                
                #mead_datadir + 'IE256_Mead',
                #mead_datadir + 'IE256_PhraseMead',
                #mead_datadir + 'IE256_PhraseMeadMMR',
                #mead_datadir + 'IE256_PhraseLexRank',
                #mead_datadir + 'IE256_PhraseLexRankMMR',
                #mead_datadir + 'IE256_keyphrase',
                #mead_datadir + 'IE256_ClusterARank',
                #IE256_datadir + 'ILP_Sentence_MC',
                #IE256_datadir + 'ILP_Baseline_Sentence'
               ]
    
    get_phrase_reference_summary_phrase(outputs)
    
    