import requests
from bs4 import BeautifulSoup
import time
import speech_recognition as sr
from selenium import webdriver
from selenium.webdriver.common.by import By
import tkinter as tk
from pathlib import Path


def hasNextButton(url):
    # url受け取ってBSオブジェクトの作成
    html = requests.get(url)
    soup = BeautifulSoup(html.content, "html.parser")
    # 「次のページ」のidを探して取得
    bpol = soup.find(id="blog-pager-older-link")
    # なにもなければ「None」で, あるなら中身あるでよし
    if bpol is None:
        return False
    else:
        return True

# 検索結果画面のurlと空のsetを引数に入れ、詳細画面のurlが入ったsetを返す関数
def readResultHtml(targetUrl, urls):
    # レスポンスオブジェクトの作成
    html = requests.get(targetUrl)
    # BSオブジェクトの作成
    soup = BeautifulSoup(html.content, "html.parser")
    wb = soup.find(class_="widget Blog")
    for a in wb.find_all("a"):
        wb_a_href = a.get("href")
        if "/blog-post_" in wb_a_href and "#comment-form" not in wb_a_href:

            urls.add(wb_a_href)
    return urls

# 引数にしていされたキーワードをいらすとやで検索し、検索語のurlを返す
def search(keyword):
    # クロームの立ち上げ
    driver = webdriver.Chrome()
    # ページ接続
    driver.get('https://www.irasutoya.com/')
    # 入力欄を取得
    input = driver.find_element(By.NAME, "q")
    input.send_keys(keyword)
    # 検索ボタンの取得
    searchButton = driver.find_element(By.ID, "searchBtn")
    searchButton.click()
    # 今いるページのurlを取得する
    searchUrl = driver.current_url
    # 10秒終了を待つ
    time.sleep(1)
    # クロームの終了処理
    driver.close()
    # 検索した先のurlを返す
    return searchUrl

# 次へボタンがあるか判断し、なければfalseを返す
def hasNext(url):
    html = requests.get(url)
    soup = BeautifulSoup(html.content, "html.parser")
    judge = soup.find(id="blog-pager-older-link")

#     次へボタンが存在するか判定
    if judge is None:
        return False
    else:
        return True

# urlを次のページにこうしんする関数
def getNextURL(url):
    html = requests.get(url)
    soup = BeautifulSoup(html.content, "html.parser")

    nextURL = soup.find(id="blog-pager-older-link").find("a").get("href")

    return nextURL

# 詳細urlを全て取得しsetに格納後、setを返す
def getImagesFromKeyword(search_url):
    # print(search_url)
    result = set()
    while True:

        flag = hasNext(search_url)
        res = readResultHtml(search_url, result)
        print(f'res:{res}')
        for i in res:
            result.add(i)

        if flag:
            # 次のページのurlを取得
            search_url = getNextURL(search_url)
        else:
            break

    return result

def handleSpeechInput():
    recognizer = sr.Recognizer()
    text = None
    while True:
        # マイクから音声を連続録音
        with sr.Microphone() as source:
            print("音声を録音してください...（5秒以内）")
            audio_data = recognizer.listen(source, phrase_time_limit=5) #5秒で録音を停止する

        try:
            # 音声をテキストに変換
            text = recognizer.recognize_google(audio_data, language="ja-JP") # テキスト内容
            print("テキスト化結果: " + text)
            return text

        except sr.UnknownValueError:
            print("音声を理解できませんでした。")

        except sr.RequestError as e:
            print("音声認識サービスにアクセスできませんでした。")

# 詳細URLを引数で１つ受け取り、画像ページのURLを返す
def getImageUrl(detailsUrl):
    # 詳細ページにあるaタグの画像urlをセットで保存
    linkSet = set()

    html = requests.get(detailsUrl)
    content = BeautifulSoup(html.content, "html.parser")
    entry = content.find(class_="entry")

    for a in entry.find_all("a"):
        link = a.get("href")
        # downloadImage関数でlinkにアクセルするためhttps:がついていないリンクにはhttpsをつける
        if not link.startswith("https:"):
            link = "https:" + link

        linkSet.add(link)

    return linkSet

# 引数でgetImage関数から詳細ページから取得した画像ページのurlを取得(linkSetはセット型)
def downloadImage(linkSet):

    for imageURL in linkSet:

        imageData = requests.get(imageURL)

        out_folder = Path("tkImage")
        # フォルダを作成
        out_folder.mkdir(exist_ok=True)
#       ファイル名を指定
        filename = imageURL.split("/")[-1]
        out_path = out_folder.joinpath(filename)

#         画像をダウンロード
        with open(out_path, mode="wb") as f:
            f.write(imageData.content)

def speechText(): 

    # 音声入力を処理
    keyword = 'ロケット' #handleSpeechInput()
    if keyword is not None:
        search_url = search(keyword)
        print(f"検索結果のURL: {search_url}")

        # キーワードを使って画像を取得
        image_urls = getImagesFromKeyword(search_url)

        # 取得した画像が最大で何枚になるか表示する
        print(f"取得可能な画像の最大枚数: {len(image_urls)}")
    
    return image_urls



def startDownload(image_urls, max):
    # 取得した画像のURLをすべて表示する
    print("取得した画像のURL:")
    for idx, detail_url in enumerate(image_urls, 1):
        print('idx:{}, max{}'.format(idx, max))
        if idx > max:
            break
        print(f"Image {idx}: {detail_url}")
        # 詳細urlを受け取りその画像urlを返却
        url = getImageUrl(detail_url)
        #setに保存されたurlから画像をダウンロード
        downloadImage(url)

