import argparse
import re
import numpy as np
import theano
import theano.tensor as T

parser = argparse.ArgumentParser(description='invert sentence with RNN encoder decoder')
parser.add_argument('-H', metavar='nr_hidden', dest="nr_hidden",type=int,
                   help='number of hidden nodes')

trainD = None
vecs = None

def load_data():
    global trainD
    global vecs

    fns = ['qa1_single-supporting-fact_train.txt',
           'qa2_two-supporting-facts_train.txt',
           'qa3_three-supporting-facts_train.txt',
           'qa4_two-arg-relations_train.txt',
           'qa5_three-arg-relations_train.txt']

    
    trainD = []


    # split data into only lowercases words (remove punctiation and numbers) 
    for fn in fns:
        with open('tasksv11/en/'+fn) as f:
            trainD.extend(np.array([re.sub("[^a-zA-Z]", " " , l).lower().split() for l in  f.readlines()]))

    trainD = np.array(trainD)
    voc = np.unique(np.hstack(trainD)).tolist()
    voc.append('<BOS>')
    #print(voc)
    y = np.eye(len(voc))
    vecs = {voc[i] : y[i] for i in range(len(voc))}


# copied from illctheanotutorial - modified for use here
def w_init():
    shape = (nr_hidden,len(vecs))
    a = np.random.normal(0.0, 1.0, shape)
    u, _, v = np.linalg.svd(a, full_matrices=False)
    q = u if u.shape == shape else v
    q = q.reshape(shape)
    return q

# copied from illctheanotutorial - modified for use here
def u_init():
    shape = (nr_hidden, nr_hidden)
    a = np.random.normal(0.0, 1.0, shape)
    u, _, v = np.linalg.svd(a, full_matrices=False)
    q = u if u.shape == shape else v
    q = q.reshape(shape)
    return q


def embedding_init():
    return np.random.randn(1, len(vecs)) * 0.01

# copied from illctheanotutorial - modified for use here
class EmbeddingLayer(object):
    def __init__(self, embedding_init):
        self.embedding_matrix = theano.shared(embedding_init())

    def get_output_expr(self, input_expr):
        return self.embedding_matrix[input_expr]

    def get_parameters(self):
        return [self.embedding_matrix]

# copied from illctheanotutorial - RnnLayer
class Encoder(object):
    def __init__(self, w_init, u_init):
        self.W = theano.shared(w_init())
        self.U = theano.shared(u_init())

    def get_output_expr(self, input_sequence):
        h0 = T.zeros((self.U.shape[0], ))

        h, _ = theano.scan(fn=self.__get_rnn_step_expr,
                           sequences=input_sequence,
                           outputs_info=[h0])
        return h

    def __get_rnn_step_expr(self, x_t, h_tm1):
        return T.tanh(T.dot( self.U,h_tm1) + T.dot( self.W,x_t))

    def get_parameters(self):
        return [self.W, self.U]

class Decoder(object):
    def __init__(self, w_init, u_init):
        self.O = theano.shared(w_init())
        self.V = theano.shared(u_init())
        self.Yh = theano.shared(w_init())
        
    def get_output_expr(self,h,l):
        #y0 = theano.shared(vecs['<BOS>'])
        y0 = T.zeros((self.O.shape[1], ))

        h0 = h
        
        self.c = h
        [y,h], _ = theano.scan(fn=self.__get_rnn_step_expr,
                           #sequences=input_sequence,
                           #non_sequences=[self.O,self.V,self.Yh],
                           n_steps = l,
                           outputs_info=[y0,h0])
        return y

    def __get_rnn_step_expr(self, y_tm1, h_tm1):
        y_t = T.tanh(T.dot(self.O,h_tm1)+T.dot(self.Yh,y_tm1))
        h_t = T.tanh(T.dot( self.V,h_tm1))
        return [y_t,h_t]
        
    def get_parameters(self):
        return [self.W, self.U]


def train():
    #embedding_layer = EmbeddingLayer(embedding_init)
    encoder = Encoder(w_init, u_init)
    decoder = Decoder(w_init, u_init)
    x = T.imatrix()

    #embedding_expr = embedding_layer.get_output_expr(x)
    h=encoder.get_output_expr(x)
    encode = theano.function(inputs=[x],outputs=[h])    

    #l = 1
    #y=decoder.get_output_expr(h,l)
    #decode = theano.function(inputs=[h,l],outputs=[y])    
    
    for sen in trainD:
        x = np.array([vecs[sen[i]] for i in range(len(sen))],dtype=np.int32)
        H = encode(x)
        #print('H: ', H[0][-1])
        #print(h)
        #   l = len(sen)
        #decode(H[0][-1],l)

    print(H)
    

    
if __name__ == "__main__":
    args = parser.parse_args()
    nr_hidden = args.nr_hidden
    load_data()
    train()
    