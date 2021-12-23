\c mosip_regdevice sysadmin

\set CSVDataPath '\'/home/dbadmin/mosip_regdevice/dml'

-------------- Level 1 data load scripts ------------------------

----- TRUNCATE regdevice.reg_device_type TABLE Data and It's reference Data and COPY Data from CSV file -----
TRUNCATE TABLE regdevice.reg_device_type cascade ;

\COPY regdevice.reg_device_type (code,name,descr,is_active,cr_by,cr_dtimes) FROM './dml/regdevice-reg_device_type.csv' delimiter ',' HEADER  csv;

-------------- Level 2 data load scripts ------------------------

----- TRUNCATE regdevice.reg_device_sub_type TABLE Data and It's reference Data and COPY Data from CSV file -----
TRUNCATE TABLE regdevice.reg_device_sub_type cascade ;

\COPY regdevice.reg_device_sub_type (code,dtyp_code,name,descr,is_active,cr_by,cr_dtimes) FROM './dml/regdevice-reg_device_sub_type.csv' delimiter ',' HEADER  csv;


----- TRUNCATE regdevice.registered_device_master TABLE Data and It's reference Data and COPY Data from CSV file -----
TRUNCATE TABLE regdevice.registered_device_master cascade ;

\COPY regdevice.registered_device_master (code,status_code,device_id,device_sub_id,digital_id,serial_number,device_detail_id,purpose,firmware,expiry_date,certification_level,foundational_trust_provider_id,hotlisted,is_active,cr_by,cr_dtimes,upd_by,upd_dtimes) FROM './dml/regdevice-registered_device_master.csv' delimiter ',' HEADER  csv;


----- TRUNCATE regdevice.registered_device_master_h TABLE Data and It's reference Data and COPY Data from CSV file -----
TRUNCATE TABLE regdevice.registered_device_master_h cascade ;

\COPY regdevice.registered_device_master_h (code,status_code,device_id,device_sub_id,digital_id,serial_number,device_detail_id,purpose,firmware,expiry_date,certification_level,foundational_trust_provider_id,hotlisted,is_active,cr_by,cr_dtimes,upd_by,upd_dtimes,eff_dtimes) FROM './dml/regdevice-registered_device_master_h.csv' delimiter ',' HEADER  csv;

















