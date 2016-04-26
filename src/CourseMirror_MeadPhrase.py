import sys
import re
import fio
import xml.etree.ElementTree as ET
import os
import phraseClusteringKmedoid
import SennaParser
import CourseMirror_Survey

def WriteDocsent(excelfile, folder, phrasedir, np=None):
    sheets = range(0,maxWeek)
    
    for i, sheet in enumerate(sheets):
        week = i + 1
        
        for type in ['q1', 'q2', 'q3', 'q4']:
            
            phrasefile = os.path.join(phrasedir, str(week), type + '.' + method + '.key')
            if not fio.IsExist(phrasefile): continue
            
            DID = str(week) + '_' + type
            
            path = folder + str(week)+ '/'
            fio.NewPath(path)
            path = path + type + '/'
            fio.NewPath(path)
            path = path + 'docsent/'
            fio.NewPath(path)
            filename = path + DID + '.docsent'
            
            #create a XML file
            root = ET.Element(tag='DOCSENT', attrib = {'DID':DID, 'LANG':"ENG"})
            root.tail = '\n'
            tree = ET.ElementTree(root)
            
            phrases = fio.ReadFile(phrasefile)
            
            sno_id = 1
            for par, phrase in enumerate(phrases):
                phrase = phrase.rstrip()
                s = [phrase]
                
                for RSNT, value in enumerate(s):
                    node = ET.Element(tag='S', attrib={'PAR':str(par+1), 'RSNT':str(RSNT+1), 'SNO':str(sno_id)})
                    node.text = value
                    node.tail = '\n'
                    root.append(node)
                    sno_id = sno_id + 1
            
            tree.write(filename)
            
def WriteCluster(excelfile, folder, np=None):
    sheets = range(0,maxWeek)
    
    for type in ['q1', 'q2', 'q3', 'q4']:
        for sheet in sheets:
            week = sheet + 1
            student_summaryList = CourseMirror_Survey.getStudentResponseList(excelfile, course, week, type, withSource=True)
            if len(student_summaryList) == 0: continue
            
            path = folder + str(week)+ '/'
            fio.NewPath(path)
            
            path = path + type + '/'
            fio.NewPath(path)
            filename = path + type + '.cluster'
            
            #create a XML file
            root = ET.Element(tag='CLUSTER', attrib = {'LANG':"ENG"})
            root.tail = '\n'
            tree = ET.ElementTree(root)
        
            DID = str(sheet+1) + '_' + type
            
            node = ET.Element(tag='D', attrib={'DID':str(DID)})
            node.tail = '\n'
            root.append(node)
        
            tree.write(filename)
            
def Write2Mead(excelfile, datadir, phrasedir, np=None):
    #assume one week is a one document
    WriteDocsent(excelfile, datadir, phrasedir, np)
    WriteCluster(excelfile, datadir)
                
if __name__ == '__main__':
    
    course = sys.argv[1]
    maxWeek = int(sys.argv[2])
    system = sys.argv[3]
    method = sys.argv[4]
    
    excelfile = "../data/CourseMIRROR/reflections.json"
    
    phrasedir = "../data/"+course+"/"+system+"/phrase/"
    datadir = "../data/"+course+ '/'+system+'/' + "PhraseMead/"
    
    fio.DeleteFolder(datadir)
    Write2Mead(excelfile, datadir, phrasedir, np=method)
            
    #Step5: get PhraseMead output
    
    print "done"