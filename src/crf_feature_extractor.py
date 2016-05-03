import json
import file_util
import codecs

class CRF_Extractor:
    '''
    extract features for the CRF model
    each line is a feature vector for a token
    '''
    def __init__(self):
        '''
        if phrase_dict_json != None: extract the phrase features
        if subtype_flag = True, extract the features by sub parse_type
        if bioe_flag = True, use the BIOE tags
        '''
        self.features = ['basic']
    
    def get_feature_names(self):
        return '_'.join(self.features)
    
    def get_i_j(self, body, i, j):
        '''
        return the value of the crf template feature u[i, j]
        intput: 
            body: [][], two-dimentionary array, representing the crf features for a sentence
            i: int, the index of i
            j: int, the index of j
        '''
        n = len(body)
        if i < 0:
            v = '_x%d'%(i)
        elif i >= n:
            v = '_x+%d'%(i-n+1)
        else:
            v = body[i][j]
        return v
    
    def extract_U_i_j(self, data_body, feature_body, i, j, tag):
        '''
        extract the U[i, j] feature, and add it to the end of each row
        intput: 
            data_body: [][], two-dimentionary array, representing the crf data for a sentence
            feature_body: [][], two-dimentionary array, the resulting feature data for a sentence
            i: int, the index of i
            j: int, the index of j
            tag: the prefix of the feature name
        '''
        for k, row in enumerate(feature_body):
            row.append('%s:%s'%(tag, self.get_i_j(data_body, k+i, j)))
    
    def extract_U_i_j_m_n(self, data_body, feature_body, i, j, m, n, tag):
        '''
        extract the U[i, j]/U[m, n] feature, and add it to the end of each row
        '''
        for k, row in enumerate(feature_body):
            row.append('%s:%s/%s'%(tag, self.get_i_j(data_body, k+i, j), self.get_i_j(data_body, k+m, n)))
    
    def extract_U_i_j_m_n_x_y(self, data_body, feature_body, i, j, m, n, x, y, tag):
        '''
        extract the U[i, j]/U[m, n]/U[x,y] feature, and add it to the end of each row
        '''
        for k, row in enumerate(feature_body):
            row.append('%s:%s/%s/%s'%(tag, self.get_i_j(data_body, k+i, j), self.get_i_j(data_body, k+m, n), self.get_i_j(data_body, k+x, y)))
    
    def extract_word_U_i_j(self, data_body, index, feature_body, i, j, tag):
        '''
        extract the U[i, j] feature, and add it to the end of each row
        '''
        for k, row in zip(index, feature_body):
            row.append('%s:%s'%(tag, self.get_i_j(data_body, k+i, j)))
    
    def extract_word_U_i_j_m_n(self, data_body, index, feature_body, i, j, m, n, tag):
        '''
        extract the U[i, j]/U[m, n] feature, and add it to the end of each row
        '''
        for k, row in zip(index, feature_body):
            row.append('%s:%s/%s'%(tag, self.get_i_j(data_body, k+i, j), self.get_i_j(data_body, k+m, n)))
    
    def extract_word_U_i_j_m_n_x_y(self, data_body, index, feature_body, i, j, m, n, x, y, tag):
        '''
        extract the U[i, j]/U[m, n] feature, and add it to the end of each row
        '''
        for k, row in zip(index, feature_body):
            row.append('%s:%s/%s/%s'%(tag, self.get_i_j(data_body, k+i, j), self.get_i_j(data_body, k+m, n), self.get_i_j(data_body, k+x, y)))
            
    def extract_bigram(self, body):
        '''
        extract the bigram feature for the crf template
        '''
        for row in body:
            row.append('b')
    
    def extract_crf_features(self, tokens, tags):
        '''
        Extract the character features, each token a line
        return: [][], two dimentionary array, representing the feature data of the sentence
        '''
    
        body = []

        words = tokens
        N = len(tokens)
        
        #first row: the word token
        for word in words:
            row = []
            row.append(word)
            body.append(row)
        
        #last row:
        tags = [tag for tag in tags]
        
        for i, tag in enumerate(tags):
            body[i].append(tag)
        
        return body
