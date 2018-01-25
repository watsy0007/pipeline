from pipe import *
import json


@Pipe
def to_dict(x):
    return json.loads(x)


@Pipe
def to_json(x):
    return json.dumps(x)
