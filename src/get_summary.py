import annotation
import os
import fio
import NLTKWrapper
import numpy
import sys

def get_phrase_reference_summary_phrase(outputs = None):
    
    for output in outputs:
        fio.NewPath(output)
        
        counts = []
        for doc, lec, annotator in annotation.generate_all_files(annotation.datadir + 'json/', '.json', anotators = ['Youngmin', 'Trevor']):
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
                    
                    count = 0
                    for summary in summaries:
                        count += len(NLTKWrapper.wordtokenizer(summary))
                    
                    counts.append(count)
                    fio.SaveList(summaries, summary_filename)
        
        print counts
        print numpy.mean(counts)
        print numpy.median(counts)
        
if __name__ == '__main__':
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
    
    