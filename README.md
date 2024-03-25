# Curamatic system design challenge

DAGs for Airflow 1.10.x. The soliddags package and tests are in https://github.com/LarkTechnologies/airflow-soliddags.

### Environment setup

Run the `setup-pyenv.sh` script to set up your local dev environment
To execute tests locally, run the following commands (in the Python environment):
```
PYTHONPATH=./src pytest
```

### Ingesting files

Start up the docker containers with:
```
docker compose up
```
Check that the containers are running and the database is initialized
```
docker ps -a
docker logs --follow postgres-db
```
Run the first step in the ingestion process to process the data from the raw zone using the `structured_zone_transformer`:
```
docker exec ingest-service python /src/structured_zone_transformer.py
```
This runs validations on each of the JSON entries, checking for required fields. It also handles each of these cases:
- Update the schema of the different files without telling us, changing the names of columns
- Send a completely different group of patients in the Patient.ndjson file
- Include duplicate records. Assume that occurrence in the file indicates the order in which they are updated, i.e lower in the file = more recent.
- Column values don’t conform to the proposed schema
    - Formats not as defined
- NULL values in one update that are filled in in later updates
    - Send a small number of claims with no corresponding users one week, only to include the patients in a subsequent update.

The `structured_zone_transformer` supports each of these cases respectively by:
- running validations on each of the JSON entries, checking for required fields.
- checking that the percentage of patient IDs in the history table is above a certain threshold before inserting rows 
into tables (see `test_percent_above_threshold`)
- using upserts to update existing patients and claims with the `upsert_patient` and `upsert_claim` methods 
- checking for formats of date fields and checking field values for enum fields; checks for other formats and other
enum fields can follow the same structure
- for NULL fields that get filled in at a later date, the `map_values` method sets those mapped field values to `None`,
which shows up as NULL in the database. There is a test case `test_map_values_with_null_patient_reference` that validates
this behavior. Once the field is filled in at a later date, the `upsert_patient` and `upsert_claim` methods update the
current tables, and the consumer zone transformer would load the data into the warehouse.


### Out of scope
This design does not aim to implement the full ETL pipeline, which requires Airflow and EMR to run. However, to scale up
to data set sizes that are 10,000 times larger, the `validate`, `map_values`, and `normalize` methods can each be implemented
in Spark, and the upsert methods can be modified to write files in parallel to S3.

#### Soda validations
API keys are required to run validations (https://docs.soda.io/soda-library/install.html#configure-soda). Once they are configured, 
after running the transformer, one can run the validations on the data that was produced:
```
docker exec ingest-service python /src/structured_zone_validations.py
```
