#https://github.com/dgrtwo/ParsePy
from parse_rest.connection import register
import parse_rest

from tables import *
import json
import os
import cmd
from cmd import Cmd
import subprocess
import re
import fio

TypeMap = {"q1":'q1_summaries', "q2":'q2_summaries', "q3":'q3_summaries', "q4":'q4_summaries'}
TypeMapReverse = {"q1_summaries":'Point of Interest', "q2_summaries":'Muddiest Point', "q3_summaries":'Learning Point'}

from parse_rest.user import User

class CourseMIRROR:
    def __init__(self, app_id, api_key, master_key, config=None, system=None, method=None, similarity=None):
        register(app_id, api_key)
        
        self.old_N = 0
        self.config = config
        self.email_from = 'wencanluo.cn@gmail.com'
        self.system = system
        self.method = method
        self.similarity = similarity
    
    def get_data_top(self, table, topK, cid=None, order_by = None):
        data = {'results':[]}

        if cid == None:
            if order_by != None:
                rows = table.Query.all().order_by(order_by)
            else:
                rows = table.Query.all()
        else:
            if order_by != None:
                rows = table.Query.filter(cid=cid).order_by(order_by)
            else:
                rows = table.Query.filter(cid=cid)
        
        assert(topK <= 100)
        page = rows.limit(topK)
    
        dict = {}
        for row in page:
            for key in row.__dict__.keys():
                if key in ['_created_at', '_updated_at']: continue
                dict[key] = row.__dict__[key]
        
        data['results'].append(dict)
               
        return data
    
    def get_data(self, table, cid=None, order_by = None, withtime=False):
        data = {'results':[]}

        if cid == None:
            if order_by != None:
                rows = table.Query.all().order_by(order_by)
            else:
                rows = table.Query.all()
        else:
            if order_by != None:
                rows = table.Query.filter(cid=cid).order_by(order_by)
            else:
                rows = table.Query.filter(cid=cid)
        
        totalN = 0
        N = 100
        page = rows.limit(N)
        while(True):
            for row in page:
                dict = {}
                for key in row.__dict__.keys():
                    if not withtime:
                        if key in ['_created_at', '_updated_at']: continue
                    dict[key] = row.__dict__[key]
            
                data['results'].append(dict)
            
            totalN += N
            page = rows.skip(totalN).limit(N)
            
            if len(page) == 0:
                break
            
        return data
    
    def print_data(self, table, cid=None):
        data = self.get_data(table, cid, withtime=True)
        
        for dict in data['results']:
            for key in dict.keys():
                print dict[key], '\t',
            print
    
    def get_lectures(self, cid=None):
        return self.get_data(Lecture, cid)
    
    def get_reflections(self, cid):
        return self.get_data(Reflection, cid)
    
    def get_questions(self, cid):
        courses = self.get_data(Course, cid)
        
        for course in courses['results']:
            return json.loads(course['questions'])
        
        return None
    
    def get_max_lecture_num(self, cid):
        reflection = self.get_data_top(Reflection, 1, cid, order_by='-lecture_number')['results']
        
        return reflection[0]['lecture_number']
    
    def remove_sumamry(self, cid):
        max_lecture = self.get_max_lecture_num(cid)
        
        try:
            summary_Object = Summarization.Query.get(cid=cid, lecture_number = max_lecture, method='ClusterARank')
            summary_Object.delete()
        except parse_rest.query.QueryResourceDoesNotExist:
            pass
    
    def getDate(self, lectures, cid, lecture):
        for dict in lectures['results']:
            if dict['cid'] != cid: continue
            if dict['number'] == lecture:
                return dict['date']
        
        return ""

    def run(self, cid, summarylastlecture=False):
        max_lecture = self.get_max_lecture_num(cid)
        print "max_lecture", max_lecture
        
#         #get reflections
#         reflections = self.get_reflections(cid)
#         jsonfile = '../data/CourseMIRROR/reflections.json' 
#         with open(jsonfile, 'w') as outfile:
#             json.dump(reflections, outfile, encoding='utf-8', indent=2)
#           
#         #get lectures
#         lectures = self.get_lectures(cid)
#         jsonfile = '../data/CourseMIRROR/lectures.json' 
#         with open(jsonfile, 'w') as outfile:
#             json.dump(lectures, outfile, encoding='utf-8', indent=2)
#           
#         self.N = len(reflections['results'])
#         print "total number of reflections:", self.N
#            
#         if self.N == self.old_N: #no need to summary
#             return
#            
#         self.old_N = self.N
#           
#         #run senna
#         os.system('python CourseMirror_Survey.py ' + str(cid) + ' ' +  str(max_lecture))
#             
#         cmd = 'cmd /C "runSennaCourseMirror.bat '+str(cid)+ ' ' + str(max_lecture) + '"'
#         os.system(cmd)
#            
        cmd = 'python QPS_prepare.py ' + str(cid) + ' ' +  str(max_lecture) + ' ' + str(self.system) + ' ' + str(self.method)
        os.system(cmd)
#                     
#         #     . get PhraseMead input (CourseMirror_MeadPhrase.py)
#         cmd = 'python CourseMirror_MeadPhrase.py ' + str(cid) + ' ' +  str(max_lecture) + ' ' + str(self.system) + ' ' + str(self.method)
#         print cmd
#         os.system(cmd)
#              
#         olddir = os.path.dirname(os.path.realpath(__file__))
#              
#         #     . get PhraseMead output
#         meaddir = '/cygdrive/e/project/Fall2014/summarization/mead/bin/'
#         cmd = './get_mead_summary_phrase_qps.sh ' + str(cid) + ' ' +  str(max_lecture) + ' ' + str(self.system)
#         os.chdir(meaddir)
#         retcode = subprocess.call([cmd], shell=True)
#         print retcode
#         subprocess.call("exit 1", shell=True)
#              
#         os.chdir(olddir)
#         #     . get LSA results (CourseMirrorphrase2phraseSimilarity.java)
#         cmd = 'cmd /C "runLSA.bat '+str(cid)+ ' ' + str(max_lecture) + ' ' + str(self.system) + ' ' + str(self.method) + '"'
#         os.system(cmd)
#              
        #     . get ClusterARank (CourseMirror_phraseClusteringbasedShallowSummaryKmedoid-New-Malformed-LexRank.py)
#         cmd = "python CourseMirror_ClusterARank.py %s %d %s %s %s" %(cid, max_lecture, self.system, self.method, self.similarity)
#         print cmd
#         os.system(cmd)
#             
#         cmd = "python get_summary.py %s %s" % (cid, self.system)
#         print cmd
#         os.system(cmd)
#         
        cmd = "python get_Rouge.py %s %d %s" % (cid, max_lecture, self.system)
        print cmd
        os.system(cmd)
        
if __name__ == '__main__':
    
    import ConfigParser
    import sys
    
    course = sys.argv[1]
    
    config = ConfigParser.RawConfigParser()
    config.read('../config/config_'+course+'.cfg')
    
    cid = config.get('course', 'cid')
    
    #system = 'phrasesummarization'
    #method = 'syntax'

#     system = 'oracle_annotator_1'
#     method = 'annotator1'
#     similarity = 'oracle'
     
    
    system = 'oracle_annotator_2'
    method = 'annotator2'
    similarity = 'oracle'
    
#     system = 'oracle_union'
#     method = 'union'
#     
#     system = 'oracle_intersect'
#     method = 'intersect'
    
    course_mirror_server = CourseMIRROR(config.get('Parse', 'PARSE_APP_ID'), 
                                        config.get('Parse', 'PARSE_REST_API_KEY'), 
                                        config.get('Parse', 'PARSE_MASTER_KEY'),
                                        config,
                                        system,
                                        method,
                                        similarity,
                                        )
    
    course_mirror_server.run(cid, summarylastlecture=config.getint('course', 'summarylastlecture'))
    
    
    