#!/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-

'''
Get tag accuracy, mention precision, recall and f-measure of a model
input:
    method: string, config file session name
'''

import os, file_util
import codecs
import sys

crf_ext = '.out'

class CRFEval:
    def __init__(self, class_index_dict_file=None, data_folder=None):
        if class_index_dict_file != None:
            self.class_index_dict = file_util.load_dictjson(class_index_dict_file)
            self.class_index_dict = sorted(self.class_index_dict)
            
        self.data_folder = data_folder
        self.dict = {}
    
    def get_tokens(self, input):
        tokens = []        
        
        tmp = []
        for line in codecs.open(input, 'r', 'utf-8'):
            line = line.strip()
            
            if len(line) == 0:
                tokens.append(tmp)
                tmp = []
                continue
                
            token = line.split()
            tmp.append(token[0].split(':')[-1])
            
        return tokens
    
    def get_raw_data(self, input):
        body = []
        
        sentence = []
        for line in codecs.open(input, "r", "utf-8"):
            line = line.strip()
            
            if len(line) == 0:
                body.append(sentence)
                
                sentence = []
                continue
                
            tokens = line.split()
            
            sentence.append(tokens)
        
        return body
    
    def get_labels_generator(self, input):
        one_true = []
        one_predict = []
        for line in open(input):
            line = line.strip()
            
            if len(line) == 0:
                yield one_true, one_predict
                
                one_true = []
                one_predict = []
                
                continue
                
            tokens = line.split()
            
            one_true.append( tokens[-2] )
            one_predict.append( tokens[-1] )
        
    def get_labels(self, input):
        trues = []
        predicts = []
        
        one_true = []
        one_predict = []
        for line in open(input):
            line = line.strip()
            
            if len(line) == 0:
                trues.append(one_true)
                predicts.append(one_predict)
                
                one_true = []
                one_predict = []
                
                continue
                
            tokens = line.split()
            
            one_true.append( tokens[-2] )
            one_predict.append( tokens[-1] )
        
        return trues, predicts
    
    def get_label_only(self, input):
        trues = []
        one_true = []
        for line in open(input):
            line = line.strip()
            
            if len(line) == 0:
                trues.append(one_true)
                one_true = []
                continue
                
            tokens = line.split()
            
            one_true.append( tokens[-1] )
        
        return trues
        
    def get_label_accuracy_one_file(self, input):
        metric_dict = {}
        
        trues, predicts = self.get_labels(input)
            
        if len(trues) == 0:
            metric_dict['correct'] = 0
            metric_dict['total'] = 0
            metric_dict['value'] = 0
        else:
            correct = 0
            total = 0
            for one_true, one_predict in zip(trues, predicts):
                for true, predict in zip(one_true, one_predict):
                    total += 1
                    if true == predict:
                        correct += 1
            
            metric_dict['correct'] = correct
            metric_dict['total'] = total
            if total == 0:
                metric_dict['value'] = 0
            else:
                metric_dict['value'] = float(correct) / total
        
        return metric_dict
        
    def get_label_accuracy(self):
        '''
        get the label accuracy on character level
        '''
        for parse_type in self.class_index_dict:
            if parse_type not in self.dict:
                self.dict[parse_type] = {}
                
            input = os.path.join(self.data_folder, parse_type + crf_ext)
            self.dict[parse_type]['accuracy'] = self.get_label_accuracy_one_file(input)
        
        correct = 0
        total = 0
        for parse_type in self.class_index_dict:
            metric_dict = self.dict[parse_type]['accuracy']
            correct += metric_dict['correct']
            total += metric_dict['total']
        
        metric_dict = {}
        metric_dict['correct'] = correct
        metric_dict['total'] = total
        if total == 0:
            metric_dict['value'] = 0
        else:
            metric_dict['value'] = float(correct) / total
                
        self.dict['overall_accuracy'] = metric_dict
        
        return self.dict['overall_accuracy']['value']
    
    def get_sentence_label_accuracy(self):
        '''
        get the label accuracy on character level
        '''
        for parse_type in self.class_index_dict:
            if parse_type not in self.dict:
                self.dict[parse_type] = {}
                
            input = os.path.join(self.data_folder, parse_type + crf_ext)
            trues, predicts = self.get_labels(input)
            
            if len(trues) == 0:
                metric_dict = {}
                metric_dict['correct'] = 0
                metric_dict['total'] = 0
                metric_dict['value'] = 0
                
                self.dict[parse_type]['sentence_accuracy'] = metric_dict
                continue

            correct = 0
            total = 0
            for one_true, one_predict in zip(trues, predicts):
                total += 1
                if one_true == one_predict:
                    correct += 1
            
            metric_dict = {}
            metric_dict['correct'] = correct
            metric_dict['total'] = total
            if total == 0:
                metric_dict['value'] = 0
            else:
                metric_dict['value'] = float(correct) / total
            
            self.dict[parse_type]['sentence_accuracy'] = metric_dict
        
        correct = 0
        total = 0
        for parse_type in self.class_index_dict:
            metric_dict = self.dict[parse_type]['sentence_accuracy']
            correct += metric_dict['correct']
            total += metric_dict['total']
        
        metric_dict = {}
        metric_dict['correct'] = correct
        metric_dict['total'] = total
        if total == 0:
            metric_dict['value'] = 0
        else:
            metric_dict['value'] = float(correct) / total
                
        self.dict['sentence_accuracy'] = metric_dict
        
        return self.dict['sentence_accuracy']['value']
    
    def check_error_type(self, tags, predicts_tags, i):
        #type 0: a complete miss
        #type 1: an overlap miss
        
        while tags[i] != 'O':
            if predicts_tags[i] == tags[i]: return 1
            i -= 1
        return 0
            
    def get_mention_recall_sentence(self, trues, predicts):
        tags = ['O'] + [tag for tag in trues] + ['O']
        predicts_tags = ['O'] + [tag for tag in predicts] + ['O']
        
        correct = 0
        total = 0
        complete_miss = 0
        overlap_miss = 0
        
        hit = True
        for i in range(1, len(tags)-1):
            if tags[i] != 'O':
                if tags[i] != tags[i-1]: #begin
                    hit = True
                    if predicts_tags[i] == predicts_tags[i-1] or predicts_tags[i] != tags[i]: #if the prediction doesn't start or doesn't have the same tag
                        hit = False
                    
                    if tags[i] != tags[i+1]: #single character tag
                        if predicts_tags[i] == predicts_tags[i+1]: #if the prediction doesn't end
                            hit = False
                        
                        #a mention is completed
                        total += 1
                        if hit:
                            correct += 1
                        else:
                            if self.check_error_type(tags, predicts_tags, i) == 0:
                                complete_miss += 1
                            else:
                                overlap_miss += 1
                    
                elif tags[i] == tags[i-1]:
                    if tags[i] != tags[i+1]: #end
                        if predicts_tags[i] == predicts_tags[i+1] or predicts_tags[i] != tags[i]: #if the prediction doesn't end or doesn't have the same tag
                            hit = False
                        
                        #a mention is completed
                        total += 1
                        if hit:
                            correct += 1
                        else:
                            if self.check_error_type(tags, predicts_tags, i) == 0:
                                complete_miss += 1
                            else:
                                overlap_miss += 1
                            
                    else: #inside
                        if predicts_tags[i] != tags[i]:
                            hit = False
        
        return correct, total, complete_miss, overlap_miss
    
    def get_mention_recall_one_file(self, input):
        trues, predicts = self.get_labels(input)
            #print len(trues), len(predicts)
        
        metric_dict = {}
        
        if len(trues) == 0:
            metric_dict['correct'] = 0
            metric_dict['total'] = 0
            metric_dict['value'] = 0
            metric_dict['complete_miss'] = 0
            metric_dict['overlap_miss'] = 0
        
        else:
            total = 0
            correct = 0
            complete_miss = 0
            overlap_miss = 0
            for one_true, one_predict in zip(trues, predicts):
                one_correct, one_total, one_complete_miss, one_overlap_miss = self.get_mention_recall_sentence(one_true, one_predict)
                
                total += one_total
                correct += one_correct
                complete_miss += one_complete_miss
                overlap_miss += one_overlap_miss
            
            metric_dict['correct'] = correct
            metric_dict['total'] = total
            metric_dict['complete_miss'] = complete_miss
            metric_dict['overlap_miss'] = overlap_miss
            
            if total == 0:
                metric_dict['value'] = 0
            else:
                metric_dict['value'] = float(correct) / total
        return metric_dict
        
    def get_mention_recall(self):
        '''
        get the recall on mention level, only an exact match is considered
        '''
        for parse_type in self.class_index_dict:
            if parse_type not in self.dict:
                self.dict[parse_type] = {}
                
            input = os.path.join(self.data_folder, parse_type + crf_ext)
            self.dict[parse_type]['mention_recall'] = self.get_mention_recall_one_file(input)
        
        correct = 0
        total = 0
        complete_miss = 0
        overlap_miss = 0
        for parse_type in self.class_index_dict:
            metric_dict = self.dict[parse_type]['mention_recall']
            correct += metric_dict['correct']
            total += metric_dict['total']
            complete_miss += metric_dict['complete_miss']
            overlap_miss += metric_dict['overlap_miss']
            
        metric_dict = {}
        metric_dict['correct'] = correct
        metric_dict['total'] = total
        metric_dict['complete_miss'] = complete_miss
        metric_dict['overlap_miss'] = overlap_miss
        if total == 0:
            metric_dict['value'] = 0
        else:
            metric_dict['value'] = float(correct) / total
                
        self.dict['overall_mention_recall'] = metric_dict
        
        return self.dict['overall_mention_recall']['value']
    
    def get_mention_precision_one_file(self, input):
        trues, predicts = self.get_labels(input)
        
        metric_dict = {}
        
        if len(trues) == 0:
            metric_dict['correct'] = 0
            metric_dict['total'] = 0
            metric_dict['value'] = 0
            metric_dict['complete_miss'] = 0
            metric_dict['overlap_miss'] = 0
        else:
            total = 0
            correct = 0
            complete_miss = 0
            overlap_miss = 0
            for one_true, one_predict in zip(trues, predicts):
                one_correct, one_total, one_complete_miss, one_overlap_miss = self.get_mention_recall_sentence(one_predict, one_true)
                
                total += one_total
                correct += one_correct
                complete_miss += one_complete_miss
                overlap_miss += one_overlap_miss
                
            
            metric_dict = {}
            metric_dict['correct'] = correct
            metric_dict['total'] = total
            metric_dict['complete_miss'] = complete_miss
            metric_dict['overlap_miss'] = overlap_miss
                
            if total == 0:
                metric_dict['value'] = 0
            else:
                metric_dict['value'] = float(correct) / total
        return metric_dict
        
    def get_mention_precision(self):
        '''
        get the precision on mention level, only an exact match is considered
        '''
        for parse_type in self.class_index_dict:
            if parse_type not in self.dict:
                self.dict[parse_type] = {}
                
            input = os.path.join(self.data_folder, parse_type + crf_ext)
            self.dict[parse_type]['mention_precision'] = self.get_mention_precision_one_file(input)
        
        correct = 0
        total = 0
        complete_miss = 0
        overlap_miss = 0
        for parse_type in self.class_index_dict:
            metric_dict = self.dict[parse_type]['mention_precision']
            correct += metric_dict['correct']
            total += metric_dict['total']
            complete_miss += metric_dict['complete_miss']
            overlap_miss += metric_dict['overlap_miss']
        
        metric_dict = {}
        metric_dict['correct'] = correct
        metric_dict['total'] = total
        metric_dict['complete_miss'] = complete_miss
        metric_dict['overlap_miss'] = overlap_miss
        if total == 0:
            metric_dict['value'] = 0
        else:
            metric_dict['value'] = float(correct) / total
                
        self.dict['overall_mention_precision'] = metric_dict
        
        return self.dict['overall_mention_precision']['value']
        
    def get_mention_F_measure(self):
        precision = self.dict['overall_mention_precision']['value']
        recall = self.dict['overall_mention_recall']['value']
        f_score = 2*precision*recall / (precision + recall)
        
        self.dict['overall_mention_F_measure'] = f_score
        
        return f_score
            
class CRFEval_Filter(CRFEval):
    '''
    filter out some parse types
    '''
    
    def __init__(self, class_index_dict_file=None, data_folder=None, parse_type_filters = None):
        CRFEval.__init__(self, class_index_dict_file, data_folder)
        
        parse_type_filtered = [line.rstrip(' \r\n') for line in open(parse_type_filters, 'r')]
        
        for parse_type in parse_type_filtered:
            print "@%s@" % parse_type
            self.class_index_dict.pop(parse_type)
        
        print len(self.class_index_dict)
        
def test(eval):
    #print eval.get_label_accuracy()
    #print eval.get_mention_recall()
    trues, predicts = eval.get_labels(crf_sub_output_nobie + 'event:lookupwho.crf.label')
    tokens = eval.get_tokens(crf_sub_output_nobie + 'event:lookupwho.crf.label')
    
    total = 0
    for i, (one_true, one_predict) in enumerate(zip(trues, predicts)):
        print one_true
        print one_predict
        
        one_correct, one_total, one_complete_miss, one_overlap_miss = eval.get_mention_recall_sentence(one_true, one_predict)
        print ' '.join(tokens[i])
        
        print "correct:", one_correct, "total:", one_total, "complete miss:", one_complete_miss, "overlap miss:", one_overlap_miss
        
        total += one_total
    
    print total
        
if __name__ == '__main__':
    class_index_dict_file = '../data/IE256/class_dict.json'
    crf_sub_output = '../data/IE256/QPS_A1/extraction/all_output/'
    
    eval = CRFEval(class_index_dict_file, crf_sub_output)
        
    eval.get_label_accuracy()
    print 'accuracy:%.4f (%d/%d)' % (eval.dict['overall_accuracy']['value'], eval.dict['overall_accuracy']['correct'], eval.dict['overall_accuracy']['total'])
    
    eval.get_mention_precision()
    print 'precision:%.4f (%d/%d)' % (eval.dict['overall_mention_precision']['value'], eval.dict['overall_mention_precision']['correct'], eval.dict['overall_mention_precision']['total'])
    print '\tfalse positive (no-overlap):', eval.dict['overall_mention_precision']['complete_miss'],  'wrong segmentation:', eval.dict['overall_mention_precision']['overlap_miss']
    
    eval.get_mention_recall()
    print 'recall:%.4f (%d/%d)' % (eval.dict['overall_mention_recall']['value'], eval.dict['overall_mention_recall']['correct'], eval.dict['overall_mention_recall']['total'])
    print '\tfalse negative (no-overlap):', eval.dict['overall_mention_recall']['complete_miss'],  'wrong segmentation:', eval.dict['overall_mention_recall']['overlap_miss']

    eval.get_mention_F_measure()
    print 'F-measure:%.4f' % eval.dict['overall_mention_F_measure']
    