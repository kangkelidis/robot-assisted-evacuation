import logging
import subprocess
from subprocess import call

import keras
import numpy as np
import pandas as pd
from imblearn.over_sampling import RandomOverSampler
from keras import layers
from keras import models
from keras.callbacks import History
from keras.layers import Dropout
from keras.optimizers import Optimizer
from keras.wrappers.scikit_learn import KerasClassifier
from sklearn.base import BaseEstimator
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.utils import resample, class_weight
from tensorflow.python.keras.models import load_model
from typing import List, Optional, Dict

from environment import GROUP_IDENTITY_CLASS
from gamemodel import SHARED_IDENTITY_TYPE, PERSONAL_IDENTITY_TYPE

TYPE_TO_CLASS = {
    PERSONAL_IDENTITY_TYPE: 0,
    SHARED_IDENTITY_TYPE: 1
}


class CalibratedTypeAnalyser(object):

    def __init__(self, base_estimator, method):
        # type: (BaseEstimator, str) -> None
        self.calibrated_classifier = CalibratedClassifierCV(base_estimator=base_estimator, cv="prefit",
                                                            method=method)  # type: CalibratedClassifierCV

    def train(self, sensor_data_validation, person_type_validation):
        # type: (np.ndarray, np.ndarray) -> None
        self.calibrated_classifier.fit(sensor_data_validation, person_type_validation)

    def obtain_probabilities(self, sensor_data):
        # type: (np.ndarray) -> np.ndarray
        return self.calibrated_classifier.predict_proba(sensor_data)[:, 1]


class NeuralNetworkTypeAnalyser(object):

    def __init__(self, num_features=0, metric="", learning_rate=0.001, units_per_layer=None,
                 model_file=None):
        self.units_per_layer = units_per_layer
        self.num_features = num_features
        self.learning_rate = learning_rate
        self.metric = metric

        if model_file is not None:
            network_from_file = load_model(model_file)  # type: models.Sequential
            self.keras_classifier = KerasClassifier(build_fn=self.get_network)
            self.keras_classifier.model = network_from_file
            self.keras_classifier.classes_ = [False, True]

            logging.info("Model loaded from {}".format(model_file))
        else:
            self.keras_classifier = KerasClassifier(build_fn=self.get_network)

    def __str__(self):
        return self.keras_classifier.model.summary()

    def get_network(self):
        if self.units_per_layer is None:
            self.units_per_layer = []  # type: List[int]

        if len(self.units_per_layer) > 0:
            network = models.Sequential()  # type: models.Sequential

            network.add(
                layers.Dense(units=self.units_per_layer[0], activation="relu", input_shape=(self.num_features,)))
            network.add(Dropout(rate=0.4))

            for units in self.units_per_layer[1:]:
                network.add(layers.Dense(units=units, activation="relu"))
                network.add(Dropout(rate=0.4))

            network.add(layers.Dense(units=1, activation="sigmoid"))
        else:
            network = models.Sequential(
                [layers.Dense(units=1, activation="sigmoid", input_shape=(self.num_features,))])

        optimizer = keras.optimizers.Adam(lr=self.learning_rate)  # type: Optimizer
        network.compile(loss="binary_crossentropy", optimizer=optimizer, metrics=[self.metric, "accuracy"])

        network.summary()

        return network

    def do_sanity_check(self, sensor_data, person_type, epochs, batch_size):
        # type: (np.ndarray, np.ndarray, int, int) -> History

        training_history = self.keras_classifier.fit(sensor_data,
                                                     person_type,
                                                     epochs=epochs,
                                                     batch_size=batch_size)  # type: History
        last_recorded_accuracy = training_history.history["acc"][-1]  # type: float
        logging.info(
            "last_recorded_accuracy: {}. Training samples: {}".format(last_recorded_accuracy, sensor_data.shape[0]))
        if last_recorded_accuracy < 1.0:
            raise Exception(
                "On sanity check, final accuracy is {} after {} epochs".format(last_recorded_accuracy,
                                                                               epochs))
        return training_history

    def train(self, sensor_data_training, person_type_training, sensor_data_validation, person_type_validation,
              epochs, batch_size, callbacks=None, calculate_weights=False):
        # type: (np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, int, List, bool) -> None

        class_weights = None  # type: Optional[Dict]
        if calculate_weights:
            class_weights = self.obtain_weights(person_type_training)

        self.keras_classifier.fit(sensor_data_training,
                                  person_type_training,
                                  epochs=epochs,
                                  verbose=1,
                                  callbacks=callbacks,
                                  batch_size=batch_size,
                                  class_weight=class_weights,
                                  validation_data=(
                                      sensor_data_validation, person_type_validation))

        return None

    @staticmethod
    def obtain_weights(person_type_training):
        # type: (np.ndarray) -> Dict
        weights_per_class = class_weight.compute_class_weight("balanced", np.unique(person_type_training),
                                                              person_type_training)  # type: Dict

        logging.info(
            "Personal weight: {} Group weight: {}".format(weights_per_class[TYPE_TO_CLASS[PERSONAL_IDENTITY_TYPE]],
                                                          weights_per_class[TYPE_TO_CLASS[SHARED_IDENTITY_TYPE]], ))

        return weights_per_class

    def obtain_probabilities(self, sensor_data):
        # type: (np.ndarray) -> np.ndarray
        return self.keras_classifier.predict_proba(sensor_data)[:, 1]

    def predict_type(self, sensor_data):
        # type: (np.ndarray) -> np.ndarray
        return self.keras_classifier.predict(sensor_data)


class NaiveBayesTypeAnalyser(object):

    def __init__(self):
        self.count_vectorizer = CountVectorizer()
        self.classifier = MultinomialNB()

    def train(self, text_train, labels_train, random_state):
        text_train, labels_train = self.upsample_minority(text_train, labels_train, random_state)
        text_train_counts = self.count_vectorizer.fit_transform(text_train)
        self.classifier.fit(text_train_counts, labels_train)

    def obtain_probabilities(self, text_features):
        return self.classifier.predict_proba(text_features)[:, GROUP_IDENTITY_CLASS]

    def predict_type(self, text_features):
        return self.classifier.predict(text_features)

    def convert_text_to_features(self, text):
        return self.count_vectorizer.transform(text)

    @staticmethod
    def upsample_minority(text_train, labels_train, random_state):
        logging.info("Before upsampling -> text_train.shape {}".format(text_train.shape))
        logging.info("Before upsampling -> label_train.shape {}".format(labels_train.shape))

        text_train = np.expand_dims(text_train, axis=1)
        over_sampler = RandomOverSampler(random_state=random_state)

        text_train, label_train = over_sampler.fit_resample(text_train, labels_train)
        text_train = np.squeeze(text_train)

        logging.info("After upsampling -> text_train.shape {}".format(text_train.shape))
        logging.info("After upsampling -> label_train.shape {}".format(label_train.shape))

        return text_train, label_train


class TunedTransformerTypeAnalyser(object):

    def __init__(self, testing_csv_file="testing_data.csv", prefix='conda run -n wdywfm-adaptive-robot-p36 ',
                 model_directory="./model"):
        # type: (str, str, str) ->  None
        self.training_csv_file = "training_data.csv"  # type: str
        self.testing_csv_file = testing_csv_file  # type: str
        self.validation_csv_file = "validation_data.csv"  # type: str
        self.validation_size = 0.4  # type: float
        self.model_directory = model_directory  # type: str

        self.prefix = prefix
        self.python_script = '../transformer-type-estimator/transformer_analyser.py'
        self.training_command = self.prefix + 'python {} --trainlocal --train_csv "{}" --test_csv "{}"'
        self.prediction_command = self.prefix + 'python {} --predlocal --input_text "{}" --modelDirectory "{}"'

    def train(self, original_dataframe, test_size, label_column, random_seed):
        logging.info("Test size {}".format(test_size))

        training_validation_dataframe, testing_dataframe = train_test_split(original_dataframe,
                                                                            stratify=original_dataframe[label_column],
                                                                            test_size=test_size,
                                                                            random_state=random_seed)

        training_validation_dataframe = self.upsample_minority(training_validation_dataframe, label_column, random_seed)
        training_dataframe, validation_dataframe = train_test_split(training_validation_dataframe,
                                                                    stratify=training_validation_dataframe[
                                                                        label_column],
                                                                    test_size=self.validation_size,
                                                                    random_state=random_seed)
        training_dataframe.to_csv(self.training_csv_file, index=False)
        logging.info("Training data file created at {} - {} records".format(self.training_csv_file,
                                                                            len(training_dataframe)))
        validation_dataframe.to_csv(self.validation_csv_file, index=False)
        logging.info("Validation data file created at {} - {} records".format(self.validation_csv_file,
                                                                              len(validation_dataframe)))

        testing_dataframe.to_csv(self.testing_csv_file, index=False)
        logging.info("Testing data file created at {} - {} records".format(self.testing_csv_file,
                                                                           len(testing_dataframe)))

        command = self.training_command.format(self.python_script, self.training_csv_file, self.validation_csv_file)
        logging.info("Running {}".format(command))
        exit_code = call(command, shell=True)
        logging.info("exit_code {}".format(exit_code))

    def obtain_probabilities(self, text_features):
        # type: (np.ndarray) -> np.ndarray

        text_as_string = text_features.item()
        command = self.prediction_command.format(self.python_script, text_as_string, self.model_directory)  # type: str

        logging.info("Running {}".format(command))
        standard_output = subprocess.check_output(command, shell=True)  # type:str
        logging.debug("standard_output {}".format(standard_output))

        return np.array([float(standard_output)])

    @staticmethod
    def convert_text_to_features(text_series):
        # type: (pd.Series) -> np.ndarray
        return np.expand_dims(text_series.to_numpy(), axis=1)

    @staticmethod
    def upsample_minority(training_dataframe, label_column, random_state):
        logging.info("Counts before upsampling")
        logging.info(training_dataframe[label_column].value_counts())

        group_identity_mask = training_dataframe[label_column] == GROUP_IDENTITY_CLASS
        group_identity_dataframe = training_dataframe[group_identity_mask]
        personal_identity_dataframe = training_dataframe[~group_identity_mask]

        personal_identity_upsample = resample(personal_identity_dataframe,
                                              replace=True,
                                              n_samples=len(group_identity_dataframe),
                                              random_state=random_state)

        training_dataframe = pd.concat([group_identity_dataframe, personal_identity_upsample])

        logging.info("Counts after upsampling")
        logging.info(training_dataframe[label_column].value_counts())
        return training_dataframe
