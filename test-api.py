import os
from kaggle.api.kaggle_api_extended import KaggleApi
import pandas as pd
import streamlit as st

api = KaggleApi()
api.authenticate()

dataset = 'uciml/default-of-credit-card-clients-dataset'
file_name = 'UCI_Credit_Card.csv'

if not os.path.exists(file_name):
    api.dataset_download_file(dataset, file_name, path='.', unzip=True)

df = pd.read_csv(file_name)

st.write(df.head())