# the system should match the status of sources at a given time
# we should be able to retrieve:
#      the original uri (even if do not exists anymore)
#      the parsed content at the time of crawling
# we should parse / embbed / index only when necessary
# if DB containes a parsed_hash, it should always exists in parsed_doc_repo and in search_engine

# 1. crawling a source return a list of (uri, raw_hash) pairs
# 2. we find in the DB:
#      - uris not existing in the DB -> uris to add to the db
#      - uris in the db with a different raw_hash -> uris to update
#      - raw_hash not existing in the DB -> contents to parse and index
#      - uris in the db but not in crawling results-> uris to remove from the DB
# 3. we parse all not parsed raw_hash
# 4. add missing parsed_hash -> parsed_content dict
# 5. add vector store chunk -> parsed_hash for missing hashes
# ...At this point a vector search could point to parsed_hash not yet in DB, but it cannot point to a deleted
# parsed_hash
# 6. update DB
# at this point, if vector search points to parsed_hash not in DB, it is that it has been deleted or replaced
# if so, all corrects search results will point to a valid parsed_hash already in DB
# 7. remove vector store chunks pointing to parsed_hash not in DB anymore
# 8. remove parsed_hash to content not in Db anymore

# => if it fails at any point, we can restart and search results are always valid
