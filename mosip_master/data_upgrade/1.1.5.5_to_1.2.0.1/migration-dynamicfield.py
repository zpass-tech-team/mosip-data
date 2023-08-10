#!/usr/bin/python3

import psycopg2
import json
import sys

conn = psycopg2.connect(database="mosip_master", user = sys.argv[1], password = sys.argv[2], host = sys.argv[3], port = sys.argv[4])

print("Opened database successfully")

cur = conn.cursor()

#Backup existing dynamic_field table
cur.execute('ALTER TABLE master.dynamic_field RENAME TO dynamic_field_migr_bkp;')

print("Renamed dynamic_field table to dynamic_field_migr_bkp")

#Create dynamic_field table
cur.execute('''CREATE TABLE master.dynamic_field(
	id character varying(36) NOT NULL,
	name character varying(36) NOT NULL,
	description character varying(256),
	data_type character varying(16),
	value_json character varying,
	lang_code character varying(3) NOT NULL,
	is_active boolean NOT NULL,
	cr_by character varying(256) NOT NULL,
	cr_dtimes timestamp NOT NULL,
	upd_by character varying(256),
	upd_dtimes timestamp,
	is_deleted boolean DEFAULT FALSE,
	del_dtimes timestamp,
	CONSTRAINT pk_dynamic_id PRIMARY KEY (id));''')

print("created table dynamic_field")


cur.execute('GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES ON master.dynamic_field TO masteruser;')
print("Applied grant on dynamic_field")

#Query all the records from backup table
cur.execute('select * from master.dynamic_field_migr_bkp;')
rows = cur.fetchall()

print("Data fetched from backup table")

list_entities = []

#Iterate through each row and create new insert statements
for row in rows:
 values = json.loads(row[4])
 for val in values:
   vmap = {'code' : val['code'], 'value': val['value']}
   list_entities.append(json.dumps({"name": row[1], "langCode" : val['langCode'], "value_json": json.dumps(vmap), "is_active": row[6]}))


#Query all the records from gender table
cur.execute('select * from master.gender;')
gender_rows = cur.fetchall()
for row in gender_rows:
  vmap = {'code' : row[0], 'value': row[1]}
  list_entities.append(json.dumps({"name": sys.argv[5], "langCode" : row[2],"value_json": json.dumps(vmap), "is_active": row[3]}))


#Query all the records from individual_type table
cur.execute('select * from master.individual_type;')
individual_type_rows = cur.fetchall()
for row in individual_type_rows:
  vmap = {'code' : row[0], 'value': row[1]}
  list_entities.append(json.dumps({"name": sys.argv[6], "langCode" : row[2],"value_json": json.dumps(vmap), "is_active": row[3]}))


id = 1000
stmt = 'insert into dynamic_field values (%s,%s,%s,%s,%s,%s,%s,%s,now(),NULL,NULL,False,NULL);'
unique_entities = set(list_entities)
for entity_str in unique_entities:
  id = id + 1
  entity = json.loads(entity_str)
  status = False
  if(entity['is_active'] == True):
    status = True
  #Execute the insert statement
  cur.execute(stmt, (str(id), entity['name'], entity['name'], 'string', entity['value_json'], entity['langCode'], status, 'migration-script'))


# Commit and close connection
conn.commit()

print("Closing the database connection")
conn.close()
