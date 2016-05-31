import global_params
import fio
import os

class OSLOM:
    def __init__(self, oslom_parms=""):
        self.oslom_parms = oslom_parms
    
    def solve_graph(self, inputfile, undirect=True, weighted=False):
        weight_parm = "-w" if weighted else "-uw"
        
        direct_parm = global_params.graphexe_undir if undirect else global_params.graphexe_dir
        
        cmd = "%s -f %s %s %s"%(direct_parm, inputfile, weight_parm, self.oslom_parms)
            
        print cmd
        
        os.system(cmd)
    
    def readgraph_partitions(self, input):
        lines = fio.ReadFile(input)
        
        communites = [] 
        for line in lines:
            if line.startswith('#'): continue
            
            nodes = [int(x) for x in line.strip().split()]
            
            communites.append(nodes)
        
        return communites
