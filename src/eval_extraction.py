from eval import CRFEval
import fio
import crf
import sys

if __name__ == '__main__':
    
    #course = sys.argv[1]
    course = "CS0445"
    
    class_index_dict_file = '../data/%s/class_dict.json'%course
    
    output = '../data/%s/phrase_extraction.txt'%course
    
    body = []
    head = ['system', 'test', 'precision', 'recall', 'F-measure']
    #for system in ['QPS_NP', 'QPS_A1_N', 'QPS_A1_Y', 'QPS_A2_N', 'QPS_A2_Y', 'QPS_union', 'QPS_intersect', 'QPS_combine']:
    for system in ['QPS_NP', 'QPS_combine']:
            crf_sub_output = '../data/%s/%s/extraction/all_output/'%(course, system)
    
            eval = CRFEval(class_index_dict_file, crf_sub_output)
                
            eval.get_label_accuracy()
            eval.get_mention_precision()
            eval.get_mention_recall()
            eval.get_mention_F_measure()
            
            for test in sorted(eval.dict):
                if test.startswith('overall'): continue
                
                #row = [system, eval.dict['overall_accuracy']['value'], eval.dict['overall_mention_precision']['value'],eval.dict['overall_mention_recall']['value'], eval.dict['overall_mention_F_measure']]
                row = [system, test, eval.dict[test]['mention_precision']['value'],eval.dict[test]['mention_recall']['value'], eval.dict[test]['mention_F_measure']]
                body.append(row)
            
            eval.get_sentence_label_accuracy()
            print 'accuracy:%.4f (%d/%d)' % (eval.dict['sentence_accuracy']['value'], eval.dict['sentence_accuracy']['correct'], eval.dict['sentence_accuracy']['total'])
            
            #print 'accuracy:%.4f\tprecision:%.4f\trecall:%.4f\tF-measure:%.4f'%(eval.dict['overall_accuracy']['value'], eval.dict['overall_mention_precision']['value'],eval.dict['overall_mention_recall']['value'], eval.dict['overall_mention_F_measure'])
    
    fio.WriteMatrix(output, body, head)
    
