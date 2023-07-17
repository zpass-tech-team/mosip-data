## Data migration Procedure

All the masterdata DDL’s and platform specific tables DML’s will stay in the admin-services repository.

Any language-dependent or country specific data change(new/update/deletion) will be in mosip_data repository.

mosip_data  → repository

	xlsx → all the Upto date DMLs

	data_upgrade → folder to hold only the delta

		1.1.5.5_to_1.2.0.1 → Folder to contain scripts and data files required for country-specific data migration.

			data → folder to hold the CSV / xlsx files 

			scripts to handle specific data change eg: change in UI spec

			Readme

			upgrade.sh

			upgrade.properties

			upgrade_commands.txt

			rollback_commands.txt





