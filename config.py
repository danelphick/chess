import yaml

with open('config.yaml', 'r') as file:
    __CONFIG__ = yaml.safe_load(file)

def config():
    return __CONFIG__
