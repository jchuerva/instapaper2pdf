#!/usr/bin/env python
# coding: utf-8

import requests
import time
from bs4 import BeautifulSoup
import pdfkit
import os
import pdb

BASE_URL = "https://www.instapaper.com/"
HOMEPAGE = BASE_URL + 'u/'
DEFAULT_OUTPUT_FOLDER = "./pdfs/homepage/"
CATEGORIES = [
  {"name": "react", "id": 4131451},
  {"name": "ruby", "id": 4131452},
  {"name": "tech", "id": 4131463},
  {"name": "food", "id": 4131464},
  {"name": "sports", "id": 4131465},
  {"name": "deno", "id": 4132578},
  {"name": "typescript", "id": 4134534},
  {"name": "golang", "id": 4137642},
  {"name": "photography", "id": 4202728},
  {"name": "career", "id": 4355149},
  ]


class Instapaper:
  def __init__(self):
    self.session = self._login()

  def _login(self):
    session = requests.Session()
    session.post("https://www.instapaper.com/user/login", data={
        "username": os.getenv('INSTAPAPER_USERNAME'),
        "password": os.getenv('INSTAPAPER_PASSWORD'),
        "keep_logged_in": "yes"
    })
    return session

  def _build_output_folder(self, subfolder):
    output_folder = DEFAULT_OUTPUT_FOLDER
    if subfolder is not None:
      output_folder = output_folder + subfolder + "/"

    # ensure the folder is created
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    return output_folder
  
  def _get_ids(self, page_url, page = 1):    
    request = self.session.get(page_url + str(page))
    soup = BeautifulSoup(request.text, "html.parser")

    articles = soup.find(id="article_list").find_all("article")
    ids = [i["id"].replace("article_", "") for i in articles]
    has_more = soup.find(class_="paginate_older") is not None
    return ids, has_more

  def _article_converted(self, id, output_folder):
    for file_name in os.listdir(output_folder):
        if file_name.startswith(id) and file_name.endswith(".pdf"):
            return output_folder + os.path.basename(file_name)
    return None

  def _get_article(self, id):
    url = "https://www.instapaper.com/read/" + str(id)
    print(url)
    r = self.session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.find(id="titlebar").find("h1").getText()
    origin = soup.find(id="titlebar").find(class_="origin_line").getText()
    content = soup.find(id="story").decode_contents()
    return {
        "title": title.strip(),
        "origin": origin.strip(),
        "content": content.strip()
    }

  def _download_article(self, id, output_folder):
    article = self._get_article(id)
    file_name = id + " " + article["title"]
    file_name = "".join([c for c in file_name if c.isalpha()
                        or c.isdigit() or c == " "]).rstrip()
    file_name = output_folder + file_name + ".html"

    print("DOWNLOAD_ARTICLE!!!" + file_name)

    with open(file_name, "w") as file:
        file.write("<h1>%s</h1>" % (article["title"]))
        file.write("<div id='origin'>%s · %s</div>" % (article["origin"], id))
        file.write(article["content"])

    return file_name

  def _failure_log(self, text):
    file = open("failed.txt", "a+")
    file.write(text)
    file.flush()

  def _remove_html(self, file_name):
    os.remove(file_name) 

  def _convert_to_pdf(self, file_name):
    new_name = file_name[:-5] + ".pdf"
    margin = "0.75in"
    options = {
      "page-size": "Letter",
      "margin-top": margin,
      "margin-right": margin,
      "margin-bottom": margin,
      "margin-left": margin,
      "encoding": "UTF-8",
      "no-outline": None,
      "user-style-sheet": "styles.css",
      "load-error-handling": "ignore",
      "quiet": "",
    }

    pdfkit.from_file(file_name, new_name, options=options)
    return new_name

  def get_articles(self, page_url, subfolder = None):
    has_more = True
    ini_page = 1

    # build output folder
    output_folder = self._build_output_folder(subfolder)

    while has_more:
      print(page_url + " - Page " + str(ini_page))
      ids, has_more = self._get_ids(page_url, ini_page)
      for id in ids:
          print("  " + id + ": ", end="")
          existing_file = self._article_converted(id, output_folder)
          if existing_file:
            print("exists")
          else:
            start = time.time()
            try:
              file_name = self._download_article(id, output_folder)
            except Exception as e:
              print("failed downloading the article!")
              self._failure_log("%s\t%s\n" % (id, str(e)))
              continue
              retries = 10
            while True:
              try:
                self._convert_to_pdf(file_name)
                os.remove(file_name) # remove html file
              except Exception as e:
                retries -= 1
                if retries < 0:
                  print("failed converting to pdf!")
                  print(e)
                  self._failure_log("%s\t%s\n" % (id, str(e)))
                  break
                continue
              break
            duration = time.time() - start
            print(str(round(duration, 2)) + " seconds")
            if duration < 1:  # wait a second
              time.sleep(1 - duration)
    ini_page += 1 


def get_all_categories():
  pages = [] #include home page by default
  for category in CATEGORIES:
    url = (BASE_URL + "u/folder/" + str(category["id"]) + "/" + category["name"])
    pages.append(url)

  return pages

def defined_local_envs():
  username = os.getenv('INSTAPAPER_USERNAME')
  password = os.getenv('INSTAPAPER_PASSWORD')

  if username is None or password is None:
    return False
  else:
    return True

def main():
  if defined_local_envs() is True:
    instapaper = Instapaper()
    _convert_homepage = instapaper.get_articles(HOMEPAGE)

    for category in CATEGORIES:
      subfolder = category["name"]
      url = BASE_URL + "u/folder/" + str(category["id"]) + "/" + category["name"]

      instapaper.get_articles(url, subfolder)
  else:
    print("You need to define the INSTAPAPER_USERNAME and INSTAPAPER_PASSWORD local env variables")


if __name__ == '__main__':
  main()