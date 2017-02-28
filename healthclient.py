import time
import re
import kubernetes.client
from kubernetes import config
from kubernetes.client import configuration
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException
from flask import Flask
from flask.ext import restful
from flask_restful import (reqparse, abort, fields, marshal_with, marshal)

app = Flask(__name__)
api = restful.Api(app)

TODOS = { 'response':'200'},

#only output the task field
fields = {
    'response': fields.String
}

class Todo(restful.Resource):
    @marshal_with(fields)
    def get(self, todo_id):
        if not(len(TODOS) > todo_id > 0) or TODOS[todo_id] is None:
            abort(404, message="Todo {} doesn't exist".format(todo_id))
        return TODOS[todo_id]

parser = reqparse.RequestParser()
parser.add_argument('task', type=str)

class status(restful.Resource):
    @marshal_with(fields)
    def get(self):
        resp_ingress_conf = None
        resp_ingress_master = None
        pod_list = None
        try:
            config.load_kube_config()
            api = core_v1_api.CoreV1Api()
            api_instance = kubernetes.client.ExtensionsV1beta1Api()


            # Listing pod lbel for nginx-ingress
            pod_list = api.list_namespaced_pod('kube-system', label_selector='name=nginx-ingress')

            # Listing ingress from master
            resp_ingress_master = api_instance.list_ingress_for_all_namespaces()
            print("+++++++++++++++++++++++++++")
            print(resp_ingress_master)
            print("+++++++++++++++++++++++++++")

            # Reading nginx.conf
            exec_command = ['cat','/etc/nginx/nginx.conf']
            for pod in pod_list.items:
                resp_ingress_conf = api.connect_get_namespaced_pod_exec(pod.metadata.name, 'kube-system',
                                                           command= exec_command,
                                                           stderr = True, stdin = False,
                                                           stdout = True, tty = False)

            regex = r"(?:server_name)(?:\s(.*);)"
            for _, match in enumerate(re.finditer(regex, resp_ingress_conf)):
                print match.group(1)
        #resp_ingress_master = # todo after ingress response done

        except ApiException as e:
            if e.status != 404:
                print("Unknown Error: %s" % e)
                exit(1)

        # Todo
        #if not resp_ingress_conf:

        # Todo
        #if not resp_ingress_master:

        return TODOS

## Actually setup the Api resource routing here ;)
api.add_resource(status, '/healthcheck')

## enable
if __name__ == '__main__':
        app.run(host= '0.0.0.0', port=5000, debug=False)

