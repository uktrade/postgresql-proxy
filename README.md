# postgresql-proxy



### Onboarding a new client

#### In proxy space
- `cf push postgresql-proxy-for-<client>` 

- `cf create-service postgres small-10 postgresql-proxy-db-for-<client>`

- `cf bind-service postgresql-proxy-for-<client> postgresql-proxy-db-for-<client>`

- `cf restage postgresql-proxy-for-<client>`

- `cf map-route postgresql-proxy-for-<client> apps.internal --hostname data-workspace-datasets-for-<client>`

- `cf delete-route london.cloudapps.digital --hostname postgresql-proxy-for-<client>`

- `cf share-service postgresql-proxy-db-for-<client> -s <data-flow-space>`

#### In Data Flow space 

- `cf bind-service data-flow-<env> postgresql-proxy-db-for-<client>`

- Run `cf env data-flow-<env>` and copy uri for the client's database in `VCAP_SERVICES['postgres']`

- Set `AIRFLOW_CONN_<client>` in vault with the uri value copied in the previous step

- Deploy app via jenkins

### Configuring client database

#### In proxy space

- `cf conduit postgresql-proxy-db-for-<client> -- psql`

- Run the following SQL statements:
```sql
CREATE SCHEMA dataflow

CREATE TABLE dataflow.metadata (
    id integer NOT NULL,
    table_schema text,
    table_name text,
    source_data_modified_utc timestamp without time zone,
    dataflow_swapped_tables_utc timestamp without time zone,
    table_structure jsonb,
    data_type integer NOT NULL,
    data_hash_v1 bytea,
    primary_keys text[],
    data_ids text[]
);

CREATE SEQUENCE dataflow.metadata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dataflow.metadata_id_seq OWNED BY dataflow.metadata.id;

ALTER TABLE ONLY dataflow.metadata ALTER COLUMN id SET DEFAULT nextval('dataflow.metadata_id_seq'::regclass);

ALTER TABLE ONLY dataflow.metadata ADD CONSTRAINT metadata_pkey PRIMARY KEY (id);

CREATE TABLE dataflow.table_dependencies (
    id integer NOT NULL,
    view_schema text NOT NULL,
    view_name text NOT NULL,
    ddl_to_run text NOT NULL
);

CREATE SEQUENCE dataflow.table_dependencies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE dataflow.table_dependencies_id_seq OWNED BY dataflow.table_dependencies.id;

ALTER TABLE ONLY dataflow.table_dependencies ALTER COLUMN id SET DEFAULT nextval('dataflow.table_dependencies_id_seq'::regclass);

ALTER TABLE ONLY dataflow.table_dependencies ADD CONSTRAINT table_dependencies_pkey PRIMARY KEY (id);
```
- Run SQL statements found at https://github.com/uktrade/data-flow/blob/master/alembic/versions/e7b0c0fba2e3_table_deps_save_and_restore.py#L36-L144

### Setting up networking between proxy and client space  

#### In client space

- `cf add-network-policy <client-app> --destination-app postgresql-proxy-for-<client> -s <proxy-space> --protocol tcp --port 5432`
