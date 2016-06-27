import json
import file_util
import codecs
from nltk.tag import SennaTagger
from nltk.tag import SennaChunkTagger
 
import global_params
from CourseMirror_Survey import stopwords
from annotation import prompt_words
from porter import PorterStemmer              
from collections import defaultdict
                
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
        self.features = ['pos', 'chunk', 'promptword', 'stopword', 'tf', 'rank', 'color']
        
        if 'pos' in self.features:
            self.pos_tagger = SennaTagger(global_params.sennadir)
        
        if 'chunk' in self.features:
            self.chunk_tagger = SennaChunkTagger(global_params.sennadir)
        
        self.sentences = []
        
        self.porter = PorterStemmer()
        
        self.token_dict = None
        self.bins = 50
    
    def add_sentence(self, sentence):
        self.sentences.append(sentence)
    
    def get_token_tf(self):
        self.token_dict = defaultdict(float)
        
        for tokens, _, _ in self.sentences:
            for token in self.porter.stem_tokens(tokens):
                self.token_dict[token] += 1.0
        
        self.rank_dict = defaultdict(int)
        rank_tokens = sorted(self.token_dict, key=self.token_dict.get, reverse=True)
        
        self.rank_dict = defaultdict(int)
        for i, token in enumerate(rank_tokens):
            self.rank_dict[token] = int(i*10/len(rank_tokens))
        
        for t, v in self.token_dict.items(): #normalized by the number of sentences
            x = v/len(self.sentences)
            if x > 1.0: x = 1.0
            
            self.token_dict[t] = x
        
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
    
    def extract_crf_features(self, tokens, tags, prompt, colors=None):
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
        
        if 'pos' in self.features:
            pos_tags = self.pos_tagger.tag(tokens)
            
            for i, (_, p_tag) in enumerate(pos_tags):
                body[i].append(p_tag)
        
        if 'chunk' in self.features:
            chunk_tags = self.chunk_tagger.tag(tokens)
            
            for i, (_, c_tag) in enumerate(chunk_tags):
                body[i].append(c_tag)
        
        if 'promptword' in self.features:
            for i, token in enumerate(tokens):
                if token in prompt_words[prompt]:
                    body[i].append('Y')
                else:
                    body[i].append('N')
        
        if 'stopword' in self.features:
            for i, token in enumerate(tokens):
                if token in stopwords:
                    body[i].append('Y')
                else:
                    body[i].append('N')
        
        if 'tf' in self.features:
            if self.token_dict == None:
                self.get_token_tf()
            
            for i, token in enumerate(self.porter.stem_tokens(tokens)):
                assert(token in self.token_dict)
                
                x = int(self.token_dict[token]*self.bins)
                body[i].append(str(x))
        
        if 'rank' in self.features:
            if self.rank_dict == None:
                self.get_token_tf()
            
            for i, token in enumerate(self.porter.stem_tokens(tokens)):
                assert(token in self.rank_dict)
                
                x = self.rank_dict[token]
                body[i].append(str(x))        
        
        if 'color' in self.features and colors != None:
            for color in colors:
                for i, tag in enumerate(tags):
                    body[i].append(str(color[i]))
        
        #last row:
        tags = [tag for tag in tags]
        
        for i, tag in enumerate(tags):
            body[i].append(tag)
        
        return body

if __name__ == '__main__':
    extractor = CRF_Extractor()
    
    extractor.extract_crf_features("I do not know", 'B O O B', 'q1')