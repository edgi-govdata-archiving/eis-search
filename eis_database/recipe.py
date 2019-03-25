#!/usr/bin/python
import argparse
from bs4 import BeautifulSoup
from collections import OrderedDict
# have not yet tested with python 2 but as a start uncomment next line
#from __future__ import print_function
from tqdm import tqdm
# import cPickle
import pickle
import gzip
import json
import os
try:
  import queue as Queue
except:
  import Queue
import random
import requests
import sys
import threading
import time
import urllib
import utils


def check_id_is_valid(eisId, url, err_msg="An error occurred while executing your request. Please try again."):
  resp = requests.get(url, params={"eisId":eisId})
  if not resp.ok or err_msg in resp.text:
    return False
  else:
    return True

def fetch_page_text(eisId, url, param_name):
  resp = requests.get(url, params={param_name:eisId})
  return resp.text

def get_download_links(soup, filter_str="attachmentId="):
  all_links = soup.find_all(u'a')
  name_and_ref_list = list()
  for link in all_links:
    name = link.text.strip()
    ref = link.attrs.get('href', None)
    if ref and filter_str in ref:
      attachmentId = filter_str.split(filter_str)[-1]
      download_info = (name, ref, attachmentId)
      name_and_ref_list.append(download_info)
  return name_and_ref_list
    
def get_json_from_eis_page(html_str, eisId, handle_attachments=True):
  items = OrderedDict()
  soup = BeautifulSoup(html_str, 'html.parser')
  div_group = soup.find(class_="fieldset-wrapper")
  if div_group:
    sections = div_group.find_all(class_='form-item')
    for section in sections:
      section_header = section.find(name="h4")
      header_text = section_header.text.strip()
      vals = ""
      for child in section.children:
        if child != section_header:
          vals = child
          vals = vals.strip()
      items[header_text] = vals
  if len(items.keys()) > 0:
    items["eisId"] = eisId
    #get download links
    items["files"] = get_download_links(soup)
  return items

#---------------------------------------------------------------------
class LinkChecker(threading.Thread):
  def __init__(self, url, queue, valid_ids, invalid_ids, retry_ids):
    threading.Thread.__init__(self)
    self.queue = queue
    self.valid_ids = valid_ids
    self.invalid_ids = invalid_ids
    self.retry_ids = retry_ids
    self.url = url
  def run(self):
    while True:
      eid = self.queue.get()
      try:
        utils.wait_a_sec() # adds a < 1 sec delay between requests
        is_valid = check_id_is_valid(eid, self.url)
        if is_valid:
          self.valid_ids.put(eid)
          print(".", end="", flush=True)
        else:
          self.invalid_ids.put(eid)
          print(" ", end="", flush=True)
      except:
        print("!", end="", flush=True)
        self.retry_ids.put(eid)
      self.queue.task_done()

def checkLinks(args):
  num_threads = args.threads
  # input
  work_queue = Queue.Queue()
  # outputs
  valid_ids = Queue.Queue()
  invalid_ids = Queue.Queue()
  retry_ids = Queue.Queue()
  # create threads
  for i in range(num_threads):
    t = LinkChecker(args.url, work_queue, valid_ids, invalid_ids, retry_ids)
    t.setDaemon(True)
    t.start()
  # fill queue
  start = args.starting_id
  stop = start + args.max_pages
  ids_to_try = range(start, stop)
  for eid in ids_to_try:
    work_queue.put(eid)

  work_queue.join()
  # print result counts
  print("count in valid_ids:   {:>6}".format(valid_ids.qsize()))
  print("count in invalid_ids: {:>6}".format(invalid_ids.qsize()))
  print("count in retry_ids:   {:>6}".format(retry_ids.qsize()))
  #TODO: do retry

  id_list = list(valid_ids.queue)
  invalid_list = list(invalid_ids.queue)
  retry_list = list(retry_ids.queue)

  return id_list, invalid_list, retry_list
  #save valid ids
  with open(args.id_file, "w") as fp:
    id_list = list(valid_ids.queue)
    fp.write(json.dumps(id_list, indent=2))
    print("...saved {} valid ids to '{}' (max valid id was {})".format(len(id_list), args.id_file, max(id_list)))
  #TODO make this optional
  retry_path = args.id_file.replace(".json", "_invalid.json")
  with open(retry_path, "w") as fp:
    fp.write(json.dumps(retry_list, indent=2))
    print("...(temporary) saved list of page ids to retry to '{}'".format(retry_path)) 
  #temp: save retry list
  retry_path = args.id_file.replace(".json", "_retry.json")
  with open(retry_path, "w") as fp:
    fp.write(json.dumps(retry_list, indent=2))
    print("...(temporary) saved list of page ids to retry to '{}'".format(retry_path))

#---------------------------------------------------------------------
class PageExtractor(threading.Thread):
  def __init__(self, url, param_name, queue, success_q, fail_q1, fail_q2, extract_func):
    threading.Thread.__init__(self)
    self.queue = queue
    self.success_q = success_q
    self.fail_q1 = fail_q1
    self.fail_q2 = fail_q2
    self.url = url
    self.param_name = param_name
    self.extract_func = extract_func
  def run(self):
    while True:
      eisId = self.queue.get()
      try:
        page_text = fetch_page_text(eisId, self.url, self.param_name)
        # utils.wait_a_sec() # adds a < 1 sec delay between requests
        # result = self.extract_func(page_text, eisId)
        # if len(result.keys()) > 0:
        #   self.success_q.put(result)
        #   print(".", end='', flush=True)
        # else:
        #   self.fail_q2.put(eisId)
        #   print("*", end='', flush=True)
        try:
          utils.wait_a_sec() # adds a < 1 sec delay between requests
          result = self.extract_func(page_text, eisId)
          # x = 1
          if len(result.keys()) > 0:
            self.success_q.put(result)
            print(".", end='', flush=True)
          else:
            self.fail_q2.put(eisId)
            print("*", end='', flush=True)
        except:
          self.fail_q2.put(eisId)
          print("~", end='', flush=True)
      except:
        self.fail_q1.put(eisId)
        print("!", end='', flush=True)
      self.queue.task_done()

def extractPages(args):
  num_threads = args.threads
  # input
  work_queue = Queue.Queue()
  # outputs
  success_q = Queue.Queue()
  fail_q1 = Queue.Queue()
  fail_q2 = Queue.Queue()

  for i in range(num_threads):
    t = PageExtractor(args.url, args.qparam, work_queue, success_q, fail_q1, fail_q2, get_json_from_eis_page)
    t.setDaemon(True)
    t.start()
  
  with open(args.id_file, "r") as fp:
    id_list = json.load(fp)

  for eid in id_list:
    work_queue.put(eid)

  work_queue.join()
  # print results
  print("count in success_q: {:>6}".format(success_q.qsize()))
  print("count in fail_q1: {:>6}".format(fail_q1.qsize()))
  print("count in fail_q2: {:>6}".format(fail_q2.qsize()))

  metadata_list = list(success_q.queue)
  return metadata_list

#---------------------------------------------------------------------
class FileDownloader(threading.Thread):
  def __init__(self, url, work_queue, success_q, fail_q1, temp_dir):
    threading.Thread.__init__(self)
    self.work_queue = work_queue
    # self.add_queue = add_queue
    self.success_q = success_q
    self.fail_q1 = fail_q1
    self.url = url
    self.temp_dir = temp_dir
  def run(self):
    while True:
      item = self.work_queue.get()
      #try:
      if 'files' in item:
        files = item['files']
        file_hashes = dict()
        for file in files:
          name, ref, attachmentId  = file
          name = name.replace(" ", "_")
          download_url = urllib.parse.urljoin(self.url, ref)
          # utils.wait_a_sec()
          utils.download_temp_file(download_url, name, self.temp_dir, self.fail_q1)
          #temp_path = utils.download_temp_file(download_url, name)
          #utils.wait_a_sec()
          #ipfs_hash = utils.fetch_and_add_to_ipfs(download_url, name, temp_dir=self.temp_dir)
          #file_hashes[name] = ipfs_hash
        #item['files'] = file_hashes
        self.success_q.put(item)
        # self.add_queue.put(item)
        print(".", end="", flush=True)
        self.work_queue.task_done
      # else:
      #   self.fail_q1.put(item)
      self.work_queue.task_done()

def downladFiles(args):
  num_threads = args.threads
  # input
  work_queue = Queue.Queue()
  # outputs
  add_queue = Queue.Queue()
  success_q = Queue.Queue()
  fail_q1 = Queue.Queue()
  fail_q2 = Queue.Queue()
  for i in range(num_threads):
    t = FileDownloader(args.url, work_queue, success_q, fail_q1, args.temp_dir)
    t.setDaemon(True)
    t.start()
  # for i in range(num_threads):
  #   t = FileAdder(add_queue, success_q, fail_q2)
  with open(args.output_file, "r") as fp:
    metadata_list = json.load(fp)

  for item in metadata_list:
    work_queue.put(item)

  work_queue.join()
  # add_queue.join()
  # print results
  print("count in success_q: {:>6}".format(success_q.qsize()))
  print("count in fail_q1: {:>6}".format(fail_q1.qsize()))

  metadata_list = list(success_q.queue)
  fail_list = list(fail_q1.queue)
  return metadata_list, fail_list

#---------------------------------------------------------------------
class IPFSAdder(threading.Thread):
  def __init__(self, work_queue, success_q, fail_q1, nofile_q, temp_dir):
    threading.Thread.__init__(self)
    self.work_queue = work_queue
    self.success_q = success_q
    self.nofile_q = nofile_q
    self.fail_q1 = fail_q1
    self.temp_dir = temp_dir
  def run(self):
    while True:
      item = self.work_queue.get()
      try:
        file_hashes = dict()
        has_all_files = True

        for f in item["files"]:
          name, ref, attachmentId  = f
          name = name.replace(" ", "_")
          file_path = os.path.join(self.temp_dir, name)
          if os.path.exists(file_path):
            ipfs_hash = utils.add_to_ipfs(file_path)
            file_hashes[name] = ipfs_hash
          else:
            has_all_files = False
        if has_all_files:
          item["file_hashes"] = file_hashes
          self.success_q.put(item)
          print(".", end="", flush=True)
        else:
          self.nofile_q.put(item)
          print("-", end="", flush=True)
      except:
        self.fail_q1.put(item)
        print("*", end="", flush=True)
      self.work_queue.task_done()

    

def put_on_ipfs(args):
  # num_threads = args.threads
  num_threads = 1
  temp_dir = args.temp_dir
  # input
  work_queue = Queue.Queue()
  success_q = Queue.Queue()
  fail_q1 = Queue.Queue()
  nofile_q = Queue.Queue()

  for i in range(num_threads):
    t = IPFSAdder(work_queue, success_q, fail_q1, nofile_q, temp_dir)
    t.setDaemon(True)
    t.start()

  with open(args.output_file, "r") as fp:
    metadata_list = json.load(fp)

  for item in metadata_list:
    work_queue.put(item)
  work_queue.join()
  print("count in success_q:            {:>6}".format(success_q.qsize()))
  print("count in fail_q1:              {:>6}".format(fail_q1.qsize()))
  print("count not tried (in nofile_q): {:>6}".format(nofile_q.qsize()))

  metadata_list = list(success_q.queue)
  nofile_list = list(nofile_q.queue)
  fail_list = list(fail_q1.queue)
  return metadata_list, fail_list, nofile_list

#---------------------------------------------------------------------
def fetch_valid_id_list(args):
  print("...checking pages to generate valid_id_list")
  id_list, invalid_list, retry_list = checkLinks(args)
  #save valid ids
  with open(args.id_file, "w") as fp:
    id_list = list(valid_ids.queue)
    fp.write(json.dumps(id_list, indent=2))
    print("...saved {} valid ids to '{}' (max valid id was {})".format(len(id_list), args.id_file, max(id_list)))
  #TODO make this optional
  invalid_path = args.id_file.replace(".json", "_invalid.json")
  with open(invalid_path, "w") as fp:
    fp.write(json.dumps(invalid_list, indent=2))
    print("...(temporary) saved list of invalid page ids to '{}'".format(invalid_path)) 
  #temp: save retry list
  retry_path = args.id_file.replace(".json", "_retry.json")
  with open(retry_path, "w") as fp:
    fp.write(json.dumps(retry_list, indent=2))
    print("...(temporary) saved list of page ids to retry to '{}'".format(retry_path))

def extract_data_from_pages(args):
  print ("...extracting metadata from pages")
  metadata_list = extractPages(args)
  # save extracted metadata
  with open(args.output_file, "w") as fp:
    fp.write(json.dumps(metadata_list, indent=2))
    print("...saved metadata for {} pages to '{}'".format(len(metadata_list), args.output_file))

def fetch_attachment_files(args):
  print("...downloading attachments and adding to '{}'".format(args.temp_dir))
  metadata_list, fail_list = downladFiles(args)
  # output_with_hashes = args.output_file.replace(".json", "_with_hashes.json")
  # with open(output_with_hashes, "w") as fp:
  #   fp.write(json.dumps(metadata_list, indent=2))
  #   print("...saved metadata with hashes to '{}'".format(output_with_hashes))
  # if len(fail_list) > 0:
  #   fail_path = args.output_file.replace(".json", "_with_hashes_failures.json")
  #   with open(fail_path, "w") as fp:
  #     fp.write(json.dumps(fail_list, indent=2))

def add_to_ipfs_and_save_results(args):
  print("...attempting to add files to IPFS from '{}'".format(args.temp_dir))
  metadata_list, fail_list, nofile_list = put_on_ipfs(args)
  output_with_hashes = args.output_file.replace(".json", "_with_hashes.json")
  with open(output_with_hashes, "w") as fp:
    fp.write(json.dumps(metadata_list, indent=2))
    print("...saved metadata with hashes to '{}'".format(output_with_hashes))
  if len(fail_list) > 0:
    fail_path = args.output_file.replace(".json", "_with_hashes_failures.json")
    with open(fail_path, "w") as fp:
      fp.write(json.dumps(fail_list, indent=2))
  if len(nofile_list) > 0:
    nofile_path = args.output_file.replace(".json", "_not_downloaded.json")
    with open(nofile, "w") as fp:
      fp.write(json.dumps(nofile_list, indent=2))



#---------------------------------------------------------------------
def main(args):
  # print config
  utils.print_config(args)
  if args.config:
    return
  id_file_path = args.id_file
  overwrite_ids = args.update_ids
  dont_have_id_file = not os.path.exists(id_file_path)

  data_file_path = args.output_file
  update_data = args.update_data
  dont_have_data = not os.path.exists(data_file_path)

  download_attachments = args.download
  add_to_ipfs = args.ipfs
  add_to_qri = args.qri
  #-------------------------------------------------------------------
  if overwrite_ids or dont_have_id_file:
    fetch_valid_id_list(args)
  else:
    print("...using existing id list '{}'".format(id_file_path))
  #-------------------------------------------------------------------
  if update_data or dont_have_data:
    extract_data_from_pages(args)
  else:
    print("...using existing data file '{}'".format(data_file_path))
  #-------------------------------------------------------------------
  if download_attachments:
    fetch_attachment_files(args)
  else:
    print("...skipping attachment download")
  #-------------------------------------------------------------------
  if add_to_ipfs:
    add_to_ipfs_and_save_results(args)
  else:
    print("...skipping IPFS add")
  #-------------------------------------------------------------------
  if add_to_qri:
    data_file_path = args.output_file.replace(".json", "_with_hashes.json")
    utils.add_or_save_to_qri(args.dsname, data_file_path, "templates/structure.json", "templates/meta.json")
  else:
    print("...skipping QRI add")
  #-------------------------------------------------------------------



#---------------------------------------------------------------------
#---------------------------------------------------------------------

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="This recipe fetches Metadata from the Environmental Impact Statement (EIS) Database.  Content (such as the url and query params can be modified using the arguments under the 'content' section and execution and control flow can be modified using the arguments under the 'execution' section")
  # Add arguments
  g_content = parser.add_argument_group('content', 'control content parameters')
  g_content.add_argument(
    "-u", "--url", 
    default="https://cdxnodengn.epa.gov/cdx-enepa-II/public/action/eis/details",
    help="base url to fetch; defaults to 'https://cdxnodengn.epa.gov/cdx-enepa-II/public/action/eis/details'",
    )
  g_content.add_argument(
    "-q", "--qparam", 
    default="eisId",
    help="name of query param to include in http url; defaults to 'eisId'",
    )
  g_content.add_argument(
    "-s", "--starting-id",
    default=75042, type=int,
    help="starting eisId number to use when checking for valid eisIds; defaults to 75042"
    )
  g_content.add_argument(
    "-m", "--max-pages",
    default=20000, type=int,
    help="maximum number of pages to check; defaults to 20,000"
    )
  g_content.add_argument(
    "-i", "--id-file", 
    default="id_list.json",
    help="path to list of id file to be used as query parameter values to iterate through; defaults to 'id_list.json'", 
    )
  g_content.add_argument(
    "-o", "--output-file", 
    default="data.json",
    help="extracted json output path; defaults to 'data.json'", 
    )
  g_content.add_argument(
    "--dsname",
    default="eis_database",
    help="qri dataset name"
    )
  g_content.add_argument(
    "--temp-dir",
    # default="/Volumes/LaCie/eis/",
    help="default_location to save files to temporarily")
  # g_content.add_argument(
  #   "--")
  # parser.add_argument(
  #   "--url", help='base url to fetch', default="https://cdxnodengn.epa.gov/cdx-enepa-II/public/action/eis/details")
  g_flow = parser.add_argument_group('execution', 'control execution and control flow')
  g_flow.add_argument(
    "-c", "--config", 
    action="store_true",
    help='display default or received config and return', 
    )
  g_flow.add_argument(
    "-t", "--threads", 
    default=16, type=int, 
    help='number of threads to run in parallel; defaults to 16', 
    )
  g_flow.add_argument(
    "--update-ids", 
    action="store_true", 
    default=False,
    help="update the id_list independent of whether there is a pre-existing id list; defaults to False")
  g_flow.add_argument(
    "--update-data", 
    action="store_true",
    default=False,
    help="update the output data independent of whether there not there is a pre-existing id list; defaults to True")
  g_flow.add_argument(
    "-d", "--download",
    action="store_true",
    default=False,
    help="download attachments and add to ipfs; defaults to True")
  g_flow.add_argument(
    "--ipfs",
    action="store_true",
    default=False,
    help="add to qri; defaults to True")
  g_flow.add_argument(
    "--qri",
    action="store_true",
    default=False,
    help="add to qri; defaults to True")


  args = parser.parse_args()
  main(args)