from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, JsonResponse
from django.utils.feedgenerator import Rss201rev2Feed
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from .models import Category, ArticleCategory
from pymongo import MongoClient
from django.db.models import Count
from datetime import datetime
from django.conf import settings
from bson import ObjectId
from collections import Counter
from unidecode import unidecode

# Create your views here.
def home(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            logout(request) 
            messages.success(request, 'Logout Successful')
            return redirect('registration/login.html')
    # Nếu là admin -> vào trang admin
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/admin/')  # Django admin dashboard

    # Kết nối MongoDB
    client = MongoClient("mongodb+srv://root:12345@cluster0.p1zfuq5.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    db = client['news_db']
    collection = db['vnexpress_articles']

    # Lấy tin tức nổi bật (tin mới nhất)
    featured_news = collection.find_one(
        sort=[('published_date', -1)]
    )

    # Lấy tất cả danh mục từ MongoDB
    categories = collection.distinct('category')
    
    # Tạo danh sách danh mục với thông tin chi tiết
    category_list = []
    for category in categories:
        # Đếm số bài viết trong danh mục
        article_count = collection.count_documents({'category': category})
        
        # Lấy bài viết mới nhất trong danh mục
        latest_articles_raw = list(collection.find(
            {'category': category},
            sort=[('published_date', -1)],
        ))
        # Chỉ giữ lại bài có url hợp lệ
        latest_articles = []
        for article in latest_articles_raw:
            url = article.get('url') or article.get('link')
            if url and url.startswith('http'):
                article['url'] = url
                if '_id' in article:
                    article['id'] = str(article['_id'])
                latest_articles.append(article)
        category_list.append({
            'name': category,
            'display_name': category.replace('-', ' ').title(),
            'slug': category.lower().replace(' ', '-'),
            'article_count': article_count,
            'latest_articles': latest_articles
        })

    # Thống kê
    total_articles = collection.count_documents({})
    total_categories = len(categories)
    last_update = datetime.now()

    context = {
        'featured_news': featured_news,
        'categories': category_list,
        'total_articles': total_articles,
        'total_categories': total_categories,
        'last_update': last_update,
        'show_favorites': request.user.is_authenticated  # Chỉ hiển thị mục yêu thích nếu đã đăng nhập
    }

    return render(request, 'home.html', context)

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect('base:login')
    else:
        form = UserCreationForm()
    return render(request,"registration/register.html",{"form":form})

def latest_news(request):
    client = MongoClient("mongodb+srv://root:12345@cluster0.p1zfuq5.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    db = client['news_db']
    collection = db['vnexpress_articles']
    
    # Lấy danh sách tất cả danh mục
    categories = collection.distinct('category')
    
    # Lọc theo danh mục nếu có
    category = request.GET.get('category')
    if category:
        news = list(collection.find(
            {'category': category}
        ).sort('published_date', -1))
    else:
        news = list(collection.find().sort('published_date', -1))
    
    return render(request, 'news_rss_atlats/lastest_news.html', {
        'news': news,
        'categories': categories
    })

def all_articles(request):
    client = MongoClient("mongodb+srv://root:12345@cluster0.p1zfuq5.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    db = client['news_db']
    collection = db['vnexpress_articles']

    # Lấy danh sách tất cả danh mục
    categories = collection.distinct('category')

    # Lọc theo danh mục nếu có
    category = request.GET.get('category')
    if category:
        articles = list(collection.find(
            {'category': category}
        ).sort('published_date', -1))
    else:
        articles = list(collection.find().sort('published_date', -1))

    # Phân trang: 10 bài/trang
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news_rss_atlats/all_articles.html', {
        'page_obj': page_obj,
        'categories': categories
    })

@login_required
def category_list(request):
    categories = Category.objects.annotate(
        article_count=Count('articlecategory')
    )
    return render(request, 'news_rss_atlats/category_list.html', {
        'categories': categories
    })

@login_required
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    
    # Lấy danh sách ID bài viết thuộc danh mục này
    article_ids = ArticleCategory.objects.filter(
        category=category
    ).values_list('article_id', flat=True)
    
    # Kết nối MongoDB và lấy thông tin bài viết
    client = MongoClient("mongodb+srv://root:12345@cluster0.p1zfuq5.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    db = client['news_db']
    collection = db['vnexpress_articles']
    
    # Lấy thông tin bài viết từ MongoDB
    articles = list(collection.find(
        {'_id': {'$in': list(article_ids)}}
    ).sort('pub_date', -1))
    
    # Thêm thông tin confidence score cho mỗi bài viết
    for article in articles:
        article_category = ArticleCategory.objects.get(
            article_id=str(article['_id']),
            category=category
        )
        article['confidence_score'] = article_category.confidence_score
    
    return render(request, 'news_rss_atlats/category_detail.html', {
        'category': category,
        'articles': articles
    })

@login_required
def categorize_article(request, article_id):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        confidence_score = float(request.POST.get('confidence_score', 0.0))
        
        try:
            category = Category.objects.get(id=category_id)
            ArticleCategory.objects.update_or_create(
                article_id=article_id,
                category=category,
                defaults={'confidence_score': confidence_score}
            )
            return JsonResponse({'status': 'success'})
        except Category.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Category not found'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def categorized_articles(request):
    # Lấy danh sách ID bài viết đã được phân loại
    article_ids = ArticleCategory.objects.values_list('article_id', flat=True).distinct()
    
    # Kết nối MongoDB và lấy thông tin bài viết
    client = MongoClient("mongodb+srv://root:12345@cluster0.p1zfuq5.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    db = client['news_db']
    collection = db['vnexpress_articles']
    
    # Lấy thông tin bài viết từ MongoDB
    articles = list(collection.find(
        {'_id': {'$in': list(article_ids)}}
    ).sort('pub_date', -1))
    
    # Thêm thông tin danh mục cho mỗi bài viết
    for article in articles:
        categories = ArticleCategory.objects.filter(article_id=str(article['_id']))
        article['categories'] = [
            {
                'name': ac.category.name,
                'confidence_score': ac.confidence_score
            }
            for ac in categories
        ]
    
    # Phân trang
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Lấy danh sách tất cả danh mục để hiển thị bộ lọc
    categories = Category.objects.all()
    
    return render(request, 'news_rss_atlats/categorized_articles.html', {
        'page_obj': page_obj,
        'categories': categories
    })

# tìm kiếm tin tức elasticsearch
from elasticsearch import Elasticsearch
from django.shortcuts import render
import certifi

def search_news(request):
    query = request.GET.get('q', '')
    
    # Kết nối đến Elastic Cloud
    es = Elasticsearch(
        cloud_id="7625433a80d24956afcdbb3b4b7d8536:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyQyN2Q5NmE2Yjc5MmU0Y2U1ODBkZjJjOWU4MDEzNjA1ZSQ1ZTA1MWY5ODM4ODE0YTgzOWVhODdkMmRlMzhlN2E5Mg==",
        basic_auth=("elastic", "6Doq58TB3cYO5wj9K5E7WdMN"),
        ca_certs=certifi.where()
    )
    
    results = []
    if query:
        resp = es.search(
            index="news",
            query={
                "bool": {
                    "should": [
                        # Ưu tiên khớp cụm từ chính xác trong tiêu đề và tóm tắt
                        {
                            "match_phrase": {
                                "title": {
                                    "query": query,
                                    "boost": 10
                                }
                            }
                        },
                        {
                            "match_phrase": {
                                "summary": {
                                    "query": query,
                                    "boost": 6
                                }
                            }
                        },
                        # Tìm kiếm mờ đa trường kết hợp với boost và fuzziness
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "title^4",
                                    "summary^2",
                                    "content",
                                    "category^2"
                                ],
                                "fuzziness": "AUTO",
                                "minimum_should_match": "70%"
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            size=30
        )
        
        # Lưu kết quả (có thể thêm "_score" để debug nếu cần)
        results = [hit["_source"] for hit in resp["hits"]["hits"]]
        # Chuyển _id thành id để dùng trong template
        for i, hit in enumerate(resp["hits"]["hits"]):
            if "_id" in hit:
                results[i]["id"] = hit["_id"]
    
    return render(request, "Search_news/search_results.html", {"results": results, "query": query})


# mục yêu thích
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from pymongo import MongoClient

@login_required
def favorite_article(request):
    if request.method == 'POST':
        article_id = request.POST.get('article_id')
        action = request.POST.get('action', 'add')  # Mặc định là thêm vào yêu thích
        user_id = str(request.user.id)
        client = MongoClient(settings.MONGO_URI)
        db = client['news_db']
        favorites = db['favorite_articles']
        
        if action == 'remove':
            # Xóa bài viết khỏi danh sách yêu thích
            favorites.delete_one({'user_id': user_id, 'article_id': article_id})
            return JsonResponse({'status': 'success'})
        else:
            # Thêm vào yêu thích (hành động mặc định)
            # Tránh lưu trùng
            if not favorites.find_one({'user_id': user_id, 'article_id': article_id}):
                favorites.insert_one({
                    'user_id': user_id,
                    'article_id': article_id,
                    'favorited_at': datetime.now()
                })
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

# lấy danh sách yêu thích
@login_required
def user_favorites(request):
    user_id = str(request.user.id)
    client = MongoClient(settings.MONGO_URI)
    db = client['news_db']
    favorites = db['favorite_articles']
    articles_col = db['vnexpress_articles']
    favorite_ids = [f['article_id'] for f in favorites.find({'user_id': user_id})]
    # Chuyển favorite_ids sang ObjectId nếu có thể
    object_ids = []
    for aid in favorite_ids:
        try:
            object_ids.append(ObjectId(aid))
        except Exception:
            pass
    articles = list(articles_col.find({'_id': {'$in': object_ids}}))
    # Chuyển _id thành id để dùng trong template
    for article in articles:
        if '_id' in article:
            article['id'] = str(article['_id'])
    return render(request, 'favorite/user_favorites.html', {'articles': articles})


# đề xuất bài báo yêu thích
@login_required
def recommend(request):
    user_id = str(request.user.id)
    client = MongoClient(settings.MONGO_URI)
    db = client['news_db']
    favorites = db['favorite_articles']
    articles_col = db['vnexpress_articles']

    # Lấy danh sách id bài đã yêu thích
    favorite_ids = [f['article_id'] for f in favorites.find({'user_id': user_id})]
    object_ids = []
    for aid in favorite_ids:
        try:
            object_ids.append(ObjectId(aid))
        except Exception:
            pass

    # Lấy tất cả bài đã yêu thích
    favorite_articles = list(articles_col.find({'_id': {'$in': object_ids}}))

    # Lấy tất cả category mà user đã từng yêu thích
    categories = list(set([a.get('category') for a in favorite_articles if a.get('category')]))

    recommended = []
    recommended_links = set()
    for cat in categories:
        # Lấy 5 bài mới nhất của mỗi chuyên mục, chưa yêu thích
        articles = list(articles_col.find({
            'category': cat,
            '_id': {'$nin': object_ids}
        }).sort('published_date', -1).limit(5))
        for article in articles:
            if '_id' in article:
                article['id'] = str(article['_id'])
            # Tránh trùng lặp bài báo
            link = article.get('url') or article.get('link')
            if link and link not in recommended_links:
                recommended.append(article)
                recommended_links.add(link)

    # Sắp xếp lại theo ngày đăng mới nhất (nếu có)
    recommended.sort(key=lambda x: x.get('published_date', ''), reverse=True)

    return render(request, 'favorite/recommend.html', {
        'articles': recommended
    })