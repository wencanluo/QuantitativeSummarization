#!/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-

'''
CRF wrapper for wapiti
'''

from classifier import *
import os, codecs

class CRF(Classifier):
    '''
    The Wrapper of the Wapiti CRF
    '''
    def __init__(self, root=None):
        '''
        @param root: string, the root folder of the Wapiti toolkit, it should contain the execute file
        '''
        self.root = root
       
    def train(self, training_set_file, pattern_file, model_file):
        '''
        @param training_set_file, the crf feature file for the training set
        @param pattern_file, the feature pattern file
        @param model_file, the output model
        '''
        print "training..."
        script = os.path.join(self.root, 'wapiti.exe')
        cmd = ' '.join([script, 'train', '-e 0.00002 -t 1 -T crf -a l-bfgs -1 0 -2 1 --histsz 5', '-p', pattern_file, training_set_file, model_file])
        print cmd
        os.system(cmd)
    
    def predict(self, test_file, model_file, output_file):
        '''
        do the decoding, use the post-probability decoding
        '''
        
        print "testing..."
        script = os.path.join(self.root, 'wapiti.exe')
        cmd = ' '.join([script, 'label', '-p -m', model_file, test_file, output_file])
        print cmd
        os.system(cmd)
    
    def read_file_raw(self, input, has_score=False):
        '''
        read the crf file: all the row will be extracted
        '''
        sentence = []
        score = None
        
        for line in codecs.open(input, "r", "utf-8"):
            line = line.strip()
            
            if len(line) == 0:
                if score:
                    try:
                        score = float(score)
                    except Exception as e:
                        score = 0
                    
                if has_score:
                    yield sentence, score
                else:
                    yield sentence
                
                sentence = []
                continue
            elif line[0] == '#': #score
                score = line.split()[-1]
                continue
                
            tmp = line.split()
            
            sentence.append( tmp )
    
    def read_file_generator_index(self, input, index=None, has_score=False):
        '''
        read the crf file: the first row is the token and the last row is the label
        '''
        data = []
        
        for x in index:
            data.append([])
        
        score = None
        
        for line in codecs.open(input, "r", "utf-8"):
            line = line.strip()
            
            if len(line) == 0:
                if score:
                    try:
                        score = float(score)
                    except Exception as e:
                        score = 0
                    yield data, score
                else:
                    yield data
                
                data = []
                for x in index:
                    data.append([])
            
                continue
            elif line[0] == '#': #score
                score = line.split()[2]
                continue
                
            tmp = line.split()
            
            for i, x in enumerate(index):
                if x == -1:
                    data[i].append(tmp[-1].split('/')[0])
                elif x == 0:
                    data[i].append(tmp[0].split(':')[-1])
                else:
                    data[i].append(tmp[x])
            
    def read_file_generator(self, input, has_score=False):
        '''
        read the crf file: the first row is the token and the last row is the label
        '''
        one_tokens = []
        one_labels = []
        score = None
        
        for line in codecs.open(input, "r", "utf-8"):
            line = line.strip()
            
            if len(line) == 0:
                if score:
                    try:
                        score = float(score)
                    except Exception as e:
                        score = 0
                    yield one_tokens, one_labels, score
                else:
                    yield one_tokens, one_labels
                
                one_tokens = []
                one_labels = []
                
                continue
            elif line[0] == '#': #score
                score = line.split()[2]
                continue
                
            tmp = line.split()
            
            one_tokens.append( tmp[0].split(':')[-1] )
            one_labels.append( tmp[-1].split('/')[0] )
            
    def read_file(self, input, has_score=False):
        '''
        read the crf file: only the first row (token) and the last row (label)
        '''
        tokens = []
        labels = []
        
        one_tokens = []
        one_labels = []
        scores = []
        
        score = None
        
        for line in codecs.open(input, "r", "utf-8"):
            line = line.strip()
            
            if len(line) == 0:
                tokens.append(one_tokens)
                labels.append(one_labels)
                
                one_tokens = []
                one_labels = []
                if score:
                    try:
                        score = float(score)
                    except Exception as e:
                        score = 0
                    
                    scores.append(score)
                continue
            elif line[0] == '#': #score
                score = line.split()[2]
                continue
                
            tmp = line.split()
            
            one_tokens.append( tmp[0].split(':')[-1] )
            one_labels.append( tmp[-1].split('/')[0] )
        
        if has_score:
            return tokens, labels, scores
        else:
            return tokens, labels
    
    def read_npost_output(self, input, tags):
        '''
        read the crf file (with the nbest post probability for each tags): only the first row (token) and the last row (label)
        '''
        sentence_count = 0
        
        one_sentence = []
        for line in codecs.open(input, "r", "utf-8"):
            line = line.strip()
            
            if len(line) == 0:
                yield one_sentence
                
                one_sentence = []
                sentence_count += 1
                continue
                
            tmp = line.split()
            
            one_word = []
            one_word.append(tmp[0].split(':')[-1])  #token
            one_word.append(tmp[len(tmp)-len(tags)-1])#tag
            
            dict = {}
            for i in range(len(tags)):
                t_p = tmp[len(tmp) - i - 1].split('/')
                dict[t_p[0]] = float(t_p[1])
            
            one_word.append(dict)
            
            one_sentence.append(one_word)
                
    def write_file(self, tokens, true_tags, predict_tags, output):
        fout = codecs.open(output, "w", "utf-8")
        
        for token, true_tag, predict_tag in zip(tokens, true_tags, predict_tags):
            for t, t_tag, p_tag in zip(token, true_tag, predict_tag):
                fout.write(' '.join([t, t_tag, p_tag]))
                fout.write('\n')
            fout.write('\n')
        
class CRF_Vertibi(CRF):
    def predict(self, test_file, model_file, output_file):
        '''
        use the vertibi decoding
        '''
        print "testing..."
        script = os.path.join(self.root, 'wapiti')
        cmd = ' '.join([script, 'label', '-m', model_file, test_file, output_file])
        print cmd
        os.system(cmd)

class CRF_Score(CRF):
    def predict(self, test_file, model_file, output_file):
        '''
        output the score as probability
        '''
        print "testing..."
        script = os.path.join(self.root, 'wapiti')
        cmd = ' '.join([script, 'label', '-s -p -m', model_file, test_file, output_file])
        print cmd
        os.system(cmd)

class CRF_Interpolation(CRF):
    '''
    interplation of two models
    '''
    def predict(self, test_file, model_file, model_file2, flambda, output_file):
        print "testing..."
        script = os.path.join(self.root, 'wapiti')
        cmd = ' '.join([script, 'label', '-p -m', model_file, '--model2', model_file2, '--lamda', flambda, test_file, output_file])
        print cmd
        os.system(cmd)
        
class CRF_Score_Nbest(CRF):
    '''
    output the n-best with scores
    '''
    def predict(self, test_file, model_file, output_file):
        print "testing..."
        script = os.path.join(self.root, 'wapiti')
        cmd = ' '.join([script, 'label', '-s -n 10 -p -m', model_file, test_file, output_file])
        print cmd
        os.system(cmd)
        
class CRF_NoPattern(CRF):
    '''
    train a crf model without using the pattern file
    '''
    def train(self, training_set_file, model_file):
        '''
        @param training_set_file, the crf feature file for the training set
        @param model_file, the output model
        '''
        print "training..."
        script = os.path.join(self.root, 'wapiti')
        cmd = ' '.join([script, 'train', '-e 0.00002 -t 1 -T crf -a l-bfgs -1 0 -2 1 --histsz 5', training_set_file, model_file])
        print cmd
        os.system(cmd)
        
    def predict(self, test_file, model_file, output_file):
        print "testing..."
        script = os.path.join(self.root, 'wapiti')
        cmd = ' '.join([script, 'label', '-c -p -m', model_file, test_file, output_file])
        print cmd
        os.system(cmd)

if __name__ == '__main__':
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config.read('/lm/scratch/wencan_luo/wencan_luo/cws_slu/config/default.cfg')
    
    cwc_train_output = config.get('cwc', 'cwc_train_output_npost')
    cwc_test_output = config.get('cwc', 'cwc_test_output_npost')
    
    cwc_train_json_output = config.get('cwc', 'cwc_train_output_npost_json')
    cwc_test_json_output = config.get('cwc', 'cwc_test_output_npost_json')
    
    import time
    time_start = time.clock()
    
    tags=['b', 'i', 'e', 's']
    
    crf = CRF()
    
    time_end = time.clock()
    print "running time: %s" % (time_end - time_start)
    
    