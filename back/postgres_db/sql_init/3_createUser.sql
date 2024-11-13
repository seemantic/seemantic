-- TODO: security; restrict rights to select/update/delete/insert

CREATE USER seemantic_back PASSWORD 'seemantic_back_test_pwd';
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA seemantic_schema TO seemantic_back;
GRANT ALL PRIVILEGES ON SCHEMA seemantic_schema TO seemantic_back;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA seemantic_schema TO seemantic_back;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA seemantic_schema TO seemantic_back;
