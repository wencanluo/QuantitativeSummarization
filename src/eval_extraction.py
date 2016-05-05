from eval import CRFEval
import fio

if __name__ == '__main__':
    class_index_dict_file = '../data/IE256/class_dict.json'
    
    output = "log.txt"
    
    body = []
    head = ['system', 'accuracy', 'precision', 'recall', 'F-measure']
    for system in ['QPS_A1_N', 'QPS_A1_Y', 'QPS_A2_N', 'QPS_A2_Y', 'QPS_NP']:
            crf_sub_output = '../data/IE256/%s/extraction/all_output/'%system
    
            eval = CRFEval(class_index_dict_file, crf_sub_output)
                
            eval.get_label_accuracy()
            eval.get_mention_precision()
            eval.get_mention_recall()
            eval.get_mention_F_measure()
            
            row = [system, eval.dict['overall_accuracy']['value'], eval.dict['overall_mention_precision']['value'],eval.dict['overall_mention_recall']['value'], eval.dict['overall_mention_F_measure']]
            body.append(row)
            
            #print 'accuracy:%.4f\tprecision:%.4f\trecall:%.4f\tF-measure:%.4f'%(eval.dict['overall_accuracy']['value'], eval.dict['overall_mention_precision']['value'],eval.dict['overall_mention_recall']['value'], eval.dict['overall_mention_F_measure'])
    
    fio.WriteMatrix(output, body, head)
    
