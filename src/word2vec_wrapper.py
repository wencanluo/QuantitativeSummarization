from gensim.models import Word2Vec
import json
import fio
import global_params
import numpy as np

def load_bin_vec(fname, vocab):
    """
    Loads 300x1 word vecs from Google (Mikolov) word2vec
    https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py
    
    """
    word_vecs = {}
    with open(fname, "rb") as f:
        header = f.readline()
        vocab_size, layer1_size = map(int, header.split())
        binary_len = np.dtype('float32').itemsize * layer1_size
        for line in xrange(vocab_size):
            word = []
            while True:
                ch = f.read(1)
                if ch == ' ':
                    word = ''.join(word)
                    break
                if ch != '\n':
                    word.append(ch)   
            if word in vocab:
                word_vecs[word] = [float(x) for x in np.fromstring(f.read(binary_len), dtype='float32')]
            else:
                f.read(binary_len)
    return word_vecs

def loadmodel(modelbin, vocabjson, output):
    vocab = fio.LoadDictJson(vocabjson)
    
    word_vecs = load_bin_vec(modelbin, vocab)
    
    fio.SaveDict2Json(word_vecs, output)

if __name__ == '__main__':
    loadmodel(global_params.word2vecfile, global_params.vocab, global_params.word2vec_model)
    
