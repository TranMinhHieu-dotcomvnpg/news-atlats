from elasticsearch import Elasticsearch
from pymongo import MongoClient
import certifi
from bson.objectid import ObjectId

# 1. Kết nối tới Elastic Cloud
es = Elasticsearch(
    cloud_id="7625433a80d24956afcdbb3b4b7d8536:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyQyN2Q5NmE2Yjc5MmU0Y2U1ODBkZjJjOWU4MDEzNjA1ZSQ1ZTA1MWY5ODM4ODE0YTgzOWVhODdkMmRlMzhlN2E5Mg==",
    basic_auth=("elastic", "6Doq58TB3cYO5wj9K5E7WdMN"),
    ca_certs=certifi.where()
)

# 2. Kết nối MongoDB (chỉnh host nếu không chạy local)
mongo = MongoClient("mongodb+srv://root:12345@cluster0.p1zfuq5.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
db = mongo['news_db']
collection = db['vnexpress_articles']

# 3. Kiểm tra số lượng document trong MongoDB
doc_count = collection.count_documents({})
print(f"MongoDB documents: {doc_count}")
if doc_count == 0:
    print("❌ Không có dữ liệu trong MongoDB. Hãy kiểm tra lại!")
    exit()

# 4. Kiểm tra và tạo index 'news' nếu chưa có, có mapping tối thiểu
index_name = "news"
try:
    if not es.indices.exists(index=index_name):
        mapping = {
            "mappings": {
                "properties": {
                    "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "summary": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "content": {"type": "text"},
                    "category": {"type": "keyword"},
                    "published_date": {"type": "date", "format": "yyyy-MM-dd||yyyy-MM-dd HH:mm:ss||yyyy-MM-dd'T'HH:mm:ss||epoch_millis||yyyy-MM-dd HH:mm"},
                    "url": {"type": "keyword"},
                    "image_url": {"type": "keyword"},
                    "suggest": {"type": "completion"}
                }
            }
        }
        es.indices.create(index=index_name, body=mapping)
        print(f"✅ Created index: {index_name} with mapping")
    else:
        print(f"ℹ️ Index '{index_name}' already exists.")
except Exception as e:
    print(f"❌ Error creating index: {e}")

# 5. Duyệt qua từng document và ghi vào Elasticsearch, có bắt lỗi
count = 0
for article in collection.find():
    url = article.get("url") or article.get("link", "")
    title = article.get("title", "")
    if not url or not url.startswith("http") or not title:
        continue  # Bỏ qua bài không có title hoặc url hợp lệ
    doc = {
        "title": title,
        "summary": article.get("summary", ""),
        "content": article.get("content", ""),
        "category": article.get("category", ""),
        "image_url": article.get("image_url", ""),
        "url": url,
        "suggest": {
            "input": [title] + article.get("summary", "").split(),
            "weight": 10
        }
    }
    published_date = article.get("published_date", "")
    if published_date:
        doc["published_date"] = str(published_date)
    try:
        resp = es.index(index=index_name, id=str(article["_id"]), document=doc)
        count += 1
        if count <= 3:  # In thử 3 kết quả đầu
            print(f"Indexed: {doc['title'][:30]}... => {resp['result']}")
    except Exception as e:
        print(f"❌ Error indexing doc {article.get('_id')}: {e}")

print(f"✅ Indexing completed! Total documents indexed: {count}")