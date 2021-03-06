# -*- coding: utf-8 -*-



# %reset

import os
import datetime

import IPython
import IPython.display
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import tensorflow as tf
import pandas as pd
import numpy as np
from pandas import ExcelWriter
from pandas import ExcelFile
import numpy as np
import scipy.stats as st
import collections
import random
import plotly.graph_objects as go
from statistics import mean, median, mode, stdev, variance
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings("ignore")
from math import sqrt
from numpy import concatenate
from matplotlib import pyplot
from pandas import read_csv
from pandas import DataFrame
from pandas import concat
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
import datetime
import tensorflow as tf
import random
random.seed(10)
mpl.rcParams['figure.figsize'] = (8, 6)
mpl.rcParams['axes.grid'] = False

df = pd.read_excel('drive/MyDrive/Odometria2.xlsx')
#df=df[['T','t']]
#T_yolo = np.array(T_yolo)
df = df[9::10]

df.head(10)

df.describe().transpose()

column_indices = {name: i for i, name in enumerate(df.columns)}

n = len(df)
train_df = df[0:int(n*0.7)]
val_df = df[int(n*0.7):int(n*0.9)]
test_df = df[int(n*0.9):]

num_features = df.shape[1]

scaler = MinMaxScaler(feature_range=(0, 1))
train_df = scaler.fit_transform(train_df)
val_df = scaler.fit_transform(val_df)
test_df = scaler.fit_transform(test_df)
train_df = pd.DataFrame(train_df, columns = ["Frequencia", "Voltagem", "Temperatura", "Tempo"])
test_df = pd.DataFrame(test_df, columns = ["Frequencia", "Voltagem", "Temperatura", "Tempo"])
val_df = pd.DataFrame(val_df, columns = ["Frequencia", "Voltagem", "Temperatura", "Tempo"])
test_df.head()

class WindowGenerator():
  def __init__(self, input_width, label_width, shift,
               train_df=train_df, val_df=val_df, test_df=test_df,
               label_columns=None):
    # Store the raw data.
    self.train_df = train_df
    self.val_df = val_df
    self.test_df = test_df

    # Work out the label column indices.
    self.label_columns = label_columns
    if label_columns is not None:
      self.label_columns_indices = {name: i for i, name in
                                    enumerate(label_columns)}
    self.column_indices = {name: i for i, name in
                           enumerate(train_df.columns)}

    # Work out the window parameters.
    self.input_width = input_width
    self.label_width = label_width
    self.shift = shift

    self.total_window_size = input_width + shift

    self.input_slice = slice(0, input_width)
    self.input_indices = np.arange(self.total_window_size)[self.input_slice]

    self.label_start = self.total_window_size - self.label_width
    self.labels_slice = slice(self.label_start, None)
    self.label_indices = np.arange(self.total_window_size)[self.labels_slice]

  def __repr__(self):
    return '\n'.join([
        f'Total window size: {self.total_window_size}',
        f'Input indices: {self.input_indices}',
        f'Label indices: {self.label_indices}',
        f'Label column name(s): {self.label_columns}'])

def split_window(self, features):
  inputs = features[:, self.input_slice, :]
  labels = features[:, self.labels_slice, :]
  if self.label_columns is not None:
    labels = tf.stack(
        [labels[:, :, self.column_indices[name]] for name in self.label_columns],
        axis=-1)

  # Slicing doesn't preserve static shape information, so set the shapes
  # manually. This way the `tf.data.Datasets` are easier to inspect.
  inputs.set_shape([None, self.input_width, None])
  labels.set_shape([None, self.label_width, None])

  return inputs, labels

WindowGenerator.split_window = split_window

def plot(self, model=None, plot_col='Temperatura', max_subplots=3):
  inputs, labels = self.example
  plt.figure(figsize=(12, 9))
  plot_col_index = self.column_indices[plot_col]
  max_n = min(max_subplots, len(inputs))
  for n in range(max_n):
    plt.xlim(90,150)
    plt.subplot(max_n, 1, n+1)
    plt.ylabel(f'{plot_col} [normed]')
    plt.plot(self.input_indices, inputs[n, :, plot_col_index],
             label='Inputs', marker='.', zorder=-10)

    if self.label_columns:
      label_col_index = self.label_columns_indices.get(plot_col, None)
    else:
      label_col_index = plot_col_index

    if label_col_index is None:
      continue

    plt.plot(self.label_indices, labels[n, :, label_col_index],
               label='Labels',marker='.', c='#2ca02c')
    if model is not None:
      predictions = model(inputs)
      plt.plot(self.label_indices, predictions[n, :, label_col_index],
                  marker='X', label='Predictions',
                  c='#ff7f0e')


    if n == 0:
      plt.legend()
  print(predictions[n, :, label_col_index])
  print(labels[n, :, label_col_index])
  plt.xlabel('Tempo [s]')
  plt.xlim(90,150)

WindowGenerator.plot = plot

@property
def train(self):
  return self.make_dataset(self.train_df)

@property
def val(self):
  return self.make_dataset(self.val_df)

@property
def test(self):
  return self.make_dataset(self.test_df)

@property
def example(self):
  """Get and cache an example batch of `inputs, labels` for plotting."""
  result = getattr(self, '_example', None)
  if result is None:
    # No example batch was found, so get one from the `.train` dataset
    result = next(iter(self.train))
    # And cache it for next time
    self._example = result
  return result

WindowGenerator.train = train
WindowGenerator.val = val
WindowGenerator.test = test
WindowGenerator.example = example

def make_dataset(self, data):
  data = np.array(data, dtype=np.float32)
  ds = tf.keras.preprocessing.timeseries_dataset_from_array(
      data=data,
      targets=None,
      sequence_length=self.total_window_size,
      sequence_stride=1,
      shuffle=True,
      batch_size=12,)

  ds = ds.map(self.split_window)

  return ds

WindowGenerator.make_dataset = make_dataset

MAX_EPOCHS = 200

def compile_and_fit(model, window, patience=200):
  early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_loss',
                                                    patience=patience,
                                                    mode='min')

  model.compile(loss=tf.losses.MeanSquaredError(),
                optimizer=tf.optimizers.Adam(),
                metrics=[tf.metrics.MeanAbsoluteError()])

  history = model.fit(window.train, epochs=MAX_EPOCHS,
                      validation_data=window.val,
                      callbacks=[early_stopping])
  return history

OUT_STEPS = 60
multi_window = WindowGenerator(input_width=90,
                               label_width=60,
                               shift=60,
                               label_columns=['Temperatura'])

multi_val_performance = {}
multi_performance = {}

multi_lstm_model = tf.keras.Sequential([
    # Shape [batch, time, features] => [batch, lstm_units]
    # Adding more `lstm_units` just overfits more quickly.
    tf.keras.layers.LSTM(50, return_sequences=False),
    # Shape => [batch, out_steps*features]
    tf.keras.layers.Dense(OUT_STEPS*num_features,
                          kernel_initializer=tf.initializers.zeros()),
    # Shape => [batch, out_steps, features]
    tf.keras.layers.Reshape([OUT_STEPS, num_features])
])

history = compile_and_fit(multi_lstm_model, multi_window)

IPython.display.clear_output()

multi_val_performance['LSTM'] = multi_lstm_model.evaluate(multi_window.val)
multi_performance['LSTM'] = multi_lstm_model.evaluate(multi_window.test, verbose=0)
multi_window.plot(multi_lstm_model)

def visualize_loss(history, title):
    loss = history.history["loss"]
    val_loss = history.history["val_loss"]
    epochs = range(len(loss))
    plt.figure()
    plt.plot(epochs, loss, "b", label="Training loss")
    plt.plot(epochs, val_loss, "r", label="Validation loss")
    plt.title(title)
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.legend()
    plt.show()

#print(loss)
visualize_loss(history, "Training and Validation Loss")

multi_window.plot(multi_lstm_model)

from sklearn.metrics import mean_squared_error
import numpy as np

# Given values
Y_true = np.array()

# calculated values
Y_pred = np.array()

# Calculation of Mean Squared Error (MSE)
A=np.mean(np.abs((Y_true - Y_pred) / Y_true)) * 100

Yolo = pd.read_excel('drive/MyDrive/Odometria2.xlsx')
T_yolo = Yolo['T'].tolist()
T_yolo = np.array(T_yolo)
scaler2 = MinMaxScaler(feature_range=(0, 1))
a=T_yolo.reshape(-1, 1)
a= scaler2.fit_transform(a)
new_Y_true = Y_true.reshape(-1, 1)
new_Y_pred = Y_pred.reshape(-1, 1)
new_Y_true
print(a[5])
unscaled0 = scaler2.inverse_transform(new_Y_true)
unscaled = scaler2.inverse_transform(new_Y_pred)
print(unscaled[0])
print(unscaled0[0])
print(A)
b=np.mean(np.abs((unscaled0 - unscaled) / unscaled0)) * 100
print(b)
from sklearn.metrics import mean_squared_error
mean_squared_error(Y_true,Y_pred)

plt.figure(figsize=(15,5))
plt.plot(unscaled0, label="Labels", marker='.')
plt.plot(unscaled, label="Predictions", marker='x')
plt.xlabel('Tempo(s)')
plt.ylabel('Temperatura')
#plt.xlim(0,10)
#plt.ylim(50,61)
plt.legend()
plt.show()

class FeedBack(tf.keras.Model):
  def __init__(self, units, out_steps):
    super().__init__()
    self.out_steps = out_steps
    self.units = units
    self.lstm_cell = tf.keras.layers.LSTMCell(units)
    # Also wrap the LSTMCell in an RNN to simplify the `warmup` method.
    self.lstm_rnn = tf.keras.layers.RNN(self.lstm_cell, return_state=True)
    self.dense = tf.keras.layers.Dense(num_features)

feedback_model = FeedBack(units=150, out_steps=OUT_STEPS)

def warmup(self, inputs):
  # inputs.shape => (batch, time, features)
  # x.shape => (batch, lstm_units)
  x, *state = self.lstm_rnn(inputs)

  # predictions.shape => (batch, features)
  prediction = self.dense(x)
  return prediction, state

FeedBack.warmup = warmup

def call(self, inputs, training=None):
  # Use a TensorArray to capture dynamically unrolled outputs.
  predictions = []
  # Initialize the lstm state
  prediction, state = self.warmup(inputs)

  # Insert the first prediction
  predictions.append(prediction)

  # Run the rest of the prediction steps
  for n in range(1, self.out_steps):
    # Use the last prediction as input.
    x = prediction
    # Execute one lstm step.
    x, state = self.lstm_cell(x, states=state,
                              training=training)
    # Convert the lstm output to a prediction.
    prediction = self.dense(x)
    # Add the prediction to the output
    predictions.append(prediction)

  # predictions.shape => (time, batch, features)
  predictions = tf.stack(predictions)
  # predictions.shape => (batch, time, features)
  predictions = tf.transpose(predictions, [1, 0, 2])
  return predictions

FeedBack.call = call

history = compile_and_fit(feedback_model, multi_window)

IPython.display.clear_output()

multi_val_performance['AR LSTM'] = feedback_model.evaluate(multi_window.val)
multi_performance['AR LSTM'] = feedback_model.evaluate(multi_window.test, verbose=0)

multi_window.plot(feedback_model)

def visualize_loss(history, title):
    loss = history.history["loss"]
    val_loss = history.history["val_loss"]
    epochs = range(len(loss))
    plt.figure()
    plt.plot(epochs, loss, "b", label="Training loss")
    plt.plot(epochs, val_loss, "r", label="Validation loss")
    plt.title(title)
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.legend()
    plt.show()

#print(loss)
visualize_loss(history, "Training and Validation Loss")

lstm_model = tf.keras.models.Sequential([
    # Shape [batch, time, features] => [batch, time, lstm_units]
    tf.keras.layers.LSTM(32, return_sequences=True),
    # Shape => [batch, time, features]
    tf.keras.layers.Dense(units=1)
])

for name, value in multi_val_performance.items():
  print(f'{name:8s}: {value[1]:0.4f}')

print(multi_val_performance)

linear = tf.keras.Sequential([
    tf.keras.layers.Dense(units=1)
])
