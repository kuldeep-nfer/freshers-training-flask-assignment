class MongoConstants:
    HOST = 'ovh-mongo-prestaging.nferx.com'
    PORT = 27017
    USER = 'knigam'
    PASS = 'Xrvg5U4wCAwtkr6j'
    DATABASE = 'Kushagra'
    PROJECTS_COLLECTION = 'projects_collection'
    DATASETS_COLLECTIONS = 'datasets_collection'
    MODELS_COLLECTION = 'models_collection'
    DATASET_MODEL_MAPPING_COLLECTION = 'dataset_model_mapping_collection'

class ProjectService:
    URL = 'http://sentenceapi2.servers.nferx.com:8015/tagrecorder/v3/projects/{}'