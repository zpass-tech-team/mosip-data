# -*- coding: utf-8 -*-

#!/usr/bin/python3


## This script should be executed after DB upgrade and 1.2.0.* masterdata-service deployment

from datetime import datetime, timezone, timedelta
import argparse
import requests
import json
import sys

parser = argparse.ArgumentParser(description='This is UI spec migration script. Migrates 1.1.5.5 UI spec to 1.2.0 compatible SPEC and the same is published to the server. This script should be executed after DB upgrade and 1.2.0.* masterdata-service deployment.')
parser.add_argument("-d", "--domain", type=str, required=True, help="Server domain name, eg: dev.mosip.net")
parser.add_argument("-u", "--username", type=str, required=True, help="User with GLOBAL_ADMIN & REGISTRATION_ADMIN role")
parser.add_argument("-p", "--password", type=str, required=True, help="User password")
parser.add_argument("-pl", "--primaryLanguage", type=str, required=True, help="3 letter primary language code as used in 1.1.5.5")
parser.add_argument("-sl", "--secondaryLanguage", type=str, required=True, help="3 letter secondary language code as used in 1.1.5.5")
parser.add_argument("--identityMappingJsonUrl", type=str, required=True, help="URL to download identity_mapping.json")
parser.add_argument("--ageGroupConfig", type=str, required=True, help="Age group configuration")
parser.add_argument("--infantAgeGroup", type=str, required=True, help="Infant Age group name")
parser.add_argument("--allowedBioAttributes", type=str, required=True, help="Comma separated list of allowed biometric attributes")

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
agegroup_config=args.ageGroupConfig
infantAgeGroup = args.infantAgeGroup.strip()
allBioAttributes= args.allowedBioAttributes.strip().split(",")

## values loaded from identity-mapping.json
individual_bio_field=None
auth_bio_field=None
guardian_bio_field=None
guardian_demo_fields=[]
ageGroupBasedModalities = {}
ageGroupRequiresGuardian = []

def getSupportedAgeGroups():
	agegroup_config_json=json.loads(agegroup_config)
	for ageGroup in agegroup_config_json.keys():
		modalities = []
		while not modalities:
			modalities = agegroup_config_json.get(ageGroup).get("bioAttributes")
		ageGroupBasedModalities[ageGroup] = modalities

		requiresGuardianAuth = agegroup_config_json.get(ageGroup).get("isGuardianAuthRequired")
		if(requiresGuardianAuth == True):
			ageGroupRequiresGuardian.append(ageGroup)


def getConditionalBioAttributes():
	conditionalBioAttributes = []
	for ageGroup in ageGroupBasedModalities.keys():
		bioAttributes = ageGroupBasedModalities.get(ageGroup)
		if(len(bioAttributes) < 13):
			conditionalBioAttributes.append({
								"ageGroup": ageGroup,
								"process": "ALL",
								"validationExpr": " && ".join(bioAttributes),
								"bioAttributes": bioAttributes
							})
	return conditionalBioAttributes


def getGaurdianConditionalBioAttributes():
	conditionalBioAttributes = []
	for ageGroup in ageGroupBasedModalities.keys():
		if ageGroup in ageGroupRequiresGuardian:
			conditionalBioAttributes.append({
								"ageGroup": ageGroup,
								"process": "ALL",
								"validationExpr": " || ".join(allBioAttributes),
								"bioAttributes": allBioAttributes
							})
	return conditionalBioAttributes


def getGaurdianFieldRequiredOn():
	exprs = []
	for ageGroup in ageGroupBasedModalities.keys():
		if ageGroup in ageGroupRequiresGuardian:
			exprs.append("identity.get('ageGroup') == '"+ageGroup+"'")
	return [{ "engine": "MVEL", "expr": " || ".join(exprs) }]


def getCurrentDateTime():
  dt_now = datetime.now(timezone.utc)
  dt_now_str = dt_now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
  return dt_now_str+'Z'

def isValidBioFieldIds(values):
	if individual_bio_field.get('value') in values and auth_bio_field.get('value') in values and guardian_bio_field.get('value') in values:
		return True
	else:
		print(values)
		return False

def getGuardianDemographicFieldGroup(demographics):
	guardian_group = None
	for field in demographics:
		if field['id'] in guardian_demo_fields:
			guardian_group = field['group']
			break

	if guardian_group == None:
		sys.exit("Kindly check the provided Guardian/Introducer demographic field Id (Any one).")

	return guardian_group


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
  print(authresponse)
  return authresponse.headers["authorization"]


def publish_spec(domain, spec_type, specjson):
	print("identity schema id : " + identity_schema_id)
	print("identity spec_type : " + spec_type)
	spec = json.dumps(specjson)
	spec = spec.replace("identity.?isChild", "identity.get('ageGroup') == '"+infantAgeGroup+"'")
	spec = spec.replace("identity.isChild", "identity.get('ageGroup') == '"+infantAgeGroup+"'")
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
									    "jsonspec": json.loads(spec)
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


def buildNewRegistrationSpec(demographic_fields, document_fields, biometric_fields):
	spec = {
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
					           "fields": demographic_fields,
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
					           "fields": document_fields,
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
	
	for field in biometric_fields:
		if field['id'] == individual_bio_field.get('value'):
			individualBioField = {key: value for key, value in field.items()}
			individualBioField["conditionalBioAttributes"]=getConditionalBioAttributes()
			individualBioField["required"] = True
			individualBioField["requiredOn"] = []
			individualBioField["exceptionPhotoRequired"] = True
			individualBioField["subType"] = "applicant"

			spec['screens'].append({
					           "order": 4,
					           "name": "IndividualBiometricDetails",
					           "label": individualBioField["label"],
					           "caption": individualBioField["label"],
					           "fields": [individualBioField],
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       })

		if field['id'] == guardian_bio_field.get('value'):
			guardianBioField = {key: value for key, value in field.items()}
			guardianBioField["conditionalBioAttributes"]=getGaurdianConditionalBioAttributes()
			guardianBioField["required"] = False
			guardianBioField["requiredOn"] = getGaurdianFieldRequiredOn()
			guardianBioField["subType"] = "introducer"

			spec['screens'].append({
					           "order": 5,
					           "name": "GaurdianBiometricDetails",
					           "label": guardianBioField["label"],
					           "caption": guardianBioField["label"],
					           "fields": [guardianBioField],
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       })
	return spec


def buildSettingsSpec():
	return [{
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

def buildUpdateRegistrationSpec(demographic_fields, document_fields, biometric_fields, guardian_group_name):
	spec = {
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
					   "autoSelectedGroups": ["Consent","Documents","Biometrics"],
					   "caption": {
					       "eng": "Update UIN",
		              "ara": "تحديث UIN",
		              "fra": "Mettre à jour l'UIN"
					   },
					   "icon": "UINUpdate.png",
					   "isActive": True
					}
	

	for field in biometric_fields:
		if field['id'] == individual_bio_field.get('value'):
			individualBioField = {key: value for key, value in field.items()}
			individualBioField["conditionalBioAttributes"]=getConditionalBioAttributes()
			individualBioField["exceptionPhotoRequired"] = True
			individualBioField["required"] = True
			individualBioField["group"] = "Biometrics"
			individualBioField["groupLabel"] = {
								"ara": "القياسات الحيوية",
								"fra": "Biométrie",
								"eng": "Biometrics"
							}
			individualBioField["requiredOn"] = [{
								"engine": "MVEL",
								"expr": "identity.updatableFieldGroups contains 'Biometrics'"
							}]
			individualBioField["subType"] = "applicant"

			spec['screens'].append({
					           "order": 4,
					           "name": "IndividualBiometricDetails",
					           "label": individualBioField["label"],
					           "caption": individualBioField["label"],
					           "fields": [individualBioField],
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       })

		if field['id'] == auth_bio_field.get('value'):
			authBioField = {key: value for key, value in field.items()}
			authBioField["conditionalBioAttributes"]=[{
								"ageGroup": "ALL",
								"process": "ALL",
								"validationExpr": " || ".join(allBioAttributes),
								"bioAttributes": allBioAttributes
							}]
			authBioField["required"] = False
			authBioField["group"] = "Biometrics"
			authBioField["groupLabel"] = {
								"ara": "القياسات الحيوية",
								"fra": "Biométrie",
								"eng": "Biometrics"
							}
			authBioField["requiredOn"] = [{
								"engine": "MVEL",
								"expr": "!(identity.get('ageGroup') == '"+infantAgeGroup+"') && !(identity.updatableFieldGroups contains 'Biometrics')"
							}]
			authBioField["subType"] = "applicant-auth"

			spec['screens'].append({
					           "order": 5,
					           "name": "AuthBiometricDetails",
					           "label": authBioField["label"],
					           "caption": authBioField["label"],
					           "fields": [authBioField],
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       })

		if field['id'] == guardian_bio_field.get('value'):
			guardianBioField = {key: value for key, value in field.items()}
			guardianBioField["conditionalBioAttributes"]=[{
								"ageGroup": "ALL",
								"process": "ALL",
								"validationExpr": " || ".join(allBioAttributes),
								"bioAttributes": allBioAttributes
							}]
			guardianBioField["group"] = "Biometrics"
			guardianBioField["required"] = False
			guardianBioField["requiredOn"] = [{
								"engine": "MVEL",
								"expr": "identity.get('ageGroup') == '"+infantAgeGroup+"' || identity.updatableFieldGroups contains '"+guardian_group_name+"'"
							}]
			guardianBioField["subType"] = "introducer"

			spec['screens'].append({
					           "order": 6,
					           "name": "GuardianBiometricDetails",
					           "label": guardianBioField["label"],
					           "caption": guardianBioField["label"],
					           "fields": [guardianBioField],
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       })	
	return spec


def buildLostRegistrationSpec(demographic_fields, document_fields, biometric_fields):
	spec = {
					   "id": "LOST",
					   "order": 3,
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

	for field in biometric_fields:
		if field['id'] == individual_bio_field.get('value'):
			individualBioField = {key: value for key, value in field.items()}
			individualBioField["conditionalBioAttributes"]=getConditionalBioAttributes()
			individualBioField["required"] = True
			individualBioField["requiredOn"] = []
			individualBioField["subType"] = "applicant"

			spec['screens'].append({
					           "order": 4,
					           "name": "BiometricDetails",
					           "label": individualBioField["label"],
					           "caption": individualBioField["label"],
					           "fields": [individualBioField],
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       })

		if field['id'] == guardian_bio_field.get('value'):
			guardianBioField = {key: value for key, value in field.items()}
			guardianBioField["conditionalBioAttributes"]=[{
								"ageGroup": "ALL",
								"process": "ALL",
								"validationExpr": " || ".join(allBioAttributes),
								"bioAttributes": allBioAttributes
							}]
			guardianBioField["group"] = "Biometrics"
			guardianBioField["required"] = False
			guardianBioField["requiredOn"] = [{
								"engine": "MVEL",
								"expr": "identity.get('ageGroup') == '"+infantAgeGroup+"'"
							}]
			guardianBioField["subType"] = "introducer"

			spec['screens'].append({
					           "order": 5,
					           "name": "GuardianBiometricDetails",
					           "label": guardianBioField["label"],
					           "caption": guardianBioField["label"],
					           "fields": [guardianBioField],
					           "preRegFetchRequired": False,
					           "additionalInfoRequestIdRequired": False,
					           "active": False
					       })

	for field in demographics:
		field["required"] = False

	return spec




# invoke syncdata service with authtoken in headers
req_headers={'Cookie' : 'Authorization='+getAccessToken()}
get_schema_resp=requests.get(schemaURL, headers=req_headers)
print(get_schema_resp)
schema_resp_json=get_schema_resp.json()
schema_resp=schema_resp_json['response']
identity_schema_id=schema_resp['id']
cur_schema=schema_resp['schema']
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
			if field['fieldType'] == 'dynamic':
				newSubType = field['id']
				field['subType'] = newSubType
			demographics.append(field)


#set all the required field mappings
response = requests.get(args.identityMappingJsonUrl)
data = json.loads(response.text)
identity_mapping_json = data['identity']
if(identity_mapping_json.get('individualBiometrics') != None):
	individual_bio_field=identity_mapping_json.get('individualBiometrics')
if(identity_mapping_json.get('introducerBiometrics') != None):
	guardian_bio_field=identity_mapping_json.get('introducerBiometrics')
if(identity_mapping_json.get('individualAuthBiometrics') != None):
	auth_bio_field=identity_mapping_json.get('individualAuthBiometrics')

if(identity_mapping_json.get('introducerName') != None):
	guardian_demo_fields.append(identity_mapping_json.get('introducerName').get('value'))
if(identity_mapping_json.get('introducerUIN') != None):
	guardian_demo_fields.append(identity_mapping_json.get('introducerUIN').get('value'))
if(identity_mapping_json.get('introducerVID') != None):
	guardian_demo_fields.append(identity_mapping_json.get('introducerVID').get('value'))
if(identity_mapping_json.get('introducerRID') != None):
	guardian_demo_fields.append(identity_mapping_json.get('introducerRID').get('value'))


guardian_group = getGuardianDemographicFieldGroup(demographics);

## should take user input about biometric fields:
bioFieldIds = []
for field in biometrics:
	bioFieldIds.append(field['id'])

isValid = isValidBioFieldIds(bioFieldIds)
if isValid == False:
	sys.exit("Kindly check the biometics field Ids provided as input. Must be one in above valid values")


#Read ageGroup config and take the modalities input
getSupportedAgeGroups()

#publish ui-spec with for new process
publish_spec(domain, 'newProcess', buildNewRegistrationSpec(demographics, documents, biometrics))


#publish ui-spec with for update process
publish_spec(domain, 'updateProcess', buildUpdateRegistrationSpec(demographics, documents, biometrics, guardian_group))


#publish ui-spec with for lost process
publish_spec(domain, 'lostProcess', buildLostRegistrationSpec(demographics, documents, biometrics))


#publish ui-spec with for settings screens
publish_spec(domain, 'settings', buildSettingsSpec())
