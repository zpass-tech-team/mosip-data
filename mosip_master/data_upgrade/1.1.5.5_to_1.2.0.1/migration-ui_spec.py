# -*- coding: utf-8 -*-

#!/usr/bin/python3


## This script should be executed after DB upgrade and 1.2.0.* masterdata-service deployment

from datetime import datetime, timezone, timedelta
import argparse
import requests
import json

parser = argparse.ArgumentParser(description='This is UI spec migration script. Migrates 1.1.5.5 UI spec to 1.2.0 compatible SPEC and the same is published to the server. This script should be executed after DB upgrade and 1.2.0.* masterdata-service deployment.')
parser.add_argument("-d", "--domain", type=str, required=True, help="Server domain name, eg: dev.mosip.net")
parser.add_argument("-u", "--username", type=str, required=True, help="User with GLOBAL_ADMIN & REGISTRATION_ADMIN role")
parser.add_argument("-p", "--password", type=str, required=True, help="User password")
parser.add_argument("-pl", "--primaryLanguage", type=str, required=True, help="3 letter primary language code as used in 1.1.5.5")
parser.add_argument("-sl", "--secondaryLanguage", type=str, required=True, help="3 letter secondary language code as used in 1.1.5.5")


args = parser.parse_args()


## Values to be updated as per the deployment
authURL='https://'+args.domain+'/v1/authmanager/authenticate/useridPwd'
schemaURL='https://'+args.domain+'/v1/syncdata/latestidschema?schemaVersion=0'
uispecURL='https://'+args.domain+'/v1/masterdata/uispec'
uispecPublishURL='https://'+args.domain+'/v1/masterdata/uispec/publish'
primaryLang=args.primaryLanguage
secondaryLang=args.secondaryLanguage
username=args.username
password=args.password


def getCurrentDateTime():
  dt_now = datetime.now(timezone.utc)
  dt_now_str = dt_now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
  return dt_now_str+'Z'

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
  return authresponse.headers["authorization"]


def publish_spec(domain, spec_type, specjson):
	print("identity schema id : " + identity_schema_id)
	print("identity spec_type : " + spec_type)
	request_json = {
									  "id": "string",
									  "version": "string",
									  "requesttime": getCurrentDateTime(),
									  "metadata": {},
									  "request": {
									    "identitySchemaId": identity_schema_id,
									    "domain": domain,
									    "type": spec_type,
									    "title": spec_type + " UI spec",
									    "description": spec_type + " UI spec",
									    "jsonspec": specjson
									  }
									}
	spec_resp = requests.post(uispecURL, json=request_json, headers=req_headers)
	spec_resp_json = spec_resp.json()
	#print("UI spec POST response : " + json.dumps(spec_resp_json))

	spec_resp_json_2 = spec_resp_json['response']
	spec_id = spec_resp_json_2['id']
	dt_now = datetime.now(timezone.utc)
	dt_now = dt_now + timedelta(minutes=2)
	dt_now_str = dt_now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]

	print("UI spec publish request spec_id: " + spec_id)

	publish_spec_req = {
											  "id": "string",
											  "version": "string",
											  "requesttime": getCurrentDateTime(),
											  "metadata": {},
											  "request": {
											    "id": spec_id,
											    "effectiveFrom": dt_now_str+'Z'
											  }
											}
	print("UI spec publish request : " + json.dumps(publish_spec_req))
	publish_resp = requests.put(uispecPublishURL, json=publish_spec_req, headers=req_headers)
	publish_resp_json = publish_resp.json()
	print("UI spec published : " + json.dumps(publish_resp_json))


def getConsentFields():
	return	[{ "id": "IDSchemaVersion",
						"inputRequired": False,
						"type": "number",
						"minimum": 0,
						"maximum": 0,
						"description": "ID Schema Version",
						"label": {
							"eng": "IDSchemaVersion"
						},
						"fieldType": "default",
						"format": "none",
						"validators": [],
						"fieldCategory": "none",
						"transliterate": False,
						"required": True,
						"requiredOn": [],
						"subType": "IdSchemaVersion",
						"exceptionPhotoRequired": False
					}, {
						"id": "consentText",
						"inputRequired": True,
						"type": "simpleType",
						"minimum": 0,
						"maximum": 0,
						"description": "Consent",
						"label": {},
						"controlType": "html",
						"fieldType": "default",
						"format": "none",
						"validators": [],
						"fieldCategory": "evidence",
						"group": "consentText",
						"transliterate": False,
						"templateName": "reg-consent-template",
						"required": True,
						"requiredOn": [],
						"subType": "consentText",
						"exceptionPhotoRequired": False
					}, {
						"id": "consent",
						"inputRequired": True,
						"type": "string",
						"minimum": 0,
						"maximum": 0,
						"description": "consent accepted",
						"label": {
							"ara": "الاسم الكامل الكامل الكامل",
							"fra": "J'ai lu et j'accepte les termes et conditions pour partager mes PII",
							"eng": "I have read and accept terms and conditions to share my PII"
						},
						"controlType": "checkbox",
						"fieldType": "default",
						"format": "none",
						"validators": [],
						"fieldCategory": "evidence",
						"group": "consent",
						"transliterate": False,
						"required": True,
						"requiredOn": [],
						"subType": "consent",
						"exceptionPhotoRequired": False
					}]




# invoke syncdata service with authtoken in headers
req_headers={'Cookie' : 'Authorization='+getAccessToken()}
schema_resp=requests.get(schemaURL, headers=req_headers)
print(schema_resp)
schema_resp_1=schema_resp.json()
schema_resp_2=schema_resp_1['response']

identity_schema_id=schema_resp_2['id']
cur_schema=schema_resp_2['schema']
domain='registration-client'


demographics=[]
documents=[]
biometrics=[]
# read response json and create UI-specs
for field in cur_schema:
	if(field['inputRequired']):
		#Add labels		
		labels=field['label']
		labels[primaryLang]=labels['primary']
		if(labels.get('secondary') != None):
			labels[secondaryLang]=labels['secondary']
		
		field['label']=labels

		if field['type'] == 'documentType':
			documents.append(field)
		elif field['type'] == 'biometricsType':
			biometrics.append(field)
		else:
			demographics.append(field)


new_spec = {
					   "id": "NEW",
					   "order": 1,
					   "flow": "NEW",
					   "label": {
					        "eng": "New Registration",
		              "ara": "تسجيل جديد",
		              "fra": "Nouvelle inscription"
					   },
					   "screens": [{
														"order": 1,
														"name": "consentdet",
														"label": {
															"ara": "موافقة",
															"fra": "Consentement",
															"eng": "Consent"
														},
														"caption": {
															"ara": "موافقة",
															"fra": "Consentement",
															"eng": "Consent"
														},
														"fields": getConsentFields(),
														"preRegFetchRequired": False,
														"additionalInfoRequestIdRequired": False,
														"active": False
									},{
					           "order": 2,
					           "name": "DemographicsDetails",
					           "label": {
					              "ara": "التفاصيل الديموغرافية",
			                  "fra": "Détails démographiques",
			                  "eng": "Demographic Details"
					           },
					           "caption": {
					               "ara": "التفاصيل الديموغرافية",
			                  "fra": "Détails démographiques",
			                  "eng": "Demographic Details"
					           },
					           "fields": demographics,
					           "preRegFetchRequired": True,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       },
					       {
					           "order": 3,
					           "name": "DocumentDetails",
					           "label": {
					               "ara": "تحميل الوثيقة",
			                  "fra": "Des documents",
			                  "eng": "Document Upload"
					           },
					           "caption": {
					               "ara": "وثائق",
			                  "fra": "Des documents",
			                  "eng": "Documents"
					           },
					           "fields": documents,
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       },
					       {
					           "order": 4,
					           "name": "BiometricDetails",
					           "label": {
					              "ara": "التفاصيل البيومترية",
			                  "fra": "Détails biométriques",
			                  "eng": "Biometric Details"
					           },
					           "caption": {
					               "ara": "التفاصيل البيومترية",
				                  "fra": "Détails biométriques",
				                  "eng": "Biometric Details"
					           },
					           "fields": biometrics,
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       }
					   ],
					   "caption": {
					       "eng": "New Registration",
		              "ara": "تسجيل جديد",
		              "fra": "Nouvelle inscription"
					   },
					   "icon": "NewReg.png",
					   "isActive": True,
					}
	

#publish ui-spec with for new process
publish_spec(domain, 'newProcess', new_spec)


update_spec = {
					   "id": "UPDATE",
					   "order": 2,
					   "flow": "UPDATE",
					   "label": {
					        "eng": "Update UIN",
		              "ara": "تحديث UIN",
		              "fra": "Mettre à jour l'UIN"
					   },
					   "screens": [{
														"order": 1,
														"name": "consentdet",
														"label": {
															"ara": "موافقة",
															"fra": "Consentement",
															"eng": "Consent"
														},
														"caption": {
															"ara": "موافقة",
															"fra": "Consentement",
															"eng": "Consent"
														},
														"fields": getConsentFields(),
														"preRegFetchRequired": False,
														"additionalInfoRequestIdRequired": False,
														"active": False
									},{
					           "order": 2,
					           "name": "DemographicsDetails",
					           "label": {
					              "ara": "التفاصيل الديموغرافية",
			                  "fra": "Détails démographiques",
			                  "eng": "Demographic Details"
					           },
					           "caption": {
					               "ara": "التفاصيل الديموغرافية",
			                  "fra": "Détails démographiques",
			                  "eng": "Demographic Details"
					           },
					           "fields": demographics,
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       },
					       {
					           "order": 3,
					           "name": "DocumentDetails",
					           "label": {
					               "ara": "تحميل الوثيقة",
			                  "fra": "Des documents",
			                  "eng": "Document Upload"
					           },
					           "caption": {
					               "ara": "وثائق",
			                  "fra": "Des documents",
			                  "eng": "Documents"
					           },
					           "fields": documents,
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       },
					       {
					           "order": 4,
					           "name": "BiometricDetails",
					           "label": {
					              "ara": "التفاصيل البيومترية",
			                  "fra": "Détails biométriques",
			                  "eng": "Biometric Details"
					           },
					           "caption": {
					               "ara": "التفاصيل البيومترية",
				                  "fra": "Détails biométriques",
				                  "eng": "Biometric Details"
					           },
					           "fields": biometrics,
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       }
					   ],
					   "caption": {
					       "eng": "Update UIN",
		              "ara": "تحديث UIN",
		              "fra": "Mettre à jour l'UIN"
					   },
					   "icon": "UINUpdate.png",
					   "isActive": True
					}
	

#publish ui-spec with for update process
publish_spec(domain, 'updateProcess', update_spec)


lost_spec = {
					   "id": "LOST",
					   "order": 2,
					   "flow": "LOST",
					   "label": {
					        "eng": "Lost UIN",
		              "ara": "فقدت UIN",
		              "fra": "UIN perdu"
					   },
					   "screens": [{
														"order": 1,
														"name": "consentdet",
														"label": {
															"ara": "موافقة",
															"fra": "Consentement",
															"eng": "Consent"
														},
														"caption": {
															"ara": "موافقة",
															"fra": "Consentement",
															"eng": "Consent"
														},
														"fields": getConsentFields(),
														"preRegFetchRequired": False,
														"additionalInfoRequestIdRequired": False,
														"active": False
									},{
					           "order": 2,
					           "name": "DemographicsDetails",
					           "label": {
					              "ara": "التفاصيل الديموغرافية",
			                  "fra": "Détails démographiques",
			                  "eng": "Demographic Details"
					           },
					           "caption": {
					               "ara": "التفاصيل الديموغرافية",
			                  "fra": "Détails démographiques",
			                  "eng": "Demographic Details"
					           },
					           "fields": demographics,
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       },
					       {
					           "order": 3,
					           "name": "DocumentDetails",
					           "label": {
					               "ara": "تحميل الوثيقة",
			                  "fra": "Des documents",
			                  "eng": "Document Upload"
					           },
					           "caption": {
					               "ara": "وثائق",
			                  "fra": "Des documents",
			                  "eng": "Documents"
					           },
					           "fields": documents,
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       },
					       {
					           "order": 4,
					           "name": "BiometricDetails",
					           "label": {
					              "ara": "التفاصيل البيومترية",
			                  "fra": "Détails biométriques",
			                  "eng": "Biometric Details"
					           },
					           "caption": {
					               "ara": "التفاصيل البيومترية",
				                  "fra": "Détails biométriques",
				                  "eng": "Biometric Details"
					           },
					           "fields": biometrics,
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       }
					   ],
					   "caption": {
					       "eng": "Lost UIN",
		              "ara": "فقدت UIN",
		              "fra": "UIN perdu"
					   },
					   "icon": "LostUIN.png",
					   "isActive": True
					}
	

#publish ui-spec with for lost process
publish_spec(domain, 'lostProcess', lost_spec)

settings_spec = [{
	"name": "scheduledjobs",
	"description": {
		"ara": "إعدادات الوظائف المجدولة",
		"fra": "Paramètres des travaux planifiés",
		"eng": "Scheduled Jobs Settings"
	},
	"label": {
		"ara": "إعدادات الوظائف المجدولة",
		"fra": "Paramètres des travaux planifiés",
		"eng": "Scheduled Jobs Settings"
	},
	"fxml": "ScheduledJobsSettings.fxml",
	"icon": "scheduledjobs.png",
	"order": "1",
	"shortcut-icon": "scheduledjobs-shortcut.png",
	"access-control": ["REGISTRATION_SUPERVISOR"]
}, {
	"name": "globalconfigs",
	"description": {
		"ara": "إعدادات التكوين العامة",
		"fra": "Paramètres de configuration globale",
		"eng": "Global Config Settings"
	},
	"label": {
		"ara": "إعدادات التكوين العامة",
		"fra": "Paramètres de configuration globale",
		"eng": "Global Config Settings"
	},
	"fxml": "GlobalConfigSettings.fxml",
	"icon": "globalconfigs.png",
	"order": "2",
	"shortcut-icon": "globalconfigs-shortcut.png",
	"access-control": ["REGISTRATION_SUPERVISOR", "REGISTRATION_OFFICER"]
}, {
	"name": "devices",
	"description": {
		"ara": "إعدادات الجهاز",
		"fra": "Réglages de l'appareil",
		"eng": "Device Settings"
	},
	"label": {
		"ara": "إعدادات الجهاز",
		"fra": "Réglages de l'appareil",
		"eng": "Device Settings"
	},
	"fxml": "DeviceSettings.fxml",
	"icon": "devices.png",
	"order": "3",
	"shortcut-icon": "devices-shortcut.png",
	"access-control": ["REGISTRATION_SUPERVISOR", "REGISTRATION_OFFICER"]
}]

#publish ui-spec with for settings screens
publish_spec(domain, 'settings', settings_spec)
