## Data migration Procedure

All the masterdata DDL’s and platform specific tables DML’s will stay in the admin-services repository.

Any language-dependent or country specific data change(new/update/deletion) will be in mosip_data repository.

mosip_data  → repository

	xlsx → all the Upto date DMLs

	data_upgrade → folder to hold only the delta

		1.1.5.5_to_1.2.0.1 → Folder to contain scripts and data files required for country-specific data migration.

			scripts to handle specific data change eg: change in UI spec

			Readme

			upgrade.sh

			upgrade.properties

			upgrade_commands.txt

			rollback_commands.txt


## How to run the migration script

`bash upgrade.sh upgrade.properties`

upgrade.sh file execute the list of commands one after the other listed in upgrade_commands.txt
Before executing the script, kindly update the upgrade.properties with valid values.








