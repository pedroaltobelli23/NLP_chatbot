import numpy as np
import os
import sys
import pathlib
import keras
from keras.layers import Input, Dense, TextVectorization, Embedding, LSTM, Softmax
from keras.models import Model
import tensorflow as tf
from utils.functions import Website,get_texts_with_word

# print(pathlib.Path.cwd().parent)


class ModelGenerate:
    def __init__(self,vocab_size=5000,name='model2'):
        self.vocab_size = vocab_size
        self.name = name
        self.vectorize_layer = TextVectorization(max_tokens=vocab_size,output_sequence_length=10)
        if os.path.exists(name):
            self.model = tf.keras.saving.load_model(self.name)
        else:
            self.model = self.__create_model()
            tf.keras.saving.save_model(self.model,filepath=self.name)
            
    def __create_model(self):
        #create the model and save it
        predictor,latent = self.__predict_word(10,15,self.vocab_size)
        opt = keras.optimizers.Nadam(learning_rate=0.1)
        loss_fn = keras.losses.SparseCategoricalCrossentropy(
            ignore_class=1,
            name="sparse_categorical_crossentropy",
        )

        # print(predictor.summary())  
        predictor.compile(loss=loss_fn, optimizer=opt, metrics=["accuracy"])
        return predictor   
    
    def __predict_word(self,seq_len, latent_dim, vocab_size):
        input_layer = Input(shape=(seq_len-1,))
        x = input_layer #input e uma matriz frase por palavra
        x = Embedding(vocab_size, latent_dim, name='embedding', mask_zero=True)(x) #vetoriza para dimensao = latent_dim
        x = LSTM(latent_dim, kernel_initializer='glorot_uniform')(x)
        latent_rep = x
        x = Dense(vocab_size)(x)
        x = Softmax()(x)
        return Model(input_layer, x), Model(input_layer, latent_rep)
    
    def __adapt_texts(self,texts):
        self.vectorize_layer.adapt(texts)
        
    def __separar_ultimo_token(self,texts):
        x_ = self.vectorize_layer(texts)
        x_ = x_[:,:-1]
        y_ = x_[:,-1:]
        return x_, y_
    
    def __fitter(self,texts):
        self.__adapt_texts(texts)
        x_,y_ = self.__separar_ultimo_token(texts)
        history = self.model.fit(x_,y_,epochs=20,verbose=1)
        
    def prediction(self,texts,input_,n_pred=10):
        self.__fitter(texts)
        phrase = input_
        context = phrase
        for n in range(n_pred):
            pred = self.model.predict(self.vectorize_layer([context])[:,:-1])
            tentando = True
            while tentando:
                # Selectionar de k-best
                candidatos = tf.math.top_k(pred, k=10).indices[0,:]
                idx = np.random.choice(candidatos.numpy())
                # idx = tf.argmax(pred, axis=1)[0]
                word = self.vectorize_layer.get_vocabulary()[idx]
                if word in phrase.split():
                    pred[0][idx] = 0
                else:
                    tentando = False
            phrase = phrase + " " + word
            context = context + " " + word
            contexto = " ".join(phrase.split()[1:])
        return phrase
        
if __name__ == '__main__':
    word = '2002'
    all_texts = get_texts_with_word(word)
    print(len(all_texts))
    # print(all_texts)
    a = ModelGenerate()
    p = a.prediction(all_texts,word)
    print(p)
    sys.exit()