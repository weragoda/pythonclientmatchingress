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



class status(restful.Resource):
    @marshal_with(fields)
    def get(self):
        resp_ingress_conf = None
        resp_ingress_master = None
        pod_list = None

        master_list_array = []
        ingress_list_array = []

        try:
            config.load_kube_config()
            api = core_v1_api.CoreV1Api()
            api_instance = kubernetes.client.ExtensionsV1beta1Api()

            # Listing pod lbel for nginx-ingress
            pod_list = api.list_namespaced_pod('kube-system', label_selector='name=nginx-ingress')

            # Listing ingress from master
            resp_ingress_master = api_instance.list_ingress_for_all_namespaces()

            # Reading nginx.conf
            exec_command = ['cat','/etc/nginx/nginx.conf']
            for pod in pod_list.items:
                resp_ingress_conf = api.connect_get_namespaced_pod_exec(pod.metadata.name, 'kube-system',
                                                           command= exec_command,
                                                           stderr = True, stdin = False,
                                                           stdout = True, tty = False)

            # filter ingress server names and put to new array
            regex_ingress = r"(?:server_name)(?:\s(.*);)"
            for _, match in enumerate(re.finditer(regex_ingress, resp_ingress_conf)):
                value =  match.group(1)
                ingress_list_array.append(value)

            #filter ingre master host put in to new array
            regex_master = r"(?:'host':\s*')(.*)(?:'\n*,)"
            for _, match in enumerate(re.finditer(regex_master, str(resp_ingress_master))):
                value =  match.group(1)
                master_list_array.append(value)

            if ingress_list_array == master_list_array:
                TODOS = { 'response':'ingress list comparision completed. ' + str(master_list_array) + ' ingres conf : ' + str(ingress_list_array)}
            else:
                abort(400, message="ingress list comparision fail :( master list: {} ingres conf:{}".format(master_list_array, ingress_list_array))

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
