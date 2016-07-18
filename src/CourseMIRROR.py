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
import global_params

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
        max_lecture = 26
#         
#         max_lecture = self.get_max_lecture_num(cid)
#         print "max_lecture", max_lecture
#           
#         #get reflections
#         reflections = self.get_reflections(cid)
#         jsonfile = '../data/CourseMIRROR/reflections.json' 
#         with open(jsonfile, 'w') as outfile:
#             json.dump(reflections, outfile, encoding='utf-8', indent=2)
#             
#         
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
#         cmd = 'python QPS_prepare.py ' + str(cid) + ' ' +  str(max_lecture) + ' ' + str(self.system) + ' ' + str(self.method)
#         os.system(cmd)
#           
#         #cmd = 'python QPS_extraction.py %s %d %s %s %s'%(cid, max_lecture, self.system, str(self.method), 'N')
#         #os.system(cmd)
#           
#         #     . get PhraseMead input (CourseMirror_MeadPhrase.py)
#         cmd = 'python CourseMirror_MeadPhrase.py ' + str(cid) + ' ' +  str(max_lecture) + ' ' + str(self.system) + ' ' + str(self.method)
#         print cmd
#         os.system(cmd)
#                     
#         olddir = os.path.dirname(os.path.realpath(__file__))
#                    
#         #     . get PhraseMead output
#         meaddir = global_params.meaddir
#         cmd = './get_mead_summary_phrase_qps.sh ' + str(cid) + ' ' +  str(max_lecture) + ' ' + str(self.system)
#         os.chdir(meaddir)
#         retcode = subprocess.call([cmd], shell=True)
#         print retcode
#         subprocess.call("exit 1", shell=True)
#         os.chdir(olddir)
#           
#         #     . get LSA results (CourseMirrorphrase2phraseSimilarity.java)
#         #cmd = 'cmd /C "runLSA.bat '+str(cid)+ ' ' + str(max_lecture) + ' ' + str(self.system) + ' ' + str(self.method) + '"'
#         cmd = 'cmd /C "runLSA_All.bat '+str(cid)+ ' ' + str(max_lecture) + ' ' + str(self.system) + ' ' + str(self.method) + '"'
#         os.system(cmd)
#               
#         # get ClusterARank (CourseMirror_phraseClusteringbasedShallowSummaryKmedoid-New-Malformed-LexRank.py)
#         cmd = "python CourseMirror_ClusterARank.py %s %d %s %s %s" %(cid, max_lecture, self.system, self.method, self.similarity)
#         print cmd
#         os.system(cmd)
#                   
#         cmd = "python get_summary.py %s %s" % (cid, self.system)
#         print cmd
#         os.system(cmd)
#                 
#         cmd = "python get_Rouge.py %s %d %s %s" % (cid, max_lecture, self.system, self.method + '_' + self.similarity)
#         print cmd
#         os.system(cmd)

def gather_rouge(output):
    datadir = '../data/%s/'%course
    
    #output = '../data/IE256/result.rouge.txt'
    
    models = ['QPS_NP', 
              #'QPS_A1_N', 'QPS_A2_N', 'QPS_union', 'QPS_intersect', 
              'QPS_combine'
              ]
    methods = ['rouge_crf_optimumComparerLSATasa',
               'rouge_crf_ct.svm.default',
               #'rouge_crf_svm', 
               #'rouge_crf_svr', 
               #'rouge_crf_ct.svm.default', 
               #'rouge_crf_ct.svr.default', 
               ]
    
    Header = ['method', 'model', 'R1-R', 'R1-P', 'R1-F', 'R2-R', 'R2-P', 'R2-F', 'RSU4-R', 'RSU4-P', 'RSU4-F',]
    
    
    xbody = []
    for method in methods:
        for model in models:
            
            filename = os.path.join(datadir, model, "%s.txt"%method)
            
            if not fio.IsExist(filename): continue
                        
            head, body = fio.ReadMatrix(filename, hasHead=True)
            
            row = [method, model]
            row += body[-1][1:]
            
            xbody.append(row)
    
    fio.WriteMatrix(output, xbody, Header)
        
if __name__ == '__main__':
    
#     exit(-1)
    
    import ConfigParser
    import sys
    
    course = sys.argv[1]
    
    config = ConfigParser.RawConfigParser()
    config.read('../config/config_'+course+'.cfg')
    
    cid = config.get('course', 'cid')
    

#     oslom_parms = '1'# -cp 0.1
    
#     cmd = 'python QPS_community_detection.py %s'%(oslom_parms)
#     os.system(cmd)
    
    N = 0
    
    for system, method, similarity in [
#                                         ('oracle_annotator_1', 'annotator1', 'optimumComparerLSATasa'),
#                                         ('oracle_annotator_2', 'annotator2', 'optimumComparerLSATasa'),
#                                         ('oracle_annotator_1', 'annotator1', 'oracle'),
#                                         ('oracle_annotator_2', 'annotator2', 'oracle'),
#                                         ('QPS_A1', 'annotator1', 'optimumComparerLSATasa'),
#                                         ('QPS_A2', 'annotator2', 'optimumComparerLSATasa'),
#                                         ('QPS_NP', 'syntax', 'optimumComparerLSATasa'),
#                                         ('QPS_NP', 'crf', 'optimumComparerLSATasa'),
#                                         ('QPS_union', 'union', 'optimumComparerLSATasa'),
#                                         ('QPS_intersect', 'intersect', 'optimumComparerLSATasa'),
#                                         ('QPS_combine', 'combine', 'optimumComparerLSATasa'),
 
#                                        ('QPS_A1', 'crf', 'optimumComparerLSATasa'),
#                                        ('QPS_A2', 'crf', 'optimumComparerLSATasa'),
#                                         ('QPS_NP', 'crf', 'optimumComparerLSATasa'),
#                                         ('QPS_union', 'crf', 'optimumComparerLSATasa'),
#                                         ('QPS_intersect', 'crf', 'optimumComparerLSATasa'),
#                                         ('QPS_combine', 'crf', 'optimumComparerLSATasa'),
 
#                                         ('QPS_A1_N', 'crf', 'svr'),
#                                         ('QPS_A2_N', 'crf', 'svr'),
#                                         #('QPS_NP', 'syntax', 'svr'),
#                                         ('QPS_union', 'crf', 'svr'),
#                                         ('QPS_intersect', 'crf', 'svr'),
#                                         ('QPS_combine', 'crf', 'svr'),
#                                          
#                                         ('QPS_A1_N', 'crf', 'svm'),
#                                         ('QPS_A2_N', 'crf', 'svm'),
#                                         #('QPS_NP', 'syntax', 'svm'),
#                                         ('QPS_union', 'crf', 'svm'),
#                                         ('QPS_intersect', 'crf', 'svm'),
                                        ('QPS_combine', 'crf', 'svm'),
 
#                                         ('QPS_A1_N', 'crf', 'ct.svr.default'),
#                                         ('QPS_A2_N', 'crf', 'ct.svr.default'),
#                                         #('QPS_NP', 'syntax', 'ct.svr.default'),
#                                         ('QPS_union', 'crf', 'ct.svr.default'),
#                                         ('QPS_intersect', 'crf', 'ct.svr.default'),
#                                         ('QPS_combine', 'crf', 'ct.svr.default'),
# #                                           
#                                         ('QPS_A1_N', 'crf', 'ct.svm.default'),
#                                         ('QPS_A2_N', 'crf', 'ct.svm.default'),
#                                         ('QPS_NP', 'syntax', 'ct.svm.default'),
#                                         ('QPS_union', 'crf', 'ct.svm.default'),
#                                         ('QPS_intersect', 'crf', 'ct.svm.default'),
#                                         ('QPS_combine', 'crf', 'ct.svm.default'),
#
#                                         ('QPS_NP', 'syntax', 'ct.lsa.default'),
                                       ]:
     
        course_mirror_server = CourseMIRROR(config.get('Parse', 'PARSE_APP_ID'), 
                                            config.get('Parse', 'PARSE_REST_API_KEY'), 
                                            config.get('Parse', 'PARSE_MASTER_KEY'),
                                            config,
                                            system,
                                            method,
                                            similarity,
                                            )
         
        course_mirror_server.run(cid, summarylastlecture=config.getint('course', 'summarylastlecture'))
    
    output = '../data/%s/result.rouge.N%d.txt'%(course,N)
    gather_rouge(output)
#     
    