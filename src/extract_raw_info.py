import fio
import os
from annotation import *

python_tool = "E:\project\TabelFormat\python-docx\example-extracttext.py"

def extract_text():
    for doc, lec, annotator in generate_all_files(datadir + 'raw/', '.docx'):
        output = datadir + 'text/' + get_name(lec, annotator) + '.txt'
        
        cmd = 'python ' + python_tool + ' ' + doc + ' ' + output
        
        print cmd
        os.system(cmd)

def extract_infomration():
    for doc, lec, annotator in generate_all_files(datadir + 'text/', '.txt'):
        task = Task()
        task.load(doc)
        
        output = datadir + 'json/' + get_name(lec, annotator) + '.json'
        task.save2json(output)
        
if __name__ == '__main__':
    extract_text()
    extract_infomration()
    