from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser

# Define a schema for your documents
schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)

# Create an index directory (or open an existing one)
# For a new index:
ix = create_in("/tmp/indexdir", schema)
# For an existing index:
# ix = open_dir("indexdir")

# Add documents to the index
writer = ix.writer()
writer.add_document(title="First Document", path="/a", content="This is the content of the first document.")
writer.add_document(title="Second Document", path="/b", content="Another document with different content.")
writer.commit()

# Search the index
with ix.searcher() as searcher:
    query = QueryParser("content", ix.schema).parse("document")
    results = searcher.search(query)
    for hit in results:
        print(f"Title: {hit['title']}, Path: {hit['path']}")
