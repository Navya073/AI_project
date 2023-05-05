# -*- coding: utf-8 -*-
"""dog-vision.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1b9q9LANr1tvWbFwknTzRRA3j0BysotV8
"""

#Uploading data into Google Drive
#!unzip "/content/drive/My Drive/Dog-vision/dog-breed-identification.zip" -d "/content/drive/My Drive/Dog-vision"

"""# 🐶 End-to-end Multi-class Dog breed classification

End-to-end multi-class image classifier using TensorFlow 2.0 & TensorFlow Hub.

## 1. Problem
Identifying the breed of a dog, given an image of a dog.
## 2. Data
Kaggle's dog breed identification competition.
## 3. Evaluation
The evaluation is a file with prediction probabilities for each dog breed of each test image.
## 4. Features
Info about data:
* Unstructured images
Best to use deep learning/transfer learning.

## Workspace
* Import TensorFlow, TensorFlow Hub
* Using a GPU
"""

#Importing TensorFlow into Colab
import tensorflow as tf
print("TF version:", tf.__version__)

#Importing necessary tools
import tensorflow_hub as hub
print("TF Hub version:", hub.__version__)

#Check for GPU availability
print("GPU", "available!" if tf.config.list_physical_devices("GPU")else "not available")

#Accessing data and turning it into Tensors(numerical representation)
#Checking the labels of our data
import pandas as pd
labels_csv = pd.read_csv("drive/My Drive/Dog-vision/labels.csv")
print(labels_csv.describe())
print(labels_csv.head())

labels_csv.head()

labels_csv.tail()

# How many images are there of each breed?
labels_csv["breed"].value_counts().plot.bar(figsize=(20,10))

labels_csv["breed"].value_counts().median()

# Let's view an image
from IPython.display import Image
Image("/content/drive/My Drive/Dog-vision/train/ffe2ca6c940cddfee68fa3cc6c63213f.jpg")

"""#Getting images and their labels
Let's get a list of all our images file pathnames
"""

# Create pathnames from image ID's
filenames = ["/content/drive/My Drive/Dog-vision/train/" + fname + ".jpg" for fname in labels_csv["id"]]
filenames

# Checking wheather number of filenames matches with actual number of image files
import os
if len(os.listdir("/content/drive/My Drive/Dog-vision/train")) == len(filenames):
  print("Filenames match actual amount of files!")
else:
  print("Filenames do not match :(")

# One more check
Image(filenames[9000])

labels_csv["breed"][9000]

"""We now got our training image filepaths in a list, let's prepare our labels."""

import numpy as np
labels = labels_csv["breed"]
labels = np.array(labels)
labels

len(labels)

#See if number of labels matches the number of filenames
if len(labels) == len(filenames):
  print("Matches!")
else:
  print("Do not match :(")

# Find the unique label values
unique_breeds = np.unique(labels)
unique_breeds
len(unique_breeds)

# Turn a single label into an array of booleans
print(labels[0])
labels[0] == unique_breeds

print(labels)

# Turn every label into a boolean array
boolean_labels = [label == unique_breeds for label in labels]
boolean_labels[:]

len(boolean_labels)

# Example: Turning boolean array into integers
print(labels[0]) #ORigina label
print(np.where(unique_breeds == labels[0])) #index where label occurs
print(boolean_labels[0].argmax()) #index where label occurs in boolean array
print(boolean_labels[0].astype(int)) # there will be a 1 where the sample lable occurs

filenames[:]

"""### Creating our own validation set
Since the dataset from Kaggle doesn't come with a validation set, let's create our own.
"""

#Setup x & y variables
x = filenames
y = boolean_labels

len(filenames)

"""We're going to start off experimenting with ~1000 images and increase as needed."""

# Set number of images to use for experimenting
NUM_IMAGES = 1000 #@param {type:"slider", min:1, max:1000, step:1}

# Let's split our data into train and validation sets
from sklearn.model_selection import train_test_split

# Split them into training and validation of total size NUM_IMAGES
x_train, x_val, y_train, y_val = train_test_split(x[:NUM_IMAGES],
                                                  y[:NUM_IMAGES],
                                                  test_size = 0.2,
                                                  random_state = 42)
len(x_train), len(y_train), len(x_val), len(y_val)

# Let's have a geez at training data
x_train, y_train

"""## Preprocessing Images(turning images
into Tensors)
Function that preprocess our images into Tensors:
1. Take an image filepath as i/p.
2. Use TensorFlow to read the file and save it to a variable, `image`
3. Turn our `image` (jpg) into Tensors.
4. Resize the image to a shape of (224, 224).
5. Return the modified `image`
"""

# Convert image to NumPy array
from matplotlib.pyplot import imread
image = imread(filenames[42])
image.shape

image.max(), image.min()

image[:2]

# turn image into data
tf.constant(image)[:2]

# Define image size
IMG_SIZE = 224

# Create a function for preprocessing images
def process_image(image_path, img_size= IMG_SIZE):
  """
  Takes an iamge file and turn the image into a tensor.
  """
  #Read an image file
  image = tf. io.read_file(image_path)
  #Turn th jpeg image into numerical Tensor with 3 colour RGB channel
  image = tf.image.decode_jpeg(image, channels=3)
  #Convert the colour channels from 0-255 to 0-1
  image = tf.image.convert_image_dtype(image, tf.float32)
  #Resize the image to our desired values(224, 224)
  image = tf.image.resize(image, size=[IMG_SIZE, IMG_SIZE])

  return image

"""## Turning into batches (minibatches of size 32 is good)

why batches?

Let's day you're trying to process 10,000+ images in one go.. they all might not fit into memory, so we do 32 images at a time. (batch size can manualy adjusted)

we need our data in the form of Tensor tuples `(image, label)` for TensorFlow to run effectively.
"""

# Create a dimple function to return a tuple (image, label)
def get_image_label(image_path, label):
  """
  Takes an image file path name and assosciated label, processes the image and return a tuple 
  """
  image = process_image(image_path)
  return image, label

# Demo of the above
(process_image(x[42]), tf.constant(y[42]))

"""Now we've got a way to turn our data into tuples of Tensors in the form : `(image, label)`, let's make a function to turn all of our data (`x` & `y`) into batches!"""

# Define the batch size, 32 is a good start
BATCH_SIZE = 32

# Create a function to turn data into batches
def create_data_batches(X, y=None, batch_size=BATCH_SIZE, valid_data=False, test_data=False):
  """
  Creates batches of data out of image (X) and label (y) pairs.
  Shuffles the data if it's training data but doesn't shuffle if it's validation data.
  Also accepts test data as input (no labels).
  """
  # If the data is a test dataset, we probably don't have have labels
  if test_data:
    print("Creating test data batches...")
    data = tf.data.Dataset.from_tensor_slices((tf.constant(X))) # only filepaths (no labels)
    data_batch = data.map(process_image).batch(BATCH_SIZE)
    return data_batch
  
  # If the data is a valid dataset, we don't need to shuffle it
  elif valid_data:
    print("Creating validation data batches...")
    data = tf.data.Dataset.from_tensor_slices((tf.constant(X), # filepaths
                                               tf.constant(y))) # labels
    data_batch = data.map(get_image_label).batch(BATCH_SIZE)
    return data_batch

  else:
    print("Creating training data batches...")
    # Turn filepaths and labels into Tensors
    data = tf.data.Dataset.from_tensor_slices((tf.constant(X),
                                               tf.constant(y)))
    # Shuffling pathnames and labels before mapping image processor function is faster than shuffling images
    data = data.shuffle(buffer_size=len(X))

    # Create (image, label) tuples (this also turns the iamge path into a preprocessed image)
    data = data.map(get_image_label)

    # Turn the training data into batches
    data_batch = data.batch(BATCH_SIZE)
  return data_batch

# Create training and validation data batches
train_data = create_data_batches(x_train, y_train)
val_data = create_data_batches(x_val, y_val, valid_data= True)

# Check out the different attributes of our data batches
train_data.element_spec, val_data.element_spec

# Check out the different attributes of our data batches
train_data.element_spec, val_data.element_spec

y[0]

"""## Visyalizing Data Batches

Our data is now in batches, however, these can be a little hard to understand/comprehend, let's visualize them!
"""

import matplotlib.pyplot as plt

#Create a function for viewing images in a data batches
def show_25_images(images, labels):
  """
  Display a plot of 25 images and their labels from a data batch.
  """
  # Setup the figure
  plt.figure(figsize=(10, 10))
  # Loopthrougn 25 (for displaying 25 images)
  for i in range(25):
    # Create subplots (5 rows, 5 Columns)
    ax = plt.subplot(5, 5, i+1)
    # Display an image
    plt.imshow(images[i])
    # Add the image label as the title
    plt.title(unique_breeds[labels[i].argmax()])
    # Turn the grid lines off
    plt.axis("off")

# Let's visualize the data in a training batch
train_images, train_labels = next(train_data.as_numpy_iterator())
show_25_images(train_images, train_labels)

# Let's visualize our validation set
val_images, val_labels = next(train_data.as_numpy_iterator())
show_25_images(val_images, val_labels)

"""## Building a model

Before we build a model, there a few things we need to define:
* The input shape (our images shape, in the form of Tensors) to our model.
* The output shape (image labels, in the form of Tensors) of our model.
* The URL of the model we want to use.
"""

IMG_SIZE

# Setup image shape to the model
INPUT_SHAPE = [None, IMG_SIZE, IMG_SIZE, 3] # batch, height, width, colour channels
 
# Setup output shape of our model
OUTPUT_SHAPE = len(unique_breeds)

#Setup model URL from TensorFlow Hub
MODEL_URL = "https://tfhub.dev/google/imagenet/mobilenet_v2_130_224/classification/4"

"""Now we've got our i/p s, o/p s and model ready to go. Let's put them together into a keras deep learning model!

Let's create a function that:
* Takes the i/p shape, o/p shape and the mdel we've chosen as parameters.
* Defines the layer in a keras model in sequential fashion(step by step).
*Builds the model(tells the model the i/p shape it'll be getting).
*Returns the model.
- https://www.tensorflow.org/api_docs/python/tf/keras/applications/MobileNetV2
"""

# Create a function which builds a Keras model
def create_model(input_shaape = INPUT_SHAPE, output_shape = OUTPUT_SHAPE, model_url = MODEL_URL):
  print("Building with:", MODEL_URL)

  #Setup the model layers
  model = tf.keras.Sequential([
    hub.KerasLayer(MODEL_URL), #Layer 1 (i/p layer)
    tf.keras.layers.Dense(units = OUTPUT_SHAPE,
                         activation = "softmax") #LAyer 2 (o/p layer)
  ])

  # Compile the model
  model.compile(
      loss = tf.keras.losses.CategoricalCrossentropy(),
      optimizer = tf.keras.optimizers.Adam(),
      metrics = ["accuracy"]
  )

  #Build the model
  model.build(INPUT_SHAPE)

  return model

model = create_model()
model.summary()

"""## Callbacks

callbacks are helper functions a moedl can use during training to do such things, as saving progress or stop training early if a model stops imporving.

We'll create two callbacks, one for TensorBoard which helps track our models progess and another for early stopping which prevents our model from training for too long.

## TensorBoard callbacks

To setup a TensorBoard callback:
1. Load TensorBoard extension.
2. Create a TensorBoard callback which is able to save ogs to a directory and pass it to our model's `fit()` function.
3. Visualize our models training logs with the `%tensorboard` magic function(done after model training).
"""

# Commented out IPython magic to ensure Python compatibility.
# Load TensorBoard notebook extension
# %load_ext tensorboard

import datetime

# Create a function to build a TensorBoard callback
def create_tensorboard_callback():
  # Create a log directory for storing TensorBoard logs
  logdir = os.path.join("/content/drive/My Drive/Dog-vision/logs",
                        #Make it so the logs gets tracked whenever we run an experiment
                        datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
  return tf.keras.callbacks.TensorBoard(logdir)

"""### Early stopping callback
Stops our model from overfitting by stopping training if a certain evaluation metric stops improving.

https://www.tensorflow.org/api_docs/python/tf/keras/callbacks/EarlyStopping
"""

# Create early stopping callback
early_stopping = tf.keras.callbacks.EarlyStopping(monitor="val_accuracy",
                                                  patience=3)

"""## Training a model (on subset of data)

Our first model is only going to train on 1000 images, to make sure everything is working. 
"""

NUM_EPOCHS = 100 #@param  {type:"slider", min:10, max:100, step:10}

# Checking if GPU is running fine:
print("GPU:", "True!" if tf.config.list_physical_devices("GPU")else "False!")

"""Function which trains a model.

* Create a model using `create_model()`
* Setup a TensorBoard callabck using `create_tensorboard_callback()`
* Call the `fit()` function on our model passing it the training data, validation data, number of epochs to train for (`NUM_EPOCHS`) and the callbacks we'd like to use.
* Return the model.
"""

# Building a function to train and return a trained model
def train_model():
  """
  Trains a given model and returns the trained version.
  """
  # Create a model
  model = create_model()

  # Create new TensorBoard session everytime we train a model
  tensorboard = create_tensorboard_callback()

  # Fit the model to the data passing it the callabcks we created
  model.fit(x = train_data,
           epochs = NUM_EPOCHS,
           validation_data = val_data,
           validation_freq = 1,
           callbacks = [tensorboard, early_stopping])
  # Return the fitted model
  return model

# Fit the model to the data
model = train_model()

"""### Checking the TensorBoard logs

The TensorBoard magic function (`%tensorboard`) will access the logs directory we created earlier and visualize its content.
"""

# Commented out IPython magic to ensure Python compatibility.
# %tensorboard --logdir drive/My\ Drive/Dog-vision/logs

"""## Making and evaluating predictions using a trained model"""

# Make redictions on the validation data (not used to train on)
predictions = model.predict(val_data, verbose=1)
predictions

predictions.shape

len(y_val)

len(unique_breeds)

# First prediction
index = 0
print(predictions[index])
print(f"Max value (probability of prediction): {np.max(predictions[index])}")
print(f"Sum: {np.sum(predictions[index])}")
print(f"Max index: {np.argmax(predictions[index])}")
print(f"Predicted label: {unique_breeds[np.argmax(predictions[index])]}")

"""Having this information is great but it would be even better if we could compare a prediction to its true label and original image.

To help us, let's first build a little function to convert prediction probabilities into predicted labels.

Note: Prediction probabilities are also known as confidence levels.
"""

# Turn prediction probabilities into their respective label (easier to understand)
def get_pred_label(prediction_probabilities):
  """
  Turns an array of prediction probabilities into a label.
  """
  return unique_breeds[np.argmax(prediction_probabilities)]

# Get a predicted label based on an array of prediction probabilities
pred_label = get_pred_label(predictions[0])
pred_label

"""Wonderful! Now we've got a list of all different predictions our model has made, we'll do the same for the validation images and validation labels.

Remember, the model hasn't trained on the validation data, during the fit() function, it only used the validation data to evaluate itself. So we can use the validation images to visually compare our models predictions with the validation labels.

Since our validation data (val_data) is in batch form, to get a list of validation images and labels, we'll have to unbatch it (using unbatch()) and then turn it into an iterator using as_numpy_iterator().

Let's make a small function to do so.
"""

# Create a function to unbatch a batched dataset
def unbatchify(data):
  """
  Takes a batched dataset of (image, label) Tensors and returns separate arrays
  of images and labels.
  """
  images = []
  labels = []
  # Loop through unbatched data
  for image, label in data.unbatch().as_numpy_iterator():
    images.append(image)
    labels.append(unique_breeds[np.argmax(label)])
  return images, labels

# Unbatchify the validation data
val_images, val_labels = unbatchify(val_data)
val_images[0], val_labels[0]

"""Now we've got ways to get:

Prediction labels
Validation labels (truth labels)
Validation images
Let's make some functions to make these all a bit more visualize.

More specifically, we want to be able to view an image, its predicted label and its actual label (true label).

The first function we'll create will:

Take an array of prediction probabilities, an array of truth labels, an array of images and an integer.
Convert the prediction probabilities to a predicted label.
Plot the predicted label, its predicted probability, the truth label and target image on a single plot.
"""

def plot_pred(prediction_probabilities, labels, images, n=1):
  """
  View the prediction, ground truth label and image for sample n.
  """
  pred_prob, true_label, image = prediction_probabilities[n], labels[n], images[n]
  
  # Get the pred label
  pred_label = get_pred_label(pred_prob)
  
  # Plot image & remove ticks
  plt.imshow(image)
  plt.xticks([])
  plt.yticks([])

  # Change the color of the title depending on if the prediction is right or wrong
  if pred_label == true_label:
    color = "green"
  else:
    color = "red"

  plt.title("{} {:2.0f}% ({})".format(pred_label,
                                      np.max(pred_prob)*100,
                                      true_label),
                                      color=color)

# View an example prediction, original image and truth label
plot_pred(prediction_probabilities=predictions,
          labels=val_labels,
          images=val_images)

"""Let's build a function to demonstrate. The function will:

* Take an input of a prediction probabilities array, a ground truth labels array and an integer.
* Find the predicted label using get_pred_label().
* Find the top 10:
 * Prediction probabilities indexes
 * Prediction probabilities values
 * Prediction labels
*Plot the top 10 prediction probability values and labels, coloring the true label green.

"""

def plot_pred_conf(prediction_probabilities, labels, n=1):
  """
  Plots the top 10 highest prediction confidences along with
  the truth label for sample n.
  """
  pred_prob, true_label = prediction_probabilities[n], labels[n]

  # Get the predicted label
  pred_label = get_pred_label(pred_prob)

  # Find the top 10 prediction confidence indexes
  top_10_pred_indexes = pred_prob.argsort()[-10:][::-1]
  # Find the top 10 prediction confidence values
  top_10_pred_values = pred_prob[top_10_pred_indexes]
  # Find the top 10 prediction labels
  top_10_pred_labels = unique_breeds[top_10_pred_indexes]

  # Setup plot
  top_plot = plt.bar(np.arange(len(top_10_pred_labels)), 
                     top_10_pred_values, 
                     color="grey")
  plt.xticks(np.arange(len(top_10_pred_labels)),
             labels=top_10_pred_labels,
             rotation="vertical")

  # Change color of true label
  if np.isin(true_label, top_10_pred_labels):
    top_plot[np.argmax(top_10_pred_labels == true_label)].set_color("green")
  else:
    pass

plot_pred_conf(prediction_probabilities=predictions,
               labels=val_labels,
               n=9)

# Let's check a few predictions and their different values
i_multiplier = 0
num_rows = 3
num_cols = 2
num_images = num_rows*num_cols
plt.figure(figsize=(5*2*num_cols, 5*num_rows))
for i in range(num_images):
  plt.subplot(num_rows, 2*num_cols, 2*i+1)
  plot_pred(prediction_probabilities=predictions,
            labels=val_labels,
            images=val_images,
            n=i+i_multiplier)
  plt.subplot(num_rows, 2*num_cols, 2*i+2)
  plot_pred_conf(prediction_probabilities=predictions,
                labels=val_labels,
                n=i+i_multiplier)
plt.tight_layout(h_pad=1.0)
plt.show()

"""## Saving and reloading a model
After training a model, it's a good idea to save it. Saving it means you can share it with colleagues, put it in an application and more importantly, won't have to go through the potentially expensive step of retraining it.

The format of an entire saved Keras model is h5. So we'll make a function which can take a model as input and utilise the save() method to save it as a h5 file to a specified directory.


"""

def save_model(model, suffix=None):
  """
  Saves a given model in a models directory and appends a suffix (str)
  for clarity and reuse.
  """
  # Create model directory with current time
  modeldir = os.path.join("drive/My Drive/Data/models",
                          datetime.datetime.now().strftime("%Y%m%d-%H%M%s"))
  model_path = modeldir + "-" + suffix + ".h5" # save format of model
  print(f"Saving model to: {model_path}...")
  model.save(model_path)
  return model_path

def load_model(model_path):
  """
  Loads a saved model from a specified path.
  """
  print(f"Loading saved model from: {model_path}")
  model = tf.keras.models.load_model(model_path,
                                     custom_objects={"KerasLayer":hub.KerasLayer})
  return model

# Save our model trained on 1000 images
save_model(model, suffix="1000-images-Adam")

# Load our model trained on 1000 images
model_1000_images = load_model('/content/drive/My Drive/Data/models/20201012-15531602518032-1000-images-Adam.h5')

"""Compare the two models"""

# Evaluate the pre-saved model
model.evaluate(val_data)

# Evaluate the loaded model
model_1000_images.evaluate(val_data)

"""## Training a model (on the full data)"""

# Remind ourselves of the size of the full dataset
len(x), len(y)

# Turn full training data in a data batch
full_data = create_data_batches(x, y)

# Instantiate a new model for training on the full dataset
full_model = create_model()

# Create full model callbacks

# TensorBoard callback
full_model_tensorboard = create_tensorboard_callback()

# Early stopping callback
# Note: No validation set when training on all the data, therefore can't monitor validation accruacy
full_model_early_stopping = tf.keras.callbacks.EarlyStopping(monitor="accuracy",
                                                             patience=3)

# Commented out IPython magic to ensure Python compatibility.
# %tensorboard --logdir drive/My\ Drive/Dog-vision/logs

# Fit the full model to the full training data
full_model.fit(x=full_data,
               epochs=NUM_EPOCHS,
               callbacks=[full_model_tensorboard, 
                          full_model_early_stopping])

"""## Saving and reloading the full model"""

# Save model to file
save_model(full_model, suffix="all-images-Adam")

# Load in the full model
loaded_full_model = load_model('/content/drive/My Drive/Data/models/20201012-15531602518032-1000-images-Adam.h5')

"""##Making predictions on the test dataset"""

# Load test image filenames (since we're using os.listdir(), these already have .jpg)
test_path = "drive/My Drive/Data/test/"
test_filenames = [test_path + fname for fname in os.listdir(test_path)]

test_filenames[:10]

# How many test images are there?
len(test_filenames)

# Create test data batch
test_data = create_data_batches(test_filenames, test_data=True)

# Make predictions on test data batch using the loaded full model
test_predictions = loaded_full_model.predict(test_data,
                                             verbose=1)

# Check out the test predictions
test_predictions[:10]

"""##Preparing test dataset predictions for Kaggle
Looking at the Kaggle sample submission, it looks like they want the models output probabilities each for label along with the image ID's.

To get the data in this format, we'll:

* Create a pandas DataFrame with an ID column as well as a column for each dog breed.
* Add data to the ID column by extracting the test image ID's from their filepaths.
* Add data (the prediction probabilities) to each of the dog breed columns using the unique_breeds list and the test_predictions list.
* Export the DataFrame as a CSV to submit it to Kaggle.
"""

# Create pandas DataFrame with empty columns
preds_df = pd.DataFrame(columns=["id"] + list(unique_breeds))
preds_df.head()

# Append test image ID's to predictions DataFrame
test_path = "drive/My Drive/Data/test/"
preds_df["id"] = [os.path.splitext(path)[0] for path in os.listdir(test_path)]
preds_df.head()

# Add the prediction probabilities to each dog breed column
preds_df[list(unique_breeds)] = test_predictions
preds_df.head()

preds_df.to_csv("drive/My Drive/Data/full_submission_1_mobilienetV2_adam.csv",
                 index=False)

"""##Making predictions on custom images
It's great being able to make predictions on a test dataset already provided for us.

But how could we use our model on our own images?

The premise remains, if we want to make predictions on our own custom images, we have to pass them to the model in the same format the model was trained on.

To do so, we'll:

* Get the filepaths of our own images.
* Turn the filepaths into data batches using create_data_batches(). And since our custom images won't have labels, we set the test_data parameter to True.
* Pass the custom image data batch to our model's predict() method.
* Convert the prediction output probabilities to prediction labels.
* Compare the predicted labels to the custom images.
Note: To make predictions on custom images, I've uploaded pictures of my own to a directory located at drive/My Drive/Data/dogs/ (as seen in the cell below). In order to make predictions on your own images, you will have to do something similar.
"""

# Get custom image filepaths
custom_path = "drive/My Drive/Data/dogs/"
custom_image_paths = [custom_path + fname for fname in os.listdir(custom_path)]

# Turn custom image into batch (set to test data because there are no labels)
custom_data = create_data_batches(custom_image_paths, test_data=True)

# Make predictions on the custom data
custom_preds = loaded_full_model.predict(custom_data)

# Get custom image prediction labels
custom_pred_labels = [get_pred_label(custom_preds[i]) for i in range(len(custom_preds))]
custom_pred_labels

# Get custom images (our unbatchify() function won't work since there aren't labels)
custom_images = []
# Loop through unbatched data
for image in custom_data.unbatch().as_numpy_iterator():
  custom_images.append(image)