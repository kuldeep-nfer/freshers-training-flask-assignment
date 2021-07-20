import requests
import json
import hashlib

from flask import Flask, jsonify, request
from pymongo import MongoClient

from config import MongoConstants, ProjectService



client = MongoClient(connect=False,
					 host=MongoConstants.HOST,
					 port=MongoConstants.PORT,
					 username=MongoConstants.USER,
					 password=MongoConstants.PASS)

DATABASE = client[MongoConstants.DATABASE]
projects_coll = DATABASE[MongoConstants.PROJECTS_COLLECTION]
datasets_coll = DATABASE[MongoConstants.DATASETS_COLLECTIONS]
models_coll = DATABASE[MongoConstants.MODELS_COLLECTION]
dataset_model_mapping_coll = DATABASE[MongoConstants.DATASET_MODEL_MAPPING_COLLECTION]

app = Flask(__name__)

@app.route('/health')
def health_check():
	
	try:
		client.server_info()
	except:
		resp = {
			'message' : 'Mongo Server is Down',
			'success' : False
		}
		resp = jsonify(resp)
		resp.status_code = 500
		return resp
	
	resp = {
		'message' : 'Service is up!',
		'success' : True
	}
	resp = jsonify(resp)
	resp.status_code = 200
	return resp

@app.route('/process/<project_id>')
def process(project_id):
	"""
		API to process project data from logs of project_id
	"""
	url = ProjectService.URL.format(project_id)
	project_data = json.loads(requests.get(url).text)['result']['project']

	project_query = projects_coll.find_one({'_id' : project_id})

	if project_query and project_query['last_updated'] == project_data['last_updated']:
		resp = {
		'message' : 'Updated project is already present in database',
		'success' : True
		}
		resp = jsonify(resp)
		resp.status_code = 200
		return resp

	datasets = project_data['associated_datasets']
	models = project_data['models']

	dataset_ids = []
	for dataset in datasets:
		dataset_ids.append(dataset['_id'])
		datasets_coll.update_one({'_id' : dataset['_id']},{'$set' : dataset},upsert=True)
	
	model_ids = []
	for model in models:
		model_name = model["model_name"]
		model_id = hashlib.md5(model_name.encode()).hexdigest()
		model_ids.append(model_id)
		for dataset in model['datasets_used']:
			dataset_id = dataset['dataset_id']
			dataset_model_mapping_coll.update_one({'_id' : dataset_id}, {'$addToSet' : {'model' : model_id}}, upsert=True)
		models_coll.update_one({'_id' : model_id}, {'$set' : model}, upsert=True)
	
	projects_coll.update_one({'_id' : project_id}, {'$set' : {'_id' : project_id, 'datasets' : dataset_ids, 'models' : model_ids, 'last_updated' : project_data['last_updated']}}, upsert=True)
	
	resp = {
	'message' : 'Project added to database',
	'success' : True
	}
	resp = jsonify(resp)
	resp.status_code = 200
	return resp

@app.route('/getProjectDetails/<project_id>')
def get_project_details(project_id):
	"""
		API to get project details related to project_id
	"""
	project_query = projects_coll.find_one({'_id' : project_id})
	if not project_query:
		resp = {
		'message' : 'Project not present in database',
		'success' : False
		}
		resp = jsonify(resp)
		resp.status_code = 400
		return resp
	
	dataset_ids = list(project_query['datasets'])
	model_ids = list(project_query['models'])

	datasets_data = list(datasets_coll.find({'_id' : {'$in' : dataset_ids}}))
	models_data = list(models_coll.find({'_id' : {'$in' : model_ids}}))
	resp = {
	'message' : 'Project is present is database, here are the details',
	'result' : {
		'associated_datasets' : datasets_data,
		'associated_models' : models_data,
		'last_updated' : project_query['last_updated']
	},
	'success' : True
	}
	resp = jsonify(resp)
	resp.status_code = 200
	return resp


@app.route('/getDatasetDetails/<dataset_id>')
def get_dataset_details(dataset_id):
	"""
		API to get model details for the given dataset_id
	"""
	dataset_query = datasets_coll.find_one({'_id' : dataset_id})
	if not dataset_query:
		resp = {
		'message' : 'This Dataset ID is not part of any project',
		'success' : False
		}
		resp = jsonify(resp)
		resp.status_code = 400
		return resp
	
	resp = {
	'message' : 'Dataset ID exists',
	'result' : dataset_query,
	'success' : True
	}
	resp = jsonify(resp)
	resp.status_code = 200
	return resp

@app.route('/getModelDetails/<model_name>')
def get_model_details(model_name):
	"""
		API to get model details for the given model_name
	"""
	model_id = hashlib.md5(model_name.encode()).hexdigest()
	model_query = models_coll.find_one({'_id' : model_id})
	if not model_query:
		resp = {
		'message' : 'This Model is not part of any project',
		'success' : False
		}
		resp = jsonify(resp)
		resp.status_code = 400
		return resp
	
	resp = {
	'message' : 'Model exists',
	'result' : model_query,
	'success' : True
	}
	resp = jsonify(resp)
	resp.status_code = 200
	return resp
	
@app.route('/getAssociatedModels/<dataset_id>')
def get_associated_models(dataset_id):
	"""
		API to get models used with the given dataset_id.
	"""
	dataset_query = dataset_model_mapping_coll.find_one({'_id' : dataset_id})
	if not dataset_query:
		resp = {
		'message' : 'This Dataset ID is not part of any project',
		'success' : False
		}
		resp = jsonify(resp)
		resp.status_code = 400
		return resp
	
	model_ids = list(dataset_query['model'])

	models_data = list(models_coll.find({'_id' : {'$in' : model_ids}},{'_id' : 0, 'model_name' : 1}))
	resp = {
	'message' : 'He are are models associated with the dataset',
	'result' : models_data,
	'success' : False
	}
	resp = jsonify(resp)
	resp.status_code = 200
	return resp

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=4444, debug = True)
	