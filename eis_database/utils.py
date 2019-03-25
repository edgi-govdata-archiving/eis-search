from collections import OrderedDict
from subprocess import Popen, PIPE
import datetime
import json
import os
import random
import re
import requests
import shlex
import sys
import time


_MAX_ATTEMPTS = 10
_DELAY = .1
NOW = datetime.datetime.now()
TIME_STAMP = datetime.datetime.strftime(NOW, "%Y-%m-%dT%H:%M:%S")


def wait_a_sec():
  sleep_time = random.random()
  time.sleep(sleep_time)

def print_config(args):
  config = vars(args) # same as args just in dict format
  print("---\nConfiguration\n---")
  col_width = max([len(x) for x in config.keys()]) + 2
  template = "  {:>%d} {}" % col_width
  for k in sorted(config.keys()):
    v = config[k]
    print(template.format("{}:".format(k), v))
  print("---")


# _dataset_exists checks whether a dataset exists by attempting to 
#   request info on the dataset and seeing if it errors or not
def _dataset_exists(dataset_name):
  exists = True
  cmd = "qri info me/{}".format(dataset_name)
  result = _shell_exec_once(cmd)
  for line in result.split("\n"):
    if re.match(r'^error', line) or "key not found" in line:
      exists = False
      break
  return exists

# --------------------------------------------------------------------
def _shell_exec_once(command):
    proc = Popen(shlex.split(command), stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdoutdata, err = proc.communicate()
    if len(stdoutdata) > 0:
      try:
        return stdoutdata.decode("utf-8")
      except:
        return stdoutdata
    if len(err) > 0:
      try:
        return err.decode("utf-8")
      except:
        return err
    # if err != "" and err.decode("utf-8") != "":
    #     # print("err was: '{}' type: {}".format(err, type(err)))
    #     raise Exception(err)
    # return stdoutdata.decode("utf-8")

# def _shell_exec(command):
#     stdoutdata = _shell_exec_once(command)
#     for _ in range(_MAX_ATTEMPTS - 1):
#         if "error" not in stdoutdata[:15]:
#             break
#         time.sleep(_DELAY)
#         stdoutdata = _shell_exec_once(command)
#     return stdoutdata

# --------------------------------------------------------------------
def download_temp_file(url, name, temp_dir, fail_queue):
  temp_path = os.path.join(temp_dir, name)
  if not os.path.exists(temp_path):
    wait_a_sec()
    try:
      resp = requests.get(url, timeout=0.01)
      with open(temp_path, "wb+") as fp:
        fp.write(resp.content)
      if os.path.exists(temp_path):
        os.chmod(temp_path, 0o777)
    except:
      details = (url, name, temp_dir)
      fail_queue.put(details)
  return temp_path



def add_to_ipfs(path):
  ipfs_hash = ""
  cmd = "ipfs add \"{}\"".format(path)
  result = _shell_exec_once(cmd)
  wait_a_sec()
  if result.split(" ")[0] == "added":
    info = result.split(" ")
    ipfs_hash = info[1]
  else:
    print("failed to add '{}' to ipfs".format(path))
  return ipfs_hash

# def fetch_and_add_to_ipfs(url, name, temp_dir="temp/"):
#   temp_path = download_temp_file(url, name, temp_dir)
#   ipfs_hash = add_to_ipfs(temp_path)
#   cmd = "rm -f \"{}\"".format(temp_path)
#   _shell_exec_once(cmd)
#   return ipfs_hash

# def fetch_and_add_to_ipfs(url, name):
#   #download file to /tmp/[name]
#   # add to ipfs
#   # return hash
#   # tmp_path = os.path.join("/tmp/", name)
#   tmp_path = os.path.join("temp/", name)
#   cmd = "curl -o \"{}\" {}".format(tmp_path, url)
#   result = _shell_exec_once(cmd)
#   return add_to_ipfs(tmp_path)



# --------------------------------------------------------------------

def add_qri_dataset(dataset_name, data_path, structure_path, meta_path):
  cmd = "qri add "
  cmd += "--data \"{}\" ".format(data_path)
  cmd += "--structure \"{}\" ".format(structure_path)
  cmd += "--meta \"{}\" ".format(meta_path)
  cmd += "me/{} ".format(dataset_name)
  # result = _shell_exec(cmd)
  result = _shell_exec_once(cmd)
  return result


def update_qri_dataset(dataset_name, data_path, structure_path, meta_path, commit_msg):
  cmd = "qri save "
  cmd += "-m \"{}\" ".format(commit_msg)
  cmd += "--data \"{}\" ".format(data_path)
  cmd += "--structure \"{}\" ".format(structure_path)
  cmd += "--meta \"{}\" ".format(meta_path)
  cmd += "me/{} ".format(dataset_name)
  # result = _shell_exec(cmd)
  result = _shell_exec_once(cmd)
  return result

def add_or_save_to_qri(dataset_name, data_path, structure_path, meta_path):
  if _dataset_exists(dataset_name):
    # set commit message and choose 'save'
    commit_msg = "recipe update @ {}".format(TIME_STAMP)
    result = update_qri_dataset(dataset_name, data_path, structure_path, meta_path, commit_msg)
  else:
    result = add_qri_dataset(dataset_name, data_path, structure_path, meta_path)
  return result


def add_to_qri(args):
  print("...adding to qri")

