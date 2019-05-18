# -*- coding: utf-8 -*-
"""
Created on Fri May 17 13:42:19 2019

@author: Rufina
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler
from keras.layers import Input, Dense
from keras.models import Model
from keras.callbacks import TensorBoard
import tensorflow as tf
from keras import regularizers, backend as K
import Utils

#label 0 - normal, 1 - anomal

#train1 = pd.read_csv("dataset/UNSW-NB15_1.csv", header = None)
#train2 = pd.read_csv("dataset/UNSW-NB15_2.csv", header = None)
#test = pd.read_csv("dataset/UNSW-NB15_3.csv", header = None)
#validation = pd.read_csv("dataset/UNSW-NB15_4.csv", header = None)
#features = pd.read_csv("dataset/NUSW-NB15_features.csv")['Name'].values
#train1.columns = features
#train2.columns = features
#test.columns = features
#validation.columns = features
#DROP SOME FEATURES
#to_drop = ['srcip','dstip', 'service', 'attack_cat' ]


test = pd.read_csv("dataset/part_training_testing_set/UNSW_NB15_training-set.csv")
train = pd.read_csv("dataset/part_training_testing_set/UNSW_NB15_testing-set.csv")

nTrain = train.shape[0]
nTest = test.shape[0]

combined = pd.get_dummies(pd.concat((train,test),axis=0))

train = combined.iloc[:nTrain]
test = combined.iloc[nTrain:]

#train = pd.get_dummies(train)
#test = pd.get_dummies(test)

train_labels = train['label']
test_labels = test['label']

train=train.drop(['label'], axis = 1)
test=test.drop(['label'], axis = 1)

scaler = StandardScaler()
train = scaler.fit_transform(train)
test = scaler.transform(test)

train_normal = train[np.where(train_labels == 0)]
train_anomal = train[np.where(train_labels == 1)]

normal_validation = train_normal[50540:]
validation = np.concatenate((normal_validation, train_anomal))
validation_labels = np.concatenate((np.zeros(normal_validation.shape[0]), np.ones(train_anomal.shape[0])))
train_normal = train_normal[:50540]

#AUTOENCODER
def fit_model(X):
    input_dim = train_normal.shape[1]
    latent_space_size = 16
    K.clear_session()
    input_ = Input(shape = (input_dim, ))

    layer_1 = Dense(100, activation='tanh')(input_)
    layer_2 = Dense(50, activation='tanh')(layer_1)
    layer_3 = Dense(25, activation='tanh')(layer_2)

    encoding = Dense(latent_space_size,activation=None)(layer_3)

    layer_5 = Dense(25, activation='tanh')(encoding)
    layer_6 = Dense(50, activation='tanh')(layer_5)
    layer_7 = Dense(100, activation='tanh')(layer_6)

    decoded = Dense(input_dim,activation=None)(layer_7)

    autoencoder = Model(inputs=input_ , outputs=decoded)

    autoencoder.compile(metrics=['accuracy'],loss='mean_squared_error',optimizer='adam')
    #create TensorBoard
    tb = TensorBoard(log_dir=f'./logs1',histogram_freq=0,write_graph=False,write_images=False)

    autoencoder.fit(X, X,epochs=100,validation_split=0.1,batch_size=100,shuffle=True,verbose=1,callbacks=[tb])

    return autoencoder

"""
model = fit_model(train_normal)
with open('autoenc.pickle', 'wb') as f:
            pickle.dump(model, f)
"""  
with open('autoenc.pickle', 'rb') as fid:
    model = pickle.load(fid)
          


#GET THRESHOLD ON VALIDATION SET
losses = Utils.get_losses(model, train_normal)
validation_losses = Utils.get_losses(model, validation)
test_losses = Utils.get_losses(model, test)
max_loss = max(losses)
avg_loss = np.mean(losses)
thresholds = [max_loss, avg_loss, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.5, 1]
for thresh in thresholds:
    val_pred = (validation_losses>thresh)*1
    print("thresh = ", thresh)
    Utils.performance(validation_labels,val_pred)
    
#TEST SET PERFORMANCE
test_pred = (test_losses>0.09)*1
Utils.performance(test_labels, test_pred)

#CONF INTERVAL
thresholds = Utils.confidence_intervals(losses,0.99)

threshold = thresholds[1]

test_pred = (test_losses>threshold)*1
Utils.performance(test_labels, test_pred)




