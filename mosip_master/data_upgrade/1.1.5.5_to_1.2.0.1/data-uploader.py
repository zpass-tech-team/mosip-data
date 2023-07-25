# -*- coding: utf-8 -*-

#!/usr/bin/python3


## This script should be executed after DB upgrade and 1.2.0.* masterdata-service deployment

from datetime import datetime, timezone, timedelta
import argparse
import requests
import json
import sys
import time
import psycopg2
import openpyxl

parser = argparse.ArgumentParser(description='This is CSV/xlsx file uploader script.invokes 1.2.0.1 bulk upload endpoints')
parser.add_argument("--domain", type=str, required=True, help="Server domain name, eg: api-internal.dev.mosip.net")
parser.add_argument("--username", type=str, required=True, help="User with GLOBAL_ADMIN & REGISTRATION_ADMIN role")
parser.add_argument("--password", type=str, required=True, help="User password")
parser.add_argument("--table", type=str, required=True, help="Database table name")
parser.add_argument("--operation", type=str, required=True, help="Database operation, eg: Insert or Update or Delete")
parser.add_argument("--file", type=str, required=True, help="Input file CSV or xlsx")
parser.add_argument("--autogen", choices=(1,0), default=0, type=int, required=False, help="Autogenerate value for id column")
parser.add_argument("--idcolumn", type=str, required=False, help="id column name, eg: A or B ...")
parser.add_argument("--sheetname", type=str, required=False, help="Sheet name to operate")
parser.add_argument("--dbusername", type=str, required=False, help="DB username")
parser.add_argument("--dbpassword", type=str, required=False, help="DB username")
parser.add_argument("--dbhost", type=str, required=False, help="DB hostname")
parser.add_argument("--dbport", type=str, required=False, help="DB port number")

args = parser.parse_args()

## Values to be updated as per the deployment
authURL='https://'+args.domain+'/v1/authmanager/authenticate/useridPwd'
uploadURL='https://'+args.domain+'/v1/admin/bulkupload'
uploadStatusURL='https://'+args.domain+'/v1/admin/bulkupload/transcation/'
username=args.username
password=args.password

def getCurrentDateTime():
  dt_now = datetime.now(timezone.utc)
  dt_now_str = dt_now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
  return dt_now_str+'Z'


def get_seed_value():
  conn = psycopg2.connect(database="mosip_master", user = args.dbusername, password = args.dbpassword, host = args.dbhost, port = args.dbport)
  cursor = conn.cursor()
  cursor.execute("select id from master."+args.table+" order by id desc limit 20")
  for row in cursor.fetchall():
    id_value = row[0]
    if id_value is None:
      seed_value = 1000
      break
    if id_value.isdigit():
      seed_value = id_value
      break;
    
  if seed_value == None:
    seed_value = 1000
  return seed_value


def find_last_data_row(sheet):
    max_row = sheet.max_row

    for row in range(max_row, 0, -1):
        for cell in sheet[row]:
            if cell.value is not None:
                return row

def fill_series():
    if args.sheetname == None:
      print("Sheet name is required to fill series in id column.")
      exit(1)

    if args.idcolumn == None:
      print("id column name is required to fill series.")
      exit(1)

    seed_value = get_seed_value()

    print("Sheet name: ",args.sheetname)
    print("Id column to fill series: ", args.idcolumn)
    print("Seed value: ", seed_value)

    workbook = openpyxl.load_workbook(args.file)
    sheet = workbook[args.sheetname]
    column = sheet[args.idcolumn]

    start_row = 2
    end_row = find_last_data_row(sheet)

    print("Start Row: ", start_row)
    print("End Row: ", end_row)

    if(start_row is None and end_row is None):
      print("Need a valid start_row and end_row!")
      return

    for i, value in enumerate(range(start_row, end_row + 1), start=1):
        column[i].value = int(seed_value) + value
    
    workbook.save(args.file)
    workbook.close()



def getAccessToken():
  auth_req_data = {
    'id': 'string',
    'metadata': {},
    'request': {
      'appId': 'admin',
      'password': password,
      'userName': username
    },
    'requesttime': getCurrentDateTime(),
    'version': 'string'
  }
  authresponse=requests.post(authURL, json= auth_req_data)
  print(json.dumps(authresponse.json()))
  return authresponse.headers["authorization"]



def uploadFile():
  if args.autogen == 1 :
    fill_series()

  data = {'category': 'masterdata', 'operation': args.operation, 'tableName': args.table}
  files = {'files': open(args.file, 'rb')}
  uploadResponse = requests.post(uploadURL, data=data, files=files, headers=req_headers, verify=True)
  uploadResponse_json = uploadResponse.json()
  response = uploadResponse_json['response']
  print(json.dumps(uploadResponse_json))
  return response['transcationId']


def getTransactionStatus(transactionId):
  statusResponse = requests.get(uploadStatusURL+transactionId, headers=req_headers, verify=True)
  statusResponse_json = statusResponse.json()
  response = statusResponse_json['response']
  return response


req_headers={'Cookie' : 'Authorization='+getAccessToken()}
transactionId = uploadFile()
while True:
  time.sleep(5) ## sleep for 5 seconds
  status_response = getTransactionStatus(transactionId)
  print(json.dumps(status_response))
  status = status_response["status"]
  if status == "COMPLETED":
    break
  if status == "FAILED":
    sys.exit("Transcation failed")




