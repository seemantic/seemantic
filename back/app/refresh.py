# the system should match the status of the source at a given time
# we should be able to retrieve:
#      the original uri (even if do not exists anymore)
#      the parsed content at the time of crawling
# we should parse / embbed / index only when necessary
# if DB containes a parsed_hash, it should always exists in parsed_doc_repo and in search_engine
# we shouln't hold more than on doc content in memory at a time

# 1. crawling a source return a list of (uri)
# 2. for each uri in crawling result:
#       - get raw content
#       - compute raw_content_hash
#       if raw_content_hash not in db (or force_reparse):
#           - parse content
#           - compute parsed_content_hash
#           - if parsed_content_hash missing from parsed_doc_repo, add
#           - if parsed_content_hash missing from vector_store, or "force_reindex":
#               -chunk / embed, then replace content with same parsed_content_hash (delete/add transaction).
#       - keep track of db update to do (uri, raw_content_hash, parsed_content_hash)
# 3. update db (remove / add / update) to match crawling results
# ...at this point, crawling state is matched with DB
# ...if we have several open connections (read on other server) eventual consistency
# ...in vector store might some new parsed hash are not yet taken into account by vector store
# ...we need to to a "checkout_latest". we can keep in DB a "last update_time"
# ...as it's not yet cleaned, search results will point to parsed_hash not in Db anymore
# ...we can just ignore them, as new ones are already added in VS
# 4. remove vector store chunks pointing to parsed_hash not in DB anymore
# 5. remove parsed_hash to content not in Db anymore
# 6. compact / index vs for performance


# => if it fails at any point, we can restart and search results are always valid

