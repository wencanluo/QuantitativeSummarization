import json
from annotation import Task
import re

class AlignPhraseAnnotation:
    def __init__(self, task0=None, task1=None, prompt=None):
        self.t0 = task0
        self.t1 = task1
        self.prompt = prompt
        self.task = Task()
    
    def normalize_space(self, response):
        new = ''
        for c in response:
            if c in '.(),:?/': 
                c = ' '
            
            if c == "'":
                c = " '"
            new += c
        
        response = new
        
        response = response.replace('>', '> ')
        response = response.rstrip()
        response = ' '.join(response.split())
        response = response.replace(' >', '>')
        response = response.replace('< ', '<')
        
        response = re.sub(r'(<.*?>) (<\d>)', r'\1\2', response)
            
        return response
        
    def sequence(self, response):#use BIO
        response = self.normalize_space(response)
        #print response
        
        n_r = self.task.normalize(response)
        
        tokens = response.split(' ')
        n_tokens = n_r.split(' ')
        
        assert(len(tokens) == len(n_tokens))
        
        tags = []
        
        flag = False
        for token, n_token in zip(tokens, n_tokens):
            tag = 'O'
            if token.startswith('<'):
                flag = True
                
            if flag:
                if token.startswith('<'):
                    tag = 'B'
                else:
                    tag = 'I'
                
            if token.endswith('>'):
                flag = False
            
            tags.append(tag)
        return n_tokens, tags
     
    def extract_color(self, response, tags):
        response = self.normalize_space(response)
        #print response
        
        tokens = response.split(' ')
        
        assert(len(tokens) == len(tags))
        
        raw_colors = [int(token[-2]) if token.endswith('>') else -1 for token in tokens]
        
        colors = []
        
        color = -1
        for tag, raw_color in zip(tags[::-1], raw_colors[::-1]):
            if tag != 'O':
                if raw_color != -1:
                    color = raw_color
            else:
                color = -1
            
            colors.append(color)
            
        return colors[::-1]
        
    def align(self):
        responses0 = self.t0.get_response(self.prompt)
        responses1 = self.t1.get_response(self.prompt)
        
        self.responses = []
        for response0, response1 in zip(responses0[1:], responses1[1:]):
            assert(response0[0] == response1[0])
            if(response0[1] != response1[1]):
                print response0
                print response1
            
            tokens0, tags0 = self.sequence(response0[2])
            tokens1, tags1 = self.sequence(response1[2])
            
            if tokens0 != tokens1:
                print response0[2]
                print response1[2]
                print tokens0
                print tokens1
                continue
            
            color0 = self.extract_color(response0[2], tags0)
            color1 = self.extract_color(response1[2], tags1)
            
            dict = {'student_id': response0[0],
                        'sentence_id': response0[1],
                        'response' : tokens0,  
                        'tags' : [tags0, tags1],
                        'colors': [color0, color1],
                        }
            
            self.responses.append(dict)
        return self.responses
    
    def interset_tag(self, tags0, tags1):
        tag = []
        for t0, t1 in zip(tags0, tags1):
            if t0 == 'B':
                if t1 == 'B':
                    t = 'B' 
                elif t1 == 'I':
                    t = 'B'
                else:
                    t = 'O'
            elif t0 == 'I':
                if t1 == 'B':
                    t = 'B' 
                elif t1 == 'I':
                    t = 'I'
                else:
                    t = 'O'
            else:
                t = 'O'
                
            tag.append(t)
        return tag
    
    def union_tag(self, tags0, tags1):
        tag = []
        for t0, t1 in zip(tags0, tags1):
            if t0 == 'B':
                if t1 == 'B':
                    t = 'B' 
                elif t1 == 'I':
                    t = 'I'
                else:
                    t = 'B'
            elif t0 == 'I':
                t = 'I'
            else:
                t = t1
                
            tag.append(t)
        return tag
    
    def get_phrase(self, tokens, tags):
        phrases = []
        tmp = []
        for tag, token in zip(tags, tokens):
            if tag == 'O':
                if len(tmp) > 0:
                    phrases.append(' '.join(tmp))
                tmp = []
            elif tag == 'B':
                if len(tmp) > 0:
                    phrases.append(' '.join(tmp))
                tmp = []
                tmp.append(token)
            else:
                tmp.append(token)
        
        #last one
        if len(tmp) > 0:
            phrases.append(' '.join(tmp))
                    
        return phrases
        
    def get_union(self):
        phrases = []
        
        for d in self.responses:
            tokens = d['response']
            tags = d['tags']
            uion_tags = self.union_tag(tags[0], tags[1])
            
            for phrase in self.get_phrase(tokens, uion_tags):
                phrases.append(phrase.lower())
        
        return phrases
    
    def get_intersect(self):
        phrases = []
        
        for d in self.responses:
            tokens = d['response']
            tags = d['tags']
            uion_tags = self.interset_tag(tags[0], tags[1])
            
            for phrase in self.get_phrase(tokens, uion_tags):
                phrases.append(phrase.lower())
        
        return phrases
    
if __name__ == '__main__':
    aligner = AlignPhraseAnnotation()
    
    response = 'Choosing <the critical probability><5> is a little bit a relative subject'
    response = '<Need more clarification on the application of hypothesis testing><3>'
    response = "<critical value for><2> <hypothesis testing ><1>"
    response = 'critical value for <hypothesis testing ><1>'
    response2 = 'critical value for hypothesis testing'
    response1 = '<critical value><2> for <hypothesis testing><1>'
    #response = '<Error bounding><2> is interesting and useful'
    response = 'determining the probability of the <error><2> while rejecting <ho><4>.'
    
    response = 'Nothing,sorry:('
    tokens1, tags1 = aligner.sequence(response1)
    tokens2, tags2 = aligner.sequence(response2)
    
    color1 = aligner.extract_color(response1, tags1)
    print color1
    
#     print tokens1
#     print tags1
#     print tags2
#     tags = aligner.union_tag(tags1, tags2)
#     print aligner.get_phrase(tokens1, tags)
#     
#     tags = aligner.interset_tag(tags1, tags2)
#     print tags
#     
#     print aligner.get_phrase(tokens1, tags)
    
    