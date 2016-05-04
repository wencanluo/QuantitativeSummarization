from eval import CRFEval
import fio

if __name__ == '__main__':
    class_index_dict_file = '../data/IE256/class_dict.json'
    
    output = "log.txt"
    
    body = []
    head = ['annotator', 'empty', 'accuracy', 'precision', 'recall', 'F-measure']
    for annotator in ['1', '2']:
        for empty in ['N', 'Y']:
        
            system = 'QPS_A%s_%s'%(annotator, empty)
            crf_sub_output = '../data/IE256/%s/extraction/all_output/'%system
    
            eval = CRFEval(class_index_dict_file, crf_sub_output)
                
            eval.get_label_accuracy()
            eval.get_mention_precision()
            eval.get_mention_recall()
            eval.get_mention_F_measure()
            
            row = [annotator, empty, eval.dict['overall_accuracy']['value'], eval.dict['overall_mention_precision']['value'],eval.dict['overall_mention_recall']['value'], eval.dict['overall_mention_F_measure']]
            body.append(row)
            
            #print 'accuracy:%.4f\tprecision:%.4f\trecall:%.4f\tF-measure:%.4f'%(eval.dict['overall_accuracy']['value'], eval.dict['overall_mention_precision']['value'],eval.dict['overall_mention_recall']['value'], eval.dict['overall_mention_F_measure'])
    
    fio.WriteMatrix(output, body, head)
    
