import os
import pandas as pd

def get_access_token():
	path = os.getcwd() + '/blog/extras/task.csv'
	df = pd.read_csv(path, index_col=False)		
	return str(df['access_token'][0])

def get_task_id():
	path = os.getcwd() + '/blog/extras/task.csv'
	df = pd.read_csv(path, index_col=False)		
	return str(df['task_id'][0])

def set_task_id(task_id):
	path = os.getcwd() + '/blog/extras/task.csv'
	df = pd.read_csv(path, index_col=False)		
	df['task_id'] = str(task_id)
	df.to_csv(path, index=False)