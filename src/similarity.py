from nltk.align import bleu_score
import Cosin
import OracleExperiment
import json
import os
import fio
import numpy as np
import porter

import global_params
from CourseMirror_Survey import stopwords

class Similarity:
    def __init__(self, prefix=""):
        self.features = {
                        'optimumComparerLSATasa':self.LSA,
                        'LexicalOverlap':self.LexicalOverlap,
                        'optimumComparerWNLin':self.LIN ,
                        'BLEU':self.BLEU ,
                        'ROUGE':self.ROUGE ,
                        'Cosine':self.Cosine ,
                        'WordEmbedding':self.WordEmbedding ,
                        #'WMD': self.WMD,
                         }
        
        self.prefix = prefix
        
        self.Cache = {}
        self.cachefile = os.path.join(prefix + 'cache.json')
        print self.cachefile
        if fio.IsExist(self.cachefile):
            with open(self.cachefile, 'r') as fin:
                self.Cache = json.load(fin)
        
        if self.prefix != '':
            self.matrixdict = {}  
            for sim in ['optimumComparerLSATasa', 'LexicalOverlap', 'optimumComparerWNLin', 'BLEU']:
                self.matrixdict[sim] = {}
                
                filename = self.prefix + sim
                
                phrases, matrix = fio.ReadMatrix(filename, hasHead = True)
                
                index = {}
                for i, p in enumerate(phrases):
                    index[p] = i
                
                self.matrixdict[sim]['index'] = index
                self.matrixdict[sim]['matrix'] = matrix
        
        self.word2vec = fio.LoadDictJson(global_params.word2vec_model)
    
    def save(self):
        fio.SaveDict2Json(self.Cache, self.cachefile)
                    
    def get_features(self, p1, p2):
        features = {}
        for name, f in self.features.items():
            features[name] = f(p1, p2)
        return features
        
    def LSA(self, p1, p2, name='optimumComparerLSATasa'):
        index = self.matrixdict[name]['index']
        matrx = self.matrixdict[name]['matrix']
        try:
            score = matrx[index[p1]][index[p2]]
        except:
            score = 0.0
        if score == 'NaN': return 0.0
        return float(score)
    
    def LexicalOverlap(self, p1, p2, name='LexicalOverlap'):
        index = self.matrixdict[name]['index']
        matrx = self.matrixdict[name]['matrix']
        try:
            score = matrx[index[p1]][index[p2]]
        except:
            score = 0.0
        if score == 'NaN': return 0.0
        return float(score)
    
    def getOverlap(self, dict1, dict2, removedstop=True):
        count = 0
        for key in dict1.keys():
            if removedstop:
                if key in stopwords: continue
            
            if key in dict2:
                count = count + 1
        return count

    def getStemDict(self, words, stem=True, removedstop=True):
        dict = {}
        
        if stem:
            words = porter.getStemming(words)
            
        for token in words.split():
            if removedstop:
                if token in stopwords: continue
            
            dict[token] = 1
            
        return dict

    def LexicalOverlap_Stop(self, p1, p2, name='LexicalOverlap'):
        removedstop = True
        
        d1 = self.getStemDict(p1, False, removedstop)
        d2 = self.getStemDict(p2, False, removedstop)
        
        overlap_count = self.getOverlap(d1, d2, removedstop)
        
        if len(d1) == 0 or len(d2) == 0: return 0.0
        
        score = 2.0*overlap_count/(len(d1)+len(d2))
        
        return score
    
    def Cosine(self, p1, p2):
        return Cosin.compare(p1, p2)
    
    def LIN(self, p1, p2, name='optimumComparerWNLin'):
        index = self.matrixdict[name]['index']
        matrx = self.matrixdict[name]['matrix']
        try:
            score = matrx[index[p1]][index[p2]]
        except:
            score = 0.0
            
        if score == 'NaN': return 0.0
        return float(score)
    
    def BLEU(self, p1, p2, name = 'BLEU'):
        index = self.matrixdict[name]['index']
        matrx = self.matrixdict[name]['matrix']
        try:
            score = matrx[index[p1]][index[p2]]
        except:
            score = 0.0
        if score == 'NaN': return 0.0
        return float(score)
    
    def ROUGE(self, p1, p2, removedstop=False):
        metric = 'R1-F'
        
        if removedstop:
            t1 = [token for token in p1.split() if token not in stopwords]
            t2 = [token for token in p2.split() if token not in stopwords]
        else:
            t1 = p1.split()
            t2 = p2.split()
        
        
        ref = [' '.join(t1)]
        TmpSum = [' '.join(t2)]
        
        cacheKey = OracleExperiment.getKey(ref, TmpSum)
        if cacheKey in self.Cache:
            scores = self.Cache[cacheKey]
        else:
            scores = OracleExperiment.getRouge(ref, TmpSum)
            self.Cache[cacheKey] = scores
        
        score = float(scores[OracleExperiment.RougeHeader.index(metric)])
        
        return score
    
    def WordEmbedding(self, p1, p2, removedstop=False):
        if removedstop:
            t1 = [token for token in p1.split() if token not in stopwords]
            t2 = [token for token in p2.split() if token not in stopwords]
        else:
            t1 = p1.split()
            t2 = p2.split()
        
        if len(t1) == 0 or len(t2) == 0: return 0.0
        
        v1 = [0.] * 300
        v2 = [0.] * 300
        #add all the word vectors
        for word in t1:
            if word in self.word2vec:
                v1 = np.add(v1, self.word2vec[word])
        
        for word in t2:
            if word in self.word2vec:
                v2 = np.add(v1, self.word2vec[word])
                
        #give the cosine
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        
        if n1==0. or n2 == 0.: return 0.
        
        return float(np.dot(v1,v2) / ( n1 * n2))
        
    #def WMD(self, p1, p2):#https://github.com/mkusner/wmd
    #    pass
    
    
if __name__ == '__main__':
    p1 = 'hypothesis testing' 
    p2 = 'null and alternative hypothesis'
    
    #s = Similarity('../data/IE256/oracle_annotator_1/phrase/14/q1.annotator1.')
    
    s = Similarity()
    print s.WordEmbedding(p1, p2)
    print s.ROUGE(p1, p2)
    
    #print s.WordEmbedding("the easy", "the hard")
    #print s.WordEmbedding("easy", "hard")
    
    #print s.LexicalOverlap("the hypothesis", "the hypothesis")
    
    