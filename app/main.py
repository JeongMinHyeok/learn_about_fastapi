from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.models import mongodb
from app.models.book import BookModel
from app.book_scraper import NaverBookScraper

# from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="데이터 수집가", version="0.0.1")

# app.mount("/static", StaticFiles(directory="static"), name="static")
# mount: 일종의 미들웨어, css와 같은 static 파일을 동작


templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # book = BookModel(keyword="파이썬", publisher="BJPublic", price=1200, image="me.png")
    # print(await mongodb.engine.save(book))  # DB에 저장
    return templates.TemplateResponse(
        "./index.html",
        {"request": request, "title": "콜렉터 북북이"},
    )


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str):
    # 1. 쿼리에서 검색어 추출
    keyword = q
    # 예외처리
    # 검색어가 없을 경우 사용자에게 검색 요구
    if not keyword:
        return templates.TemplateResponse(
            "./index.html",
            {"request": request, "title": "콜렉터 북북이"},
        )
    # 해당 검색어에 대한 수집 데이터가 이미 DB에 있다면 해당 데이터를 return
    if await mongodb.engine.find_one(BookModel, BookModel.keyword == keyword):
        books = await mongodb.engine.find(BookModel, BookModel.keyword == keyword)
        return templates.TemplateResponse(
            "./index.html",
            {"request": request, "title": "콜렉터 북북이", "books": books},
        )
    # 2. 데이터 수집기로 해당 검색어에 대한 데이터 수집
    naver_book_scraper = NaverBookScraper()
    books = await naver_book_scraper.search(keyword, 10)
    book_models = []
    for book in books:
        book_model = BookModel(
            keyword=keyword,
            publisher=book["publisher"],
            price=book["discount"],
            image=book["image"],
        )
        book_models.append(book_model)

    # 3. 수집한 데이터를 DB에 저장
    await mongodb.engine.save_all(book_models)  # save_all: asyncio의 gather와 같은 기능

    return templates.TemplateResponse(
        request=request,
        context={"title": "콜렉터스 북북이", "keyword": q},
        name="index.html",
    )


@app.on_event("startup")  # 앱이 실행될 때 아래 함수 실행됨
def on_app_start():
    """before app starts"""
    mongodb.connect()


@app.on_event("shutdown")  # 앱이 종료될 때 아래 함수 실행됨
def on_app_shutdown():
    print("bye")
    """after app shutdown"""
    mongodb.close()


@app.get("/items/{id}", response_class=HTMLResponse)
# {id}: 다이나믹 URL, 해당 id가 아래 함수로 전달됨 context를 통해 전달
# response_class = HTMLResponse: return값으로 html 파일을 서빙한다는 뜻
async def read_item(request: Request, id: str):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"id": id, "hello": "hello"}
    )  # TemplateResponse는 request 키값이 필수
